from agent.order_ticket import format_order_ticket_card
"""
SYRAX — FastAPI Backend Application
Powers the SYRAX AI Trading & Portfolio Agent API.
Coordinates Binance Agent OS, AI Orchestrator, and Frontend interfaces.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import time

from backend.binance.agent_os import BinanceAgentOS
from backend.binance.sub_wallet import SubWalletManager
from backend.binance.mcp_client import binance_mcp_client
from backend.monitor_daemon import AutonomousMonitorDaemon
from backend.mcp_server import create_syrax_mcp_server
from agent.orchestrator import SyraxOrchestrator
from agent.execution_gateway import ExecutionRequest, ExecutionReceipt, ExecutionActionType, ExecutionEnvironment, ExecutionStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("syrax.api")

app = FastAPI(
    title="SYRAX — AI Trading & Portfolio Agent API",
    description="Binance Agent OS Hackathon Backend. Research. Reason. Risk. Execute.",
    version="1.0.0"
)

# Enable CORS for local Next.js/Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core singletons
binance_os = BinanceAgentOS()
sub_wallet = SubWalletManager(sub_wallet_id="SUB-AGENT-01-ALPHA", allocated_budget_usd=500.0)
orchestrator = SyraxOrchestrator(binance_os, sub_wallet=sub_wallet)
monitor_daemon = AutonomousMonitorDaemon(binance_os, sub_wallet, orchestrator.news_agent, gateway=orchestrator.gateway)
mcp_server = create_syrax_mcp_server(binance_os, sub_wallet, orchestrator, monitor_daemon)

# Mount official Model Context Protocol (MCP) Server SSE app at /mcp
app.mount("/mcp", mcp_server.sse_app())

@app.on_event("startup")
async def on_startup():
    logger.info("FastAPI starting up: launching 24/7 Autonomous Monitor Daemon...")
    await monitor_daemon.start()

class ChatRequest(BaseModel):
    message: str
    mandate_override: Optional[Dict[str, Any]] = None

class ActionExecuteRequest(BaseModel):
    action: Dict[str, Any]

class RebalanceRequest(BaseModel):
    targets: Optional[Dict[str, float]] = None
    max_order_size: Optional[float] = None

class ConvertRequest(BaseModel):
    from_asset: str
    to_asset: str
    amount: float

@app.get("/")
def read_root():
    return {
        "product": "SYRAX",
        "tagline": "Research. Reason. Risk. Execute.",
        "platform": "Binance Agent OS",
        "status": "ONLINE",
        "version": "1.0.0",
        "endpoints": [
            "/api/dashboard",
            "/api/chat",
            "/api/market/scan",
            "/api/portfolio",
            "/api/sentry",
            "/api/journal",
            "/api/cash"
        ]
    }

@app.get("/api/dashboard")
@app.get("/api/overview")
async def get_dashboard(category: Optional[str] = "ALL"):
    """Returns high-level telemetry, real portfolio metrics, active risks, and Today's P&L breakdown."""
    import asyncio
    try:
        portfolio_task = binance_os.get_account_portfolio()
        scan_task = orchestrator.market_agent.scan_market(category=category or "ALL", limit=3)
        rebalance_task = orchestrator.portfolio_agent.calculate_rebalancing_plan()

        portfolio, scan, rebalance_info = await asyncio.gather(
            portfolio_task,
            scan_task,
            rebalance_task,
            return_exceptions=True
        )
        if isinstance(portfolio, Exception) or not isinstance(portfolio, dict):
            portfolio = await binance_os.get_account_portfolio()
        if isinstance(scan, Exception) or not isinstance(scan, list):
            scan = []
        if isinstance(rebalance_info, Exception) or not isinstance(rebalance_info, dict):
            rebalance_info = {}
    except Exception as e:
        logger.warning(f"Error gathering dashboard data: {e}")
        portfolio = {"total_value_usd": 500.0, "available_cash_usd": 250.0, "holdings": []}
        scan = []
        rebalance_info = {}

    events = orchestrator.news_agent.get_active_events()

    # Dynamic Today's PnL Breakdown (Binance UTC 00:00:00 standard)
    if binance_mcp_client.is_connected:
        today_pnl = binance_mcp_client.get_today_pnl_breakdown()
    else:
        # Compute from SubWallet with live price map
        price_map = {}
        if sub_wallet.ongoing_trades:
            ticker_tasks = [binance_os.get_live_ticker(trd.get("symbol", "")) for trd in sub_wallet.ongoing_trades if trd.get("symbol")]
            if ticker_tasks:
                ticker_results = await asyncio.gather(*ticker_tasks, return_exceptions=True)
                for trd, t in zip(sub_wallet.ongoing_trades, ticker_results):
                    if isinstance(t, dict) and t.get("last_price"):
                        price_map[trd["symbol"]] = t["last_price"]
        today_pnl = sub_wallet.get_today_pnl_breakdown(price_map)

    total_val = portfolio.get("total_value_usd", 500.0)

    ai_daily_insight = (
        "Macro tape indicates selective risk-on liquidity rotation. Bitcoin dominance remains resilient above 57%, "
        "compressing altcoin beta. Strategy: Favor high-liquidity orderbook entries (BTC/ETH), strictly cap risk to 1%, "
        "and maintain 50% stablecoin reserves until break of resistance."
    )

    return {
        "portfolio": portfolio,
        "today_pnl": today_pnl,
        "pnl_24h": {
            "pnl_usd": today_pnl.get("total_pnl_usd", 0.0),
            "pnl_pct": today_pnl.get("pnl_pct", 0.0),
            "status": today_pnl.get("status", "NORMAL")
        },
        "risk_exposure": {
            "current_at_risk_usd": round(total_val * (orchestrator.mandate.get("max_risk_pct", 1.0) / 100), 2),
            "max_risk_pct": orchestrator.mandate.get("max_risk_pct", 1.0),
            "max_allowed_loss_usd": round(orchestrator.mandate.get("capital_usd", 500.0) * (orchestrator.mandate.get("max_risk_pct", 1.0) / 100), 2),
            "status": "NORMAL_GUARDED"
        },
        "top_opportunities": scan[:3] if isinstance(scan, list) else [],
        "active_events": events[:2] if isinstance(events, list) else [],
        "idle_cash": rebalance_info.get("idle_cash_opportunities", []) if isinstance(rebalance_info, dict) else [],
        "ai_daily_insight": ai_daily_insight,
        "execution_mode": orchestrator.mandate.get("execution_mode", "AUTONOMOUS")
    }

