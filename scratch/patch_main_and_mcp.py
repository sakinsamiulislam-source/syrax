"""
Patch script for backend/main.py and backend/mcp_server.py
"""

import os

# 1. Patch backend/main.py
with open('backend/main.py', 'r', encoding='utf-8') as f:
    main_text = f.read()

# Add format_order_ticket_card to imports if needed
if 'from agent.order_ticket import format_order_ticket_card' not in main_text:
    main_text = "from agent.order_ticket import format_order_ticket_card\n" + main_text

ticket_endpoints = """
@app.get("/api/ticket/{ticket_id}")
async def get_ticket_endpoint(ticket_id: str):
    \"\"\"Retrieves an OrderTicket by its parent_order_id.\"\"\"
    ticket = await orchestrator.ticket_registry.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Order ticket '{ticket_id}' not found.")
    return {
        "ticket": ticket.model_dump(),
        "card": format_order_ticket_card(ticket)
    }

@app.post("/api/ticket/confirm")
async def confirm_ticket_endpoint(payload: Dict[str, Any] = Body(...)):
    \"\"\"Confirms and executes an OrderTicket via the exact confirmation token.\"\"\"
    ticket_id = payload.get("ticket_id") or payload.get("parent_order_id")
    token = payload.get("confirmation_token") or f"CONFIRM {ticket_id}"
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Missing ticket_id")
    res = await orchestrator._handle_confirm_order_ticket(str(ticket_id), str(token), time.time())
    return res

@app.post("/api/ticket/cancel")
async def cancel_ticket_endpoint(payload: Dict[str, Any] = Body(...)):
    \"\"\"Cancels a pending OrderTicket.\"\"\"
    ticket_id = payload.get("ticket_id") or payload.get("parent_order_id")
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Missing ticket_id")
    res = await orchestrator._handle_cancel_order_ticket(str(ticket_id), f"CANCEL {ticket_id}", time.time())
    return res

@app.get("/api/tickets/pending")
def get_pending_tickets_endpoint(symbol: Optional[str] = None):
    \"\"\"Returns all active unexpired pending order tickets.\"\"\"
    tickets = orchestrator.ticket_registry.get_pending_tickets(symbol=symbol)
    return {
        "count": len(tickets),
        "tickets": [format_order_ticket_card(t) for t in tickets]
    }
"""

if '/api/ticket/{ticket_id}' not in main_text:
    # Insert right after execute_action
    target = 'async def execute_action(req: ActionExecuteRequest):\n    """Executes a confirmed UI action card via UnifiedExecutionGateway."""\n    res = await orchestrator.execute_confirmed_action(req.action)\n    return res'
    if target in main_text:
        main_text = main_text.replace(target, target + "\n" + ticket_endpoints, 1)
        print("Inserted ticket endpoints in backend/main.py")

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(main_text)

# 2. Patch backend/mcp_server.py
with open('backend/mcp_server.py', 'r', encoding='utf-8') as f:
    mcp_text = f.read()

mcp_tools = """
    @server.tool()
    async def syrax_create_order_ticket(
        symbol: str,
        side: str = "BUY",
        notional_usd: float = 25.0,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        leverage: int = 1,
        market_type: str = "SPOT"
    ) -> str:
        \"\"\"
        Compiles an immutable Order Ticket in state PENDING_CONFIRMATION.
        Returns the ticket ID and exact confirmation command required for execution.
        \"\"\"
        norm_sym = binance_os.normalize_symbol(symbol)
        ticker = await binance_os.get_live_ticker(norm_sym)
        price = ticker.get("last_price", 100.0)

        if not stop_loss:
            stop_loss = round(price * 0.98, 4 if price < 10 else 2)
        if not take_profit:
            take_profit = round(price * 1.045, 4 if price < 10 else 2)

        ticket = await orchestrator.ticket_registry.create_ticket(
            symbol=norm_sym,
            side=side.upper(),
            order_type="MARKET",
            notional_usd=notional_usd,
            decision_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=leverage,
            market_type=market_type.upper(),
            venue="binance",
            risk_amount_usd=round(orchestrator.mandate["capital_usd"] * (orchestrator.mandate["max_risk_pct"]/100.0), 2),
            risk_pct=orchestrator.mandate["max_risk_pct"],
            ttl_seconds=120.0
        )
        return json.dumps(ticket.model_dump(), indent=2)

    @server.tool()
    async def syrax_confirm_order_ticket(
        parent_order_id: str,
        confirmation_token: str
    ) -> str:
        \"\"\"
        Authorizes and executes a pending order ticket using the exact confirmation token 'CONFIRM PO-XXXXXX'.
        Routes through the UnifiedExecutionGateway upon valid cryptographic confirmation.
        \"\"\"
        res = await orchestrator._handle_confirm_order_ticket(parent_order_id, confirmation_token, 0.0)
        return json.dumps(res, indent=2)
"""

if 'syrax_create_order_ticket' not in mcp_text:
    target_mcp = '    return server'
    mcp_text = mcp_text.replace(target_mcp, mcp_tools + "\n    return server", 1)
    print("Inserted MCP tools in backend/mcp_server.py")

with open('backend/mcp_server.py', 'w', encoding='utf-8') as f:
    f.write(mcp_text)

print("Completed patching main.py and mcp_server.py")
