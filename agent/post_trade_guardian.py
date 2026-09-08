"""
SYRAX — Deterministic Post-Trade Guardian
Executes: EXECUTE → MONITOR → DETECT → PROTECT → EXPLAIN

Strict Core Principles:
1. 100% Deterministic: Zero LLM / probabilistic models in the detection and protection decision path.
2. Single Execution Authority: All protective actions MUST go through UnifiedExecutionGateway.
3. 8 Immutable Hard Rules:
   - Hard Stop Loss
   - Trailing Stop
   - Take Profit
   - Position Concentration
   - Total Portfolio Exposure
   - Flash Crash Detection
   - Daily Loss Limit
   - Max Drawdown
4. Peak Equity State Persistence: Drawdown calculation preserves peak equity across restarts.
5. Idempotent Execution: Polling deduplication prevents repeated order generation.
6. Execution Modes: MONITOR_ONLY, ASSISTED, AUTONOMOUS_GUARD.
"""

import os
import json
import time
import uuid
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

from agent.execution_gateway import (
    UnifiedExecutionGateway,
    ExecutionRequest,
    ExecutionReceipt,
    ExecutionActionType,
    ExecutionEnvironment,
    ExecutionStatus,
)

logger = logging.getLogger("syrax.guardian")


# =============================================================================
# 1. ENUMS & DATA MODELS
# =============================================================================

class GuardianExecutionMode(str, Enum):
    MONITOR_ONLY = "MONITOR_ONLY"
    ASSISTED = "ASSISTED"
    AUTONOMOUS_GUARD = "AUTONOMOUS_GUARD"


class GuardianAction(str, Enum):
    NO_ACTION = "NO_ACTION"
    ALERT = "ALERT"
    PREPARE_PROTECTION = "PREPARE_PROTECTION"
    PROTECT = "PROTECT"


class GuardianRuleType(str, Enum):
    HARD_STOP_LOSS = "HARD_STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    TAKE_PROFIT = "TAKE_PROFIT"
    POSITION_CONCENTRATION = "POSITION_CONCENTRATION"
    TOTAL_EXPOSURE = "TOTAL_EXPOSURE"
    FLASH_CRASH = "FLASH_CRASH"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"


class GuardianSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class GuardianEvaluation:
    """
    Standardized result of a deterministic rule evaluation.
    """
    action: GuardianAction
    rule: GuardianRuleType
    asset: str
    severity: GuardianSeverity
    trigger_value: float
    threshold: float
    evidence: List[str]
    reason: str
    timestamp: str
    execution_mode: GuardianExecutionMode
    requires_confirmation: bool
    target_trade_id: Optional[str] = None
    suggested_action_type: Optional[str] = None  # "CLOSE_POSITION" | "UPDATE_LEVELS" | "REDUCE_POSITION"
    suggested_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "rule": self.rule.value,
            "asset": self.asset,
            "severity": self.severity.value,
            "trigger_value": round(self.trigger_value, 4) if isinstance(self.trigger_value, float) else self.trigger_value,
            "threshold": round(self.threshold, 4) if isinstance(self.threshold, float) else self.threshold,
            "evidence": self.evidence,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "execution_mode": self.execution_mode.value,
            "requires_confirmation": self.requires_confirmation,
            "target_trade_id": self.target_trade_id,
            "suggested_action_type": self.suggested_action_type,
            "suggested_params": self.suggested_params,
        }


@dataclass
class GuardianIncident:
    """
    Permanent audit record for any triggered Guardian action or breach.
    """
    incident_id: str
    timestamp: str
    asset: str
    rule: GuardianRuleType
    trigger: float
    threshold: float
    portfolio_state_ref: Dict[str, Any]
    action: GuardianAction
    execution_environment: str
    gateway_order_id: Optional[str] = None
    gateway_receipt: Optional[Dict[str, Any]] = None
    result: str = "PENDING"  # "EXECUTED" | "PROPOSAL_GENERATED" | "ALERTED" | "SKIPPED" | "REJECTED_BY_GATEWAY"
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp,
            "asset": self.asset,
            "rule": self.rule.value,
            "trigger": round(self.trigger, 4) if isinstance(self.trigger, float) else self.trigger,
            "threshold": round(self.threshold, 4) if isinstance(self.threshold, float) else self.threshold,
            "portfolio_state_ref": self.portfolio_state_ref,
            "action": self.action.value,
            "execution_environment": self.execution_environment,
            "gateway_order_id": self.gateway_order_id,
            "gateway_receipt": self.gateway_receipt,
            "result": self.result,
            "explanation": self.explanation,
        }


