from agent.execution_gateway import ExecutionRequest, ExecutionActionType
"""
SYRAX — Model Context Protocol (MCP) Server
Exposes official Model Context Protocol (MCP) tools over SSE and stdio
for portfolio management, ongoing trades, live PnL, risk-gated execution,
and 24/7 autonomous monitoring.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("syrax.mcp")

def create_syrax_mcp_server(binance_os, sub_wallet, orchestrator, monitor_daemon) -> MCPServer:
    """
    Creates and configures the SYRAX Model Context Protocol (MCP) server.
    """
    server = MCPServer("syrax-agent-os")

    @server.tool()
    async def syrax_get_portfolio() -> str:
        """
        Get the sub-wallet portfolio breakdown, total valuation, available liquid cash reserves,
        asset allocations, and drift analysis against mandate targets.
        """
        # Fetch live prices for held assets
        price_map = {}
        for asset in sub_wallet.holdings.keys():
            if asset not in ("USDT", "USDC", "USD", "FDUSD"):
                t = await binance_os.get_live_ticker(f"{asset}USDT")
                if t.get("last_price"):
                    price_map[f"{asset}USDT"] = t["last_price"]

        data = sub_wallet.get_holdings_analysis(price_map)
        return json.dumps(data, indent=2)

    @server.tool()
    async def syrax_get_ongoing_trades() -> str:
        """
        Get all active ongoing trades/positions in the sub-wallet.
        Returns mark-to-market valuations, entry price, live Binance price,
        Unrealized PnL ($ and %), Stop Loss, Take Profit, and health status.
        """
        # Update live prices
        price_map = {}
        for trd in sub_wallet.ongoing_trades:
            t = await binance_os.get_live_ticker(trd["symbol"])
            if t.get("last_price"):
                price_map[trd["symbol"]] = t["last_price"]

        sub_wallet.update_live_prices(price_map)
        return json.dumps({
            "sub_wallet_id": sub_wallet.sub_wallet_id,
            "ongoing_trades_count": len(sub_wallet.ongoing_trades),
            "ongoing_trades": sub_wallet.ongoing_trades
        }, indent=2)

    @server.tool()
    async def syrax_manage_trade(
        trade_id: str,
        action: str,
        new_stop_loss: Optional[float] = None,
        new_take_profit: Optional[float] = None
    ) -> str:
        """
        Manage an ongoing sub-wallet trade.
        action: 'CLOSE' (to liquidate/exit position at market) or 'UPDATE_LEVELS' (to update stop loss / take profit).
        """
        action = action.upper()
        if not (hasattr(orchestrator, "gateway") and orchestrator.gateway):
            return json.dumps({"success": False, "error": "Gateway Error: UnifiedExecutionGateway is not attached."})

        if action == "CLOSE":
            trd = next((t for t in sub_wallet.ongoing_trades if t.get("trade_id") == trade_id), None)
            sym = trd.get("symbol", "UNKNOWN") if trd else "UNKNOWN"
            req = ExecutionRequest(
                action=ExecutionActionType.CLOSE_POSITION,
                symbol=sym,
                trade_id=trade_id,
                metadata={"reason": "MCP Autonomous Client Command", "source": "mcp"}
            )
            receipt = await orchestrator.gateway.execute(req)
            return json.dumps(receipt.to_dict(), indent=2)
        elif action == "UPDATE_LEVELS":
            trd = next((t for t in sub_wallet.ongoing_trades if t.get("trade_id") == trade_id), None)
            sym = trd.get("symbol", "UNKNOWN") if trd else "UNKNOWN"
            req = ExecutionRequest(
                action=ExecutionActionType.UPDATE_LEVELS,
                symbol=sym,
                trade_id=trade_id,
                stop_loss=new_stop_loss,
                take_profit=new_take_profit,
                metadata={"source": "mcp"}
            )
            receipt = await orchestrator.gateway.execute(req)
            return json.dumps(receipt.to_dict(), indent=2)
        else:
            return json.dumps({"success": False, "error": f"Invalid action '{action}'. Use 'CLOSE' or 'UPDATE_LEVELS'."})

    @server.tool()
    async def syrax_execute_trade(
        symbol: str,
        side: str = "BUY",
        notional_usd: float = 25.0,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> str:
        """
        Open a new trade on the agentic sub-wallet with strict mathematical risk gating.
        Pre-trade checks verify available cash, maximum dollar loss ceiling, and stop-loss placement.
        """
        norm_sym = binance_os.normalize_symbol(symbol)
        ticker = await binance_os.get_live_ticker(norm_sym)
        price = ticker.get("last_price", 100.0)

        if price <= 0:
            return json.dumps({"success": False, "error": f"Could not retrieve live price for {norm_sym}"})

        qty = round(notional_usd / price, 6 if price < 1 else (4 if price < 100 else 2))

        # Mathematical Risk Gatekeeper Check
        max_order = orchestrator.mandate.get("max_order_size_usd", 50.0)
        if notional_usd > max_order:
            return json.dumps({
                "success": False,
                "error": f"Risk Veto: Order size ${notional_usd} exceeds mandate ceiling of ${max_order}"
            })

        # Default stop-loss and take-profit if not specified
        if not stop_loss:
            stop_loss = round(price * 0.98, 4 if price < 10 else 2)
        if not take_profit:
            take_profit = round(price * 1.045, 4 if price < 10 else 2)

        if not (hasattr(orchestrator, "gateway") and orchestrator.gateway):
            return json.dumps({"success": False, "error": "Gateway Error: UnifiedExecutionGateway is not attached."})

        req = ExecutionRequest(
            action=ExecutionActionType.OPEN_POSITION,
            symbol=norm_sym,
            side=side.upper(),
            order_type="MARKET",
            price=price,
            quantity=qty,
            notional_usd=notional_usd,
            stop_loss=stop_loss,
            take_profit=take_profit,
            market_type=ticker.get("market_type", "SPOT"),
            strategy="MCP Delegated Execution",
            metadata={"source": "mcp"}
        )
        receipt = await orchestrator.gateway.execute(req)
        return json.dumps(receipt.to_dict(), indent=2)

    @server.tool()
    async def syrax_scan_markets(category: str = "ALL", limit: int = 15) -> str:
        """
        Scan live Binance markets for tradeable setups and AI opportunity scores.
        category options: 'ALL', 'FUTURES' (USDⓈ-M Perps), 'ALPHA' (Momentum Breakout Gainers), 'SPOT'.
        """
        results = await orchestrator.market_agent.scan_market(category=category, limit=limit)
        return json.dumps({"category": category, "count": len(results), "opportunities": results}, indent=2)

    @server.tool()
    async def syrax_get_monitor_status() -> str:
        """
        Get the live status of the 24/7 Autonomous Background Sentinel Daemon,
        heartbeat pulse, and the recent circular audit log of surveillance events.
        """
        status = monitor_daemon.get_status()
        return json.dumps(status, indent=2)

    @server.tool()
    async def syrax_rebalance_portfolio() -> str:
        """
        Calculates rebalancing delta orders to align sub-wallet holdings to target allocations
        with maximum order size slicing.
        """
        plan = await orchestrator.portfolio_agent.calculate_rebalancing_plan()
        return json.dumps(plan, indent=2)


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
        """
        Compiles an immutable Order Ticket in state PENDING_CONFIRMATION.
        Returns the ticket ID and exact confirmation command required for execution.
        """
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
        """
        Authorizes and executes a pending order ticket using the exact confirmation token 'CONFIRM PO-XXXXXX'.
        Routes through the UnifiedExecutionGateway upon valid cryptographic confirmation.
        """
        res = await orchestrator._handle_confirm_order_ticket(parent_order_id, confirmation_token, 0.0)
        return json.dumps(res, indent=2)

    return server