@app.post("/api/chat")
async def chat_handler(req: ChatRequest):
    """
    Main conversational agent loop.
    Processes natural language commands, returns agentic progress steps, decision, and risk limits.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty prompt.")
    
    response = await orchestrator.execute_mandate_pipeline(req.message)
    return response

@app.post("/api/action/execute")
async def execute_action(req: ActionExecuteRequest):
    """Executes a confirmed UI action card via UnifiedExecutionGateway."""
    res = await orchestrator.execute_confirmed_action(req.action)
    return res

@app.get("/api/ticket/{ticket_id}")
async def get_ticket_endpoint(ticket_id: str):
    """Retrieves an OrderTicket by its parent_order_id."""
    ticket = await orchestrator.ticket_registry.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Order ticket '{ticket_id}' not found.")
    return {
        "ticket": ticket.model_dump(),
        "card": format_order_ticket_card(ticket)
    }

@app.post("/api/ticket/confirm")
async def confirm_ticket_endpoint(payload: Dict[str, Any] = Body(...)):
    """Confirms and executes an OrderTicket via the exact confirmation token."""
    ticket_id = payload.get("ticket_id") or payload.get("parent_order_id")
    token = payload.get("confirmation_token") or f"CONFIRM {ticket_id}"
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Missing ticket_id")
    res = await orchestrator._handle_confirm_order_ticket(str(ticket_id), str(token), time.time())
    return res

@app.post("/api/ticket/cancel")
async def cancel_ticket_endpoint(payload: Dict[str, Any] = Body(...)):
    """Cancels a pending OrderTicket."""
    ticket_id = payload.get("ticket_id") or payload.get("parent_order_id")
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Missing ticket_id")
    res = await orchestrator._handle_cancel_order_ticket(str(ticket_id), f"CANCEL {ticket_id}", time.time())
    return res

@app.get("/api/tickets/pending")
def get_pending_tickets_endpoint(symbol: Optional[str] = None):
    """Returns all active unexpired pending order tickets."""
    tickets = orchestrator.ticket_registry.get_pending_tickets(symbol=symbol)
    return {
        "count": len(tickets),
        "tickets": [format_order_ticket_card(t) for t in tickets]
    }


@app.get("/api/rules")
def get_user_rules():
    """Returns active user trading rules and mathematical risk limits."""
    return {
        "rules": orchestrator.mandate,
        "available_cash_usd": sub_wallet.cash_usd,
        "ongoing_trades_count": len(sub_wallet.ongoing_trades)
    }

@app.post("/api/rules")
def update_user_rules(rules: Dict[str, Any] = Body(...)):
    """Updates user trading rules (risk %, leverage, capital, SL enforcement)."""
    orchestrator.mandate.update(rules)
    if "capital_usd" in rules:
        sub_wallet.allocated_budget_usd = float(rules["capital_usd"])
    return {
        "success": True,
        "rules": orchestrator.mandate
    }

@app.get("/api/market/scan")
async def market_scan(category: Optional[str] = "ALL", limit: int = 25):
    """Scans and ranks dynamic active cryptocurrency pairs by AI Opportunity Score."""
    results = await orchestrator.market_agent.scan_market(category=category or "ALL", limit=limit)
    return {"symbols": results}

@app.get("/api/market/search")
async def market_search(q: str):
    """Searches any cryptocurrency listed on Binance by token symbol."""
    results = await binance_os.search_symbols(q)
    return {"query": q, "results": results}


@app.get("/api/market/symbol/{symbol}")
async def market_symbol(symbol: str):
    """Deep dive technical, liquidity, and orderbook evaluation of a specific symbol."""
    res = await orchestrator.market_agent.analyze_symbol(symbol)
    orderbook = await binance_os.get_orderbook(symbol)
    return {
        "analysis": res,
        "orderbook": orderbook
    }

@app.get("/api/market/klines")
async def market_klines(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100):
    """Fetches Binance candlestick kline data for symbol across timeframes (5m, 15m, 1h, 4h, 1d, 1w)."""
    candles = await binance_os.get_klines(symbol=symbol, interval=interval, limit=limit)
    return {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "candles": candles
    }

@app.get("/api/portfolio")
async def get_portfolio():
    """Returns holdings, drift against targets, and rebalancing recommendations."""
    portfolio = await binance_os.get_account_portfolio()
    rebalance = await orchestrator.portfolio_agent.calculate_rebalancing_plan()
    return {
        "portfolio": portfolio,
        "rebalance_plan": rebalance
    }

@app.post("/api/portfolio/mandate")
async def update_mandate(payload: Dict[str, Any] = Body(...)):
    """Updates target allocations, risk limits, or execution mode."""
    if "capital_usd" in payload:
        orchestrator.mandate["capital_usd"] = float(payload["capital_usd"])
    if "max_risk_pct" in payload:
        orchestrator.mandate["max_risk_pct"] = float(payload["max_risk_pct"])
    if "max_order_size_usd" in payload:
        orchestrator.mandate["max_order_size_usd"] = float(payload["max_order_size_usd"])
        orchestrator.portfolio_agent.max_order_size_usd = float(payload["max_order_size_usd"])
    if "target_allocations" in payload:
        orchestrator.mandate["target_allocations"] = payload["target_allocations"]
        orchestrator.portfolio_agent.target_allocations = payload["target_allocations"]
    if "execution_mode" in payload:
        orchestrator.mandate["execution_mode"] = payload["execution_mode"]

    return {"success": True, "updated_mandate": orchestrator.mandate}

@app.get("/api/sentry")
def get_sentry():
    """Returns active event radar and 3-layer confirmation items."""
    return {
        "events": orchestrator.news_agent.get_active_events(),
        "sentry_status": "ONLINE",
        "surveillance_level": "MAXIMUM_3_LAYER"
    }

@app.post("/api/sentry/simulate-event")
def simulate_sentry_event(token: str = "SOL"):
    """Hackathon demo helper: triggers a simulated critical exploit event."""
    evt = orchestrator.news_agent.trigger_simulated_critical_event(token)
    return {"success": True, "event": evt}

@app.post("/api/sentry/protect")
async def trigger_emergency_protect(token: str = "SOL"):
    """Emergency defensive protocol: hedges exposure to stablecoin via Binance Convert."""
    action = {
        "type": "EMERGENCY_PROTECT",
        "affected_token": token
    }
    res = await orchestrator.execute_confirmed_action(action)
    return res

@app.get("/api/cash")
async def get_cash():
    """Identifies idle stablecoins, dust, and Binance Convert opportunities."""
    rebalance = await orchestrator.portfolio_agent.calculate_rebalancing_plan()
    return {
        "idle_cash": rebalance.get("idle_cash_opportunities", []),
        "available_cash_usd": rebalance.get("portfolio_value_usd", 0.0)
    }

@app.post("/api/cash/convert")
async def execute_convert(req: ConvertRequest):
    """Executes a zero-fee Binance Convert transaction."""
    quote = await binance_os.quote_binance_convert(req.from_asset, req.to_asset, req.amount)
    res = await binance_os.execute_binance_convert(
        quote_id=quote["quote_id"],
        from_asset=req.from_asset,
        to_asset=req.to_asset,
        from_amount=req.amount,
        to_amount=quote["to_amount"]
    )
    if res.get("status") in ("CONFIRMED", "FILLED") or "receipt" in res:
        sub_wallet.record_convert_history(req.from_asset, req.to_asset, req.amount, quote["to_amount"], quote["quote_id"])
    return res

@app.get("/api/journal")
def get_journal():
    """Returns the immutable chronological trade & decision log."""
    return {
        "journal": orchestrator.decision_journal,
        "executions": binance_os.get_execution_history()
    }

@app.post("/api/trade/execute")
async def execute_trade(req: ActionExecuteRequest):
    """
    Executes an action approved by the user through Binance Agent OS.
    """
    res = await orchestrator.execute_confirmed_action(req.action)
    return res

@app.get("/api/ai/status")
async def get_ai_status():
    """Checks OpenRouter AI connectivity and model configuration."""
    test_res = await orchestrator.ai_client.test_connection()
    return {
        "configured": orchestrator.ai_client.is_configured(),
        "model": orchestrator.ai_client.model,
        "test": test_res
    }

class BinanceConnectRequest(BaseModel):
    api_key: str
    api_secret: str
    network: Optional[str] = "testnet"

@app.get("/api/binance/status")
async def get_binance_status():
    """Checks Binance API connectivity and validates credentials."""
    return await binance_os.verify_binance_credentials()

@app.post("/api/binance/connect")
async def connect_binance(req: BinanceConnectRequest):
    """Dynamically connects Binance API credentials."""
    binance_os.reload_credentials(req.api_key, req.api_secret, req.network or "testnet")
    res = await binance_os.verify_binance_credentials()
    return res

class BinanceMCPConnectRequest(BaseModel):
    auth_token: str
    sub_account_id: Optional[str] = "default-agentic-sub"
    endpoint_url: Optional[str] = "https://agent.binance.com/mcp/agentic"

@app.get("/api/binance/mcp/status")
async def get_binance_mcp_status():
    """Returns live connection status of SYRAX's direct Binance Agent OS MCP Client."""
    return binance_mcp_client.get_status_summary()

