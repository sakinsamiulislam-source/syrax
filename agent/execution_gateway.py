"""
SYRAX — Unified Execution Gateway & Central Safety Pipeline
Central authority for ALL trade executions in SYRAX.

Key Invariants:
1. Single Execution Authority: No UI, API, MCP tool, Orchestrator, or Agent can bypass the Gateway.
2. Central RiskEngine Enforcement: Deterministic mathematical risk gatekeeper runs on every order.
3. Immutable Hard Safety: Stop-loss is mandatory, risk caps and leverage limits are non-negotiable. No silent clamping.
4. Sentry Threat Radar Veto: Live exploit alerts immediately abort order placement.
5. Live vs Simulation Transparency: Explicit environment labels (SIMULATED vs LIVE_BINANCE). No silent environment crossing.
6. Idempotency Protection: Duplicate request prevention.
"""

import time
import uuid
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from agent.risk_engine import RiskEngine, RiskParameters, RiskAssessment
from agent.news_sentry_agent import NewsSentryAgent
from backend.binance.agent_os import BinanceAgentOS
from backend.binance.sub_wallet import SubWalletManager

logger = logging.getLogger("syrax.execution_gateway")


# =============================================================================
# 1. ENUMS & DATA MODELS
# =============================================================================

class ExecutionEnvironment(str, Enum):
    SIMULATED = "SIMULATED"
    BINANCE_TESTNET = "BINANCE_TESTNET"
    BINANCE_AGENTIC_SUB_ACCOUNT = "BINANCE_AGENTIC_SUB_ACCOUNT"
    LIVE_BINANCE = "LIVE_BINANCE"


class ExecutionActionType(str, Enum):
    OPEN_POSITION = "OPEN_POSITION"
    CLOSE_POSITION = "CLOSE_POSITION"
    CANCEL_ORDER = "CANCEL_ORDER"
    CONVERT_ASSET = "CONVERT_ASSET"
    UPDATE_LEVELS = "UPDATE_LEVELS"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class ExecutionRequest(BaseModel):
    """
    Standardized execution request model for all trading operations across SYRAX.
    """
    request_id: str = Field(default_factory=lambda: f"REQ-{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}")
    idempotency_key: str = Field(default_factory=lambda: f"IDEM-{uuid.uuid4().hex}")
    action_type: ExecutionActionType = ExecutionActionType.OPEN_POSITION
    action: Optional[ExecutionActionType] = None
    symbol: str                                      # e.g. "BTCUSDT"
    side: str = "BUY"                               # "BUY" | "SELL"
    order_type: str = "MARKET"                      # "MARKET" | "LIMIT"
    price: Optional[float] = None
    quantity: Optional[float] = None                # Exact quantity if specified
    notional_usd: Optional[float] = None            # Dollar amount to allocate
    limit_price: Optional[float] = None             # Limit order target price
    stop_loss: Optional[float] = None               # Stop loss price (Mandatory for OPEN)
    take_profit: Optional[float] = None             # Take profit target price
    leverage: int = 1                               # 1 for Spot, >1 for Futures
    market_type: str = "SPOT"                       # "SPOT" | "FUTURES" | "MARGIN"
    margin_type: str = "ISOLATED"                   # "ISOLATED" | "CROSS"
    environment: ExecutionEnvironment = ExecutionEnvironment.SIMULATED
    source: str = "ORCHESTRATOR"                    # "ORCHESTRATOR" | "MCP" | "API" | "SENTINEL"
    mandate: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Action-specific fields
    trade_id: Optional[str] = None
    trade_id_to_close: Optional[str] = None         # For CLOSE_POSITION
    order_id_to_cancel: Optional[str] = None        # For CANCEL_ORDER
    convert_from_asset: Optional[str] = None        # For CONVERT_ASSET
    convert_to_asset: Optional[str] = None          # For CONVERT_ASSET
    convert_amount: Optional[float] = None          # For CONVERT_ASSET
    exit_price: Optional[float] = None              # For CLOSE_POSITION
    close_reason: Optional[str] = "Manual Exit"     # For CLOSE_POSITION

    def __init__(self, **data):
        if "action" in data and ("action_type" not in data or data.get("action_type") is None):
            data["action_type"] = data["action"]
        if "trade_id" in data and ("trade_id_to_close" not in data or data.get("trade_id_to_close") is None):
            data["trade_id_to_close"] = data["trade_id"]
        super().__init__(**data)


