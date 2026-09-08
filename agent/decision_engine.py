"""
SYRAX — Master Decision Engine
The cognitive core of SYRAX.
Synthesizes market structure, liquidity quality, event risk, deterministic risk limits,
and available account cash into an authoritative decision:
TRADE | WAIT | NO TRADE | PROTECT
"""

from typing import Dict, Any, Optional

class DecisionEngine:
    """
    Decides the final course of action.
    SYRAX is celebrated not for trading constantly, but for knowing when NOT to trade.
    """

    @staticmethod
    def adjudicate(
        market_analysis: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        sentry_status: Dict[str, Any],
        available_cash_usd: float
    ) -> Dict[str, Any]:
        """
        Adjudicates final trade conviction and safety protocol.
        """
        symbol = market_analysis.get("symbol", "UNKNOWN")
        ai_score = market_analysis.get("ai_score", 50)
        label = market_analysis.get("label", "WATCH")
        liquidity = market_analysis.get("liquidity_quality", "MEDIUM")
        
        # 1. Check Sentry PROTECT Trigger First (Black Swan Guard)
        if sentry_status.get("protect_triggered", False) or sentry_status.get("severity") in ["CRITICAL", "HIGH"]:
            return {
                "decision": "PROTECT",
                "headline": f"DEFENSIVE PROTOCOL ACTIVATED FOR {symbol}",
                "primary_reason": sentry_status.get("explanation", "High event risk detected. Halting aggressive entries."),
                "risk_status": "PROTECT_MODE",
                "invalidation_condition": "Resolution of active security incident and resumption of normal orderbook depth.",
                "max_risk_usd": 0.0,
                "execution_permitted": False,
                "action_type": "PROTECT_PORTFOLIO",
                "confidence_score": 95,
                "explanation": "Event risk takes precedence over all technical chart patterns. Capital preservation protocol activated."
            }

        # 2. Check Trap or Avoid from Market Agent
        if label == "TRAP":
            return {
                "decision": "NO TRADE",
                "headline": f"REJECTED: SUSPECTED LIQUIDITY TRAP ON {symbol}",
                "primary_reason": market_analysis.get("reasoning", "Volume and orderbook depth do not support the price spike."),
                "risk_status": "TRAP_VETO",
                "invalidation_condition": "Sustained price consolidation with genuine institutional volume expansion above resistance.",
                "max_risk_usd": 0.0,
                "execution_permitted": False,
                "action_type": "DO_NOT_ENGAGE",
                "confidence_score": 88,
                "explanation": "SYRAX protects traders from chasing low-volume pumps. Orderbook depth confirms lack of institutional backing."
            }

        if label == "AVOID":
            return {
                "decision": "NO TRADE",
                "headline": f"REJECTED: UNFAVORABLE MARKET PROFILE ON {symbol}",
                "primary_reason": market_analysis.get("reasoning", "Weak orderbook liquidity or strong downtrend."),
                "risk_status": "LIQUIDITY_VETO",
                "invalidation_condition": "Market structure shift and liquidity replenishment.",
                "max_risk_usd": 0.0,
                "execution_permitted": False,
                "action_type": "DO_NOT_ENGAGE",
                "confidence_score": 85,
                "explanation": "Illiquid orderbooks cause excessive execution slippage and erratic wicks."
            }

        # 3. Check Risk Engine Assessment
        if not risk_assessment.get("mandate_compliant", False) or risk_assessment.get("status") == "REJECTED":
            rejection_details = "; ".join(risk_assessment.get("rejection_reasons", ["Risk criteria violated."]))
            return {
                "decision": "NO TRADE",
                "headline": f"RISK ENGINE VETO ON {symbol}",
                "primary_reason": f"Setup failed user-defined risk mandate: {rejection_details}",
                "risk_status": "RISK_REJECTED",
                "invalidation_condition": "Adjusting stop distance or waiting for a setup offering higher Risk/Reward ratio (>1.5R).",
                "max_risk_usd": 0.0,
                "execution_permitted": False,
                "action_type": "HOLD_CASH",
                "confidence_score": 92,
                "explanation": "The trade may look promising on a chart, but the mathematical risk profile violates your mandate. The risk engine has absolute veto power."
            }

        # 4. Check Cash Availability
        recommended_pos = risk_assessment.get("recommended_position_usd", 0.0)
        if recommended_pos > available_cash_usd:
            return {
                "decision": "WAIT",
                "headline": f"INSUFFICIENT UNALLOCATED CASH FOR {symbol}",
                "primary_reason": f"Recommended safe position (${recommended_pos:.2f}) exceeds available liquid cash (${available_cash_usd:.2f}).",
                "risk_status": "CASH_CONSTRAINED",
                "invalidation_condition": "Consolidating idle stablecoins or rebalancing portfolio holdings.",
                "max_risk_usd": 0.0,
                "execution_permitted": False,
                "action_type": "REBALANCE_OR_WAIT",
                "confidence_score": 80,
                "explanation": "SYRAX will not force over-leverage. Use the Cash Manager to convert idle stablecoins or rebalance before entering."
            }

        # 5. Check Market Timing: TRADE vs WAIT
        if ai_score >= 75 and label == "TRADEABLE" and liquidity in ["HIGH", "MEDIUM"]:
            return {
                "decision": "TRADE",
                "headline": f"HIGH CONVICTION OPPORTUNITY IDENTIFIED ON {symbol}",
                "primary_reason": market_analysis.get("reasoning", "Strong market alignment with favorable R:R and deep liquidity."),
                "risk_status": "RISK_APPROVED",
                "invalidation_condition": f"Price breaking and closing below stop loss (${risk_assessment.get('stop_distance_usd')} drawdown).",
                "max_risk_usd": risk_assessment.get("max_dollar_loss", 5.0),
                "execution_permitted": True,
                "action_type": "PREPARE_ASSISTED_ORDER",
                "confidence_score": ai_score,
                "explanation": f"Mandate fully satisfied. Capped at max ${risk_assessment.get('max_dollar_loss', 5.0):.2f} risk with {risk_assessment.get('risk_reward_ratio')}R upside potential."
            }
        else:
            return {
                "decision": "WAIT",
                "headline": f"WAITING FOR OPTIMAL TRIGGER ON {symbol}",
                "primary_reason": market_analysis.get("reasoning", "Setup is consolidating near key pivot. Awaiting volume confirmation."),
                "risk_status": "STANDBY",
                "invalidation_condition": "Loss of structural support or breakdown of the current consolidation zone.",
                "max_risk_usd": 0.0,
                "execution_permitted": False,
                "action_type": "MONITOR_PIVOT",
                "confidence_score": ai_score,
                "explanation": "Patience is alpha. Entering prematurely degrades risk/reward. SYRAX will alert you when breakout confirmation prints."
            }