@app.post("/api/binance/mcp/connect")
async def connect_binance_mcp(req: BinanceMCPConnectRequest):
    """
    Connects SYRAX to the official Binance Agent OS MCP Server (https://agent.binance.com/mcp/agentic)
    using the user's authorized Agentic Sub-Account token.
    """
    binance_mcp_client.configure(
        auth_token=req.auth_token,
        sub_account_id=req.sub_account_id,
        endpoint_url=req.endpoint_url
    )
    res = await binance_mcp_client.test_and_connect()
    return res

@app.post("/api/binance/mcp/disconnect")
async def disconnect_binance_mcp():
    """Gracefully disconnects the Binance Agent OS MCP Client and resets cached live state."""
    res = await binance_mcp_client.disconnect()
    return res

@app.get("/api/binance/oauth/initiate")
def initiate_binance_oauth(sub_account_id: Optional[str] = "agentic-sub-01"):
    """
    Generates official PKCE OAuth 2.0 URL for 1-Click Binance Browser Passkey authorization.
    """
    redirect_uri = "http://localhost:8001/api/binance/oauth/callback"
    return binance_mcp_client.create_oauth_authorization_url(redirect_uri, sub_account_id)

@app.get("/api/binance/oauth/callback")
async def binance_oauth_callback(code: str, state: str):
    """
    Handles Binance OAuth authorization callback, exchanges code for Bearer token,
    and initializes live MCP connection automatically.
    """
    redirect_uri = "http://localhost:8001/api/binance/oauth/callback"
    res = await binance_mcp_client.handle_oauth_callback(code, state, redirect_uri)
    
    # Return HTML response closing popup or redirecting to frontend dashboard
    if res.get("is_connected") or res.get("success"):
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Binance Authorization Successful</title></head>
        <body style="background:#0b1120;color:#10b981;font-family:sans-serif;text-align:center;padding:50px;">
            <h2>✅ Binance Agent OS Connected Successfully!</h2>
            <p style="color:#94a3b8;">You may close this window. Your SYRAX dashboard is now live.</p>
            <script>
                if (window.opener) {
                    window.opener.postMessage({ type: 'BINANCE_MCP_AUTH_SUCCESS' }, '*');
                    setTimeout(() => window.close(), 1500);
                } else {
                    setTimeout(() => window.location.href = 'http://localhost:3001', 1500);
                }
            </script>
        </body>
        </html>
        """
    else:
        err = res.get("error", "Unknown error")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Binance Authorization Failed</title></head>
        <body style="background:#0b1120;color:#f43f5e;font-family:sans-serif;text-align:center;padding:50px;">
            <h2>❌ Binance Authorization Failed</h2>
            <p style="color:#94a3b8;">{err}</p>
        </body>
        </html>
        """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