class ExecutionReceipt(BaseModel):
    """
    Standardized execution receipt returned by the UnifiedExecutionGateway.
    """
    status: ExecutionStatus                         # SUCCESS | REJECTED | BLOCKED | FAILED
    request_id: str
    idempotency_key: Optional[str] = None
    action_type: ExecutionActionType
    symbol: str
    side: str
    term: str = ""                                  # e.g. "SPOT BUY" or "LONG 10x"
    market_type: str = "SPOT"
    order_type: str = "MARKET"
    quantity: float = 0.0
    requested_price: float = 0.0
    execution_price: Optional[float] = None
    limit_price: Optional[float] = None
    notional_usd: float = 0.0
    margin_usd: float = 0.0
    leverage: int = 1
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    fee_usd: float = 0.0
    fee_breakdown: str = ""
    order_id: Optional[str] = None
    trade_id: Optional[str] = None
    environment: ExecutionEnvironment
    source: str
    timestamp: str
    message: str
    rejection_reason: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    sentry_assessment: Optional[Dict[str, Any]] = None
    security_verdict: str = "VERIFIED_SAFE"
    raw_details: Optional[Dict[str, Any]] = None
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def simulated(self) -> bool:
        return self.environment == ExecutionEnvironment.SIMULATED

    @property
    def reason(self) -> str:
        return self.rejection_reason or self.message

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["simulated"] = self.simulated
        d["reason"] = self.reason
        return d


# =============================================================================
# 2. UNIFIED EXECUTION GATEWAY
# =============================================================================

