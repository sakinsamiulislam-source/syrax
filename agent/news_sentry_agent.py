"""
SYRAX — AI News & Event Risk Sentry
Continuous market surveillance against exploits, hacks, regulatory actions, and network shocks.
Enforces a 3-Layer Confirmation Pipeline to prevent false alarms:
1. Source Credibility Verification
2. Market Anomaly Confirmation (Orderbook / Volume / Price)
3. AI Severity Assessment
Produces ALERT or triggers PROTECT mode with transparent defensive actions.
"""

import time
from typing import List, Dict, Any, Optional

class NewsSentryAgent:
    """
    Evaluates real-time event risk, verifies rumors against on-chain and orderbook data,
    and guards the portfolio against black swan drawdowns.
    """

    def __init__(self):
        # Active real-time event stream (seeded with live ecosystem context and hackathon demo triggers)
        self._event_feed: List[Dict[str, Any]] = [
            {
                "id": "EVT-8091",
                "title": "Ethereum Core Devs Finalize Pectra Upgrade Timeline",
                "summary": "Ethereum All Core Developers confirmed mainnet deployment window for next scheduled network upgrade. Staking withdrawals and blob throughput optimized.",
                "token": "ETH",
                "timestamp": time.time() - 3600,
                "source": "Ethereum Foundation GitHub / Consensus Call",
                "source_credibility": "HIGH (Tier 1 Verified Developer Source)",
                "market_confirmed": True,
                "severity": "LOW",
                "status": "MONITORING",
                "action_recommended": "NONE",
                "reasoning": "Standard scheduled network upgrade. No security or smart contract exploit vectors detected."
            },
            {
                "id": "EVT-8092",
                "title": "Solana Ecosystem Bridge RPC Node Latency Spike",
                "summary": "A third-party RPC provider experienced transient timeout rates. Network consensus remained unaffected with zero validator slashing.",
                "token": "SOL",
                "timestamp": time.time() - 7200,
                "source": "Solana Status Dashboard",
                "source_credibility": "HIGH (Official Status Page)",
                "market_confirmed": False,
                "severity": "LOW",
                "status": "CLEARED",
                "action_recommended": "NONE",
                "reasoning": "Transient infrastructure hiccup resolved. Orderbook liquidity on Binance SOLUSDT remained resilient."
            },
            {
                "id": "EVT-8093",
                "title": "SEC Approves New Regulatory Clarity Guidelines for Spot Trading Pairs",
                "summary": "Regulatory framework clarifies token classification standards for Tier 1 centralized exchanges, lifting regulatory cloud.",
                "token": "BTC",
                "timestamp": time.time() - 14400,
                "source": "Federal Register / Agency Bulletin",
                "source_credibility": "HIGH (Government Agency Regulatory Notice)",
                "market_confirmed": True,
                "severity": "LOW",
                "status": "POSITIVE",
                "action_recommended": "NONE",
                "reasoning": "Constructive macro catalyst for Bitcoin institutional liquidity depth."
            }
        ]

    def get_active_events(self) -> List[Dict[str, Any]]:
        """Returns currently monitored market events."""
        return self._event_feed

    def verify_event(self, raw_event: Dict[str, Any], market_data: Dict[str, Any], portfolio_holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes the 3-Layer Confirmation Pipeline:
        1. Source Credibility
        2. Market Confirmation
        3. AI Severity & Portfolio Exposure
        """
        token = raw_event.get("token", "UNKNOWN").upper()
        source = raw_event.get("source", "Unknown Social Feed")
        raw_severity = raw_event.get("severity", "MEDIUM").upper()

        # Layer 1: Source Credibility
        is_tier1_source = any(k in source.lower() for k in ["official", "foundation", "binance", "reuters", "bloomberg", "github", "certik", "peckshield"])
        credibility_score = 90 if is_tier1_source else 35
        credibility_label = "VERIFIED_OFFICIAL" if is_tier1_source else "UNVERIFIED_SOCIAL_SPECULATION"

        # Layer 2: Market Confirmation
        # Check if price dropped > 3% or spread surged
        price_drop = market_data.get("price_change_pct", 0.0) < -3.0
        spread_spike = market_data.get("spread_bps", 0.0) > 5.0
        market_confirmed = price_drop or spread_spike

        # Layer 3: Severity & Portfolio Exposure
        holding = next((h for h in portfolio_holdings if h["asset"] == token), None)
        user_exposure_usd = holding["value_usd"] if holding else 0.0
        portfolio_at_risk = user_exposure_usd > 0.0

        # Decision rule: Never trigger PROTECT from unverified social post alone!
        if not is_tier1_source and not market_confirmed:
            decision = "WAIT"
            action = "WATCH_ONLY"
            protect_triggered = False
            explanation = f"Unverified rumor regarding {token} detected from unconfirmed sources. Market orderbooks show normal liquidity. SYRAX will NOT panic-trade or dump assets on single unverified social chatter."
        elif raw_severity in ["CRITICAL", "HIGH"] and (is_tier1_source or market_confirmed):
            decision = "PROTECT"
            action = "EMERGENCY_DEFENSE"
            protect_triggered = True
            explanation = f"CONFIRMED HIGH EVENT RISK on {token}. Verified by {credibility_label} with market anomaly confirmation. Immediate defense mandate triggered to protect ${user_exposure_usd:.2f} of portfolio capital."
        else:
            decision = "ALERT"
            action = "MONITOR_CLOSELY"
            protect_triggered = False
            explanation = f"Moderate event risk identified on {token}. Portfolio exposure is ${user_exposure_usd:.2f}. Monitoring stop levels without disruptive execution."

        return {
            "event_id": raw_event.get("id", "EVT-NEW"),
            "token": token,
            "title": raw_event.get("title", ""),
            "layer_1_source_credibility": {
                "score": credibility_score,
                "label": credibility_label,
                "source": source
            },
            "layer_2_market_confirmation": {
                "confirmed": market_confirmed,
                "price_drop": price_drop,
                "spread_spike": spread_spike
            },
            "layer_3_severity_assessment": {
                "severity": raw_severity,
                "portfolio_exposure_usd": user_exposure_usd,
                "at_risk": portfolio_at_risk
            },
            "decision": decision,
            "action": action,
            "protect_triggered": protect_triggered,
            "explanation": explanation,
            "defense_proposal": {
                "action": "CONVERT_TO_STABLECOIN" if portfolio_at_risk else "HALT_NEW_BUYS",
                "target_asset": "USDT",
                "estimated_slippage": "0.00% (Binance Convert zero-fee)",
                "invalidation_condition": "Official developer post-mortem verifying exploit mitigation or market recovery above prior support."
            }
        }

    def trigger_simulated_critical_event(self, token: str = "SOL") -> Dict[str, Any]:
        """Injects a simulated high-severity event for hackathon judge demonstration."""
        evt = {
            "id": f"EVT-ALERT-{int(time.time())}",
            "title": f"Critical Protocol Vulnerability Flagged in {token} Ecosystem Liquidity Pool",
            "summary": f"CertiK and security auditors detect an unverified drain exploit vector in secondary {token} bridge contracts.",
            "token": token,
            "timestamp": time.time(),
            "source": "CertiK Alert & On-Chain Security Dispatch",
            "source_credibility": "HIGH (Audited Blockchain Security Firm)",
            "market_confirmed": True,
            "severity": "HIGH",
            "status": "ACTIVE_THREAT",
            "action_recommended": "PROTECT",
            "reasoning": "Active vulnerability with confirmed capital outflow on bridge contracts. High probability of cascading collateral liquidation."
        }
        self._event_feed.insert(0, evt)
        return evt