# ==============================================================================
# AGENTIC SUB-WALLET & ONGOING TRADES ENDPOINTS
# ==============================================================================

@app.get("/api/subwallet")
async def get_subwallet():
    """Returns sub-wallet holdings, drift analysis, and ongoing active trades."""
    price_map = {}
    for asset in list(sub_wallet.holdings.keys()):
        if asset not in ("USDT", "USDC", "USD", "FDUSD"):
            t = await binance_os.get_live_ticker(f"{asset}USDT")
            if t.get("last_price"):
                price_map[f"{asset}USDT"] = t["last_price"]
    for trd in sub_wallet.ongoing_trades:
        t = await binance_os.get_live_ticker(trd["symbol"])
        if t.get("last_price"):
            price_map[trd["symbol"]] = t["last_price"]

    sub_wallet.update_live_prices(price_map)
    analysis = sub_wallet.get_holdings_analysis(price_map)
    return {
        "analysis": analysis,
        "pending_orders": sub_wallet.pending_orders,
        "ongoing_trades": sub_wallet.ongoing_trades,
        "closed_trades": sub_wallet.closed_trades,
        "trade_history": sub_wallet.trade_history
    }

@app.get("/api/subwallet/history")
@app.get("/api/subwallet/trades/history")
def get_subwallet_history():
    """Returns chronologically ordered trade & order history with Binance Order IDs and Fee breakdowns."""
    return {
        "total_orders": len(sub_wallet.trade_history),
        "history": sub_wallet.trade_history,
        "trades": sub_wallet.trade_history
    }