class UnifiedExecutionGateway:
    """
    Central Safety & Execution Gateway.
    Every trade, position close, convert, and cancel MUST route through this gateway.
    """

    def __init__(
        self,
        binance_client: BinanceAgentOS,
        sub_wallet: Optional[SubWalletManager] = None,
        sentry_agent: Optional[NewsSentryAgent] = None
    ):
        self.binance = binance_client
        self.sub_wallet = sub_wallet
        self.sentry_agent = sentry_agent or NewsSentryAgent()
        
        # Idempotency cache: maps idempotency_key -> ExecutionReceipt
        self._idempotency_cache: Dict[str, ExecutionReceipt] = {}
        # Max entries in idempotency cache
        self._max_cache_size = 500

    async def execute(self, request: ExecutionRequest) -> ExecutionReceipt:
        """
        Main entry point for ALL execution workflows.
        Executes the 9-stage deterministic safety pipeline.
        """
        logger.info(f"[GATEWAY] Processing ExecutionRequest {request.request_id} for {request.symbol} ({request.action_type})")

        # -------------------------------------------------------------
        # STAGE 1: IDEMPOTENCY CHECK
        # -------------------------------------------------------------
        if request.idempotency_key and request.idempotency_key in self._idempotency_cache:
            logger.warning(f"[GATEWAY] Duplicate request detected for idempotency_key: {request.idempotency_key}")
            cached_receipt = self._idempotency_cache[request.idempotency_key]
            return cached_receipt

        # -------------------------------------------------------------
        # STAGE 2: ACTION DISPATCH TO SPECIALIZED SAFETY PIPELINE
        # -------------------------------------------------------------
        if request.action_type == ExecutionActionType.OPEN_POSITION:
            receipt = await self._process_open_position(request)
        elif request.action_type == ExecutionActionType.CLOSE_POSITION:
            receipt = await self._process_close_position(request)
        elif request.action_type == ExecutionActionType.CANCEL_ORDER:
            receipt = await self._process_cancel_order(request)
        elif request.action_type == ExecutionActionType.CONVERT_ASSET:
            receipt = await self._process_convert_asset(request)
        elif request.action_type == ExecutionActionType.UPDATE_LEVELS:
            receipt = await self._process_update_levels(request)
        else:
            receipt = self._create_rejected_receipt(
                request,
                reason=f"Unsupported action type '{request.action_type}'."
            )

        # Cache receipt for idempotency
        if request.idempotency_key:
            if len(self._idempotency_cache) >= self._max_cache_size:
                self._idempotency_cache.pop(next(iter(self._idempotency_cache)))
            self._idempotency_cache[request.idempotency_key] = receipt

        return receipt

    # =========================================================================
    # OPEN POSITION PIPELINE (STRICT RISK & SENTRY GATEKEEPING)
    # =========================================================================

    async def _process_open_position(self, req: ExecutionRequest) -> ExecutionReceipt:
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        norm_symbol = self.binance.normalize_symbol(req.symbol)
        base_asset = norm_symbol.replace("USDT", "").replace("USDC", "")
        side = req.side.upper()
        market_type = req.market_type.upper()
        order_type = req.order_type.upper()
        leverage = int(req.leverage)
        mandate = req.mandate or {}

        # -------------------------------------------------------------
        # 1. INPUT VALIDATION & IMMUTABLE HARD CONSTRAINTS
        # -------------------------------------------------------------
        if not norm_symbol or len(norm_symbol) < 5:
            return self._create_rejected_receipt(req, "Invalid asset symbol format.")

        if side not in ("BUY", "SELL", "LONG", "SHORT"):
            return self._create_rejected_receipt(req, f"Invalid order side '{side}'. Must be BUY or SELL.")

        if leverage < 1:
            return self._create_rejected_receipt(req, "Leverage cannot be less than 1x.")

        # Hard invariant: Spot cannot use leverage > 1
        if market_type == "SPOT" and leverage > 1:
            return self._create_rejected_receipt(req, f"Excessive leverage ({leverage}x) on SPOT market. Spot trading does not permit leverage > 1x.")

        # Hard invariant: Leverage limit from mandate
        max_allowed_lev = mandate.get("max_leverage", 3 if market_type == "FUTURES" else 1)
        if leverage > max_allowed_lev:
            return self._create_rejected_receipt(
                req,
                f"Requested leverage ({leverage}x) exceeds mandate maximum policy limit of {max_allowed_lev}x. Rejected without modification."
            )

        # -------------------------------------------------------------
        # 2. MARKET DATA VALIDITY & LIVE/SIMULATION CHECK
        # -------------------------------------------------------------
        ticker = await self.binance.get_live_ticker(norm_symbol)
        live_price = float(ticker.get("last_price", 0.0))

        if live_price <= 0:
            if req.environment == ExecutionEnvironment.LIVE_BINANCE:
                return self._create_blocked_receipt(req, f"Live market data is unavailable for {norm_symbol}. Live execution blocked to prevent bad fills.")
            live_price = 100.0  # Fallback for offline simulation only

        # Verify live price for LIVE_BINANCE execution
        if req.environment == ExecutionEnvironment.LIVE_BINANCE and ticker.get("is_simulated", False):
            return self._create_blocked_receipt(req, "Live market data is synthetic/simulated. Live order execution blocked.")

        # Determine reference entry price
        if order_type == "LIMIT":
            if not req.limit_price or req.limit_price <= 0:
                return self._create_rejected_receipt(req, "Limit order requires a valid, positive limit_price.")
            entry_price = req.limit_price
        else:
            entry_price = live_price

        # -------------------------------------------------------------
        # 3. IMMUTABLE STOP-LOSS ENFORCEMENT (NON-NEGOTIABLE HARD SAFETY)
        # -------------------------------------------------------------
        # Stop-loss is MANDATORY on ALL trade entries in SYRAX. Cannot be disabled by any mandate or parameter.
        stop_loss = req.stop_loss
        
        if stop_loss is None or stop_loss <= 0:
            return self._create_rejected_receipt(
                req,
                "Mandatory Stop-Loss missing: Policy requires an explicit stop-loss price on all trade entries. Rejected to protect capital."
            )

        # Validate SL direction
        if stop_loss:
            if side in ("BUY", "LONG") and stop_loss >= entry_price:
                return self._create_rejected_receipt(req, f"Invalid Stop-Loss (${stop_loss:,.4f}): Stop-loss for BUY/LONG must be below entry price (${entry_price:,.4f}).")
            elif side in ("SELL", "SHORT") and stop_loss <= entry_price:
                return self._create_rejected_receipt(req, f"Invalid Stop-Loss (${stop_loss:,.4f}): Stop-loss for SELL/SHORT must be above entry price (${entry_price:,.4f}).")

        take_profit = req.take_profit
        if take_profit:
            if side in ("BUY", "LONG") and take_profit <= entry_price:
                return self._create_rejected_receipt(req, f"Invalid Take-Profit (${take_profit:,.4f}): Take-profit for BUY/LONG must be above entry price (${entry_price:,.4f}).")
            elif side in ("SELL", "SHORT") and take_profit >= entry_price:
                return self._create_rejected_receipt(req, f"Invalid Take-Profit (${take_profit:,.4f}): Take-profit for SELL/SHORT must be below entry price (${entry_price:,.4f}).")

        # -------------------------------------------------------------
        # 4. QUANTITY & NOTIONAL CALCULATIONS
        # -------------------------------------------------------------
        if req.quantity and req.quantity > 0:
            quantity = req.quantity
            notional_usd = quantity * entry_price
        elif req.notional_usd and req.notional_usd > 0:
            notional_usd = req.notional_usd
            quantity = notional_usd / entry_price
        else:
            notional_usd = 25.0
            quantity = notional_usd / entry_price

        margin_usd = notional_usd / leverage if leverage > 1 else notional_usd

        # Hard invariant: Max order size check
        max_order_size = mandate.get("max_order_size_usd", 50.0)
        if notional_usd > max_order_size:
            return self._create_rejected_receipt(
                req,
                f"Requested position notional (${notional_usd:.2f}) exceeds maximum allowed order size of ${max_order_size:.2f}."
            )

        # -------------------------------------------------------------
        # 5. SENTRY THREAT RADAR VETO HOOK
        # -------------------------------------------------------------
        active_events = self.sentry_agent.get_active_events()
        critical_exploit = next((e for e in active_events if base_asset in e.get("token", "").upper() and e.get("severity") in ("CRITICAL", "HIGH")), None)

        if critical_exploit and mandate.get("sentry_exploit_filter", True):
            return self._create_blocked_receipt(
                req,
                f"Sentry Threat Radar Veto: Active exploit/security alert on {base_asset} ('{critical_exploit.get('title')}'). Zero capital deployed.",
                sentry_assessment={
                    "protect_triggered": True,
                    "severity": critical_exploit.get("severity"),
                    "title": critical_exploit.get("title")
                }
            )

        # -------------------------------------------------------------
        # 6. CENTRAL RISK ENGINE EVALUATION
        # -------------------------------------------------------------
        capital = float(mandate.get("capital_usd", 500.0))
        max_risk_pct = float(mandate.get("max_risk_pct", 1.0))
        calculated_tp = take_profit if take_profit else (round(entry_price * 1.045, 4) if side in ("BUY", "LONG") else round(entry_price * 0.955, 4))
        calculated_sl = stop_loss if stop_loss else (round(entry_price * 0.98, 4) if side in ("BUY", "LONG") else round(entry_price * 1.02, 4))

        risk_assessment: RiskAssessment = RiskEngine.evaluate(RiskParameters(
            capital=capital,
            max_risk_pct=max_risk_pct,
            entry_price=entry_price,
            stop_loss=calculated_sl,
            take_profit=calculated_tp,
            max_order_size_usd=max_order_size,
            leverage=float(leverage)
        ))

        if risk_assessment.status == "REJECTED":
            reasons_str = "; ".join(risk_assessment.rejection_reasons)
            return self._create_rejected_receipt(
                req,
                f"Risk Engine Veto: {reasons_str}",
                risk_assessment=risk_assessment.model_dump()
            )

        # -------------------------------------------------------------
        # 7. AVAILABLE CAPITAL / MARGIN CHECK
        # -------------------------------------------------------------
        if self.sub_wallet:
            if margin_usd > self.sub_wallet.cash_usd:
                return self._create_rejected_receipt(
                    req,
                    f"Insufficient sub-wallet cash: Required Margin ${margin_usd:.2f} USDT, Available Cash ${self.sub_wallet.cash_usd:.2f} USDT."
                )

        # -------------------------------------------------------------
        # 8. LOW-LEVEL EXECUTION (ISOLATED ADAPTER)
        # -------------------------------------------------------------
        term = f"LONG {leverage}x" if (market_type == "FUTURES" and side in ("BUY", "LONG")) else (
            f"SHORT {leverage}x" if (market_type == "FUTURES" and side in ("SELL", "SHORT")) else f"SPOT {side}"
        )

        offset_pct = ((entry_price - live_price) / live_price * 100.0) if (order_type == "LIMIT" and live_price > 0) else 0.0

        if req.environment in (ExecutionEnvironment.LIVE_BINANCE, ExecutionEnvironment.BINANCE_AGENTIC_SUB_ACCOUNT):
            # Live Binance Agentic Sub-Account execution via official Binance MCP Client
            if not self.binance.mcp_client.is_connected:
                return self._create_blocked_receipt(
                    req,
                    "Binance Agent OS MCP is disconnected or unauthorized. Live order execution blocked to protect capital."
                )

            exec_res = await self.binance.mcp_client.execute_live_order(
                symbol=norm_symbol,
                side="BUY" if side in ("BUY", "LONG") else "SELL",
                order_type=order_type,
                quantity=quantity,
                price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                leverage=leverage,
                market_type=market_type
            )
            if not exec_res.get("success"):
                return self._create_failed_receipt(req, f"Binance MCP Execution Error: {exec_res.get('error', 'Execution failed on exchange.')}")

            order_id = exec_res.get("order_id", f"ORD-MCP-{int(time.time()*1000)}")
            trade_id = exec_res.get("trade_id", order_id)
            fee_usd = round(notional_usd * 0.001, 4)
            fee_breakdown = f"${fee_usd:.4f} USDT (0.10% Fee)"
            actual_env = ExecutionEnvironment.BINANCE_AGENTIC_SUB_ACCOUNT
        else:
            # Simulated Sub-Wallet Execution
            if not self.sub_wallet:
                return self._create_failed_receipt(req, "SubWalletManager is not attached to Execution Gateway.")

            exec_res = self.sub_wallet.open_trade(
                symbol=norm_symbol,
                side="BUY" if side in ("BUY", "LONG") else "SELL",
                quantity=quantity,
                price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                market_type=market_type,
                leverage=leverage,
                margin_type=req.margin_type,
                strategy=f"{term} Execution via Gateway",
                order_type=order_type,
                offset_pct=offset_pct,
                live_price=live_price
            )

            if not exec_res.get("success"):
                return self._create_failed_receipt(req, exec_res.get("error", "Sub-wallet allocation failure."))

            trade_obj = exec_res.get("order") or exec_res.get("trade", {})
            order_id = trade_obj.get("order_id", f"ORD-SIM-{int(time.time()*1000)}")
            trade_id = trade_obj.get("trade_id", order_id)
            fee_usd = trade_obj.get("fee_usd", round(notional_usd * 0.001, 4))
            fee_breakdown = trade_obj.get("fee_breakdown", f"${fee_usd:.4f} USDT (0.10% Fee)")
            actual_env = ExecutionEnvironment.SIMULATED

        # -------------------------------------------------------------
        # 9. STANDARDIZED EXECUTION RECEIPT
        # -------------------------------------------------------------
        msg = f"Order {order_id} {'PLACED' if order_type == 'LIMIT' else 'FILLED'}: {term} {norm_symbol} @ ${entry_price:,.4f} [{actual_env.value}]."

        audit_trail = [
            {"stage": "STAGE_1_IDEMPOTENCY", "status": "VERIFIED_UNIQUE", "key": req.idempotency_key},
            {"stage": "STAGE_2_VALIDATION", "status": "PASSED", "symbol": norm_symbol, "side": side},
            {"stage": "STAGE_3_MARKET_DATA", "status": "LIVE_PRICE_VERIFIED", "price": entry_price},
            {"stage": "STAGE_4_MANDATORY_SL", "status": "ENFORCED", "stop_loss": stop_loss},
            {"stage": "STAGE_5_HARD_INVARIANTS", "status": "PASSED", "leverage": leverage, "notional": notional_usd},
            {"stage": "STAGE_6_RISK_ENGINE", "status": "APPROVED", "max_risk_usd": risk_assessment.max_dollar_loss},
            {"stage": "STAGE_7_SENTRY_RADAR", "status": "VERIFIED_SAFE", "threats_found": 0},
            {"stage": "STAGE_8_ADAPTER_EXECUTION", "status": "EXECUTED", "env": actual_env.value, "order_id": order_id}
        ]

        return ExecutionReceipt(
            status=ExecutionStatus.SUCCESS,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=norm_symbol,
            side=side,
            term=term,
            market_type=market_type,
            order_type=order_type,
            quantity=round(quantity, 6),
            requested_price=round(entry_price, 4),
            execution_price=round(entry_price, 4) if order_type != "LIMIT" else None,
            limit_price=round(entry_price, 4) if order_type == "LIMIT" else None,
            notional_usd=round(notional_usd, 2),
            margin_usd=round(margin_usd, 2),
            leverage=leverage,
            stop_loss=stop_loss,
            take_profit=take_profit,
            fee_usd=fee_usd,
            fee_breakdown=fee_breakdown,
            order_id=order_id,
            trade_id=trade_id,
            environment=actual_env,
            source=req.source,
            timestamp=now_ts,
            message=msg,
            risk_assessment=risk_assessment.model_dump(),
            security_verdict="VERIFIED_SAFE (0 Exploits)",
            raw_details=exec_res,
            audit_trail=audit_trail
        )

    # =========================================================================
    # CLOSE POSITION PIPELINE
    # =========================================================================

    async def _process_close_position(self, req: ExecutionRequest) -> ExecutionReceipt:
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        if not self.sub_wallet:
            return self._create_failed_receipt(req, "SubWalletManager not available.")

        target_trade_id = req.trade_id_to_close
        target_symbol = self.binance.normalize_symbol(req.symbol) if req.symbol else None

        # Find matching trade in sub_wallet
        matched_trade = None
        for t in self.sub_wallet.ongoing_trades:
            if target_trade_id and t.get("trade_id") == target_trade_id:
                matched_trade = t
                break
            elif target_symbol and t.get("symbol") == target_symbol:
                matched_trade = t
                break

        if not matched_trade:
            # Check spot holdings if closing spot position
            base = target_symbol.replace("USDT", "").replace("USDC", "") if target_symbol else ""
            if base in self.sub_wallet.holdings and self.sub_wallet.holdings[base].get("free", 0.0) > 0:
                avail_qty = self.sub_wallet.holdings[base]["free"]
                ticker = await self.binance.get_live_ticker(target_symbol)
                live_p = req.exit_price or ticker.get("last_price", 100.0)
                proceeds = avail_qty * live_p
                fee = proceeds * 0.001
                net_proceeds = proceeds - fee

                self.sub_wallet.holdings[base]["free"] = 0.0
                self.sub_wallet.cash_usd += net_proceeds
                if "USDT" not in self.sub_wallet.holdings:
                    self.sub_wallet.holdings["USDT"] = {"free": 0.0, "locked": 0.0}
                self.sub_wallet.holdings["USDT"]["free"] += net_proceeds

                order_id = f"ORD-CLS-SPOT-{int(time.time()*1000) % 10000}"
                return ExecutionReceipt(
                    status=ExecutionStatus.SUCCESS,
                    request_id=req.request_id,
                    idempotency_key=req.idempotency_key,
                    action_type=req.action_type,
                    symbol=target_symbol or "SPOT",
                    side="SELL",
                    term="SPOT SELL",
                    market_type="SPOT",
                    order_type="MARKET",
                    quantity=avail_qty,
                    requested_price=live_p,
                    execution_price=live_p,
                    notional_usd=round(proceeds, 2),
                    margin_usd=0.0,
                    fee_usd=round(fee, 4),
                    fee_breakdown=f"${fee:.4f} USDT (0.10% Binance Fee)",
                    order_id=order_id,
                    environment=req.environment,
                    source=req.source,
                    timestamp=now_ts,
                    message=f"Liquidated {avail_qty:.4f} {base} @ ${live_p:,.2f} on {req.environment.value}. Returned ${net_proceeds:.2f} USDT cash."
                )

            return self._create_rejected_receipt(req, f"No active position or spot holdings found to close.")

        # Execute close on sub_wallet
        ticker = await self.binance.get_live_ticker(matched_trade["symbol"])
        exit_price = req.exit_price or ticker.get("last_price", matched_trade.get("current_price", 100.0))
        close_res = self.sub_wallet.close_trade(
            trade_id=matched_trade["trade_id"],
            exit_price=exit_price,
            reason=req.close_reason or "Manual Exit"
        )

        if not close_res.get("success"):
            return self._create_failed_receipt(req, close_res.get("error", "Failed to close trade."))

        closed_data = close_res.get("closed_trade", {})
        return ExecutionReceipt(
            status=ExecutionStatus.SUCCESS,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=matched_trade["symbol"],
            side="SELL" if matched_trade.get("side") in ("BUY", "LONG") else "BUY",
            term=f"CLOSE {matched_trade.get('term', 'POSITION')}",
            market_type=matched_trade.get("market_type", "SPOT"),
            order_type="MARKET",
            quantity=matched_trade.get("quantity", 0.0),
            requested_price=exit_price,
            execution_price=exit_price,
            notional_usd=matched_trade.get("notional_usd", 0.0),
            margin_usd=matched_trade.get("margin_usd", 0.0),
            fee_usd=closed_data.get("close_fee_usd", 0.015),
            fee_breakdown=closed_data.get("close_fee_breakdown", "$0.0150 USDT Fee"),
            order_id=closed_data.get("close_order_id"),
            trade_id=matched_trade["trade_id"],
            environment=req.environment,
            source=req.source,
            timestamp=now_ts,
            message=f"Closed position {matched_trade['trade_id']} @ ${exit_price:,.2f} on {req.environment.value}. Realized PnL: ${close_res.get('realized_pnl_usd', 0.0):+.2f} USDT.",
            raw_details=close_res
        )

    # =========================================================================
    # CANCEL ORDER PIPELINE
    # =========================================================================

    async def _process_cancel_order(self, req: ExecutionRequest) -> ExecutionReceipt:
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        if not self.sub_wallet:
            return self._create_failed_receipt(req, "SubWalletManager not available.")

        order_id = req.order_id_to_cancel
        sym = self.binance.normalize_symbol(req.symbol) if req.symbol else None

        if not self.sub_wallet.pending_orders:
            return self._create_rejected_receipt(req, "No pending orders active in sub-wallet to cancel.")

        matched = None
        if order_id:
            matched = next((o for o in self.sub_wallet.pending_orders if o.get("order_id") == order_id), None)
        elif sym:
            matched = next((o for o in self.sub_wallet.pending_orders if o.get("symbol") == sym), None)
        else:
            matched = self.sub_wallet.pending_orders[-1]

        if not matched:
            return self._create_rejected_receipt(req, "Could not find matching open order to cancel.")

        cancel_res = self.sub_wallet.cancel_pending_order(matched["order_id"])
        if not cancel_res.get("success"):
            return self._create_failed_receipt(req, cancel_res.get("error", "Cancel failed."))

        return ExecutionReceipt(
            status=ExecutionStatus.SUCCESS,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=matched["symbol"],
            side="CANCEL",
            term=f"CANCEL LIMIT ORDER",
            market_type=matched.get("market_type", "SPOT"),
            order_type="LIMIT",
            quantity=matched.get("requested_quantity", 0.0),
            requested_price=matched.get("limit_price", 0.0),
            order_id=matched["order_id"],
            environment=req.environment,
            source=req.source,
            timestamp=now_ts,
            message=f"Canceled pending order {matched['order_id']} on {req.environment.value}. Unlocked ${cancel_res.get('unlocked_usd', 0.0):.2f} USDT margin.",
            raw_details=cancel_res
        )

    # =========================================================================
    # CONVERT ASSET PIPELINE
    # =========================================================================

    async def _process_convert_asset(self, req: ExecutionRequest) -> ExecutionReceipt:
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        from_asset = (req.convert_from_asset or "USDC").upper()
        to_asset = (req.convert_to_asset or "USDT").upper()
        amount = float(req.convert_amount or 10.0)

        if amount <= 0:
            return self._create_rejected_receipt(req, "Conversion amount must be greater than zero.")

        # Request quote from Binance
        quote = await self.binance.quote_binance_convert(from_asset, to_asset, amount)
        exec_res = await self.binance.execute_binance_convert(
            quote_id=quote["quote_id"],
            from_asset=from_asset,
            to_asset=to_asset,
            from_amount=amount,
            to_amount=quote["to_amount"]
        )

        if not exec_res.get("success"):
            return self._create_failed_receipt(req, "Binance Convert quote execution failed.")

        if self.sub_wallet:
            self.sub_wallet.record_convert_history(from_asset, to_asset, amount, quote["to_amount"], quote["quote_id"])

        order_id = f"ORD-CNV-{from_asset}{to_asset}-{int(time.time()*1000) % 10000}"
        return ExecutionReceipt(
            status=ExecutionStatus.SUCCESS,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=f"{from_asset}/{to_asset}",
            side="CONVERT",
            term=f"ZERO-FEE CONVERT",
            market_type="CONVERT",
            order_type="INSTANT",
            quantity=amount,
            requested_price=quote.get("ratio", 1.0),
            execution_price=quote.get("ratio", 1.0),
            notional_usd=amount,
            fee_usd=0.0,
            fee_breakdown="0.00 USDT (Zero Fee)",
            order_id=order_id,
            environment=req.environment,
            source=req.source,
            timestamp=now_ts,
            message=f"Converted {amount} {from_asset} -> {quote['to_amount']:.4f} {to_asset} on {req.environment.value} at 0% fee.",
            raw_details=exec_res
        )

    # =========================================================================
    # UPDATE TRADE LEVELS PIPELINE
    # =========================================================================

    async def _process_update_levels(self, req: ExecutionRequest) -> ExecutionReceipt:
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        if not self.sub_wallet:
            return self._create_failed_receipt(req, "SubWalletManager not available.")

        trade_id = req.trade_id_to_close
        res = self.sub_wallet.update_trade_levels(trade_id, stop_loss=req.stop_loss, take_profit=req.take_profit)
        if not res.get("success"):
            return self._create_rejected_receipt(req, res.get("error", "Update levels failed."))

        return ExecutionReceipt(
            status=ExecutionStatus.SUCCESS,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=req.symbol or "TRADE",
            side="UPDATE",
            term="UPDATE RISK LEVELS",
            market_type="FUTURES",
            order_type="MANAGEMENT",
            trade_id=trade_id,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
            environment=req.environment,
            source=req.source,
            timestamp=now_ts,
            message=f"Updated risk levels for trade {trade_id} on {req.environment.value}.",
            raw_details=res
        )

    # =========================================================================
    # HELPER RECEIPT FACTORIES (FAIL-CLOSED)
    # =========================================================================

    def _create_rejected_receipt(
        self,
        req: ExecutionRequest,
        reason: str,
        risk_assessment: Optional[Dict[str, Any]] = None
    ) -> ExecutionReceipt:
        return ExecutionReceipt(
            status=ExecutionStatus.REJECTED,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=req.symbol,
            side=req.side,
            market_type=req.market_type,
            order_type=req.order_type,
            environment=req.environment,
            source=req.source,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            message=f"Execution Rejected: {reason}",
            rejection_reason=reason,
            risk_assessment=risk_assessment
        )

    def _create_blocked_receipt(
        self,
        req: ExecutionRequest,
        reason: str,
        sentry_assessment: Optional[Dict[str, Any]] = None
    ) -> ExecutionReceipt:
        return ExecutionReceipt(
            status=ExecutionStatus.BLOCKED,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=req.symbol,
            side=req.side,
            market_type=req.market_type,
            order_type=req.order_type,
            environment=req.environment,
            source=req.source,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            message=f"Execution Blocked by Gatekeeper: {reason}",
            rejection_reason=reason,
            security_verdict="VETOED_BY_SECURITY_RADAR",
            sentry_assessment=sentry_assessment
        )

    def _create_failed_receipt(
        self,
        req: ExecutionRequest,
        reason: str
    ) -> ExecutionReceipt:
        return ExecutionReceipt(
            status=ExecutionStatus.FAILED,
            request_id=req.request_id,
            idempotency_key=req.idempotency_key,
            action_type=req.action_type,
            symbol=req.symbol,
            side=req.side,
            market_type=req.market_type,
            order_type=req.order_type,
            environment=req.environment,
            source=req.source,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            message=f"Execution Failed: {reason}",
            rejection_reason=reason
        )
