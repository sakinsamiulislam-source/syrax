import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from collections import deque

from agent.execution_gateway import ExecutionRequest, ExecutionActionType
from agent.post_trade_guardian import (
    PostTradeGuardian,
    GuardianConfig,
    GuardianExecutionMode,
    GuardianAction,
    GuardianSeverity,
    GuardianRuleType
)

logger = logging.getLogger("syrax.monitor")


class AutonomousMonitorDaemon:
    """
    24/7 Autonomous Sentinel Daemon.
    Powered by the deterministic PostTradeGuardian.
    Periodically checks active sub-wallet trades, mark-to-market valuations,
    holding drift, trailing stops, flash crashes, drawdown, and security sentry radar.
    """

    def __init__(self, binance_os, sub_wallet, news_agent, gateway=None, guardian_config=None):
        self.binance = binance_os
        self.sub_wallet = sub_wallet
        self.news_agent = news_agent
        self.gateway = gateway
        self.is_running = False
        self.is_paused = False
        self._task: Optional[asyncio.Task] = None
        self.interval_seconds = 12
        self.last_pulse_timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        self.check_count = 0
        
        # Instantiate Deterministic Post-Trade Guardian
        self.guardian = PostTradeGuardian(
            gateway=self.gateway,
            sub_wallet=self.sub_wallet,
            binance_os=self.binance,
            sentry_agent=self.news_agent,
            config=guardian_config or GuardianConfig()
        )

        # In-memory circular event buffer
        self.event_log: deque = deque(maxlen=50)

        # Pre-seed with initial system initialization event
        self._record_event(
            severity="INFO",
            category="HEARTBEAT",
            message="Autonomous 24/7 Sentinel initialized with Deterministic Post-Trade Guardian."
        )

    def _record_event(self, severity: str, category: str, message: str, meta: Optional[Dict[str, Any]] = None):
        """Records an audit event into the circular log buffer."""
        evt = {
            "id": f"EVT-{int(time.time()*1000)}",
            "timestamp": time.strftime("%H:%M:%S UTC", time.gmtime()),
            "severity": severity,  # INFO, WARNING, CRITICAL, SUCCESS
            "category": category,  # TRADE_WATCH, PORTFOLIO_DRIFT, SENTRY_RADAR, HEARTBEAT
            "message": message,
            "meta": meta or {}
        }
        self.event_log.appendleft(evt)
        logger.info(f"[{severity}] [{category}] {message}")

    async def start(self):
        """Starts the autonomous surveillance background loop."""
        if self.is_running:
            return
        self.is_running = True
        self.is_paused = False
        self._task = asyncio.create_task(self._surveillance_loop())
        logger.info("Autonomous Monitor Daemon started.")

    def pause(self):
        """Pauses surveillance ticks."""
        self.is_paused = True
        self._record_event("WARNING", "HEARTBEAT", "Autonomous surveillance paused by user.")

    def resume(self):
        """Resumes surveillance ticks."""
        self.is_paused = False
        self._record_event("SUCCESS", "HEARTBEAT", "Autonomous surveillance resumed.")

    async def _surveillance_loop(self):
        """Main periodic surveillance tick."""
        while self.is_running:
            try:
                if not self.is_paused:
                    await self._execute_surveillance_tick()
            except Exception as e:
                logger.error(f"Error in surveillance tick: {e}")
            await asyncio.sleep(self.interval_seconds)

    async def _execute_surveillance_tick(self):
        """Executes a single surveillance pass across trades, holdings, and sentry."""
        self.check_count += 1
        self.last_pulse_timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        # 1. Fetch live prices for all relevant symbols
        symbols_to_query = set()
        for t in self.sub_wallet.ongoing_trades:
            symbols_to_query.add(t["symbol"])
        for o in getattr(self.sub_wallet, "pending_orders", []):
            symbols_to_query.add(o["symbol"])
        for asset in self.sub_wallet.holdings.keys():
            if asset not in ("USDT", "USDC", "USD", "FDUSD"):
                symbols_to_query.add(f"{asset}USDT")

        price_map = {}
        for sym in symbols_to_query:
            norm_sym = self.binance.normalize_symbol(sym)
            ticker = await self.binance.get_live_ticker(norm_sym)
            if ticker.get("last_price") and ticker["last_price"] > 0:
                price_map[sym] = ticker["last_price"]
                price_map[norm_sym] = ticker["last_price"]

        # 2. Update mark-to-market Unrealized PnL in sub-wallet
        self.sub_wallet.update_live_prices(price_map)

        # 3. Deterministic Post-Trade Guardian Surveillance Cycle (Evaluates all 8 hard rules)
        guardian_res = await self.guardian.run_cycle(live_prices=price_map)
        for inc in guardian_res.get("incidents", []):
            sev_map = {
                "PROTECT": "CRITICAL",
                "PREPARE_PROTECTION": "WARNING",
                "ALERT": "WARNING",
                "NO_ACTION": "INFO"
            }
            action_val = inc.get("action", "INFO")
            sev = sev_map.get(action_val, "INFO")
            rule_val = inc.get("rule", "GUARDIAN")
            expl_val = inc.get("explanation", "")
            res_val = inc.get("result", "")
            self._record_event(
                severity=sev,
                category="GUARDIAN_WATCH",
                message=f"[{rule_val}] {expl_val} (Result: {res_val})",
                meta=inc
            )

        # 3.5. Audit Pending Limit Orders for Fill Conditions (strictly when live market price reaches limit target)
        for order in list(getattr(self.sub_wallet, "pending_orders", [])):
            sym = order["symbol"]
            norm_sym = self.binance.normalize_symbol(sym)
            curr = price_map.get(sym) or price_map.get(norm_sym)
            
            # DO NOT fill if live price is not yet available or <= 0
            if curr is None or curr <= 0:
                continue

            side = order["side"]
            limit_p = order["limit_price"]

            # BUY condition: live market price <= limit price (price fell to or below limit)
            # SELL condition: live market price >= limit price (price rose to or above limit)
            is_fillable = (side in ("BUY", "LONG") and curr <= limit_p) or (side in ("SELL", "SHORT") and curr >= limit_p)
            if is_fillable and order.get("status") in ("PENDING", "PARTIALLY_FILLED"):
                fill_res = self.sub_wallet.process_fill(order["order_id"], fill_price=limit_p)
                if fill_res.get("success"):
                    self._record_event(
                        severity="SUCCESS",
                        category="TRADE_WATCH",
                        message=f"LIMIT ORDER FILLED: {sym} {side} @ ${limit_p:.4f} (Live Market: ${curr:.4f}). Fill: {fill_res['order']['fill_percentage']}%.",
                        meta={"order_id": order["order_id"], "symbol": sym, "fill": fill_res.get("fill")}
                    )

        # 4. Audit Portfolio Allocation Drift
        if self.check_count % 3 == 0:
            analysis = self.sub_wallet.get_holdings_analysis(price_map)
            for h in analysis["holdings"]:
                if h["drift_status"] == "OVERWEIGHT" and abs(h["drift_pct"]) > 6.0:
                    self._record_event(
                        severity="WARNING",
                        category="PORTFOLIO_DRIFT",
                        message=f"{h['asset']} allocation overweight by +{h['drift_pct']}%. Target is {h['target_allocation_pct']}%, actual is {h['actual_allocation_pct']}%."
                    )

        # 5. Audit Threat Sentry Radar
        active_events = self.news_agent.get_active_events()
        for evt in active_events:
            t = evt.get("token")
            if t and any(t in asset_name for asset_name in self.sub_wallet.holdings.keys()):
                self._record_event(
                    severity="CRITICAL",
                    category="SENTRY_RADAR",
                    message=f"SENTRY ALERT: {evt.get('title')} affecting held asset {t}. Risk Sentinel active."
                )

    def get_status(self) -> Dict[str, Any]:
        """Returns live monitoring status and recent event feed."""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "interval_seconds": self.interval_seconds,
            "last_pulse": self.last_pulse_timestamp,
            "total_checks": self.check_count,
            "active_monitored_trades": len(self.sub_wallet.ongoing_trades),
            "guardian": self.guardian.get_status_summary(),
            "events": list(self.event_log)
        }