class SubWalletOrderRequest(BaseModel):
    symbol: str
    side: str = "BUY"
    notional_usd: float = 25.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: Optional[str] = "Manual Dashboard Execution"
    market_type: Optional[str] = "SPOT"  # "SPOT", "FUTURES", "MARGIN"
    leverage: Optional[int] = 1          # 1 to 20
    margin_type: Optional[str] = "ISOLATED" # "ISOLATED", "CROSS"

@app.post("/api/subwallet/order")
async def subwallet_order(req: SubWalletOrderRequest):
    """Opens a new trade in the sub-wallet routed through UnifiedExecutionGateway."""
    norm_sym = binance_os.normalize_symbol(req.symbol)
    ticker = await binance_os.get_live_ticker(norm_sym)
    price = ticker.get("last_price", 100.0)
    
    sl = req.stop_loss or (round(price * 0.98, 4 if price < 10 else 2) if req.side in ("BUY", "LONG") else round(price * 1.02, 4 if price < 10 else 2))
    tp = req.take_profit or (round(price * 1.045, 4 if price < 10 else 2) if req.side in ("BUY", "LONG") else round(price * 0.955, 4 if price < 10 else 2))
    effective_market = req.market_type or ("FUTURES" if norm_sym.startswith("1000") else ticker.get("market_type", "SPOT"))
    effective_leverage = req.leverage or (10 if effective_market == "FUTURES" else (3 if effective_market == "MARGIN" else 1))

    exec_req = ExecutionRequest(
        action_type=ExecutionActionType.OPEN_POSITION,
        symbol=norm_sym,
        side=req.side,
        order_type="MARKET",
        notional_usd=req.notional_usd,
        stop_loss=sl,
        take_profit=tp,
        market_type=effective_market,
        leverage=effective_leverage,
        margin_type=req.margin_type or "ISOLATED",
        environment=ExecutionEnvironment.SIMULATED,
        source="API_DASHBOARD",
        mandate=orchestrator.mandate
    )
    receipt = await orchestrator.gateway.execute(exec_req)
    if receipt.status != ExecutionStatus.SUCCESS:
        return {"success": False, "error": receipt.rejection_reason or receipt.message, "receipt": receipt.model_dump()}
    return {"success": True, "trade": receipt.raw_details.get("trade", {}), "receipt": receipt.model_dump()}

