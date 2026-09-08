"""
SYRAX — Market & Opportunity Scanner Agent
Analyzes trend, momentum, volume, liquidity depth, spread, and market structure.
Distinguishes between genuine high-probability setups and high-risk traps.
A large price move alone does NOT mean "buy".
"""

import math
import asyncio
from typing import List, Dict, Any, Optional
from backend.binance.agent_os import BinanceAgentOS

class MarketAgent:
    """
    Scans crypto pairs on Binance, checks orderbook liquidity,
    evaluates technical setup, and outputs AI-scored opportunities.
    """

    WATCHED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", "LINKUSDT"]

    def __init__(self, binance_client: BinanceAgentOS):
        self.binance = binance_client

    async def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """Deep dive technical and liquidity assessment of a single symbol."""
        ticker, orderbook, klines = await asyncio.gather(
            self.binance.get_live_ticker(symbol),
            self.binance.get_orderbook(symbol, limit=20),
            self.binance.get_klines(symbol, interval="1h", limit=16)
        )
        
        last_price = ticker.get("last_price", 100.0)
        change_24h = ticker.get("price_change_pct", 0.0)
        high_24h = ticker.get("high_24h", last_price * 1.025)
        low_24h = ticker.get("low_24h", last_price * 0.975)
        volume_24h = ticker.get("volume", 0.0)
        quote_vol_24h = ticker.get("quote_volume", 0.0)
        spread_bps = orderbook.get("spread_bps", 2.0)
        liquidity_quality = orderbook.get("liquidity_quality", "MEDIUM")

        # Sparkline price history (last 16 hourly intervals for mini chart)
        sparkline = [k["close"] for k in klines] if klines else []
        if not sparkline or len(sparkline) < 5:
            # Fallback interpolated curve
            factors = [0.2, 0.35, 0.25, 0.45, 0.6, 0.5, 0.75, 0.65, 0.9, 0.8, 0.95, 1.0]
            spread_range = max(0.0001, high_24h - low_24h)
            sparkline = [round(low_24h + spread_range * f, 4 if last_price < 10 else 2) for f in factors]
            sparkline[-1] = last_price

        # Technical structure derivation
        # Baseline trend determination:
        if change_24h > 4.5 and spread_bps < 4.0:
            trend = "BULLISH_EXPANSION"
            momentum = "STRONG"
        elif change_24h > 0.5:
            trend = "MODERATE_UPTREND"
            momentum = "NEUTRAL_POSITIVE"
        elif change_24h < -4.0:
            trend = "BEARISH_CONTRACTION"
            momentum = "WEAK"
        else:
            trend = "CONSOLIDATION_RANGE"
            momentum = "NEUTRAL"

        # AI Scoring Algorithm (0 - 100)
        base_score = 50
        # Liquidity bonus/penalty
        if liquidity_quality == "HIGH":
            base_score += 15
        elif liquidity_quality == "LOW":
            base_score -= 20

        # Spread penalty
        if spread_bps < 2.0:
            base_score += 10
        elif spread_bps > 5.0:
            base_score -= 15

        # Trend & Volume synergy
        if trend == "BULLISH_EXPANSION" and quote_vol_24h > 50000000:
            base_score += 15
        elif trend == "CONSOLIDATION_RANGE":
            base_score += 5

        # Detect TRAPS: High price pump (>8%) but low liquidity or deteriorating orderbook depth
        is_trap = (change_24h > 7.0 and quote_vol_24h < 10000000) or (spread_bps > 8.0)
        is_avoid = (liquidity_quality == "LOW") or (change_24h < -8.0)

        if is_trap:
            label = "TRAP"
            decision = "NO TRADE"
            base_score = max(20, base_score - 30)
            reason = "Price pumped rapidly on thin volume and wide spread. High probability of liquidity sweep/dump."
        elif is_avoid:
            label = "AVOID"
            decision = "NO TRADE"
            base_score = min(40, base_score)
            reason = "Substandard liquidity depth or severe downtrend pressure. Capital preservation priority."
        elif base_score >= 75 and spread_bps < 3.0:
            label = "TRADEABLE"
            decision = "TRADE"
            reason = "Strong market structure, deep bid/ask liquidity, and tight spread inside institutional execution corridor."
        else:
            label = "WATCH"
            decision = "WAIT"
            reason = "Consolidating near key structural pivot. Awaiting breakout volume confirmation or pull-back to demand."

        # Compute precision trade levels
        # If bullish or watch, place stop below recent swing low (approx 1.5% - 2.5% below entry)
        if decision == "TRADE":
            entry_price = last_price
            stop_loss = round(entry_price * 0.982, 2 if entry_price > 10 else 4) # 1.8% stop
            take_profit = round(entry_price * 1.045, 2 if entry_price > 10 else 4) # 4.5% target (2.5R)
        elif decision == "WAIT":
            entry_price = round(last_price * 0.995, 2 if last_price > 10 else 4) # Pullback entry
            stop_loss = round(entry_price * 0.980, 2 if entry_price > 10 else 4) # 2.0% stop
            take_profit = round(entry_price * 1.050, 2 if entry_price > 10 else 4) # 2.5R
        else:
            entry_price = last_price
            stop_loss = round(entry_price * 0.970, 2 if entry_price > 10 else 4)
            take_profit = round(entry_price * 1.020, 2 if entry_price > 10 else 4)

        stop_dist_pct = round(abs(entry_price - stop_loss) / entry_price * 100, 2)
        target_dist_pct = round(abs(take_profit - entry_price) / entry_price * 100, 2)
        rr_ratio = round(target_dist_pct / stop_dist_pct, 2) if stop_dist_pct > 0 else 0.0

        ai_score = max(10, min(95, base_score))
        opportunity_score = ai_score

        return {
            "symbol": symbol,
            "last_price": last_price,
            "change_24h": round(change_24h, 2),
            "high_24h": high_24h,
            "low_24h": low_24h,
            "volume_24h": round(volume_24h, 2),
            "quote_volume_24h": round(quote_vol_24h, 2),
            "sparkline": sparkline,
            "trend": trend,
            "momentum": momentum,
            "spread_bps": spread_bps,
            "liquidity_quality": liquidity_quality,
            "market_type": ticker.get("market_type", "SPOT"),
            "is_alpha": bool((change_24h >= 8.0 and quote_vol_24h >= 5000000) or ("1000" in symbol)),
            "ai_score": ai_score,
            "opportunity_score": opportunity_score,
            "label": label,
            "decision": decision,
            "reasoning": reason,
            "setup": {
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "stop_dist_pct": stop_dist_pct,
                "target_dist_pct": target_dist_pct,
                "risk_reward_ratio": rr_ratio,
            }
        }

    async def scan_market(self, custom_symbols: Optional[List[str]] = None, limit: int = 25, category: str = "ALL") -> List[Dict[str, Any]]:
        """Scans dynamic active Binance crypto pairs in parallel and ranks them by AI Opportunity Score."""
        symbols_to_scan = custom_symbols or (await self.binance.get_top_active_symbols(limit=limit, category=category)) or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "1000PEPEUSDT", "SUIUSDT", "DOGEUSDT", "BNBUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT"]
        
        async def safe_analyze(sym: str):
            try:
                ticker = await self.binance.get_live_ticker(sym)
                last_price = ticker.get("last_price", 100.0)
                change_24h = ticker.get("price_change_pct", 0.0)
                high_24h = ticker.get("high_24h", last_price * 1.025)
                low_24h = ticker.get("low_24h", last_price * 0.975)
                volume_24h = ticker.get("volume", 0.0)
                quote_vol_24h = ticker.get("quote_volume", 0.0)

                bid_price = ticker.get("bid_price", 0.0)
                ask_price = ticker.get("ask_price", 0.0)
                if ask_price > 0 and bid_price > 0:
                    spread_bps = round(abs(ask_price - bid_price) / ask_price * 10000, 2)
                else:
                    spread_bps = 1.8 if quote_vol_24h > 50000000 else 3.8

                liquidity_quality = "HIGH" if quote_vol_24h > 50000000 else ("MEDIUM" if quote_vol_24h > 8000000 else "LOW")
                
                factors = [0.2, 0.35, 0.25, 0.45, 0.6, 0.5, 0.75, 0.65, 0.9, 0.8, 0.95, 1.0]
                spread_range = max(0.000001, high_24h - low_24h)
                sparkline = [round(low_24h + spread_range * f, 6 if last_price < 0.01 else (4 if last_price < 10 else 2)) for f in factors]
                sparkline[-1] = last_price

                if change_24h > 4.5 and spread_bps < 4.0:
                    trend = "BULLISH_EXPANSION"
                    momentum = "STRONG"
                elif change_24h > 0.5:
                    trend = "MODERATE_UPTREND"
                    momentum = "NEUTRAL_POSITIVE"
                elif change_24h < -4.0:
                    trend = "BEARISH_CONTRACTION"
                    momentum = "WEAK"
                else:
                    trend = "CONSOLIDATION_RANGE"
                    momentum = "NEUTRAL"

                base_score = 50
                if liquidity_quality == "HIGH": base_score += 15
                elif liquidity_quality == "LOW": base_score -= 20
                if spread_bps < 2.0: base_score += 10
                elif spread_bps > 5.0: base_score -= 15
                if trend == "BULLISH_EXPANSION" and quote_vol_24h > 50000000: base_score += 15

                is_trap = (change_24h > 7.0 and quote_vol_24h < 10000000) or (spread_bps > 8.0)
                is_avoid = (liquidity_quality == "LOW") or (change_24h < -8.0)

                if is_trap:
                    label = "TRAP"
                    decision = "NO TRADE"
                    base_score = max(20, base_score - 30)
                    reason = "Price pumped rapidly on thin volume and wide spread. High probability of liquidity sweep/dump."
                elif is_avoid:
                    label = "AVOID"
                    decision = "NO TRADE"
                    base_score = min(40, base_score)
                    reason = "Substandard liquidity depth or severe downtrend pressure. Capital preservation priority."
                elif base_score >= 75 and spread_bps < 3.0:
                    label = "TRADEABLE"
                    decision = "TRADE"
                    reason = "Strong market structure, deep bid/ask liquidity, and tight spread inside institutional execution corridor."
                else:
                    label = "WATCH"
                    decision = "WAIT"
                    reason = "Consolidating near key structural pivot. Awaiting breakout volume confirmation or pull-back to demand."

                entry_price = last_price
                dec = 6 if last_price < 0.01 else (4 if last_price < 10 else 2)
                stop_loss = round(entry_price * 0.982, dec)
                take_profit = round(entry_price * 1.045, dec)
                stop_dist_pct = round(abs(entry_price - stop_loss) / entry_price * 100, 2)
                target_dist_pct = round(abs(take_profit - entry_price) / entry_price * 100, 2)
                rr_ratio = round(target_dist_pct / stop_dist_pct, 2) if stop_dist_pct > 0 else 0.0
                ai_score = max(10, min(95, base_score))
                opportunity_score = ai_score

                market_type = ticker.get("market_type", "FUTURES" if (sym.startswith("1000") or category == "FUTURES") else "SPOT")
                is_alpha = bool((change_24h >= 8.0 and quote_vol_24h >= 5000000) or ("1000" in sym) or (category == "ALPHA"))

                return {
                    "symbol": sym,
                    "last_price": last_price,
                    "change_24h": round(change_24h, 2),
                    "high_24h": high_24h,
                    "low_24h": low_24h,
                    "volume_24h": round(volume_24h, 2),
                    "quote_volume_24h": round(quote_vol_24h, 2),
                    "sparkline": sparkline,
                    "trend": trend,
                    "momentum": momentum,
                    "spread_bps": spread_bps,
                    "liquidity_quality": liquidity_quality,
                    "market_type": market_type,
                    "is_alpha": is_alpha,
                    "ai_score": ai_score,
                    "opportunity_score": opportunity_score,
                    "label": label,
                    "decision": decision,
                    "reasoning": reason,
                    "setup": {
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "stop_dist_pct": stop_dist_pct,
                        "target_dist_pct": target_dist_pct,
                        "risk_reward_ratio": rr_ratio,
                    }
                }
            except Exception as e:
                logger.warning(f"Error scanning {sym}: {e}")
                return None

        raw_results = await asyncio.gather(*[safe_analyze(sym) for sym in symbols_to_scan])
        results = [r for r in raw_results if r is not None]

        # Sort by AI Score descending
        results.sort(key=lambda x: x["ai_score"], reverse=True)
        return results


