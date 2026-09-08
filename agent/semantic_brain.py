"""
SYRAX — General AI Semantic Brain & Task Planning Layer
Combines:
1. Multi-turn context resolution (pronouns, candidates list, previous orders, active trade plans)
2. Semantic intent understanding (TALK vs THINK vs ACT)
3. Commodity & Traditional Finance Detection (Oil, Gold, Stocks, Macro) without crypto hallucination
4. Opportunity discovery, market comparison, risk reasoning, coding, and general knowledge
5. Natural, ChatGPT/Claude-level response synthesis without canned boilerplate
"""

import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("syrax.semantic_brain")

class SemanticBrain:
    """
    Intelligent Semantic Understanding & Response Synthesis Engine for SYRAX.
    Understands user meaning first before determining domains, tools, or execution paths.
    """

    COMMODITIES = {
        "oil": "OIL",
        "crude": "CRUDE_OIL",
        "crude oil": "CRUDE_OIL",
        "brent": "BRENT_CRUDE",
        "wti": "WTI_CRUDE",
        "petroleum": "PETROLEUM",
        "gold": "GOLD",
        "xau": "GOLD",
        "xauusd": "GOLD",
        "silver": "SILVER",
        "xag": "SILVER",
        "xagusd": "SILVER",
        "natural gas": "NATURAL_GAS",
        "gasoline": "GASOLINE",
        "copper": "COPPER",
        "wheat": "WHEAT",
        "corn": "CORN"
    }

    TRADITIONAL_STOCKS = {
        "tesla": "TSLA",
        "tsla": "TSLA",
        "apple": "AAPL",
        "aapl": "AAPL",
        "nvidia": "NVDA",
        "nvda": "NVDA",
        "microsoft": "MSFT",
        "msft": "MSFT",
        "amazon": "AMZN",
        "amzn": "AMZN",
        "google": "GOOGL",
        "goog": "GOOGL",
        "googl": "GOOGL",
        "meta": "META",
        "s&p": "SP500",
        "s&p 500": "SP500",
        "sp500": "SP500",
        "nasdaq": "NASDAQ",
        "dow": "DOW_JONES",
        "dow jones": "DOW_JONES",
        "dxy": "DXY"
    }

    @classmethod
    def parse_intent(
        cls,
        query: str,
        history: List[Dict[str, Any]],
        context_state: Any
    ) -> Dict[str, Any]:
        """
        Performs semantic analysis to determine domain, intent, entity references,
        action type (TALK / THINK / ACT), and required tools.
        """
        q = query.strip()
        q_low = q.lower()

        # -------------------------------------------------------------
        # 1. CASUAL CONVERSATION & SMALL TALK (TALK)
        # -------------------------------------------------------------
        casual_greetings = [
            "hi", "hello", "hey", "hii", "heyy", "wassup", "wasup", "what's up", "whats up",
            "yo", "howdy", "sup", "good morning", "good evening", "good afternoon", "good night"
        ]
        if q_low in casual_greetings or any(q_low == f"{g} bro" or q_low == f"{g} buddy" or q_low == f"{g} man" or q_low == f"{g} syrax" for g in casual_greetings):
            return {
                "action_type": "TALK",
                "domain": "GENERAL",
                "intent": "CASUAL_CONVERSATION",
                "target_asset": None,
                "confidence": 0.99,
                "requires_tools": []
            }

        if any(w in q_low for w in [
            "how's your day", "how is your day", "hows your day", "how's your day going",
            "how are you doing", "how r u", "how do you do", "kemon acho", "ki khobor", "ki obostha", "kemon asen"
        ]):
            return {
                "action_type": "TALK",
                "domain": "GENERAL",
                "intent": "CASUAL_CONVERSATION",
                "target_asset": None,
                "confidence": 0.99,
                "requires_tools": []
            }

        if any(q_low == w or q_low.startswith(f"{w} ") for w in [
            "thanks", "thank you", "thanks bro", "dhonnobad", "thx", "thx bro", "great job", "awesome bro", "nice work"
        ]):
            return {
                "action_type": "TALK",
                "domain": "GENERAL",
                "intent": "CASUAL_CONVERSATION",
                "target_asset": None,
                "confidence": 0.99,
                "requires_tools": []
            }

        if any(w in q_low for w in ["who are you", "what are you", "what can you do", "introduce yourself", "tumi ke", "ki kaj koro", "ki korte paro"]):
            return {
                "action_type": "TALK",
                "domain": "GENERAL",
                "intent": "CASUAL_CONVERSATION",
                "target_asset": None,
                "confidence": 0.99,
                "requires_tools": []
            }

        # -------------------------------------------------------------
        # 2. GENERAL KNOWLEDGE, SCIENCE & CODING (TALK)
        # -------------------------------------------------------------
        if any(w in q_low for w in ["joke", "funny", "make me laugh", "humor", "hasao"]):
            return {
                "action_type": "TALK",
                "domain": "GENERAL",
                "intent": "GENERAL_QUESTION",
                "sub_type": "JOKE",
                "target_asset": None,
                "confidence": 0.98,
                "requires_tools": []
            }

        # Science, physics, economics & world knowledge
        general_knowledge_cues = [
            "quantum", "quantum computing", "recursion", "photosynthesis", "speed of light",
            "distance from", "capital of", "who wrote", "why is the sky blue", "why is sky blue",
            "what is inflation", "explain inflation", "what causes inflation", "how does inflation work",
            "fibonacci", "theory of relativity", "black hole", "dna", "crispr", "machine learning"
        ]
        if any(w in q_low for w in general_knowledge_cues):
            return {
                "action_type": "TALK",
                "domain": "GENERAL",
                "intent": "GENERAL_QUESTION",
                "target_asset": None,
                "confidence": 0.98,
                "requires_tools": []
            }

        # Programming & code generation
        if any(w in q_low for w in [
            "python function", "write a python", "write a code", "write a script", "javascript function",
            "reverse a string", "write code", "code for", "program to", "write an algorithm"
        ]):
            return {
                "action_type": "TALK",
                "domain": "CODING",
                "intent": "CODE_GENERATION",
                "target_asset": None,
                "confidence": 0.99,
                "requires_tools": []
            }

        # -------------------------------------------------------------
        # 3. NON-CRYPTO COMMODITIES & TRADITIONAL FINANCE (TALK / INFORM)
        # e.g., "tell me this week all news about oil and analyze its market", "analyze gold", "lets talk about oill market"
        # -------------------------------------------------------------
        for comm_name, comm_code in cls.COMMODITIES.items():
            if re.search(r'\b' + re.escape(comm_name) + r'\b', q_low) or (comm_name == "oil" and ("oill" in q_low or "oiil" in q_low or "oyl" in q_low)):
                return {
                    "action_type": "TALK",
                    "domain": "COMMODITY",
                    "intent": "NON_CRYPTO_MARKET_INQUIRY",
                    "target_asset": comm_code,
                    "asset_name": comm_name.title(),
                    "confidence": 0.98,
                    "requires_tools": []
                }

        for stock_name, stock_code in cls.TRADITIONAL_STOCKS.items():
            if re.search(r'\b' + re.escape(stock_name) + r'\b', q_low) or (stock_name == "tesla" and ("teslla" in q_low or "tslaa" in q_low)):
                return {
                    "action_type": "TALK",
                    "domain": "TRADITIONAL_FINANCE",
                    "intent": "NON_CRYPTO_MARKET_INQUIRY",
                    "target_asset": stock_code,
                    "asset_name": stock_name.upper(),
                    "confidence": 0.98,
                    "requires_tools": []
                }

        if any(re.search(r'\b' + re.escape(w) + r'\b', q_low) for w in ["forex", "commodities", "commodity", "stocks", "stock market", "traditional finance"]):
            return {
                "action_type": "TALK",
                "domain": "NON_CRYPTO_MARKET",
                "intent": "NON_CRYPTO_MARKET_INQUIRY",
                "target_asset": "NON_CRYPTO",
                "asset_name": "Traditional/Non-Crypto Markets",
                "confidence": 0.98,
                "requires_tools": []
            }

        # -------------------------------------------------------------
        # 4. EDUCATIONAL FINANCIAL & CRYPTO CONCEPTS (TALK)
        # e.g. "what is leverage?", "explain slippage", "how does funding rate work"
        # -------------------------------------------------------------
        concept_cues = [
            "what is leverage", "explain leverage", "how does leverage work", "leverage ki", "can you explain leverage",
            "what is funding rate", "explain funding", "how do funding rates work", "funding rate ki",
            "what is slippage", "explain slippage", "slippage ki", "how does slippage happen",
            "what is liquidation", "explain liquidation", "liquidation price ki",
            "what is spot", "difference between spot and futures", "spot vs future",
            "what is rsi", "what is macd", "what is orderbook depth", "what is spread in trading",
            "what is a stop loss", "why use stop loss"
        ]
        if any(w in q_low for w in concept_cues) or (
            q_low.startswith("what is ") and any(w in q_low for w in ["leverage", "funding", "slippage", "liquidation", "orderbook", "spread", "stop loss"])
        ):
            return {
                "action_type": "TALK",
                "domain": "CRYPTO",
                "intent": "EXPLANATION",
                "target_asset": None,
                "confidence": 0.98,
                "requires_tools": []
            }

        # -------------------------------------------------------------
        # 5. OPPORTUNITY DISCOVERY & RADAR (THINK)
        # -------------------------------------------------------------
        # Check if query has an explicit crypto asset mentioned first
        explicit_asset = None
        for sym in ["BTC", "ETH", "SOL", "BNB", "DOGE", "SUI", "AVAX", "LINK", "PEPE", "NEAR", "XRP", "ADA", "SHIB", "DOT", "LTC", "APT", "INJ"]:
            if re.search(r'\b' + re.escape(sym) + r'\b', query.upper()):
                explicit_asset = f"{sym}USDT"
                break

        opp_cues = [
            "potential token", "potential coin", "potential tokens", "potential coins",
            "tokens for this week", "coins for this week", "tokens to watch", "coins to watch",
            "interesting to watch", "interesting token", "interesting coins", "on your radar",
            "what's on your radar", "whats on your radar", "alts are looking good", "looking juicy",
            "worth keeping an eye on", "worth keeping tabs on", "top gainers", "alpha coins",
            "breakout tokens", "recommend some tokens", "suggest some coins", "what should i watch",
            "market radar", "best coins this week", "opportunity this week", "scan the market",
            "top opportunities", "kon coin valo", "konta kinbo", "konta valo", "kisu token suggest koro",
            "find me something interesting", "what tokens look interesting", "find me a good crypto setup",
            "find me a setup with", "find me a crypto setup", "find a setup", "find me a trade setup",
            "find me a setup", "tradeable opportunities", "tradeable opportunity", "interesting tradeable",
            "best opportunity", "find opportunities", "screen opportunities", "market scan", "scan market",
            "find the most interesting", "prioritizing liquidity", "controlled risk", "valovabei invest"
        ]

        # If it's a general discovery/setup search WITHOUT an explicit crypto asset:
        if not explicit_asset and (any(w in q_low for w in opp_cues) or (
            any(k in q_low for k in ["opportunity", "opportunities", "tradeable", "setup", "token", "coin", "alt", "market"]) and
            any(w in q_low for w in ["potential", "watch", "radar", "week", "juicy", "suggest", "good", "interesting", "eye", "find", "screen", "scan", "liquidity", "risk", "top", "best"])
        )):
            return {
                "action_type": "THINK",
                "domain": "CRYPTO_MARKET",
                "intent": "OPPORTUNITY_DISCOVERY",
                "timeframe": "THIS_WEEK" if "week" in q_low else "INTRADAY",
                "target_asset": None,
                "confidence": 0.98,
                "requires_tools": ["market_scan", "news_sentry"]
            }

        # -------------------------------------------------------------
        # 6. PRONOUN / CONTEXTUAL REFERENCE RESOLUTION (THINK / ACT)
        # e.g. "which one looks strongest?", "what about risk?", "why?", "give me an entry"
        # -------------------------------------------------------------
        if any(q_low.startswith(w) for w in ["which one", "which token", "which coin", "which is best", "pick one"]):
            return {
                "action_type": "THINK",
                "domain": "CRYPTO_MARKET",
                "intent": "CONTEXTUAL_COMPARISON",
                "target_asset": getattr(context_state, "active_asset", None),
                "confidence": 0.95,
                "requires_tools": ["market_scan", "symbol_analysis"]
            }

        if q_low in ["why", "why?", "why is that", "explain why", "karon ki"]:
            return {
                "action_type": "THINK",
                "domain": "CRYPTO_MARKET",
                "intent": "CONTEXTUAL_EXPLANATION",
                "target_asset": getattr(context_state, "active_asset", None),
                "confidence": 0.95,
                "requires_tools": ["symbol_analysis"]
            }

        if any(w in q_low for w in [
            "what about risk", "what about the risk", "how about risk", "how about the risk",
            "how is the risk", "risk comparison", "risk kemon", "is it risky", "risk evaluation",
            "risk profile", "tell me the risk", "evaluate the risk", "check the risk",
            "with 1% risk", "with 1 percent risk", "with risk"
        ]):
            return {
                "action_type": "THINK",
                "domain": "TRADING",
                "intent": "RISK_EVALUATION",
                "target_asset": getattr(context_state, "active_asset", None),
                "confidence": 0.95,
                "requires_tools": ["risk_engine", "news_sentry"]
            }

        if any(w in q_low for w in [
            "give me an entry", "what's the entry", "give me entry", "setup for that",
            "entry, sl and tp", "entry sl tp", "would you trade it", "would you buy it",
            "should i trade it", "so should i trade it", "would you long it", "should i buy it",
            "should i long it", "setup for"
        ]):
            target = explicit_asset or getattr(context_state, "active_asset", None)
            recent_cands = getattr(context_state, "recent_candidates", [])
            if not target and recent_cands:
                target = recent_cands[0]
            if not target:
                target = "BTCUSDT"

            return {
                "action_type": "THINK",
                "domain": "TRADING",
                "intent": "TRADE_PLAN",
                "target_asset": target,
                "confidence": 0.94,
                "requires_tools": ["symbol_analysis", "risk_engine"]
            }

        # Contextual execution: "do it", "execute that", "okay do it", "buy 20 dollars of that", "buy $20 of that"
        if q_low in ["do it", "okay do it", "execute it", "execute that", "go ahead", "koro", "kine felo"] or (
            any(w in q_low for w in ["of that", "of it", "of the first one", "of the second one"]) and any(w in q_low for w in ["buy", "long", "short", "sell", "kinte"])
        ):
            target = getattr(context_state, "active_asset", None)
            recent_cands = getattr(context_state, "recent_candidates", [])
            if "first" in q_low and recent_cands:
                target = recent_cands[0]
            elif "second" in q_low and len(recent_cands) > 1:
                target = recent_cands[1]
            elif not target and recent_cands:
                target = recent_cands[0]

            amt_match = re.search(r'\$\s*(\d+(?:\.\d+)?)', q) or re.search(r'(\d+(?:\.\d+)?)\s*(?:dollars?|usd|usdt|\$)', q, re.IGNORECASE)
            parsed_amt = float(amt_match.group(1)) if amt_match else 20.0

            return {
                "action_type": "ACT",
                "domain": "EXECUTION",
                "intent": "EXECUTE_TRADE",
                "target_asset": target or "BTCUSDT",
                "amount_usd": parsed_amt,
                "confidence": 0.95,
                "requires_tools": ["risk_engine", "news_sentry", "execution"]
            }

        # -------------------------------------------------------------
        # 7. ORDER CANCEL / STATUS (ACT / THINK)
        # -------------------------------------------------------------
        if any(w in q_low for w in ["cancel that order", "cancel the remainder", "forget that order", "cancel order", "cancel pending", "cancel my order", "order cancel"]):
            return {
                "action_type": "ACT",
                "domain": "EXECUTION",
                "intent": "CANCEL_ORDER",
                "target_asset": getattr(context_state, "active_asset", None),
                "confidence": 0.98,
                "requires_tools": ["execution"]
            }

        if any(w in q_low for w in ["how much has filled", "how much filled", "is it filled", "order status", "check order", "fill status"]):
            return {
                "action_type": "THINK",
                "domain": "ORDER",
                "intent": "ORDER_STATUS",
                "target_asset": getattr(context_state, "active_asset", None),
                "confidence": 0.98,
                "requires_tools": ["execution"]
            }

        # -------------------------------------------------------------
        # 8. PORTFOLIO & REBALANCE (THINK / ACT)
        # -------------------------------------------------------------
        if any(w in q_low for w in ["my assets", "my holdings", "my portfolio", "show portfolio", "check balance", "amar asset", "amar holding", "ki ki token ache", "what do i hold"]):
            return {
                "action_type": "THINK",
                "domain": "PORTFOLIO",
                "intent": "PORTFOLIO_INQUIRY",
                "target_asset": None,
                "confidence": 0.96,
                "requires_tools": ["portfolio"]
            }

        if "rebalance" in q_low:
            return {
                "action_type": "ACT",
                "domain": "EXECUTION",
                "intent": "REBALANCE",
                "target_asset": "PORTFOLIO",
                "confidence": 0.95,
                "requires_tools": ["portfolio", "execution"]
            }

        # Default fallback: return structured intent
        return {
            "action_type": "THINK",
            "domain": "GENERAL",
            "intent": "GENERAL_INQUIRY",
            "target_asset": None,
            "confidence": 0.85,
            "requires_tools": []
        }