@dataclass
class GuardianConfig:
    """
    Deterministic parameters and thresholds for all 8 Guardian rules.
    """
    execution_mode: GuardianExecutionMode = GuardianExecutionMode.AUTONOMOUS_GUARD
    max_concentration_pct: float = 30.0          # Max single asset % of total portfolio
    max_total_exposure_pct: float = 80.0         # Max aggregate active margin % of capital
    daily_loss_limit_pct: float = 3.0            # Max 24h loss % of starting equity
    max_drawdown_pct: float = 5.0                # Max portfolio equity drawdown % from peak
    flash_crash_window_seconds: int = 300        # Rolling window for rapid drop calculation (5 min)
    flash_crash_drop_pct: float = 4.0            # Minimum drop % inside window to trigger crash protocol
    trailing_stop_activation_pct: float = 1.5    # Minimum gain % to activate trailing stop ratchet
    trailing_stop_callback_pct: float = 1.0      # Callback % from high water mark for new stop
    stale_price_threshold_seconds: int = 60      # Reject prices older than this for flash crash
    state_persistence_path: str = "scratch/guardian_state.json"


# =============================================================================
# 2. DETERMINISTIC POST-TRADE GUARDIAN CLASS
# =============================================================================

class PostTradeGuardian:
    """
    SYRAX Post-Trade Guardian.
    Evaluates positions and portfolio state deterministically without LLMs.
    Guarantees that all executions pass through UnifiedExecutionGateway.
    """

    def __init__(
        self,
        gateway: Optional[UnifiedExecutionGateway] = None,
        sub_wallet: Optional[Any] = None,
        binance_os: Optional[Any] = None,
        sentry_agent: Optional[Any] = None,
        config: Optional[GuardianConfig] = None
    ):
        self.gateway = gateway
        self.sub_wallet = sub_wallet
        self.binance = binance_os
        self.sentry = sentry_agent
        self.config = config or GuardianConfig()

        # In-memory and persistent state
        self.peak_equity_usd: float = 500.0
        self.daily_starting_equity_usd: float = 500.0
        self.current_day_str: str = time.strftime("%Y-%m-%d", time.gmtime())
        self.realized_pnl_today_usd: float = 0.0

        # Trailing stop high-water marks: trade_id -> peak_price
        self.high_water_marks: Dict[str, float] = {}

        # Flash crash rolling tick buffers: symbol -> List[(timestamp, price)]
        self.recent_price_ticks: Dict[str, List[Tuple[float, float]]] = {}

        # Idempotency cache: breach_fingerprint -> last_trigger_timestamp
        self.processed_breach_fingerprints: Dict[str, float] = {}
        self.cooldown_seconds: float = 30.0

        # Incident history log
        self.incidents: List[GuardianIncident] = []

        # Load persisted peak state from disk
        self._load_state()

    # -------------------------------------------------------------------------
    # STATE PERSISTENCE (Preserves peak equity across process restarts)
    # -------------------------------------------------------------------------

    def _get_persistence_path(self) -> str:
        p = self.config.state_persistence_path
        if not os.path.isabs(p):
            p = os.path.join(os.getcwd(), p)
        return p

    def _load_state(self):
        """Restores peak equity and state from disk if available."""
        path = self._get_persistence_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.peak_equity_usd = float(data.get("peak_equity_usd", self.peak_equity_usd))
                    self.daily_starting_equity_usd = float(data.get("daily_starting_equity_usd", self.daily_starting_equity_usd))
                    saved_day = data.get("current_day_str")
                    now_day = time.strftime("%Y-%m-%d", time.gmtime())
                    if saved_day == now_day:
                        self.current_day_str = saved_day
                        self.realized_pnl_today_usd = float(data.get("realized_pnl_today_usd", 0.0))
                    else:
                        # New calendar day
                        self.current_day_str = now_day
                        self.daily_starting_equity_usd = self.peak_equity_usd
                        self.realized_pnl_today_usd = 0.0
                    self.high_water_marks = data.get("high_water_marks", {})
                logger.info(f"[GUARDIAN] Loaded persistent state from {path} (Peak Equity: ${self.peak_equity_usd:.2f})")
            except Exception as e:
                logger.warning(f"[GUARDIAN] Could not load state from {path}: {e}")

    def save_state(self):
        """Persists peak equity and runtime state to disk."""
        path = self._get_persistence_path()
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            data = {
                "peak_equity_usd": self.peak_equity_usd,
                "daily_starting_equity_usd": self.daily_starting_equity_usd,
                "current_day_str": self.current_day_str,
                "realized_pnl_today_usd": self.realized_pnl_today_usd,
                "high_water_marks": self.high_water_marks,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"[GUARDIAN] Failed to save state to {path}: {e}")

    # -------------------------------------------------------------------------
    # MARKET DATA & TICK INGESTION
    # -------------------------------------------------------------------------

    def record_price_tick(self, symbol: str, price: float, timestamp: Optional[float] = None):
        """
        Ingests a price tick for flash crash and volatility monitoring.
        Validates price is strictly positive and timestamp is valid.
        """
        if price is None or price <= 0:
            return
        ts = timestamp or time.time()
        norm_sym = symbol.upper()
        if norm_sym not in self.recent_price_ticks:
            self.recent_price_ticks[norm_sym] = []

        self.recent_price_ticks[norm_sym].append((ts, price))

        # Prune ticks older than 2x rolling window
        cutoff = ts - (self.config.flash_crash_window_seconds * 2)
        self.recent_price_ticks[norm_sym] = [
            (t, p) for t, p in self.recent_price_ticks[norm_sym] if t >= cutoff
        ]

    # -------------------------------------------------------------------------
    # RULE 1: HARD STOP LOSS
    # -------------------------------------------------------------------------

    def evaluate_hard_stop_loss(self, trade: Dict[str, Any], live_price: float) -> Optional[GuardianEvaluation]:
        """
        Rule 1: Hard Stop Loss.
        Every protected position must have a mandatory SL.
        If price crosses the stop condition, Guardian generates a protection action.
        Cannot be disabled by AI or user mandate.
        """
        if live_price is None or live_price <= 0:
            return None

        trade_id = trade.get("trade_id", "UNKNOWN")
        symbol = trade.get("symbol", "BTCUSDT")
        side = trade.get("side", "BUY").upper()
        sl = trade.get("stop_loss")
        entry_price = trade.get("entry_price", live_price)

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        # If position lacks an SL, flag as a critical invariant violation
        if sl is None or sl <= 0:
            return GuardianEvaluation(
                action=self._resolve_action(GuardianAction.PROTECT),
                rule=GuardianRuleType.HARD_STOP_LOSS,
                asset=symbol,
                severity=GuardianSeverity.CRITICAL,
                trigger_value=0.0,
                threshold=entry_price * 0.98,
                evidence=[f"Position {trade_id} is missing mandatory stop-loss price."],
                reason=f"Mandatory stop-loss missing on position {trade_id}. Protection required to guard capital.",
                timestamp=now_ts,
                execution_mode=self.config.execution_mode,
                requires_confirmation=self._requires_confirmation(),
                target_trade_id=trade_id,
                suggested_action_type="CLOSE_POSITION",
                suggested_params={"exit_price": live_price}
            )

        # Check Long position SL breach: live_price <= stop_loss
        is_long = side in ("BUY", "LONG")
        is_short = side in ("SELL", "SHORT")

        breached = False
        if is_long and live_price <= sl:
            breached = True
        elif is_short and live_price >= sl:
            breached = True

        if breached:
            loss_pct = abs(live_price - entry_price) / entry_price * 100 if entry_price > 0 else 0.0
            return GuardianEvaluation(
                action=self._resolve_action(GuardianAction.PROTECT),
                rule=GuardianRuleType.HARD_STOP_LOSS,
                asset=symbol,
                severity=GuardianSeverity.CRITICAL,
                trigger_value=live_price,
                threshold=sl,
                evidence=[
                    f"Live price ${live_price:.4f} crossed Stop Loss ${sl:.4f}.",
                    f"Position Side: {side}, Entry: ${entry_price:.4f}, Drawdown: -{loss_pct:.2f}%."
                ],
                reason=f"Hard Stop Loss breached on {symbol} (Live: ${live_price:.4f} vs SL: ${sl:.4f}). Auto-liquidating to preserve margin.",
                timestamp=now_ts,
                execution_mode=self.config.execution_mode,
                requires_confirmation=self._requires_confirmation(),
                target_trade_id=trade_id,
                suggested_action_type="CLOSE_POSITION",
                suggested_params={"exit_price": live_price, "reason": "Guardian Hard Stop Loss Trigger"}
            )

        return None

    # -------------------------------------------------------------------------
    # RULE 2: TRAILING STOP (MONOTONIC SAFETY RATCHET)
    # -------------------------------------------------------------------------

    def evaluate_trailing_stop(self, trade: Dict[str, Any], live_price: float) -> Optional[GuardianEvaluation]:
        """
        Rule 2: Trailing Stop.
        Supports deterministic trailing-stop calculation.
        Never moves a protective stop farther away from safety (strictly monotonic).
        Records every stop adjustment.
        """
        if live_price is None or live_price <= 0:
            return None

        trade_id = trade.get("trade_id", "UNKNOWN")
        symbol = trade.get("symbol", "BTCUSDT")
        side = trade.get("side", "BUY").upper()
        entry_price = float(trade.get("entry_price", live_price))
        current_sl = float(trade.get("stop_loss", 0.0))

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        # Update high-water mark
        prev_hwm = self.high_water_marks.get(trade_id, entry_price)
        is_long = side in ("BUY", "LONG")

        if is_long:
            hwm = max(prev_hwm, live_price)
            self.high_water_marks[trade_id] = hwm

            # Check if profit reached activation threshold
            gain_pct = ((hwm - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
            if gain_pct >= self.config.trailing_stop_activation_pct:
                candidate_sl = round(hwm * (1.0 - self.config.trailing_stop_callback_pct / 100.0), 4)
                
                # INVARIANT: New SL MUST be strictly higher than current SL (safer direction only!)
                if candidate_sl > current_sl * 1.0005:  # At least 0.05% improvement
                    return GuardianEvaluation(
                        action=self._resolve_action(GuardianAction.PROTECT),
                        rule=GuardianRuleType.TRAILING_STOP,
                        asset=symbol,
                        severity=GuardianSeverity.INFO,
                        trigger_value=live_price,
                        threshold=candidate_sl,
                        evidence=[
                            f"Peak Price: ${hwm:.4f} (+{gain_pct:.2f}% from entry ${entry_price:.4f}).",
                            f"Previous SL: ${current_sl:.4f} -> New Trailing SL: ${candidate_sl:.4f}."
                        ],
                        reason=f"Trailing Stop ratcheted up for {symbol} to ${candidate_sl:.4f} (Peak: ${hwm:.4f}, Callback: {self.config.trailing_stop_callback_pct}%).",
                        timestamp=now_ts,
                        execution_mode=self.config.execution_mode,
                        requires_confirmation=self._requires_confirmation(),
                        target_trade_id=trade_id,
                        suggested_action_type="UPDATE_LEVELS",
                        suggested_params={"new_stop_loss": candidate_sl, "take_profit": trade.get("take_profit")}
                    )

        return None

    # -------------------------------------------------------------------------
    # RULE 3: TAKE PROFIT
    # -------------------------------------------------------------------------

    def evaluate_take_profit(self, trade: Dict[str, Any], live_price: float) -> Optional[GuardianEvaluation]:
        """
        Rule 3: Take Profit.
        Deterministic TP condition.
        Generates close/protection action through UnifiedExecutionGateway.
        """
        if live_price is None or live_price <= 0:
            return None

        trade_id = trade.get("trade_id", "UNKNOWN")
        symbol = trade.get("symbol", "BTCUSDT")
        side = trade.get("side", "BUY").upper()
        tp = trade.get("take_profit")
        entry_price = trade.get("entry_price", live_price)

        if tp is None or tp <= 0:
            return None

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        is_long = side in ("BUY", "LONG")
        is_short = side in ("SELL", "SHORT")

        hit = False
        if is_long and live_price >= tp:
            hit = True
        elif is_short and live_price <= tp:
            hit = True

        if hit:
            gain_pct = abs(live_price - entry_price) / entry_price * 100 if entry_price > 0 else 0.0
            return GuardianEvaluation(
                action=self._resolve_action(GuardianAction.PROTECT),
                rule=GuardianRuleType.TAKE_PROFIT,
                asset=symbol,
                severity=GuardianSeverity.HIGH,
                trigger_value=live_price,
                threshold=tp,
                evidence=[
                    f"Live price ${live_price:.4f} reached Take Profit target ${tp:.4f}.",
                    f"Position Side: {side}, Entry: ${entry_price:.4f}, Gain: +{gain_pct:.2f}%."
                ],
                reason=f"Take Profit target achieved on {symbol} at ${live_price:.4f} (TP: ${tp:.4f}). Locking in profits.",
                timestamp=now_ts,
                execution_mode=self.config.execution_mode,
                requires_confirmation=self._requires_confirmation(),
                target_trade_id=trade_id,
                suggested_action_type="CLOSE_POSITION",
                suggested_params={"exit_price": live_price, "reason": "Guardian Take Profit Target Hit"}
            )

        return None

    # -------------------------------------------------------------------------
    # RULE 4: POSITION CONCENTRATION
    # -------------------------------------------------------------------------

    def evaluate_position_concentration(
        self,
        holdings: Dict[str, Any],
        ongoing_trades: List[Dict[str, Any]],
        total_portfolio_usd: float
    ) -> List[GuardianEvaluation]:
        """
        Rule 4: Position Concentration.
        Detects when a single asset exceeds configured concentration limit (default 30%).
        Creates ALERT / PREPARE_PROTECTION.
        """
        evaluations = []
        if total_portfolio_usd <= 0:
            return evaluations

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        # Aggregate exposure by asset
        asset_values: Dict[str, float] = {}

        # 1. Spot holdings
        for asset, data in holdings.items():
            if asset in ("USDT", "USDC", "USD", "FDUSD"):
                continue
            qty = data.get("free", 0.0) + data.get("locked", 0.0)
            p = data.get("price_usd", 0.0)
            val = qty * p
            if val > 0:
                asset_values[asset] = asset_values.get(asset, 0.0) + val

        # 2. Ongoing trades notional
        for trade in ongoing_trades:
            sym = trade.get("symbol", "BTCUSDT")
            base = sym.replace("USDT", "").replace("USDC", "")
            notional = float(trade.get("notional_usd", 0.0))
            asset_values[base] = asset_values.get(base, 0.0) + notional

        # Evaluate concentration %
        for asset, val in asset_values.items():
            conc_pct = (val / total_portfolio_usd) * 100.0
            if conc_pct > self.config.max_concentration_pct:
                evaluations.append(GuardianEvaluation(
                    action=GuardianAction.PREPARE_PROTECTION if self.config.execution_mode != GuardianExecutionMode.MONITOR_ONLY else GuardianAction.ALERT,
                    rule=GuardianRuleType.POSITION_CONCENTRATION,
                    asset=asset,
                    severity=GuardianSeverity.HIGH,
                    trigger_value=conc_pct,
                    threshold=self.config.max_concentration_pct,
                    evidence=[
                        f"Asset {asset} total exposure: ${val:.2f} USD.",
                        f"Concentration: {conc_pct:.1f}% vs Max Ceiling: {self.config.max_concentration_pct:.1f}%."
                    ],
                    reason=f"Position concentration limit exceeded for {asset} ({conc_pct:.1f}% > {self.config.max_concentration_pct:.1f}%). Rebalancing recommended.",
                    timestamp=now_ts,
                    execution_mode=self.config.execution_mode,
                    requires_confirmation=True,
                    suggested_action_type="REDUCE_POSITION",
                    suggested_params={"asset": asset, "excess_usd": val - (total_portfolio_usd * self.config.max_concentration_pct / 100.0)}
                ))

        return evaluations

    # -------------------------------------------------------------------------
    # RULE 5: TOTAL PORTFOLIO EXPOSURE
    # -------------------------------------------------------------------------

    def evaluate_total_exposure(
        self,
        ongoing_trades: List[Dict[str, Any]],
        total_portfolio_usd: float
    ) -> Optional[GuardianEvaluation]:
        """
        Rule 5: Total Exposure.
        Calculates total portfolio exposure deterministically.
        Detects aggregate margin exceeding configured maximum (default 80%).
        """
        if total_portfolio_usd <= 0:
            return None

        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        total_active_notional = sum(float(t.get("notional_usd", 0.0)) for t in ongoing_trades)
        exposure_pct = (total_active_notional / total_portfolio_usd) * 100.0

        if exposure_pct > self.config.max_total_exposure_pct:
            return GuardianEvaluation(
                action=GuardianAction.PREPARE_PROTECTION if self.config.execution_mode != GuardianExecutionMode.MONITOR_ONLY else GuardianAction.ALERT,
                rule=GuardianRuleType.TOTAL_EXPOSURE,
                asset="PORTFOLIO",
                severity=GuardianSeverity.HIGH,
                trigger_value=exposure_pct,
                threshold=self.config.max_total_exposure_pct,
                evidence=[
                    f"Active trades notional at risk: ${total_active_notional:.2f} USD.",
                    f"Portfolio Value: ${total_portfolio_usd:.2f} USD ({exposure_pct:.1f}% exposure)."
                ],
                reason=f"Total portfolio exposure ({exposure_pct:.1f}%) exceeds safety ceiling ({self.config.max_total_exposure_pct:.1f}%). New positions restricted.",
                timestamp=now_ts,
                execution_mode=self.config.execution_mode,
                requires_confirmation=True,
                suggested_action_type="ALERT"
            )

        return None

    # -------------------------------------------------------------------------
    # RULE 6: FLASH CRASH DETECTION
    # -------------------------------------------------------------------------

    def evaluate_flash_crash(self, symbol: str, current_price: float) -> Optional[GuardianEvaluation]:
        """
        Rule 6: Flash Crash.
        Detects deterministic abnormal rapid price drop over rolling time window.
        Does NOT rely on Gemini.
        Avoids false positives: Stale or missing data produces NO_ACTION.
        """
        if current_price is None or current_price <= 0:
            return None

        norm_sym = symbol.upper()
        ticks = self.recent_price_ticks.get(norm_sym, [])
        if not ticks or len(ticks) < 2:
            return None

        now_ts_sec = time.time()
        window_sec = self.config.flash_crash_window_seconds
        cutoff = now_ts_sec - window_sec

        # Filter ticks strictly in window
        window_ticks = [(t, p) for t, p in ticks if t >= cutoff]
        if len(window_ticks) < 2:
            return None

        # Check staleness: newest tick must not be older than threshold
        newest_tick_ts = window_ticks[-1][0]
        if (now_ts_sec - newest_tick_ts) > self.config.stale_price_threshold_seconds:
            # Stale data -> Safely fail-closed with NO_ACTION
            return None

        window_max = max(p for _, p in window_ticks)
        if window_max <= 0:
            return None

        drop_pct = ((window_max - current_price) / window_max) * 100.0
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        if drop_pct >= self.config.flash_crash_drop_pct:
            return GuardianEvaluation(
                action=self._resolve_action(GuardianAction.PROTECT),
                rule=GuardianRuleType.FLASH_CRASH,
                asset=symbol,
                severity=GuardianSeverity.CRITICAL,
                trigger_value=drop_pct,
                threshold=self.config.flash_crash_drop_pct,
                evidence=[
                    f"Rolling {window_sec}s Peak Price: ${window_max:.4f} -> Live: ${current_price:.4f}.",
                    f"Rapid Velocity Drop: -{drop_pct:.2f}% (Threshold: {self.config.flash_crash_drop_pct}%)."
                ],
                reason=f"Flash Crash detected on {symbol}: rapid collapse of -{drop_pct:.2f}% in under {window_sec}s. Emergency defensive protocol activated.",
                timestamp=now_ts,
                execution_mode=self.config.execution_mode,
                requires_confirmation=self._requires_confirmation(),
                suggested_action_type="CLOSE_POSITION",
                suggested_params={"symbol": symbol, "exit_price": current_price, "reason": "Guardian Flash Crash Protection"}
            )

        return None

    # -------------------------------------------------------------------------
    # RULE 7: DAILY LOSS LIMIT
    # -------------------------------------------------------------------------

    def evaluate_daily_loss_limit(
        self,
        ongoing_trades: List[Dict[str, Any]],
        current_equity_usd: float
    ) -> Optional[GuardianEvaluation]:
        """
        Rule 7: Daily Loss Limit.
        Calculates realized + unrealized daily loss using actual portfolio state.
        When configured daily-loss threshold is breached, triggers protection.
        Never invents PnL.
        """
        # Calendar day rollover check
        now_day = time.strftime("%Y-%m-%d", time.gmtime())
        if now_day != self.current_day_str:
            self.current_day_str = now_day
            self.daily_starting_equity_usd = current_equity_usd if current_equity_usd > 0 else self.daily_starting_equity_usd
            self.realized_pnl_today_usd = 0.0
            self.save_state()

        if self.daily_starting_equity_usd <= 0:
            return None

        unrealized_pnl = sum(float(t.get("unrealized_pnl_usd", 0.0)) for t in ongoing_trades)
        total_daily_pnl = self.realized_pnl_today_usd + unrealized_pnl

        # If net daily performance is negative, measure loss %
        if total_daily_pnl < 0:
            daily_loss_pct = (abs(total_daily_pnl) / self.daily_starting_equity_usd) * 100.0
            now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

            if daily_loss_pct >= self.config.daily_loss_limit_pct:
                return GuardianEvaluation(
                    action=self._resolve_action(GuardianAction.PROTECT),
                    rule=GuardianRuleType.DAILY_LOSS_LIMIT,
                    asset="PORTFOLIO",
                    severity=GuardianSeverity.CRITICAL,
                    trigger_value=daily_loss_pct,
                    threshold=self.config.daily_loss_limit_pct,
                    evidence=[
                        f"Daily Starting Equity: ${self.daily_starting_equity_usd:.2f} USD.",
                        f"Realized Today: ${self.realized_pnl_today_usd:+.2f}, Unrealized: ${unrealized_pnl:+.2f}.",
                        f"Cumulative Daily Loss: -${abs(total_daily_pnl):.2f} ({daily_loss_pct:.2f}%)."
                    ],
                    reason=f"Daily Loss Limit breached: cumulative 24h loss (-{daily_loss_pct:.2f}%) exceeds {self.config.daily_loss_limit_pct}% threshold. Circuit breaker triggered.",
                    timestamp=now_ts,
                    execution_mode=self.config.execution_mode,
                    requires_confirmation=self._requires_confirmation(),
                    suggested_action_type="CLOSE_POSITION"
                )

        return None

    # -------------------------------------------------------------------------
    # RULE 8: MAX DRAWDOWN (WITH RESTART EQUITY PERSISTENCE)
    # -------------------------------------------------------------------------

    def evaluate_max_drawdown(self, current_equity_usd: float) -> Optional[GuardianEvaluation]:
        """
        Rule 8: Max Drawdown.
        Tracks peak portfolio equity and current equity.
        Persists and recovers peak state across restarts.
        Never resets peak merely because the process restarted.
        """
        if current_equity_usd <= 0:
            return None

        # Monotonically update peak equity
        if current_equity_usd > self.peak_equity_usd:
            self.peak_equity_usd = current_equity_usd
            self.save_state()

        if self.peak_equity_usd <= 0:
            return None

        drawdown_pct = ((self.peak_equity_usd - current_equity_usd) / self.peak_equity_usd) * 100.0
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        if drawdown_pct >= self.config.max_drawdown_pct:
            return GuardianEvaluation(
                action=self._resolve_action(GuardianAction.PROTECT),
                rule=GuardianRuleType.MAX_DRAWDOWN,
                asset="PORTFOLIO",
                severity=GuardianSeverity.CRITICAL,
                trigger_value=drawdown_pct,
                threshold=self.config.max_drawdown_pct,
                evidence=[
                    f"Historical Peak Equity: ${self.peak_equity_usd:.2f} USD.",
                    f"Current Equity: ${current_equity_usd:.2f} USD.",
                    f"Total Drawdown: -{drawdown_pct:.2f}% (Ceiling: {self.config.max_drawdown_pct}%)."
                ],
                reason=f"Max Portfolio Drawdown breached: equity is down -{drawdown_pct:.2f}% from peak (${self.peak_equity_usd:.2f}). Trading halted to preserve capital.",
                timestamp=now_ts,
                execution_mode=self.config.execution_mode,
                requires_confirmation=self._requires_confirmation(),
                suggested_action_type="CLOSE_POSITION"
            )

        return None

    # -------------------------------------------------------------------------
    # FULL AUDIT CYCLE & UNIFIED EXECUTION GATEWAY ROUTING
    # -------------------------------------------------------------------------

    async def evaluate_all(self, live_prices: Optional[Dict[str, float]] = None) -> List[GuardianEvaluation]:
        """
        Runs deterministic evaluation across all 8 rules on active trades and portfolio.
        """
        evaluations: List[GuardianEvaluation] = []
        if not self.sub_wallet:
            return evaluations

        live_prices = live_prices or {}
        trades = list(getattr(self.sub_wallet, "ongoing_trades", []))
        holdings = getattr(self.sub_wallet, "holdings", {})

        # Compute total portfolio valuation
        cash = float(getattr(self.sub_wallet, "cash_usd", 0.0))
        spot_val = 0.0
        for asset, data in holdings.items():
            if asset in ("USDT", "USDC", "USD", "FDUSD"):
                continue
            qty = data.get("free", 0.0) + data.get("locked", 0.0)
            p = live_prices.get(f"{asset}USDT", data.get("price_usd", 0.0))
            spot_val += qty * p

        unrealized_pnl = 0.0
        for t in trades:
            sym = t.get("symbol", "BTCUSDT")
            lp = live_prices.get(sym, t.get("current_price", 0.0))
            if lp > 0:
                t["current_price"] = lp
                # Record tick for flash crash
                self.record_price_tick(sym, lp)
            unrealized_pnl += float(t.get("unrealized_pnl_usd", 0.0))

        total_portfolio_usd = cash + spot_val + unrealized_pnl

        # 1-3. Trade-Level Rules (SL, Trailing Stop, TP)
        for trade in trades:
            sym = trade.get("symbol", "BTCUSDT")
            lp = live_prices.get(sym, trade.get("current_price", 0.0))
            if lp <= 0:
                continue

            # Rule 1: Hard Stop Loss
            ev_sl = self.evaluate_hard_stop_loss(trade, lp)
            if ev_sl:
                evaluations.append(ev_sl)

            # Rule 2: Trailing Stop
            ev_ts = self.evaluate_trailing_stop(trade, lp)
            if ev_ts:
                evaluations.append(ev_ts)

            # Rule 3: Take Profit
            ev_tp = self.evaluate_take_profit(trade, lp)
            if ev_tp:
                evaluations.append(ev_tp)

            # Rule 6: Flash Crash on active symbol
            ev_fc = self.evaluate_flash_crash(sym, lp)
            if ev_fc:
                evaluations.append(ev_fc)

        # 4. Position Concentration
        eval_conc = self.evaluate_position_concentration(holdings, trades, total_portfolio_usd)
        evaluations.extend(eval_conc)

        # 5. Total Portfolio Exposure
        eval_exp = self.evaluate_total_exposure(trades, total_portfolio_usd)
        if eval_exp:
            evaluations.append(eval_exp)

        # 7. Daily Loss Limit
        eval_dll = self.evaluate_daily_loss_limit(trades, total_portfolio_usd)
        if eval_dll:
            evaluations.append(eval_dll)

        # 8. Max Drawdown
        eval_dd = self.evaluate_max_drawdown(total_portfolio_usd)
        if eval_dd:
            evaluations.append(eval_dd)

        return evaluations

    def _build_breach_fingerprint(self, ev: GuardianEvaluation) -> str:
        """Constructs a deterministic unique fingerprint for a specific breach state."""
        return f"{ev.rule.value}_{ev.asset}_{ev.target_trade_id}_{round(ev.trigger_value, 2)}"

    def _is_duplicate_breach(self, ev: GuardianEvaluation) -> bool:
        """Checks if a breach evaluation has already been processed within the cooldown window."""
        fp = self._build_breach_fingerprint(ev)
        last_triggered = self.processed_breach_fingerprints.get(fp, 0.0)
        return (time.time() - last_triggered) < self.cooldown_seconds

    async def execute_protection(self, ev: GuardianEvaluation) -> Optional[GuardianIncident]:
        """
        Routes a deterministic protection evaluation through UnifiedExecutionGateway.
        Strictly enforces idempotency and audit incident creation.
        """
        now_ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        incident_id = f"INC-{int(time.time()*1000)}-{uuid.uuid4().hex[:4]}"

        # Deduplication Fingerprint check
        if self._is_duplicate_breach(ev):
            fingerprint = self._build_breach_fingerprint(ev)
            logger.info(f"[GUARDIAN] Skipping duplicate incident for fingerprint: {fingerprint}")
            return None

        fingerprint = self._build_breach_fingerprint(ev)
        self.processed_breach_fingerprints[fingerprint] = time.time()

        # Create Incident record
        incident = GuardianIncident(
            incident_id=incident_id,
            timestamp=now_ts,
            asset=ev.asset,
            rule=ev.rule,
            trigger=ev.trigger_value,
            threshold=ev.threshold,
            portfolio_state_ref={
                "peak_equity_usd": self.peak_equity_usd,
                "daily_starting_equity_usd": self.daily_starting_equity_usd,
                "execution_mode": self.config.execution_mode.value,
            },
            action=ev.action,
            execution_environment=getattr(self.gateway, "environment", "SIMULATED") if self.gateway else "SIMULATED",
            explanation=ev.reason
        )

        # Handle Mode: MONITOR_ONLY
        if self.config.execution_mode == GuardianExecutionMode.MONITOR_ONLY:
            incident.result = "ALERTED"
            self.incidents.append(incident)
            logger.info(f"[GUARDIAN MONITOR_ONLY] Recorded Alert: {ev.reason}")
            return incident

        # Handle Mode: ASSISTED
        if self.config.execution_mode == GuardianExecutionMode.ASSISTED:
            incident.result = "PROPOSAL_GENERATED"
            self.incidents.append(incident)
            logger.info(f"[GUARDIAN ASSISTED] Generated Protection Proposal: {ev.reason}")
            return incident

        # Handle Mode: AUTONOMOUS_GUARD (Routes strictly through UnifiedExecutionGateway)
        if not self.gateway:
            incident.result = "FAILED_NO_GATEWAY"
            incident.explanation += " (UnifiedExecutionGateway not attached)."
            self.incidents.append(incident)
            logger.error("[GUARDIAN] Cannot execute protection: UnifiedExecutionGateway is not attached.")
            return incident

        try:
            # Build Gateway ExecutionRequest
            req = None
            if ev.suggested_action_type == "CLOSE_POSITION":
                req = ExecutionRequest(
                    action_type=ExecutionActionType.CLOSE_POSITION,
                    symbol=ev.asset,
                    trade_id_to_close=ev.target_trade_id,
                    exit_price=ev.suggested_params.get("exit_price"),
                    close_reason=f"Guardian [{ev.rule.value}]: {ev.reason}",
                    source="GUARDIAN",
                    idempotency_key=f"IDEM-GDN-{incident_id}"
                )
            elif ev.suggested_action_type == "UPDATE_LEVELS":
                req = ExecutionRequest(
                    action_type=ExecutionActionType.UPDATE_LEVELS,
                    symbol=ev.asset,
                    trade_id_to_close=ev.target_trade_id,
                    stop_loss=ev.suggested_params.get("new_stop_loss"),
                    take_profit=ev.suggested_params.get("take_profit"),
                    source="GUARDIAN",
                    idempotency_key=f"IDEM-GDN-{incident_id}"
                )

            if req:
                receipt: ExecutionReceipt = await self.gateway.execute(req)
                incident.gateway_order_id = receipt.order_id
                incident.gateway_receipt = receipt.dict() if hasattr(receipt, "dict") else receipt.__dict__
                if receipt.status == ExecutionStatus.SUCCESS:
                    incident.result = "EXECUTED"
                    incident.explanation += f" (Executed via Gateway Order {receipt.order_id})."
                else:
                    incident.result = "REJECTED_BY_GATEWAY"
                    incident.explanation += f" (Gateway Rejected: {receipt.rejection_reason})."
            else:
                incident.result = "SKIPPED_NO_ACTION_MAPPING"

        except Exception as e:
            incident.result = "FAILED_EXCEPTION"
            incident.explanation += f" (Execution Exception: {e})"
            logger.error(f"[GUARDIAN] Exception during gateway execution: {e}")

        self.incidents.append(incident)
        return incident

    async def run_cycle(self, live_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Executes one full surveillance, detection, and protection cycle.
        """
        evaluations = await self.evaluate_all(live_prices=live_prices)
        executed_incidents = []

        for ev in evaluations:
            if ev.action in (GuardianAction.PROTECT, GuardianAction.PREPARE_PROTECTION, GuardianAction.ALERT):
                inc = await self.execute_protection(ev)
                if inc:
                    executed_incidents.append(inc.to_dict())

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "execution_mode": self.config.execution_mode.value,
            "peak_equity_usd": self.peak_equity_usd,
            "evaluations_count": len(evaluations),
            "breaches_detected": len([e for e in evaluations if e.action != GuardianAction.NO_ACTION]),
            "incidents_created": len(executed_incidents),
            "incidents": executed_incidents,
        }

    # -------------------------------------------------------------------------
    # HELPER RESOLVERS
    # -------------------------------------------------------------------------

    def _resolve_action(self, base_action: GuardianAction) -> GuardianAction:
        if self.config.execution_mode == GuardianExecutionMode.MONITOR_ONLY:
            return GuardianAction.ALERT
        elif self.config.execution_mode == GuardianExecutionMode.ASSISTED:
            return GuardianAction.PREPARE_PROTECTION
        return base_action

    def _requires_confirmation(self) -> bool:
        return self.config.execution_mode == GuardianExecutionMode.ASSISTED

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns diagnostic status of Guardian."""
        return {
            "execution_mode": self.config.execution_mode.value,
            "peak_equity_usd": round(self.peak_equity_usd, 2),
            "daily_starting_equity_usd": round(self.daily_starting_equity_usd, 2),
            "current_day": self.current_day_str,
            "realized_pnl_today_usd": round(self.realized_pnl_today_usd, 2),
            "total_incidents": len(self.incidents),
            "recent_incidents": [inc.to_dict() for inc in self.incidents[-10:]],
            "active_high_water_marks": self.high_water_marks,
        }