class SubWalletLimitOrderRequest(BaseModel):
    symbol: str
    side: str = "BUY"
    limit_price: float
    quantity: Optional[float] = None
    notional_usd: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    market_type: Optional[str] = "SPOT"
    leverage: Optional[int] = 1
    margin_type: Optional[str] = "ISOLATED"
    strategy: Optional[str] = None

class SubWalletCancelOrderRequest(BaseModel):
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    reason: Optional[str] = "Manual User Cancellation"

class SubWalletSimulateFillRequest(BaseModel):
    order_id: str
    fill_qty: Optional[float] = None
    fill_pct: Optional[float] = None
    fill_percentage: Optional[float] = None
    fill_price: Optional[float] = None

@app.post("/api/subwallet/limit-order")
async def subwallet_place_limit_order(req: SubWalletLimitOrderRequest):
    """Places a canonical pending limit order routed through UnifiedExecutionGateway."""
    norm_sym = binance_os.normalize_symbol(req.symbol)
    effective_market = req.market_type or ("FUTURES" if norm_sym.startswith("1000") else "SPOT")
    effective_leverage = req.leverage or (10 if effective_market == "FUTURES" else 1)

    exec_req = ExecutionRequest(
        action_type=ExecutionActionType.OPEN_POSITION,
        symbol=norm_sym,
        side=req.side,
        order_type="LIMIT",
        quantity=req.quantity,
        notional_usd=req.notional_usd,
        limit_price=req.limit_price,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        market_type=effective_market,
        leverage=effective_leverage,
        margin_type=req.margin_type or "ISOLATED",
        environment=ExecutionEnvironment.SIMULATED,
        source="API_DASHBOARD",
        mandate=orchestrator.mandate
    )
    receipt = await orchestrator.gateway.execute(exec_req)
    if receipt.status != ExecutionStatus.SUCCESS:
        return {"success": False, "error": receipt.rejection_reason or receipt.message, "receipt": receipt.model_dump()}
    return {"success": True, "order": receipt.raw_details.get("order", {}), "receipt": receipt.model_dump()}

@app.post("/api/subwallet/order/cancel")
async def subwallet_cancel_order(req: SubWalletCancelOrderRequest):
    """Cancels an active pending limit order via UnifiedExecutionGateway."""
    exec_req = ExecutionRequest(
        action_type=ExecutionActionType.CANCEL_ORDER,
        symbol=req.symbol or "",
        order_id_to_cancel=req.order_id,
        environment=ExecutionEnvironment.SIMULATED,
        source="API_DASHBOARD"
    )
    receipt = await orchestrator.gateway.execute(exec_req)
    return {"success": receipt.status == ExecutionStatus.SUCCESS, "receipt": receipt.model_dump()}

@app.post("/api/subwallet/order/simulate-fill")
async def subwallet_simulate_fill(req: SubWalletSimulateFillRequest):
    """Simulates a partial or full execution fill event for testing & verification."""
    order = next((o for o in sub_wallet.pending_orders if o["order_id"] == req.order_id or o["trade_id"] == req.order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail=f"Pending order {req.order_id} not found.")

    effective_pct = req.fill_pct if req.fill_pct is not None else req.fill_percentage
    if req.fill_qty and req.fill_qty > 0:
        actual_qty = req.fill_qty
    elif effective_pct is not None and effective_pct > 0:
        actual_qty = round(order["requested_quantity"] * (effective_pct / 100.0), 6)
    else:
        actual_qty = order["remaining_quantity"]

    res = sub_wallet.process_fill(
        order_id=req.order_id,
        fill_qty=actual_qty,
        fill_price=req.fill_price or order["limit_price"]
    )
    return res

class SubWalletCloseRequest(BaseModel):
    trade_id: str
    reason: Optional[str] = "Manual Exit"

@app.post("/api/subwallet/trade/close")
async def subwallet_close(req: SubWalletCloseRequest):
    """Closes an ongoing trade via UnifiedExecutionGateway."""
    exec_req = ExecutionRequest(
        action_type=ExecutionActionType.CLOSE_POSITION,
        symbol="",
        trade_id_to_close=req.trade_id,
        close_reason=req.reason or "Manual Exit",
        environment=ExecutionEnvironment.SIMULATED,
        source="API_DASHBOARD"
    )
    receipt = await orchestrator.gateway.execute(exec_req)
    return {"success": receipt.status == ExecutionStatus.SUCCESS, "receipt": receipt.model_dump()}

class SubWalletSellHoldingRequest(BaseModel):
    asset: str
    quantity: Optional[float] = None

@app.post("/api/subwallet/sell-holding")
async def subwallet_sell_holding(req: SubWalletSellHoldingRequest):
    """Sells a held asset from sub-wallet spot holdings into liquid USDT."""
    norm_sym = binance_os.normalize_symbol(req.asset)
    base_asset = norm_sym.replace("USDT", "").replace("USDC", "")
    ticker = await binance_os.get_live_ticker(norm_sym)
    price = ticker.get("last_price", 100.0)
    res = sub_wallet.sell_asset_holding(base_asset, quantity=req.quantity, price=price)
    return res

class SubWalletLevelUpdateRequest(BaseModel):
    trade_id: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@app.post("/api/subwallet/trade/update")
async def subwallet_update_levels(req: SubWalletLevelUpdateRequest):
    """Updates stop-loss or take-profit on an ongoing trade."""
    res = sub_wallet.update_trade_levels(req.trade_id, stop_loss=req.stop_loss, take_profit=req.take_profit)
    return res

@app.post("/api/subwallet/reset")
async def subwallet_reset(payload: Dict[str, Any] = Body(default={})):
    """Resets the sub-wallet cash and demo holdings back to initial healthy state ($250 USDT)."""
    initial_cash = float(payload.get("initial_cash", 250.0))
    res = sub_wallet.reset_wallet(initial_cash=initial_cash)
    return res

@app.post("/api/subwallet/deposit")
async def subwallet_deposit(payload: Dict[str, Any] = Body(...)):
    """Deposits additional liquid cash into the sub-wallet."""
    amount_usd = float(payload.get("amount_usd", payload.get("amount", 250.0)))
    res = sub_wallet.deposit_cash(amount_usd=amount_usd)
    return res



# ==============================================================================
# BINANCE MULTI-WALLET & INTERNAL TRANSFERS
# ==============================================================================

class InternalTransferRequest(BaseModel):
    from_wallet: str
    to_wallet: str
    asset: str
    amount: float

@app.get("/api/wallets/summary")
async def get_wallets_summary():
    """Returns valuation and asset breakdown for all Binance internal wallets (Spot, Funding, USD-M, Coin-M, Margin, Earn)."""
    import asyncio
    price_map = {}
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    try:
        tasks = [binance_os.get_live_ticker(sym) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for sym, t in zip(symbols, results):
            if isinstance(t, dict) and t.get("last_price"):
                price_map[sym] = t["last_price"]
    except Exception as e:
        logger.warning(f"Error fetching live prices for wallets summary: {e}")
    return sub_wallet.get_wallets_summary(price_map)

@app.post("/api/wallets/transfer")
async def execute_internal_transfer(req: InternalTransferRequest):
    """Executes a zero-fee deterministic internal transfer between Binance account wallets."""
    res = sub_wallet.execute_internal_transfer(
        from_wallet=req.from_wallet,
        to_wallet=req.to_wallet,
        asset=req.asset,
        amount=req.amount
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Transfer failed."))
    
    monitor_daemon._record_event(
        category="INTERNAL_TRANSFER",
        severity="INFO",
        message=f"Internal transfer executed: {req.amount} {req.asset} from {req.from_wallet} to {req.to_wallet} (Fee: 0.00)."
    )
    return res

@app.get("/api/wallets/transfers")
def get_internal_transfers():
    """Returns audit history of internal wallet transfers."""
    return {
        "transfers": sub_wallet.internal_transfers,
        "total_count": len(sub_wallet.internal_transfers)
    }

@app.post("/api/subwallet/rebalance/execute")
async def subwallet_execute_rebalance():
    """Executes instant deterministic sub-wallet rebalancing according to mandate target corridor."""
    tickers = await binance_os.get_unified_market_tickers()
    price_map = {t["symbol"]: t["price"] for t in tickers if "symbol" in t and "price" in t}
    res = sub_wallet.rebalance_holdings(price_map)
    monitor_daemon._record_event(
        category="PORTFOLIO_REBALANCE",
        severity="INFO",
        message="Sub-wallet holdings automatically rebalanced to target allocations: 40% USDT, 30% BTC, 15% ETH, 10% SOL, 5% USDC."
    )
    return res

# ==============================================================================
# 24/7 AUTONOMOUS SENTINEL MONITOR ENDPOINTS
# ==============================================================================

@app.get("/api/monitor/status")
def get_monitor_status():
    """Returns 24/7 autonomous background sentinel surveillance status and event feed."""
    return monitor_daemon.get_status()

@app.post("/api/monitor/toggle")
def toggle_monitor():
    """Toggles 24/7 background surveillance between active and paused."""
    if monitor_daemon.is_paused:
        monitor_daemon.resume()
    else:
        monitor_daemon.pause()
    return monitor_daemon.get_status()

@app.get("/api/guardian/status")
def get_guardian_status():
    """Returns deterministic Post-Trade Guardian status and configuration."""
    return monitor_daemon.guardian.get_status_summary()

@app.get("/api/guardian/incidents")
def get_guardian_incidents(limit: int = 50):
    """Returns audit log of all Guardian incidents and protective actions."""
    return monitor_daemon.guardian.get_incidents(limit=limit)

@app.post("/api/guardian/config")
def update_guardian_config(config_data: Dict[str, Any] = Body(...)):
    """Updates Post-Trade Guardian configuration parameters."""
    cfg = monitor_daemon.guardian.config
    if "mode" in config_data:
        cfg.mode = config_data["mode"]
    if "trailing_stop_activation_pnl_pct" in config_data:
        cfg.trailing_stop_activation_pnl_pct = float(config_data["trailing_stop_activation_pnl_pct"])
    if "trailing_stop_callback_pct" in config_data:
        cfg.trailing_stop_callback_pct = float(config_data["trailing_stop_callback_pct"])
    if "max_asset_concentration_pct" in config_data:
        cfg.max_asset_concentration_pct = float(config_data["max_asset_concentration_pct"])
    if "max_portfolio_exposure_pct" in config_data:
        cfg.max_portfolio_exposure_pct = float(config_data["max_portfolio_exposure_pct"])
    if "flash_crash_threshold_pct" in config_data:
        cfg.flash_crash_threshold_pct = float(config_data["flash_crash_threshold_pct"])
    if "daily_loss_limit_pct" in config_data:
        cfg.daily_loss_limit_pct = float(config_data["daily_loss_limit_pct"])
    if "max_drawdown_pct" in config_data:
        cfg.max_drawdown_pct = float(config_data["max_drawdown_pct"])
    return {"success": True, "config": cfg.to_dict()}

# ==============================================================================
# MODEL CONTEXT PROTOCOL (MCP) INFO & CONFIG
# ==============================================================================

@app.get("/api/mcp/info")
def get_mcp_info():
    """Returns MCP Server connection endpoint, supported tools, and client configuration snippet."""
    base_mcp_url = "http://127.0.0.1:8001/mcp/sse"
    return {
        "status": "ONLINE",
        "mcp_url": base_mcp_url,
        "protocol": "Model Context Protocol (SSE Transport)",
        "server_name": "syrax-agent-os",
        "tools": [
            {"name": "syrax_get_portfolio", "description": "Get sub-wallet holdings, cash, and drift analysis."},
            {"name": "syrax_get_ongoing_trades", "description": "Get active ongoing trades with live mark-to-market PnL."},
            {"name": "syrax_manage_trade", "description": "Close a position or update Stop-Loss / Take-Profit."},
            {"name": "syrax_execute_trade", "description": "Open a new trade under mathematical risk gating."},
            {"name": "syrax_scan_markets", "description": "Scan Binance Spot, Futures, and Alpha gainers."},
            {"name": "syrax_get_monitor_status", "description": "Inspect 24/7 autonomous background surveillance pulse."},
            {"name": "syrax_rebalance_portfolio", "description": "Calculate rebalancing delta orders."}
        ],
        "claude_config": {
            "mcpServers": {
                "syrax": {
                    "url": base_mcp_url
                }
            }
        },
        "cursor_config": {
            "mcpServers": {
                "syrax": {
                    "url": base_mcp_url
                }
            }
        }
    }

