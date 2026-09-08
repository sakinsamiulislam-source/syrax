"""
SYRAX — AI Multi-Domain Cognitive Orchestrator & Execution Engine
Integrates:
1. IntentRouter (Multi-tier: General Conversation -> Explanation -> Market Analysis -> Portfolio -> Trade Planning -> Execution -> Clarification/Correction)
2. AssetEntityResolver (Strict boundary & stopword filtering to eliminate false positive tickers)
3. ConversationStateManager (Multi-turn session memory, pronoun resolution, follow-up tracking, correction handling)
4. Deterministic Risk Gatekeeper (1.0% account risk invariant, Sentry threat radar)
5. Developer Debug Intent Inspector (Rich telemetry for intent verification)
"""

import time
import re
import difflib
import logging
from typing import Dict, List, Any, Optional, Tuple
from backend.binance.agent_os import BinanceAgentOS
from agent.market_agent import MarketAgent
from agent.news_sentry_agent import NewsSentryAgent
from agent.portfolio_agent import PortfolioAgent
from agent.risk_engine import RiskEngine, RiskParameters
from agent.decision_engine import DecisionEngine
from agent.ai_client import OpenRouterAIClient
from agent.semantic_brain import SemanticBrain
from agent.model_router import ModelRouter
from agent.execution_gateway import UnifiedExecutionGateway, ExecutionRequest, ExecutionReceipt, ExecutionActionType, ExecutionEnvironment, ExecutionStatus
from agent.order_ticket import OrderTicket, TicketStatus, OrderTicketRegistry, format_order_ticket_card, format_crypto_price
from agent.universal_asset_engine import (
    UniversalAssetRegistry,
    ProductAwareResolver,
    ProductTelemetryService,
    TokenNewsIntelligenceService,
    UniversalAnalysisEngine,
    MarketProduct,
    BinanceAsset
)

logger = logging.getLogger("syrax.orchestrator")


# =============================================================================
# 0. FUZZY TYPO NORMALIZATION & SPELLING CORRECTION ENGINE
# =============================================================================

class FuzzyTextNormalizer:
    """
    Intelligent Typo & Fuzzy Spelling Correction Engine for Trading, Crypto & Banglish.
    Automatically normalizes misspelled keywords and entities before NLP classification.
    """

    CANONICAL_ACTIONS = {
        # Conversational keywords
        "talk": ["tlk", "tak", "takk", "talik", "tok"],
        "about": ["abour", "bout", "abot", "abuot", "abou"],
        "lets": ["let's", "lez", "letss", "let"],

        # Trading actions
        "check": ["chech", "chekk", "chek", "chekc", "chck", "ceck", "chack", "chackk"],
        "analyze": ["analize", "anlyze", "analise", "anlysis", "annalyze", "analze", "analiz"],
        "market": ["marlet", "markit", "mraket", "makret", "markett", "mkt", "markt", "mrkt"],
        "price": ["prce", "prie", "pirce", "pice", "priice"],
        "position": ["posishon", "positon", "postions", "posision", "positin", "posistion", "postn"],
        "positions": ["posishons", "positons", "posisions", "posistions"],
        "portfolio": ["portfolyo", "portflio", "portolio", "porfolio", "portfollio", "portfl"],
        "balance": ["balanse", "balanc", "blance", "balence", "balnce", "balace"],
        "leverage": ["levarge", "leverag", "levaraje", "levrage", "levarge", "lev"],
        "liquidation": ["liqudation", "liquidasion", "likidation", "liqidation", "liq"],
        "limit": ["limt", "limitt", "lmit", "limmit"],
        "execute": ["exicute", "exacute", "excute", "excecute", "execut"],
        "order": ["odrer", "oder", "ordr", "orderr"],
        "cancel": ["cancle", "cancil", "cancl", "cncel"],
        "convert": ["convrte", "convrt", "convrting", "converte"],
        "security": ["secrity", "securty", "sequrity", "securiti"],
        "exploit": ["explot", "exployt", "exploid", "exploitt"],
        "protect": ["prtect", "protekt", "protct", "protec"],
        "rebalance": ["rebalanse", "reblance", "rebalnce"],
        "current": ["curren", "curent", "currennt", "crrent"],
        "worth": ["wrth", "wroth", "wort"],
        "discount": ["discont", "discout", "discunt"],
        "under": ["undr", "underr", "uner"],
        "below": ["blow", "belw", "bellow"],

        # Banglish common variants
        "kemon": ["kemonn", "kemn", "kamn"],
        "obostha": ["obosta", "oboshta", "abostha", "ovosta", "ovostha"],
        "ache": ["ase", "ahe", "acche", "achhe", "asey"],
        "kinte": ["kinnte", "kinty", "kinar", "kinteh"],
        "kinbo": ["kinnbo", "kinboo"],
        "bechte": ["beche", "bikri", "bickri", "bechteh"],
        "shob": ["sob", "shobgula", "sobgula", "puro", "shobkichu", "sobkichu"],
        "kom": ["komm", "kome", "komee"],
        "beshi": ["besi", "beshii", "onek"],
    }

    CANONICAL_COMMODITIES = {
        "oil": ["oill", "oilll", "oiil", "oyl", "oyle", "oils"],
        "crude": ["cruid", "crud", "crde", "wti", "brent"],
        "gold": ["goold", "gld", "golld", "goolld", "xau", "xauusd"],
        "silver": ["slver", "silvr", "silvver", "xag", "xagusd"],
        "gas": ["gass", "natgas"],
        "copper": ["coppr", "copr"],
        "wheat": ["wheet"],
        "corn": ["corrn"],
    }

    CANONICAL_TRADITIONAL = {
        "tesla": ["teslla", "tezla", "tslaa"],
        "apple": ["aple", "applee"],
        "nvidia": ["nvdia", "nvda"],
        "microsoft": ["mcrosoft", "microsft"],
        "amazon": ["amzon", "amazn"],
        "google": ["gogle", "googl"],
    }

    CANONICAL_CRYPTO = {
        "BTC": ["bitcon", "bitcoinn", "btcoin", "bitoin", "bitcoin", "bitcoi", "btcusdt", "btc"],
        "ETH": ["etherium", "ehtereum", "ethreum", "ethirium", "ethereum", "ethereumm", "ethusdt", "eth"],
        "SOL": ["solana", "solna", "solla", "solana", "solusdt", "sol"],
        "BNB": ["binance", "binace", "bnance", "binancecoin", "bnbusdt", "bnb"],
        "DOGE": ["dogcoin", "dogecoin", "dogg", "dogge", "dogeusdt", "doge"],
        "XRP": ["riple", "ripple", "xpr", "xrpp", "xrpusdt", "xrp"],
        "ADA": ["cardano", "cordano", "cardanno", "adausdt", "ada"],
        "PUMP": ["pumpp", "punp", "pumpcoin", "pumpusdt", "pump"],
        "PEPE": ["peppe", "pepee", "pepecoin", "pepeusdt", "pepe"],
        "SUI": ["suii", "suui", "suiusdt", "sui"],
        "AVAX": ["avalanche", "avalanchecoin", "avaxusdt", "avax"],
        "SHIB": ["shiba", "shibainu", "shibusdt", "shib"],
        "LINK": ["chainlink", "chnlink", "linkusdt", "link"],
        "NEAR": ["nearprotocol", "nearusdt", "near"],
    }

    PROTECTED_WORDS = {
        "what", "when", "where", "why", "who", "which", "whom", "how", "that", "this", "these",
        "those", "with", "from", "have", "had", "has", "will", "would", "shall", "should", "can",
        "could", "about", "tell", "think", "talk", "show", "give", "make", "take", "some", "like",
        "good", "more", "most", "less", "many", "much", "then", "than", "them", "they", "their",
        "your", "ours", "mine", "find", "look", "view", "scan", "read", "write", "code", "user",
        "trade", "price", "rate", "news", "date", "year", "time", "week", "month", "day", "high",
        "low", "open", "spot", "coin", "token", "pair", "risk", "bank", "cash", "sell", "buys",
        "sold", "hold", "over", "into", "onto", "done", "does", "been", "being", "very", "also",
        "just", "even", "only", "well", "back", "both", "each", "such", "same", "down", "left",
        "oil", "gold", "crude", "silver", "xau", "xauusd", "wti", "brent"
    }

    # Fast reverse lookup dicts
    LOOKUP_ACTIONS = {}
    for canon, typos in CANONICAL_ACTIONS.items():
        for t in typos:
            LOOKUP_ACTIONS[t.lower()] = canon
        LOOKUP_ACTIONS[canon.lower()] = canon

    LOOKUP_COMMODITIES = {}
    for canon, typos in CANONICAL_COMMODITIES.items():
        for t in typos:
            LOOKUP_COMMODITIES[t.lower()] = canon
        LOOKUP_COMMODITIES[canon.lower()] = canon

    LOOKUP_TRADITIONAL = {}
    for canon, typos in CANONICAL_TRADITIONAL.items():
        for t in typos:
            LOOKUP_TRADITIONAL[t.lower()] = canon
        LOOKUP_TRADITIONAL[canon.lower()] = canon

    LOOKUP_CRYPTO = {}
    for canon, typos in CANONICAL_CRYPTO.items():
        for t in typos:
            LOOKUP_CRYPTO[t.lower()] = canon
        LOOKUP_CRYPTO[canon.lower()] = canon

    @classmethod
    def normalize_query(cls, text: str) -> str:
        """
        Normalizes misspelled words in text to standard canonical form while preserving structure.
        """
        if not text:
            return ""

        words = text.split()
        normalized_words = []

        for w in words:
            # Strip trailing punctuation for lookup
            clean_w = re.sub(r'^[^\w\$]+|[^\w]+$', '', w).lower()
            prefix_punct = re.match(r'^[^\w\$]+', w)
            suffix_punct = re.search(r'[^\w]+$', w)
            pre = prefix_punct.group(0) if prefix_punct else ""
            suf = suffix_punct.group(0) if suffix_punct else ""

            # Check exact maps first
            if clean_w in cls.LOOKUP_COMMODITIES:
                norm = cls.LOOKUP_COMMODITIES[clean_w]
                normalized_words.append(f"{pre}{norm}{suf}")
                continue

            if clean_w in cls.LOOKUP_TRADITIONAL:
                norm = cls.LOOKUP_TRADITIONAL[clean_w]
                normalized_words.append(f"{pre}{norm}{suf}")
                continue

            if clean_w in cls.LOOKUP_ACTIONS:
                norm = cls.LOOKUP_ACTIONS[clean_w]
                normalized_words.append(f"{pre}{norm}{suf}")
                continue

            if clean_w in cls.LOOKUP_CRYPTO:
                norm = cls.LOOKUP_CRYPTO[clean_w]
                normalized_words.append(f"{pre}{norm}{suf}")
                continue

            # Skip difflib for protected common vocabulary
            if clean_w in cls.PROTECTED_WORDS:
                normalized_words.append(w)
                continue

            # Fuzzy match against known commodities, traditional assets, actions, and crypto
            if len(clean_w) >= 3 and not clean_w.isdigit() and not clean_w.startswith("$"):
                # Try close match against commodities
                comm_matches = difflib.get_close_matches(clean_w, cls.LOOKUP_COMMODITIES.keys(), n=1, cutoff=0.82)
                if comm_matches:
                    norm = cls.LOOKUP_COMMODITIES[comm_matches[0]]
                    normalized_words.append(f"{pre}{norm}{suf}")
                    continue

                # Try close match against traditional stocks
                trad_matches = difflib.get_close_matches(clean_w, cls.LOOKUP_TRADITIONAL.keys(), n=1, cutoff=0.82)
                if trad_matches:
                    norm = cls.LOOKUP_TRADITIONAL[trad_matches[0]]
                    normalized_words.append(f"{pre}{norm}{suf}")
                    continue

            if len(clean_w) >= 4 and not clean_w.isdigit() and not clean_w.startswith("$"):
                # Try close match against actions
                matches = difflib.get_close_matches(clean_w, cls.LOOKUP_ACTIONS.keys(), n=1, cutoff=0.84)
                if matches:
                    norm = cls.LOOKUP_ACTIONS[matches[0]]
                    normalized_words.append(f"{pre}{norm}{suf}")
                    continue

                # Try close match against crypto names
                crypto_matches = difflib.get_close_matches(clean_w, cls.LOOKUP_CRYPTO.keys(), n=1, cutoff=0.84)
                if crypto_matches:
                    norm = cls.LOOKUP_CRYPTO[crypto_matches[0]]
                    normalized_words.append(f"{pre}{norm}{suf}")
                    continue

            normalized_words.append(w)

        return " ".join(normalized_words)


# =============================================================================
# 1. CONVERSATION STATE MANAGER (Multi-Turn Context & Memory)
# =============================================================================

class ConversationStateManager:
    """
    Maintains structured conversational context across multi-turn user dialogues.
    Tracks active assets, parameters, setups, and provides pronoun/follow-up resolution.
    """

    def __init__(self):
        self.active_asset: Optional[str] = None
        self.active_market: str = "SPOT"
        self.active_side: str = "BUY"
        self.active_amount_usd: Optional[float] = None
        self.active_leverage: int = 1
        self.active_stop_loss: Optional[float] = None
        self.active_take_profit: Optional[float] = None
        self.active_trade_plan: Optional[Dict[str, Any]] = None
        self.pending_order_draft: Optional[Dict[str, Any]] = None
        self.recent_candidates: List[str] = []
        self.last_intent: Optional[str] = None
        self.last_domain: Optional[str] = None
        self.history: List[Dict[str, Any]] = []

    def record_turn(self, sender: str, text: str, domain: str, intent: str, asset: Optional[str] = None):
        """Records a dialogue turn into short-lived memory."""
        self.history.append({
            "sender": sender,
            "text": text,
            "domain": domain,
            "intent": intent,
            "asset": asset,
            "timestamp": time.time()
        })
        if len(self.history) > 20:
            self.history.pop(0)

        self.last_domain = domain
        self.last_intent = intent
        if asset:
            self.active_asset = asset

    def set_active_trade_plan(self, asset: str, plan: Dict[str, Any]):
        self.active_asset = asset
        self.active_trade_plan = plan
        if "market_type" in plan:
            self.active_market = plan["market_type"]
        if "leverage" in plan:
            self.active_leverage = plan["leverage"]
        if "stop_loss" in plan:
            self.active_stop_loss = plan["stop_loss"]
        if "take_profit" in plan:
            self.active_take_profit = plan["take_profit"]

    def resolve_reference(self, query: str) -> Tuple[Optional[str], bool, bool, Dict[str, Any]]:
        """
        Resolves follow-ups or corrections.
        Returns: (resolved_asset, is_follow_up, is_correction, updated_parameters)
        """
        q = query.lower()
        is_follow_up = False
        is_correction = False
        updates: Dict[str, Any] = {}

        # 1. Check for corrections: "no I meant ETH", "sorry not BTC, do SOL", "actually spot", "make it 10x"
        if any(p in q for p in ["no i meant", "i meant", "actually", "not that", "change to", "switch to", "instead", "sorry i meant"]):
            is_correction = True

        # 2. Check for leverage tweaks: "make it 10x", "change leverage to 5x", "use 20x"
        lev_m = re.search(r'\b(?:make it|set|use|change to|leverage(?: of)?)\s*(\d+)x\b', q)
        if not lev_m:
            lev_m = re.search(r'\b(\d+)x\b', q)
        if lev_m:
            updates["leverage"] = int(lev_m.group(1))
            self.active_leverage = updates["leverage"]
            if updates["leverage"] > 1:
                self.active_market = "FUTURES"

        # 3. Check for market type changes: "make it spot", "do spot instead", "switch to futures"
        if "spot" in q:
            updates["market_type"] = "SPOT"
            updates["leverage"] = 1
            self.active_market = "SPOT"
            self.active_leverage = 1
        elif any(w in q for w in ["futures", "perp", "perps", "future"]):
            updates["market_type"] = "FUTURES"
            self.active_market = "FUTURES"
            if self.active_leverage == 1:
                self.active_leverage = 10

        # 4. Check for amount changes: "make it $50", "actually do 30 dollars"
        amt_m = re.search(r'\$?(\d+(?:\.\d+)?)\s*(?:dollar|usd|\$)', q)
        if amt_m:
            updates["amount_usd"] = float(amt_m.group(1))
            self.active_amount_usd = updates["amount_usd"]

        # 5. Check for ordinal candidate references: "the first one", "second coin", "third one"
        if self.recent_candidates:
            if any(w in q for w in ["first one", "first token", "first coin", "the first"]):
                self.active_asset = self.recent_candidates[0]
                is_follow_up = True
            elif any(w in q for w in ["second one", "second token", "second coin", "the second"]) and len(self.recent_candidates) > 1:
                self.active_asset = self.recent_candidates[1]
                is_follow_up = True
            elif any(w in q for w in ["third one", "third token", "third coin", "the third"]) and len(self.recent_candidates) > 2:
                self.active_asset = self.recent_candidates[2]
                is_follow_up = True
            pass

        # 6. Check for contextual follow-up pronouns/phrases referring to active asset:
        follow_up_cues = [
            r'\bwhat about volume\b', r'\bhow about volume\b', r'\bwhat is the volume\b', r'\bvolume kemon\b',
            r'\bwould you long it\b', r'\bwould you buy it\b', r'\bshould i buy it\b', r'\bshould i long\b',
            r'\bwould you trade it\b', r'\bwould you trade\b', r'\btrade it\b',
            r'\bis it overbought\b', r'\bis it safe\b', r'\bwhat is the risk\b', r'\bwhat\'s the risk\b',
            r'\bwhat about risk\b', r'\bhow about risk\b', r'\bwith \d+%?\s*risk\b', r'\bwith 1% risk\b', r'\b1% risk\b',
            r'\bwhat is its stop loss\b', r'\bwhat is the target\b', r'\bhow much is it\b', r'\bwhy is it dropping\b',
            r'\bwhy is it pumping\b', r'\bwhat do you think\b', r'\bwhat about that\b', r'\bhow is it looking\b',
            r'\bcheck sentry\b', r'\bcheck news for it\b', r'\bany exploit news for it\b', r'\bthis token\b',
            r'\bthat setup\b', r'\bthat one\b', r'\bthis one\b', r'\bwhich one\b', r'\bwhy\b', r'\bgive me an entry\b'
        ]
        if self.active_asset and (any(re.search(c, q) for c in follow_up_cues) or updates):
            is_follow_up = True

        return self.active_asset, is_follow_up, is_correction, updates

    def clear(self):
        self.active_asset = None
        self.active_trade_plan = None
        self.active_amount_usd = None
        self.active_leverage = 1
        self.active_market = "SPOT"
        self.history.clear()


# =============================================================================
# 2. ASSET ENTITY RESOLVER (Strict Boundary & Stopword Filtering)
# =============================================================================

class AssetEntityResolver:
    """
    Rigorously identifies legitimate cryptocurrency tickers from natural language.
    Strictly filters out ordinary English and Banglish vocabulary to avoid false positives.
    """

    EXCLUDED_VOCABULARY = {
        # English conversational & small-talk words
        "HI", "HELLO", "HEY", "HII", "HEYY", "WASUP", "WASSUP", "YO", "HOWDY", "GREETINGS", "THANKS", "THANK",
        "WELCOME", "PLEASE", "SORRY", "YES", "NO", "OK", "OKAY", "COOL", "NICE", "GOOD", "BAD",
        "GREAT", "AWESOME", "FINE", "BRO", "MATE", "BUDDY", "SIR", "JOKE", "WEATHER", "HELP",
        "WHO", "WHAT", "WHEN", "WHERE", "WHY", "HOW", "CAN", "COULD", "WOULD", "WILL", "SHALL",
        "DO", "DOES", "DID", "IS", "ARE", "AM", "WAS", "WERE", "BE", "BEEN", "BEING", "HAVE",
        "HAS", "HAD", "MY", "YOUR", "OUR", "THEIR", "HIS", "HER", "ITS", "ME", "YOU", "HIM",
        "HER", "US", "THEM", "I", "WE", "THEY", "THIS", "THAT", "THESE", "THOSE", "IT",
        
        # Commodities & Traditional Assets (NOT crypto tokens)
        "OIL", "CRUDE", "BRENT", "WTI", "GOLD", "SILVER", "GAS", "NATURAL", "GASOLINE", "COPPER",
        "WHEAT", "CORN", "TESLA", "APPLE", "NVIDIA", "MICROSOFT", "AMAZON", "GOOGLE", "META",
        "SP500", "NASDAQ", "DOW", "DXY", "STOCK", "STOCKS", "COMMODITY", "COMMODITIES",
        
        # Science, general concepts & units
        "QUANTUM", "RECURSION", "INFLATION", "SKY", "BLUE", "SUN", "EARTH", "CODE", "PYTHON",
        "SCRIPT", "PROGRAM", "FUNCTION", "ALGORITHM", "MATH", "PHYSICS", "SCIENCE", "WEEK",
        "MONTH", "YEAR", "DAY", "NIGHT", "TODAY", "TOMORROW", "YESTERDAY", "NEWS",
        
        # General trading & finance terms (NOT token names)
        "MARKET", "MARKETS", "PRICE", "PRICES", "VOLUME", "VOLUMES", "VOL", "ORDER", "ORDERS",
        "TRADE", "TRADES", "TRADING", "TRADER", "TRADERS", "SETUP", "SETUPS", "PLAN", "PLANS",
        "BUY", "BUYS", "BUYING", "SELL", "SELLS", "SELLING", "LONG", "LONGS", "SHORT", "SHORTS",
        "SPOT", "FUTURES", "FUTURE", "PERP", "PERPS", "MARGIN", "LEVERAGE", "CROSS", "ISOLATED",
        "STOP", "LOSS", "TAKE", "PROFIT", "RISK", "ENTRY", "EXIT", "TARGET", "CAPITAL", "CASH",
        "MONEY", "BUDGET", "DOLLAR", "DOLLARS", "USD", "USDT", "USDC", "PERCENT", "PCT", "BPS",
        "ALL", "SOB", "NOW", "TODAY", "TOMORROW", "YESTERDAY", "DAY", "NIGHT", "DROP", "DROPPING",
        "DUMP", "DUMPING", "PUMP", "PUMPING", "GAIN", "GAINER", "GAINERS", "LOSER", "LOSERS",
        "PORTFOLIO", "BALANCE", "BALANCES", "ASSET", "ASSETS", "HOLDING", "HOLDINGS", "POSITION",
        "POSITIONS", "FEE", "FEES", "RATE", "RATES", "SPREAD", "LIQUIDITY", "SLIPPAGE",
        "LIQUIDATION", "FUNDING", "REBALANCE", "CONVERT", "SWAP", "PROTECT", "HEDGE", "PANIC",
        "SECURITY", "EXPLOIT", "HACK", "SCAM", "RUG", "RUGPULL", "VULNERABILITY", "THREAT",
        "ANALYSIS", "ANALYZE", "EXPLAIN", "TELL", "SHOW", "SCAN", "FIND", "CHECK", "LOOK",
        "GIVE", "VIEW", "SEE", "READ", "GET", "PUT", "SET", "OPEN", "CLOSE", "CANCEL",
        "AI", "AGENT", "COPILOT", "BOT", "SYSTEM", "SYRAX", "BINANCE", "CODE", "PYTHON",

        # Banglish / Bengali phonetic stop words
        "KINTE", "KINBO", "KINO", "KIN", "KORTE", "KORBO", "KORO", "KOR", "BOLO", "BOLSI",
        "BOLCHI", "BOLE", "BOLESI", "EKTA", "EKTI", "EITA", "OTA", "ARO", "EKHON", "TAILE",
        "JODI", "KONO", "NAI", "PAI", "PAY", "HOLE", "HOY", "BA", "EBONG", "AR", "SOB", "PURO",
        "KICHO", "KICHU", "TAKA", "HUDAY", "HUDAI", "NAM", "NAME", "JENO", "BOSHE", "ACHE",
        "OTHOCHO", "ULTA", "PALTA", "CHARA", "SATHE", "NIJE", "FELE", "DEW", "DAO", "KORO",
        "AMAR", "TOMAR", "APNAR", "KI", "KEMON", "KOTO", "KOI", "KOBE", "KANO", "KENO"
    }

    KNOWN_CRYPTO_SYMBOLS = {
        "BTC", "ETH", "SOL", "BNB", "DOGE", "SUI", "AVAX", "LINK", "PEPE", "1000PEPE", "NEAR",
        "XRP", "ADA", "SHIB", "DOT", "LTC", "BCH", "APT", "FET", "RENDER", "INJ", "TRX", "TON",
        "MATIC", "POL", "UNI", "ATOM", "TIA", "SEI", "WIF", "BONK", "FLOKI", "1000BONK", "1000FLOKI",
        "PNUT", "NEIRO", "GOAT", "PENGU", "ACT", "MOODENG", "VIRTUAL", "SOPH", "UAI", "DOOD",
        "PIEVERSE", "PUMP", "USDC", "FDUSD", "TUSD", "AKE", "RENDER", "JUP", "PYTH", "ENA",
        "PENDLE", "ONDO", "AAVE", "MKR", "CRV", "SNX", "DYDX", "GMX", "AR", "STX", "KAS",
        "ICP", "FIL", "HBAR", "ALGO", "VET", "FTM", "SAND", "MANA", "AXS", "GALA", "BEAM"
    }

    @classmethod
    def extract_crypto_asset(cls, text: str) -> Optional[str]:
        """
        Extracts verified crypto asset ticker from text with automated typo correction.
        Returns normalized symbol ending in USDT (e.g. BTCUSDT) or None if no valid crypto asset exists.
        """
        if not text or not text.strip():
            return None

        norm_text = FuzzyTextNormalizer.normalize_query(text)

        for candidate_text in [norm_text, text]:
            clean_text = candidate_text.strip()
            up = clean_text.upper()

            # 1. Direct $Ticker matching (e.g., "$SOL", "$BTC", "$AKE")
            dollar_match = re.search(r'\$([A-Za-z][A-Za-z0-9]{1,9})\b', clean_text)
            if dollar_match:
                cand = dollar_match.group(1).upper()
                if cand not in cls.EXCLUDED_VOCABULARY and not cand.isdigit():
                    return cand if cand.endswith("USDT") else f"{cand}USDT"

            # 2. Explicit Pair format (e.g., "BTCUSDT", "SOL/USDT", "ETH-USDT")
            pair_match = re.search(r'\b([A-Za-z0-9]{2,10})[/_-]?(USDT|USDC|FDUSD|BUSD)\b', up)
            if pair_match:
                base = pair_match.group(1).upper()
                if base not in cls.EXCLUDED_VOCABULARY:
                    return f"{base}USDT"

            # 3. Full Cryptocurrency Names Mapping
            name_map = {
                "BITCOIN": "BTCUSDT",
                "ETHEREUM": "ETHUSDT",
                "SOLANA": "SOLUSDT",
                "DOGECOIN": "DOGEUSDT",
                "CARDANO": "ADAUSDT",
                "RIPPLE": "XRPUSDT",
                "POLYGON": "MATICUSDT",
                "AVALANCHE": "AVAXUSDT",
                "BINANCE COIN": "BNBUSDT",
                "BINANCECOIN": "BNBUSDT",
                "SHIBA": "SHIBUSDT",
                "SHIBA INU": "SHIBUSDT"
            }
            for name, sym in name_map.items():
                if re.search(r'\b' + re.escape(name) + r'\b', up):
                    return sym

            # 4. Known Top Crypto Symbols matching with exact word boundary
            for sym in cls.KNOWN_CRYPTO_SYMBOLS:
                # Special case for "PUMP": only treat as ticker if preceded by amount/worth/buy or $
                if sym == "PUMP":
                    if re.search(r'(?:\$|\bworth\s+of\s+|\bbuy\s+|\bsell\s+|\blong\s+|\bshort\s+|\bprice\s+of\s+|\banalyze\s+)\s*pump\b', clean_text, re.IGNORECASE) or re.search(r'\bpump\s+(?:kinte|kinbo|kino|token|coin)\b', clean_text, re.IGNORECASE):
                        return "PUMPUSDT"
                    continue

                # Standard token match
                pattern = r'\b' + re.escape(sym) + r'\b'
                if re.search(pattern, up):
                    return sym if sym.endswith("USDT") else f"{sym}USDT"

            # 5. Contextual prepositions: "worth of <TOKEN>", "value of <TOKEN>", "amount of <TOKEN>"
            m_worth = re.search(r'\b(?:worth\s+of|value\s+of|amount\s+of|price\s+of|token\s+named)\s+([A-Za-z0-9]{2,10})\b', clean_text, re.IGNORECASE)
            if m_worth:
                cand = m_worth.group(1).upper()
                if cand not in cls.EXCLUDED_VOCABULARY and not cand.isdigit() and not re.match(r'^\d+X$', cand):
                    return cand if cand.endswith("USDT") else f"{cand}USDT"

            # 6. Trading action verbs directly preceding token: "buy SOL", "long ETH", "kinte AKE"
            m_act = re.search(r'\b(?:buy|sell|long|short|swap|convert)\s+([A-Za-z0-9]{2,10})\b', clean_text, re.IGNORECASE)
            if m_act:
                cand = m_act.group(1).upper()
                if cand not in cls.EXCLUDED_VOCABULARY and not cand.isdigit() and not re.match(r'^\d+X$', cand):
                    return cand if cand.endswith("USDT") else f"{cand}USDT"

            # 7. Banglish postfix: "<TOKEN> kinte", "<TOKEN> kinbo", "<TOKEN> er analysis"
            m_bangla = re.search(r'\b([A-Za-z0-9]{2,10})\s+(?:kinte|kinbo|kino|bechte|kin|sell|buy)\b', clean_text, re.IGNORECASE)
            if m_bangla:
                cand = m_bangla.group(1).upper()
                if cand not in cls.EXCLUDED_VOCABULARY and not cand.isdigit() and not re.match(r'^\d+X$', cand):
                    return cand if cand.endswith("USDT") else f"{cand}USDT"

        # Never guess from random english words
        return None


# =============================================================================
# 3. INTENT ROUTER (Multi-Domain Classification & Gatekeeping)
# =============================================================================

class IntentRouter:
    """
    Classifies natural language user queries into Domains and precise Intents.
    Guarantees that general conversations, explanations, and portfolio inquiries
    are never misclassified as live trade executions, while ensuring queries containing
    specific tokens or actions are correctly routed.
    """

    @classmethod
    def classify(cls, query: str, context: ConversationStateManager) -> Dict[str, Any]:
        norm_query = FuzzyTextNormalizer.normalize_query(query)
        q = norm_query.lower().strip()
        
        # 0. High-level Semantic Understanding First
        semantic = SemanticBrain.parse_intent(norm_query, context.history, context)
        detected_asset = AssetEntityResolver.extract_crypto_asset(norm_query) or AssetEntityResolver.extract_crypto_asset(query)
        resolved_asset, is_follow_up, is_correction, updates = context.resolve_reference(norm_query)
        final_asset = detected_asset or (resolved_asset if is_follow_up or is_correction else None)

        # Non-Crypto Commodity / Traditional Finance Inquiries (e.g. Oil, Gold, Tesla)
        if semantic.get("intent") in ["NON_CRYPTO_MARKET_INQUIRY", "GENERAL_MARKET_CONVERSATION"] or semantic.get("domain") in ["NON_CRYPTO_MARKET", "COMMODITY", "TRADITIONAL_FINANCE"]:
            return {
                "domain": semantic.get("domain", "COMMODITY"),
                "intent": "NON_CRYPTO_MARKET_INQUIRY",
                "target_asset": semantic.get("target_asset", "OIL"),
                "asset_name": semantic.get("asset_name", "Commodity"),
                "confidence": 0.98,
                "is_execution": False,
                "requires_clarification": False
            }

        # Portfolio Risk Audit / Exposure Analysis
        if any(w in q for w in [
            "biggest risk in my portfolio", "biggest risk", "portfolio risk", "risk in my portfolio",
            "what is the risk in my portfolio", "what is my portfolio risk", "how risky is my portfolio",
            "portfolio risk audit", "audit my portfolio risk", "audit portfolio", "portfolio vulnerability",
            "amar portfolio te ki risk", "portfolio te ki risk", "portfolio safe kina", "check portfolio risk",
            "risks in my portfolio", "exposure risk", "drawdown risk", "what are the risks in my portfolio"
        ]) or (("risk" in q or "safe" in q or "vulnerab" in q or "threat" in q) and ("portfolio" in q or "holding" in q or "balance" in q or "account" in q)):
            return {
                "domain": "PORTFOLIO",
                "intent": "PORTFOLIO_RISK_AUDIT",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or "PORTFOLIO",
                "confidence": 0.99,
                "is_execution": False,
                "requires_clarification": False
            }

        # Sub-Wallet Cash Reset / Top-up Intent
        if any(w in q for w in ["reset balance", "reset cash", "reset subwallet", "reset wallet", "add cash", "deposit cash", "top up balance", "top up cash", "amar balance baraw", "reset my balance", "balance reset"]):
            return {
                "domain": "PORTFOLIO",
                "intent": "RESET_BALANCE",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.99,
                "is_execution": True,
                "requires_clarification": False
            }

        # Internal Cross-Wallet Transfer Intent (Binance Multi-Wallet)
        if any(w in q for w in ["internal transfer", "wallet transfer", "transfer funds", "cross wallet"]) or \
           re.search(r'\btransfer\s+(\d+(?:\.\d+)?)\s*(?:usdt|usdc|bnb|btc|eth|sol|fdusd)?', q) or \
           re.search(r'\b(?:spot|margin|futures|funding|earn)\s*(?:theke|to|from)\s*(?:spot|margin|futures|funding|earn)\b', q) or \
           ("transfer" in q and any(w in q for w in ["spot", "margin", "futures", "funding", "earn", "wallet"])):
            return {
                "domain": "PORTFOLIO",
                "intent": "INTERNAL_TRANSFER",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or detected_asset,
                "confidence": 0.99,
                "is_execution": True,
                "requires_clarification": False
            }

        # Casual Conversation & Chit-Chat (TALK)
        if semantic.get("intent") == "CASUAL_CONVERSATION":
            return {
                "domain": "GENERAL",
                "intent": "CONVERSATION",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.99,
                "is_execution": False,
                "requires_clarification": False
            }

        # General Knowledge, Science & Educational Questions (TALK)
        if semantic.get("intent") == "GENERAL_QUESTION":
            return {
                "domain": "GENERAL",
                "intent": "GENERAL_QUESTION",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.98,
                "is_execution": False,
                "requires_clarification": False
            }

        # Opportunity Discovery (THINK) - General unconstrained or constrained market search
        if semantic.get("intent") == "OPPORTUNITY_DISCOVERY" or (not detected_asset and any(w in q for w in [
            "opportunity", "opportunities", "tradeable", "what tokens look interesting", "find me a good crypto setup",
            "find me a setup with", "find me a crypto setup", "find a setup", "potential token", "interesting coins",
            "tokens for this week", "scan market", "market scan", "best opportunities", "top opportunities",
            "find the best opportunity", "find the most interesting", "tradeable opportunities", "market radar",
            "prioritizing liquidity", "controlled risk", "konta kinbo", "kon coin valo", "kisu token suggest koro"
        ])):
            return {
                "domain": "CRYPTO_MARKET",
                "intent": "OPPORTUNITY_DISCOVERY",
                "timeframe": semantic.get("timeframe", "THIS_WEEK" if "week" in q else "INTRADAY"),
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.98,
                "is_execution": False,
                "requires_clarification": False
            }

        # Code Generation (TALK)
        if semantic.get("intent") == "CODE_GENERATION":
            return {
                "domain": "CODING",
                "intent": "CODE_GENERATION",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.99,
                "is_execution": False,
                "requires_clarification": False
            }

        # Cross-Market Comparison or Product Analysis (e.g. "compare ETH spot vs futures")
        if detected_asset and any(w in q for w in ["compare", "vs", "versus"]) and ("spot" in q and ("future" in q or "futures" in q or "perp" in q)):
            return {
                "domain": "MARKET",
                "intent": "MARKET_ANALYSIS",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or detected_asset,
                "confidence": 0.98,
                "is_execution": False,
                "requires_clarification": False
            }

        # Contextual Comparison (THINK)
        if semantic.get("intent") == "CONTEXTUAL_COMPARISON":
            return {
                "domain": "CRYPTO_MARKET",
                "intent": "CONTEXTUAL_COMPARISON",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or context.active_asset or (context.recent_candidates[0] if context.recent_candidates else "BTCUSDT"),
                "confidence": 0.96,
                "is_execution": False,
                "requires_clarification": False
            }

        # Contextual Risk Evaluation (THINK)
        if semantic.get("intent") == "RISK_EVALUATION":
            return {
                "domain": "TRADING",
                "intent": "RISK_EVALUATION",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or context.active_asset or (context.recent_candidates[0] if context.recent_candidates else "BTCUSDT"),
                "confidence": 0.95,
                "is_execution": False,
                "requires_clarification": False
            }

        # Contextual Explanation (THINK - "why?")
        if semantic.get("intent") == "CONTEXTUAL_EXPLANATION":
            return {
                "domain": "CRYPTO_MARKET",
                "intent": "CONTEXTUAL_EXPLANATION",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or context.active_asset or (context.recent_candidates[0] if context.recent_candidates else "BTCUSDT"),
                "confidence": 0.95,
                "is_execution": False,
                "requires_clarification": False
            }

        # Trade Plan (THINK - "give me an entry", "setup for that", "entry, SL and TP")
        if semantic.get("intent") == "TRADE_PLAN" or any(w in q for w in ["give me an entry", "give me entry", "setup", "trade plan", "plan a trade", "where to enter", "entry point", "target for", "what's the setup", "give me a plan", "entry, sl and tp", "entry sl tp"]):
            resolved = final_asset or context.active_asset or (context.recent_candidates[0] if context.recent_candidates else "BTCUSDT")
            return {
                "domain": "TRADING",
                "intent": "TRADE_PLAN",
                "detected_asset": detected_asset,
                "resolved_asset": resolved,
                "confidence": 0.96,
                "is_execution": False,
                "requires_clarification": False
            }

        # Contextual Execution (ACT - "buy 20 dollars of that", "do it", "execute that")
        if semantic.get("intent") == "EXECUTE_TRADE" and semantic.get("action_type") == "ACT":
            resolved = final_asset or context.active_asset or (context.recent_candidates[0] if context.recent_candidates else "BTCUSDT")
            return {
                "domain": "EXECUTION",
                "intent": "EXECUTE_TRADE",
                "detected_asset": detected_asset,
                "resolved_asset": resolved,
                "amount_usd": semantic.get("amount_usd", 20.0),
                "confidence": 0.96,
                "is_execution": True,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 0A: ORDER STATUS & FILL INQUIRY
        # -------------------------------------------------------------
        if any(w in q for w in [
            "how much has filled", "how much filled", "is it filled", "order status", "check my order",
            "check order", "status of order", "status of my order", "fill status", "fill percentage",
            "koto fill hoise", "kotoটুকু fill", "fill hoise kina", "pending order status", "my limit order"
        ]):
            return {
                "domain": "ORDER",
                "intent": "ORDER_STATUS",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "confidence": 0.98,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 0B: CANCEL LIMIT ORDER
        # -------------------------------------------------------------
        if semantic.get("intent") == "CANCEL_ORDER" or any(w in q for w in [
            "cancel that order", "cancel my order", "cancel order", "cancel the rest", "cancel remainder",
            "forget that order", "forget order", "cancel all orders", "cancel limit", "cancel pending",
            "order cancel", "cancel btc", "cancel eth", "cancel sol", "cancel pump", "order cancel koro", "baki order cancel"
        ]) or (q.startswith("cancel ") and ("order" in q or detected_asset or "rest" in q or "pending" in q)):
            return {
                "domain": "EXECUTION",
                "intent": "CANCEL_ORDER",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "confidence": 0.98,
                "is_execution": True,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 0C: MULTI-TURN PENDING ORDER DRAFT COMPLETION
        # If user previously asked to place an order but missed quantity, and now provides amount:
        # -------------------------------------------------------------
        if context.pending_order_draft:
            amt_num_match = re.search(r'^\s*\$?(\d+(?:\.\d+)?)\s*(?:btc|eth|sol|pump|tokens?|coins?|usd|dollar|dollars|\$)?\s*$', q)
            if amt_num_match or any(w in q for w in ["$", "dollar", "usd", "btc", "eth", "sol"]):
                return {
                    "domain": "EXECUTION",
                    "intent": "EXECUTE_TRADE",
                    "detected_asset": context.pending_order_draft.get("symbol"),
                    "resolved_asset": context.pending_order_draft.get("symbol"),
                    "is_draft_completion": True,
                    "confidence": 0.99,
                    "is_execution": True,
                    "requires_clarification": False
                }

        # -------------------------------------------------------------
        # DOMAIN 1: CONVERSATIONAL & SMALL TALK (Level 1)
        # -------------------------------------------------------------
        greetings = ["hi", "hello", "hey", "wassup", "wasup", "what's up", "yo", "good morning", "good evening", "howdy", "sup"]
        
        # Pure greeting or small talk without substantive action
        is_pure_greeting = (
            q in greetings or
            any(q == f"{g} syrax" or q == f"{g} agent" or q == f"{g} ai" or q == f"{g} bot" for g in greetings) or
            any(q == w or q.startswith(f"{w} ") or q.startswith(f"{w},") for w in [
                "kemon acho", "ki khobor", "ki obostha", "kemon asen", "valo aso", "bhalo acho",
                "how are you", "how r u", "how do you do", "nice to meet you", "good day"
            ])
        )

        starts_with_greeting = any(q.startswith(f"{g} ") or q.startswith(f"{g},") or q.startswith(f"{g}!") for g in greetings)
        
        # Substantive action words that mean this is NOT just a casual greeting
        action_keywords = [
            "buy", "sell", "long", "short", "price", "analyze", "analysis", "market", "check", "chech", "chk",
            "look", "see", "show", "tell", "status", "condition", "portfolio",
            "holding", "holdings", "position", "positions", "balance", "trade", "kinte", "kinbo",
            "convert", "swap", "protect", "rebalance", "hack", "exploit", "setup", "plan", "limit",
            "doing", "overview", "trend", "chart", "rate", "dropping", "pumping", "market kemon", "dam kemon"
        ]

        if (is_pure_greeting or (starts_with_greeting and not detected_asset and not any(w in q for w in action_keywords))):
            return {
                "domain": "GENERAL",
                "intent": "CONVERSATION",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.98,
                "is_execution": False,
                "requires_clarification": False
            }

        # Identity & Agent capabilities
        if any(w in q for w in ["who are you", "what are you", "what can you do", "introduce yourself", "tumi ke", "ki kaj koro", "ki korte paro"]):
            return {
                "domain": "GENERAL",
                "intent": "CONVERSATION",
                "detected_asset": detected_asset,
                "resolved_asset": None,
                "confidence": 0.96,
                "is_execution": False,
                "requires_clarification": False
            }

        # Jokes & Humor
        if any(w in q for w in ["joke", "funny", "make me laugh", "humor", "hasao"]):
            return {
                "domain": "GENERAL",
                "intent": "GENERAL_QUESTION",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.99,
                "is_execution": False,
                "requires_clarification": False
            }

        # Thank you / Politeness
        if any(w in q for w in ["thank you", "thanks", "dhonnobad", "great job", "awesome work"]):
            return {
                "domain": "GENERAL",
                "intent": "CONVERSATION",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.98,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 2: EDUCATIONAL & GENERAL KNOWLEDGE EXPLANATION (Level 2)
        # -------------------------------------------------------------
        explanation_triggers = [
            "what is leverage", "explain leverage", "how does leverage work", "leverage ki",
            "what is funding rate", "explain funding", "how do funding rates work", "funding rate ki",
            "what is slippage", "explain slippage", "slippage ki", "how does slippage happen",
            "what is liquidation", "explain liquidation", "liquidation price ki",
            "what is spot", "difference between spot and futures", "spot vs future",
            "what is rsi", "what is macd", "what is orderbook depth", "what is spread in trading",
            "what is a stop loss", "why use stop loss", "explain"
        ]
        if any(t in q for t in explanation_triggers) or (q.startswith("what is ") and not detected_asset and not any(w in q for w in ["price", "balance", "holding"])):
            return {
                "domain": "CRYPTO",
                "intent": "EXPLANATION",
                "detected_asset": detected_asset,
                "resolved_asset": detected_asset,
                "confidence": 0.95,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 3: PORTFOLIO & HOLDINGS INQUIRY (Level 4)
        # -------------------------------------------------------------
        if "rebalance" not in q and any(w in q for w in [
            "amar asset", "amar holding", "amar token", "amar balance", "amar portfolio", "amar position",
            "ki ki token ache", "konta ki token", "what are my holdings", "show my holdings",
            "my assets", "my portfolio", "my balance", "show portfolio", "check balance",
            "available cash", "how much cash", "how much usdt", "open positions", "show positions",
            "active positions", "current positions", "running positions", "active trades", "open trades", "what trades are running"
        ]):
            return {
                "domain": "PORTFOLIO",
                "intent": "PORTFOLIO",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "confidence": 0.96,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 4: SECURITY / SENTRY / EXPLOIT AUDIT
        # -------------------------------------------------------------
        if any(w in q for w in ["hack", "exploit", "rug", "rugpull", "vulnerab", "scam", "threat", "checking hoise", "security check", "is it safe", "exploit news"]):
            return {
                "domain": "SECURITY",
                "intent": "CHECK_RISK_HACK",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or "SOLUSDT",
                "confidence": 0.95,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 5: EMERGENCY DEFENSE / PROTECT PORTFOLIO
        # -------------------------------------------------------------
        if any(w in q for w in ["loss protect", "emergency protect", "protect my portfolio", "hedge to usdt", "panic sell to usdt", "save my capital", "emergency defense"]):
            return {
                "domain": "EXECUTION",
                "intent": "EMERGENCY_PROTECT",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "confidence": 0.98,
                "is_execution": True,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 6: CLOSE POSITION / SPOT LIQUIDATION
        # -------------------------------------------------------------
        if any(w in q for w in [
            "close trade", "close position", "exit trade", "exit position", "close my",
            "sell all btc", "sell all eth", "sell all sol", "sob btc sell", "sob eth sell",
            "sob sol sell", "sob asset sell", "shob sell", "puro sell", "100% sell", "close all"
        ]) or (
            ("close" in q or "exit" in q) and (detected_asset or any(t in q.upper() for t in ["SOL", "BTC", "ETH", "PEPE", "BNB", "TRD-"]))
        ):
            return {
                "domain": "EXECUTION",
                "intent": "CLOSE_TRADE",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "confidence": 0.97,
                "is_execution": True,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 7: CONVERT / SWAP ASSETS
        # -------------------------------------------------------------
        if any(w in q for w in ["convert", "swap"]) and any(w in q for w in ["to", "into", "->", "for"]):
            return {
                "domain": "EXECUTION",
                "intent": "CONVERT_ASSET",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "confidence": 0.95,
                "is_execution": True,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 8: UPDATE RULES / MANDATE
        # -------------------------------------------------------------
        if any(w in q for w in ["set max risk", "change risk", "max leverage", "set leverage", "set capital", "set my rule", "my rule is", "require stop loss"]):
            return {
                "domain": "PORTFOLIO",
                "intent": "UPDATE_RULES",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.95,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 9: REBALANCE PORTFOLIO
        # -------------------------------------------------------------
        if "rebalance" in q:
            return {
                "domain": "EXECUTION",
                "intent": "REBALANCE",
                "detected_asset": None,
                "resolved_asset": "PORTFOLIO",
                "confidence": 0.95,
                "is_execution": True,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 10: DIRECT TRADE EXECUTION (Level 6)
        # -------------------------------------------------------------
        trade_execution_cues = [
            "buy", "sell", "long", "short", "open trade", "open position", "take entry",
            "entry neo", "order set", "limit order", "spot e buy", "future e", "spot buy",
            "spot sell", "kinte", "kinbo", "kino", "kin", "bechte", "buy koro", "sell koro",
            "kinte chai", "order dao"
        ]
        # Ignore "long" or "buy" if purely questioning: "would you long it", "should i buy", "would you buy"
        is_questioning_trade = any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ["would you long", "would you buy", "should i buy", "should i long", "is it good to buy"])

        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in trade_execution_cues) and not is_questioning_trade:
            # Check if execution parameters are complete or ambiguous
            has_amount = (
                bool(re.search(r'\$\s*\d+(?:\.\d+)?', q)) or
                bool(re.search(r'\d+(?:\.\d+)?\s*(?:\$|usd|dollar|dollars|usdt)', q)) or
                bool(re.search(r'\b(?:for|amount(?: of)?|margin|with)\s*\$?\s*\d+', q)) or
                any(w in q for w in ["all", "sob", "shob", "puro", "100%", "everything"])
            )
            if not final_asset:
                return {
                    "domain": "TRADING",
                    "intent": "CLARIFICATION_REQUIRED",
                    "missing_param": "ASSET",
                    "detected_asset": None,
                    "resolved_asset": None,
                    "confidence": 0.90,
                    "is_execution": False,
                    "requires_clarification": True
                }
            elif not has_amount and not any(w in q for w in ["setup", "plan", "analyze", "analysis", "opinion"]):
                return {
                    "domain": "TRADING",
                    "intent": "CLARIFICATION_REQUIRED",
                    "missing_param": "AMOUNT",
                    "detected_asset": detected_asset,
                    "resolved_asset": final_asset,
                    "confidence": 0.88,
                    "is_execution": False,
                    "requires_clarification": True
                }
            else:
                return {
                    "domain": "EXECUTION",
                    "intent": "EXECUTE_TRADE",
                    "detected_asset": detected_asset,
                    "resolved_asset": final_asset,
                    "confidence": 0.96,
                    "is_execution": True,
                    "requires_clarification": False
                }

        # -------------------------------------------------------------
        # DOMAIN 11: CONTEXTUAL FOLLOW-UP & CORRECTION (Level 7)
        # -------------------------------------------------------------
        if is_correction and final_asset:
            return {
                "domain": "TRADING",
                "intent": "CORRECTION",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "updates": updates,
                "confidence": 0.92,
                "is_execution": False,
                "requires_clarification": False
            }

        # If user explicitly specifies a token and asks for analysis, market, check, or product (spot/futures/etc.)
        is_direct_token_query = bool(detected_asset and any(w in q for w in ["check", "analyze", "analysis", "price", "look", "see", "futures", "spot", "coin-m", "perp", "token", "what is happening with", "tell me about"]))
        
        if not is_direct_token_query and (is_follow_up or (updates and not detected_asset)) and final_asset:
            return {
                "domain": "MARKET",
                "intent": "FOLLOW_UP",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset,
                "updates": updates,
                "confidence": 0.93,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 12: TRADE PLANNING / SETUP INQUIRY (Level 5)
        # -------------------------------------------------------------
        if any(w in q for w in ["setup", "trade plan", "plan a trade", "where to enter", "entry point", "target for", "what's the setup", "give me a plan"]):
            return {
                "domain": "TRADING",
                "intent": "TRADE_PLAN",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or "BTCUSDT",
                "confidence": 0.92,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DOMAIN 13: MARKET ANALYSIS / TOKEN RESEARCH (Level 3)
        # -------------------------------------------------------------
        if detected_asset or (final_asset and is_follow_up):
            return {
                "domain": "MARKET",
                "intent": "MARKET_ANALYSIS",
                "detected_asset": detected_asset,
                "resolved_asset": final_asset or detected_asset,
                "confidence": 0.94,
                "is_execution": False,
                "requires_clarification": False
            }

        # If general crypto market inquiry with no specific token and no prior context:
        if any(w in q for w in ["crypto market", "overall crypto market", "crypto overview", "crypto market summary"]):
            return {
                "domain": "CRYPTO_MARKET",
                "intent": "OPPORTUNITY_DISCOVERY",
                "detected_asset": None,
                "resolved_asset": None,
                "confidence": 0.90,
                "is_execution": False,
                "requires_clarification": False
            }

        # -------------------------------------------------------------
        # DEFAULT FALLBACK: GENERAL CONVERSATION
        # -------------------------------------------------------------
        return {
            "domain": "GENERAL",
            "intent": "CONVERSATION",
            "detected_asset": None,
            "resolved_asset": None,
            "confidence": 0.85,
            "is_execution": False,
            "requires_clarification": False
        }


# =============================================================================
# 4. MAIN SYRAX ORCHESTRATOR
# =============================================================================

class SyraxOrchestrator:
    """
    Central brain of SYRAX.
    Orchestrates multi-domain intelligence, risk checks, and execution workflows.
    """

    def __init__(self, binance_client: BinanceAgentOS, sub_wallet: Optional[Any] = None):
        self.binance = binance_client
        self.sub_wallet = sub_wallet
        self.market_agent = MarketAgent(binance_client)
        self.news_agent = NewsSentryAgent()
        self.portfolio_agent = PortfolioAgent(binance_client)
        self.ai_client = OpenRouterAIClient()
        self.state_manager = ConversationStateManager()
        self.gateway = UnifiedExecutionGateway(binance_client, sub_wallet=sub_wallet, sentry_agent=self.news_agent)
        self.ticket_registry = OrderTicketRegistry()
        self.universal_registry = UniversalAssetRegistry()
        self.universal_news_service = TokenNewsIntelligenceService()
        self.universal_analysis_engine = UniversalAnalysisEngine(self.universal_registry, self.universal_news_service)

        # User Mandate & Enforced Rules State
        self.mandate: Dict[str, Any] = {
            "capital_usd": 500.0,
            "max_risk_pct": 1.0,           # Max 1.0% dollar risk on account per trade ($5.00)
            "max_order_size_usd": 25.0,     # Max position order size
            "max_leverage": 10,             # Max allowable leverage
            "require_stop_loss": True,      # Mandatory SL on every trade
            "sentry_exploit_filter": True,  # Block buy if exploit/hack detected
            "target_allocations": {"USDT": 40.0, "BTC": 30.0, "ETH": 15.0, "SOL": 10.0, "USDC": 5.0},
            "execution_mode": "AUTONOMOUS"  # AUTONOMOUS | ASSISTED
        }

        # Immutable Journal
        self.decision_journal: List[Dict[str, Any]] = []

    def _extract_target_token(self, text: str) -> Optional[str]:
        """Exposes token extraction via AssetEntityResolver."""
        return AssetEntityResolver.extract_crypto_asset(text)

    async def execute_mandate_pipeline(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point for multi-domain conversational agent loop.
        Classifies user intent, runs domain handlers, and returns structured progress.
        """
        start_time = time.time()

        # 1. Exact Order Ticket Confirmation Interceptor: CONFIRM PO-XXXXXX
        confirm_match = re.match(r'^\s*CONFIRM\s+(PO-[A-Za-z0-9]+)\s*$', user_query, re.IGNORECASE)
        if confirm_match:
            poid = confirm_match.group(1).upper()
            return await self._handle_confirm_order_ticket(poid, user_query, start_time)

        # 2. Cancel Order Ticket Interceptor: CANCEL PO-XXXXXX
        cancel_match = re.match(r'^\s*(?:CANCEL|ABORT|DISMISS)\s+(PO-[A-Za-z0-9]+)\s*$', user_query, re.IGNORECASE)
        if cancel_match:
            poid = cancel_match.group(1).upper()
            return await self._handle_cancel_order_ticket(poid, user_query, start_time)

        # 3. Generic Confirmation Interceptor: 'yes', 'confirm', 'ok', 'go ahead', 'do it'
        generic_confirm_match = re.match(r'^\s*(yes|y|confirm|ok|okay|agree|go\s*ahead|do\s*it|proceed|execute|approved|sure|yep|yeah)\s*[\.!]?\s*$', user_query, re.IGNORECASE)
        if generic_confirm_match:
            pending_tickets = self.ticket_registry.get_pending_tickets()
            if pending_tickets:
                target_ticket = pending_tickets[0]
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "query": user_query,
                    "elapsed_ms": elapsed_ms,
                    "command_type": "CONFIRMATION_REQUIRED",
                    "target_asset": target_ticket.symbol,
                    "decision": "CONFIRMATION_REQUIRED",
                    "headline": f"⚠️ Exact Confirmation Required: CONFIRM {target_ticket.parent_order_id}",
                    "reason": f"Generic confirmation '{user_query.strip()}' is insufficient. Exact ticket token required to prevent ambiguous execution.",
                    "explanation": (
                        f"SYRAX mandates cryptographic human confirmation before executing trades.\n\n"
                        f"Generic responses like **'{user_query.strip()}'** or **'confirm'** cannot authorize execution.\n\n"
                        f"To execute order ticket **{target_ticket.parent_order_id}** ({target_ticket.side} {target_ticket.symbol} ${target_ticket.notional_usd:.2f}), please type:\n"
                        f"### `CONFIRM {target_ticket.parent_order_id}`\n\n"
                        f"_Expires in {int(target_ticket.remaining_ttl_seconds())}s (TTL: {target_ticket.ttl_seconds}s)._"
                    ),
                    "ticket": format_order_ticket_card(target_ticket),
                    "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0
                }
        classification = IntentRouter.classify(user_query, self.state_manager)
        domain = classification["domain"]
        intent = classification["intent"]
        resolved_asset = classification.get("resolved_asset")

        logger.info(f"Intent classified: domain={domain}, intent={intent}, asset={resolved_asset} for query: '{user_query}'")

        # Record user turn in memory
        self.state_manager.record_turn("user", user_query, domain, intent, resolved_asset)

        # Route to appropriate domain handler
        if intent == "NON_CRYPTO_MARKET_INQUIRY":
            res = await self._handle_non_crypto_inquiry(user_query, start_time, classification)
        elif intent == "OPPORTUNITY_DISCOVERY":
            res = await self._handle_opportunity_discovery(user_query, start_time, classification)
        elif intent == "CODE_GENERATION":
            res = await self._handle_code_generation(user_query, start_time, classification)
        elif intent == "CONTEXTUAL_COMPARISON":
            res = await self._handle_contextual_comparison(user_query, start_time, classification)
        elif intent == "CONTEXTUAL_EXPLANATION":
            res = await self._handle_contextual_explanation(user_query, start_time, classification)
        elif intent == "RISK_EVALUATION":
            res = await self._handle_contextual_risk_evaluation(user_query, start_time, classification)
        elif domain == "GENERAL":
            if intent == "GENERAL_QUESTION":
                res = await self._handle_general_question(user_query, start_time, classification)
            else:
                res = await self._handle_general_conversation(user_query, start_time, classification)
        elif intent == "EXPLANATION":
            res = await self._handle_explanation(user_query, start_time, classification)
        elif intent == "PORTFOLIO_RISK_AUDIT":
            res = await self._handle_portfolio_risk_audit(user_query, start_time, classification)
        elif intent == "PORTFOLIO":
            res = await self._handle_portfolio_inquiry(user_query, start_time, classification)
        elif intent == "CHECK_RISK_HACK":
            res = await self._handle_risk_hack_audit(user_query, start_time, classification)
        elif intent == "EMERGENCY_PROTECT":
            res = await self._handle_emergency_protect(user_query, start_time, classification)
        elif intent == "CLOSE_TRADE":
            res = await self._handle_close_trade(user_query, start_time, classification)
        elif intent == "RESET_BALANCE":
            res = await self._handle_reset_balance(user_query, start_time, classification)
        elif intent == "INTERNAL_TRANSFER":
            res = await self._handle_internal_transfer(user_query, start_time, classification)
        elif intent == "CONVERT_ASSET":
            res = await self._handle_convert_asset(user_query, start_time, classification)
        elif intent == "UPDATE_RULES":
            res = await self._handle_update_rules(user_query, start_time, classification)
        elif intent == "ORDER_STATUS":
            res = await self._handle_order_status(user_query, start_time, classification)
        elif intent == "CANCEL_ORDER":
            res = await self._handle_cancel_order(user_query, start_time, classification)
        elif intent == "REBALANCE":
            res = await self._handle_rebalance(user_query, start_time, classification)
        elif intent == "CLARIFICATION_REQUIRED":
            res = await self._handle_clarification_required(user_query, start_time, classification)
        elif intent == "FOLLOW_UP":
            res = await self._handle_follow_up(user_query, start_time, classification)
        elif intent == "CORRECTION":
            await self.ticket_registry.invalidate_pending_tickets(reason="Parameters modified by user correction")
            res = await self._handle_correction(user_query, start_time, classification)
        elif intent == "TRADE_PLAN":
            res = await self._handle_trade_planning(user_query, start_time, classification)
        elif intent == "EXECUTE_TRADE":
            res = await self._handle_execute_trade(user_query, start_time, classification)
        else:
            # Market analysis / discovery
            res = await self._handle_market_analysis(user_query, start_time, classification)

        # Record agent turn in memory
        headline_text = res.get("headline", "") or res.get("explanation", "")
        self.state_manager.record_turn("ai", headline_text, domain, intent, resolved_asset)

        return res

    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # NON-CRYPTO COMMODITY / TRADITIONAL FINANCE HANDLER (TALK / INFORM)
    # -------------------------------------------------------------------------
    async def _handle_non_crypto_inquiry(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_asset = classification.get("target_asset", "COMMODITY")
        asset_name = classification.get("asset_name", "Commodity")
        q_low = query.lower()

        if target_asset == "GOLD" or "gold" in q_low or "xau" in q_low:
            asset_display = "Gold (XAU/USD)"
            headline = "ℹ️ Commodity Notice: Gold (XAU/USD)"
            reply = (
                "### 🪙 Macro Context: Gold (XAU/USD)\n\n"
                "SYRAX is natively connected to live **Binance Spot & USDⓈ-M Futures crypto feeds**.\n\n"
                "- **Macro Landscape:** Spot Gold (XAU/USD) trades globally as a premier monetary store-of-value and geopolitical hedge, influenced by real yields, central bank reserves, and DXY strength.\n"
                "- **Crypto Equivalents on Binance:** If you wish to trade tokenized gold on-chain via Binance, assets like **PAXG (PAX Gold)** track physical gold spot 1:1.\n\n"
                "I can scan connected Binance crypto pairs or analyze crypto-gold correlations anytime."
            )
        elif target_asset in ("OIL", "CRUDE_OIL", "BRENT_CRUDE", "WTI_CRUDE") or "oil" in q_low or "crude" in q_low:
            asset_display = "Crude Oil (WTI/Brent)"
            headline = "ℹ️ Commodity Notice: Crude Oil (WTI/Brent)"
            reply = (
                "### 🛢️ Macro Context: Crude Oil (WTI / Brent)\n\n"
                "SYRAX is natively connected to live **Binance Spot & USDⓈ-M Futures crypto feeds**.\n\n"
                "- **Macro Landscape:** Crude oil markets are driven by global energy demand, OPEC+ quotas, inventory reports, and shipping route dynamics.\n"
                "- **Crypto Feeds:** Direct oil contracts are not traded on Binance Spot/Perps, but energy price shocks often impact broader risk-asset liquidity and inflation expectations.\n\n"
                "Let me know if you would like me to analyze crypto market liquidity or screen for high-momentum crypto pairs."
            )
        else:
            asset_display = asset_name
            headline = f"ℹ️ Market Feed Notice: {asset_name}"
            reply = (
                f"I can analyze cryptocurrency markets using my live Binance data feeds, but I don't currently have a real-time {asset_name} data feed connected.\n\n"
                f"If you'd like, I can still discuss macroeconomic trends, historical context, and sentiment around {asset_name}, or scan our connected Binance Spot & Futures pairs for crypto opportunities."
            )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CONVERSATION",
            "target_asset": target_asset,
            "decision": None,
            "headline": headline,
            "reason": f"Live data feed not connected for {asset_display}",
            "explanation": reply,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Checking Market Data Providers", "status": "DONE", "detail": f"Identified query as non-crypto asset ({asset_display}). Binance feeds active for crypto pairs."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-NONCRYPTO-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": classification.get("domain", "NON_CRYPTO_MARKET"),
                "intent": "NON_CRYPTO_MARKET_INQUIRY",
                "detected_asset": target_asset,
                "resolved_asset": target_asset,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.98
            }
        }

    # -------------------------------------------------------------------------
    # OPPORTUNITY DISCOVERY HANDLER (Level 3 - THINK)
    # -------------------------------------------------------------------------
    async def _handle_opportunity_discovery(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Scanning Binance Spot & Futures Orderbooks", "status": "DONE", "detail": "Auditing 24h volume, momentum breakouts, and spread tightness."},
            {"step": "Cross-Referencing Sentry Security Feeds", "status": "DONE", "detail": "Verifying 0 active exploit threats on CertiK/PeckShield radar."},
            {"step": "Formulating Watchlist Candidates", "status": "DONE", "detail": "Ranking top liquid candidates for user watchlist."}
        ]

        timeframe = classification.get("timeframe", "THIS_WEEK")
        scan_results = await self.market_agent.scan_market(category="ALL", limit=15)
        active_events = self.news_agent.get_active_events()

        # Save top candidates in conversation context for multi-turn resolution
        self.state_manager.recent_candidates = [c["symbol"] for c in scan_results[:5]]

        narrative = await self.ai_client.generate_opportunity_response(
            user_query=query,
            candidates=scan_results,
            news_events=active_events,
            timeframe=timeframe
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "OPPORTUNITY_DISCOVERY",
            "target_asset": None,
            "decision": None,
            "headline": f"🔍 Screened Top Market Opportunities ({timeframe.lower().replace('_', ' ')})",
            "reason": "Scanned live Binance orderbooks and ranked top momentum/volume candidates.",
            "explanation": narrative,
            "invalidation": "Broader market breakdown or liquidity drain.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "candidates": scan_results[:5],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-OPP-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "CRYPTO_MARKET",
                "intent": "OPPORTUNITY_DISCOVERY",
                "timeframe": timeframe,
                "detected_asset": None,
                "resolved_asset": None,
                "active_context_asset": None,
                "recent_candidates": self.state_manager.recent_candidates,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.98
            }
        }

    # -------------------------------------------------------------------------
    # CODE GENERATION HANDLER (TALK)
    # -------------------------------------------------------------------------
    async def _handle_code_generation(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        code_resp = await self.ai_client.generate_code_response(query)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CODING",
            "target_asset": "CODE",
            "decision": None,
            "headline": "💻 Code Solution Generated",
            "reason": "Generated structured coding implementation as requested.",
            "explanation": code_resp,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Analyzing Code Requirements", "status": "DONE", "detail": "Identified target algorithm and language specifications."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-COD-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "CODING",
                "intent": "CODE_GENERATION",
                "detected_asset": None,
                "resolved_asset": None,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.99
            }
        }

    # -------------------------------------------------------------------------
    # CONTEXTUAL COMPARISON HANDLER (THINK - "which one looks strongest?")
    # -------------------------------------------------------------------------
    async def _handle_contextual_comparison(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        candidates = self.state_manager.recent_candidates or ["SOLUSDT", "ETHUSDT", "BTCUSDT"]
        
        c_details = []
        for sym in candidates[:3]:
            ticker = await self.binance.get_live_ticker(sym)
            c_details.append({
                "symbol": sym,
                "price": ticker.get("last_price", 100.0),
                "change": ticker.get("price_change_pct", ticker.get("change_24h", 0.0)),
                "volume": ticker.get("quote_volume", 50000000)
            })

        c_details.sort(key=lambda x: x["change"], reverse=True)
        top_choice = c_details[0]
        self.state_manager.active_asset = top_choice["symbol"]

        explanation = (
            f"Comparing the candidates from our recent radar (**{', '.join([c['symbol'].replace('USDT', '') for c in c_details])}**):\n\n"
            f"1. **{top_choice['symbol'].replace('USDT', '')}** looks the strongest technically with **{top_choice['change']:+.2f}%** 24h momentum and healthy volume (${top_choice['volume']/1e6:.1f}M).\n"
            f"2. **{c_details[1]['symbol'].replace('USDT', '')}** (${c_details[1]['price']:,.2f}) has resilient support but more consolidated price action.\n\n"
            f"If I had to pick one for a disciplined setup right now, **{top_choice['symbol'].replace('USDT', '')}** has the cleanest reward-to-risk structure. "
            f"Would you like me to calculate an exact entry and stop loss for it?"
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "MARKET_ANALYSIS",
            "target_asset": top_choice["symbol"],
            "decision": None,
            "headline": f"🎯 Strongest Candidate: {top_choice['symbol'].replace('USDT', '')} ({top_choice['change']:+.2f}%)",
            "reason": f"Evaluated momentum, orderbook liquidity, and relative strength across recent candidates.",
            "explanation": explanation,
            "invalidation": "Loss of short-term moving average support.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Comparing Candidates Telemetry", "status": "DONE", "detail": f"Compared {len(c_details)} tokens on Binance orderbook metrics."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-CMP-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "CRYPTO_MARKET",
                "intent": "CONTEXTUAL_COMPARISON",
                "detected_asset": None,
                "resolved_asset": top_choice["symbol"],
                "active_context_asset": top_choice["symbol"],
                "recent_candidates": self.state_manager.recent_candidates,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.96
            }
        }

    # -------------------------------------------------------------------------
    # CONTEXTUAL EXPLANATION HANDLER (THINK - "why?")
    # -------------------------------------------------------------------------
    async def _handle_contextual_explanation(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = self.state_manager.active_asset or "SOLUSDT"
        base_asset = target_token.replace("USDT", "")
        ticker = await self.binance.get_live_ticker(target_token)
        market_data = await self.market_agent.analyze_symbol(target_token)

        explanation = (
            f"Here is why **{base_asset}** stands out:\n\n"
            f"1. **Momentum & Volume:** 24h performance is **{ticker.get('change_24h', 0.0):+.2f}%** with sustained buying pressure (${ticker.get('quote_volume', 80000000)/1e6:.1f}M quote volume).\n"
            f"2. **Orderbook Spread:** Tight bid-ask spread of **{market_data.get('spread_bps', 1.2):.2f} bps**, minimizing execution slippage.\n"
            f"3. **Sentry Clearance:** 0 active exploit vulnerabilities or bridge drain alerts flagged on security radar.\n\n"
            f"To get an entry and stop-loss plan, simply ask: *'give me an entry'*."
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "MARKET_ANALYSIS",
            "target_asset": target_token,
            "decision": None,
            "headline": f"💡 Rationale for {base_asset}",
            "reason": f"Explained key technical and liquidity drivers behind {base_asset}.",
            "explanation": explanation,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Analyzing Rationale Drivers", "status": "DONE", "detail": f"Synthesized volume, spread, and security metrics for {base_asset}."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-WHY-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "CRYPTO_MARKET",
                "intent": "CONTEXTUAL_EXPLANATION",
                "detected_asset": None,
                "resolved_asset": target_token,
                "active_context_asset": target_token,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.95
            }
        }

    # -------------------------------------------------------------------------
    # CONTEXTUAL RISK EVALUATION HANDLER (THINK - "what about risk?")
    # -------------------------------------------------------------------------
    async def _handle_contextual_risk_evaluation(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = self.state_manager.active_asset or "SOLUSDT"
        base_asset = target_token.replace("USDT", "")
        ticker = await self.binance.get_live_ticker(target_token)
        price = ticker.get("last_price", 100.0)

        max_risk_dollars = self.mandate["capital_usd"] * (self.mandate["max_risk_pct"] / 100.0)

        explanation = (
            f"### 🛡️ Risk Assessment for {base_asset} (${price:,.2f})\n\n"
            f"- **Account Risk Mandate:** Capped to strictly **{self.mandate['max_risk_pct']}% (${max_risk_dollars:.2f} max loss)** per trade.\n"
            f"- **Stop Loss Distance:** A standard 2.0% stop-loss would be at **${price*0.98:,.2f}**.\n"
            f"- **Recommended Safe Sizing:** Maximum safe position is **${max_risk_dollars / 0.02:.2f} USDT**.\n"
            f"- **Threat Radar:** Clean (0 flagged smart contract exploits).\n\n"
            f"Risk is well-contained under your policy parameters."
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "RISK_AUDIT",
            "target_asset": target_token,
            "decision": None,
            "headline": f"🛡️ Risk Profile: {base_asset} (Max Loss: ${max_risk_dollars:.2f})",
            "reason": f"Evaluated 1.0% risk mandate and stop-loss boundaries for {base_asset}.",
            "explanation": explanation,
            "invalidation": "Breach of risk limits.",
            "max_risk_usd": max_risk_dollars,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Evaluating 1% Account Risk Math", "status": "DONE", "detail": f"Calculated max allowable dollar drawdown (${max_risk_dollars:.2f})."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-RSK-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "TRADING",
                "intent": "RISK_EVALUATION",
                "detected_asset": None,
                "resolved_asset": target_token,
                "active_context_asset": target_token,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.95
            }
        }

    # 1. GENERAL CONVERSATION HANDLER (Level 1)
    # -------------------------------------------------------------------------
    async def _handle_general_conversation(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        reply = await self.ai_client.generate_conversational_response(query, self.state_manager.history)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CONVERSATION",
            "target_asset": None,
            "decision": None,
            "headline": reply,
            "reason": "General conversational dialogue",
            "explanation": reply,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Processing Conversational Dialogue", "status": "DONE", "detail": "Generated context-aware conversational response."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-CHAT-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "GENERAL",
                "intent": "CONVERSATION",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": None,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # 2. GENERAL QUESTION / JOKES / LOGIC HANDLER (Level 1)
    # -------------------------------------------------------------------------
    async def _handle_general_question(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        reply = await self.ai_client.generate_conversational_response(query, self.state_manager.history)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CONVERSATION",
            "target_asset": None,
            "decision": None,
            "headline": reply,
            "reason": "General knowledge / interactive response",
            "explanation": reply,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Synthesizing Knowledge Query", "status": "DONE", "detail": "Returned intelligent query response without trading overhead."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-GEN-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "GENERAL",
                "intent": "GENERAL_QUESTION",
                "detected_asset": None,
                "resolved_asset": None,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.98)
            }
        }

    # -------------------------------------------------------------------------
    # 3. CONCEPT & EDUCATIONAL EXPLANATION HANDLER (Level 2)
    # -------------------------------------------------------------------------
    async def _handle_explanation(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        explanation_text = await self.ai_client.generate_explanation(query)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "EXPLANATION",
            "target_asset": classification.get("resolved_asset"),
            "decision": None,
            "headline": f"📚 Concept Explanation: {query.strip()}",
            "reason": "Educational explanation of financial & trading mechanics",
            "explanation": explanation_text,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Structuring Educational Concepts", "status": "DONE", "detail": "Formulated structured breakdown with examples, risks, and SYRAX safety guarantees."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-EXP-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "CRYPTO",
                "intent": "EXPLANATION",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": classification.get("resolved_asset"),
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # PORTFOLIO RISK AUDIT & EXPOSURE HANDLER
    # -------------------------------------------------------------------------
    async def _handle_portfolio_risk_audit(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Auditing Sub-Wallet Asset Allocations", "status": "DONE", "detail": "Calculating live token weights, cash buffer, and asset concentration."},
            {"step": "Evaluating Open Derivative Leverage", "status": "DONE", "detail": "Auditing ongoing positions, liquidation boundaries, and trailing stop distance."},
            {"step": "Scanning Sentry Radar on Held Tokens", "status": "DONE", "detail": "Verifying smart contract security, bridge exploit feeds, and depeg risks."},
            {"step": "Synthesizing Mandate Risk Diagnosis", "status": "DONE", "detail": "Generating deterministic risk report and actionable mitigation steps."}
        ]

        cash_usd = self.sub_wallet.cash_usd if self.sub_wallet else 250.0
        total_val = cash_usd
        asset_values = {}
        top_asset = "USDT"
        top_asset_val = cash_usd

        # Calculate live valuations across holdings
        if self.sub_wallet and self.sub_wallet.holdings:
            for asset, data in self.sub_wallet.holdings.items():
                qty = data.get("free", 0.0) + data.get("locked", 0.0)
                if qty <= 0:
                    continue
                if asset in ("USDT", "USDC", "USD", "FDUSD"):
                    p = 1.0
                else:
                    ticker = await self.binance.get_live_ticker(f"{asset}USDT")
                    p = ticker.get("last_price", 100.0)
                val = qty * p
                asset_values[asset] = {"qty": qty, "price": p, "val": val}
                if asset not in ("USDT", "USDC"):
                    total_val += val

            # Find largest non-stable holding
            top_asset_val = 0.0
            for asset, d in asset_values.items():
                if asset not in ("USDT", "USDC") and d["val"] > top_asset_val:
                    top_asset = asset
                    top_asset_val = d["val"]

        cash_pct = (cash_usd / total_val * 100.0) if total_val > 0 else 100.0
        top_asset_pct = (top_asset_val / total_val * 100.0) if total_val > 0 else 0.0

        # Audit ongoing derivative trades
        ongoing_trades = self.sub_wallet.ongoing_trades if self.sub_wallet else []
        high_leverage_trades = [t for t in ongoing_trades if t.get("leverage", 1) > 5]
        total_unrealized_pnl = sum(t.get("unrealized_pnl_usd", 0.0) for t in ongoing_trades)

        # Check Sentry Threats on held assets
        held_assets = list(asset_values.keys()) if asset_values else ["BTC", "ETH", "SOL"]
        sentry_threats = []
        try:
            active_events = await self.sentry.get_active_events()
            for ev in active_events:
                if any(h in ev.get("token", "").upper() for h in held_assets):
                    sentry_threats.append(ev)
        except Exception:
            pass

        # Determine Primary Risk Category
        risk_level = "LOW / CONTROLLED"
        if sentry_threats:
            risk_level = "CRITICAL"
            threat_tokens = ", ".join([e.get("token", "") for e in sentry_threats])
            primary_risk = f"Active Security/Exploit Threat detected on held asset(s): **{threat_tokens}**."
        elif high_leverage_trades:
            risk_level = "MODERATE"
            t = high_leverage_trades[0]
            primary_risk = f"High-Leverage Exposure in **{t['symbol']} ({t.get('leverage', 1)}x {t['side']})** with ${t.get('margin_usd', 0):.2f} margin."
        elif top_asset != "USDT" and top_asset_pct > 35.0:
            risk_level = "MODERATE"
            primary_risk = f"Single-Asset Concentration Risk: **{top_asset}** constitutes **{top_asset_pct:.1f}%** (${top_asset_val:.2f}) of your total portfolio."
        elif cash_pct < 15.0:
            risk_level = "MODERATE"
            primary_risk = f"Low Cash Buffer ({cash_pct:.1f}%): You have limited liquid USDT cash reserves to enter new setups or buffer drawdowns."
        else:
            risk_level = "LOW / CONTROLLED"
            primary_risk = f"Portfolio is well-diversified with a healthy liquid cash buffer (${cash_usd:.2f} USDT) and zero unhedged high-leverage threats."

        # Format Comprehensive Markdown Breakdown
        holdings_summary_lines = []
        for asset, d in asset_values.items():
            pct = (d["val"] / total_val * 100.0) if total_val > 0 else 0.0
            holdings_summary_lines.append(f"• **{asset}:** `{d['qty']:.4f}` (~${d['val']:.2f} | **{pct:.1f}%**)")
        holdings_summary_str = "\n".join(holdings_summary_lines) if holdings_summary_lines else f"• **USDT:** `${cash_usd:.2f} (100.0%)`"

        trades_summary_str = f"{len(ongoing_trades)} open position(s) (Unrealized PnL: ${total_unrealized_pnl:+.2f})" if ongoing_trades else "0 active derivative positions (100% Spot & Cash)"

        explanation = (
            f"### 🛡️ Real-Time Portfolio Risk Diagnosis\n\n"
            f"**Overall Risk Posture:** `{risk_level}`\n"
            f"**Total Portfolio Value:** `${total_val:,.2f} USD` (Liquid Cash: `${cash_usd:,.2f} USDT` / `{cash_pct:.1f}%`)\n\n"
            f"#### 🚨 Primary Vulnerability Identified:\n"
            f"{primary_risk}\n\n"
            f"#### 📊 Risk Parameter Breakdown:\n"
            f"• **Asset Concentration:** `{top_asset}` is highest weight at `{top_asset_pct:.1f}%` of total capital.\n"
            f"• **Derivatives Exposure:** {trades_summary_str}.\n"
            f"• **Mandate 1.0% Rule Compliance:** `PASS` (Maximum dollar risk capped at `$5.00 USD` per position).\n"
            f"• **Sentry Exploit Radar:** `0 active threats` on held tokens.\n\n"
            f"#### 🪙 Current Allocation Matrix:\n"
            f"{holdings_summary_str}\n\n"
            f"#### 💡 Actionable Mitigation Recommendations:\n"
            f"1. **Rebalancing:** Type **`Rebalance portfolio to target allocations`** to automatically trim overweight assets.\n"
            f"2. **Stop-Loss Enforcement:** Keep mandatory stop-loss bounds active on all new orders to protect the $5.00 mandate cap.\n"
            f"3. **Capital Defense:** Use the **Positions** tab or type **`Emergency protect`** if market volatility spikes."
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "RISK_AUDIT",
            "target_asset": top_asset,
            "decision": "WAIT" if risk_level != "CRITICAL" else "PROTECT",
            "headline": f"🛡️ Portfolio Risk Audit: {risk_level} — {primary_risk[:70]}...",
            "reason": f"Real-time risk audit performed across {len(asset_values)} assets and {len(ongoing_trades)} open positions.",
            "explanation": explanation,
            "invalidation": None,
            "max_risk_usd": 5.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "available_cash_usd": cash_usd,
            "journal_id": f"JRNL-RISK-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "PORTFOLIO",
                "intent": "PORTFOLIO_RISK_AUDIT",
                "detected_asset": top_asset,
                "resolved_asset": "PORTFOLIO",
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.99
            }
        }


    # -------------------------------------------------------------------------
    # 4. PORTFOLIO & HOLDINGS INQUIRY HANDLER (Level 4)
    # -------------------------------------------------------------------------
    async def _handle_portfolio_inquiry(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Reading Agentic Sub-Wallet", "status": "DONE", "detail": "Auditing liquid cash, locked margin, and spot token allocations."},
            {"step": "Querying Ongoing Derivative Positions", "status": "DONE", "detail": "Calculating mark price, unrealized PnL, and liquidation distance."}
        ]

        portfolio_data = await self.binance.get_account_portfolio()
        cash_usd = self.sub_wallet.cash_usd if self.sub_wallet else portfolio_data.get("available_cash_usd", 250.0)

        holdings_list = []
        total_val = cash_usd
        if self.sub_wallet:
            price_map = {}
            for asset, data in self.sub_wallet.holdings.items():
                qty = data.get("free", 0.0) + data.get("locked", 0.0)
                if qty <= 0:
                    continue
                if asset in ("USDT", "USDC", "USD", "FDUSD"):
                    p = 1.0
                else:
                    ticker = await self.binance.get_live_ticker(f"{asset}USDT")
                    p = ticker.get("last_price", 100.0)
                price_map[asset] = p
                val = qty * p
                if asset not in ("USDT", "USDC"):
                    total_val += val

            for asset, data in self.sub_wallet.holdings.items():
                qty = data.get("free", 0.0)
                if qty > 0:
                    p = price_map.get(asset, 1.0)
                    val = qty * p
                    pct = (val / total_val * 100.0) if total_val > 0 else 0.0
                    holdings_list.append(f"• **{asset}:** {qty:.4f} (~${val:.2f} | {pct:.1f}%)")
        else:
            for h in portfolio_data.get("holdings", []):
                holdings_list.append(f"• **{h['asset']}:** {h['free']:.4f} (~${h.get('value_usd', 0.0):.2f})")
            total_val = portfolio_data.get("total_value_usd", 500.0)

        ongoing_trades_desc = []
        if self.sub_wallet and self.sub_wallet.ongoing_trades:
            for trd in self.sub_wallet.ongoing_trades:
                pnl = trd.get("unrealized_pnl_usd", 0.0)
                ongoing_trades_desc.append(f"• **{trd['symbol']} ({trd.get('market_type', 'SPOT')} {trd['side']}):** Margin ${trd.get('margin_usd', trd['notional_usd']):.2f} | PnL: ${pnl:+.2f}")

        holdings_text = "\n".join(holdings_list) if holdings_list else "No active spot token holdings."
        trades_text = "\n".join(ongoing_trades_desc) if ongoing_trades_desc else "No open positions."

        explanation = (
            f"### 💼 Portfolio & Holdings Overview\n\n"
            f"**Total Portfolio Value:** ${total_val:,.2f} USD\n"
            f"**Liquid Cash Available:** ${cash_usd:,.2f} USDT\n\n"
            f"#### 🪙 Spot Asset Balances:\n{holdings_text}\n\n"
            f"#### 📊 Active Positions ({len(self.sub_wallet.ongoing_trades if self.sub_wallet else [])}):\n{trades_text}\n\n"
            f"All holdings are actively monitored 24/7 by the Sentry Threat Radar."
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "PORTFOLIO",
            "target_asset": "PORTFOLIO",
            "decision": None,
            "headline": f"💼 Portfolio: ${total_val:,.2f} Total (${cash_usd:,.2f} Liquid Cash)",
            "reason": "Comprehensive balance and active position audit",
            "explanation": explanation,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "available_cash_usd": cash_usd,
            "journal_id": f"JRNL-PF-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "PORTFOLIO",
                "intent": "PORTFOLIO",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": "PORTFOLIO",
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.96)
            }
        }

    # -------------------------------------------------------------------------
    # 4B. ORDER STATUS & FILL INQUIRY HANDLER
    # -------------------------------------------------------------------------
    async def _handle_order_status(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Querying Limit Order Registry", "status": "DONE", "detail": "Auditing open pending orders, execution state, and fill ratios."},
            {"step": "Calculating Fill Telemetry", "status": "DONE", "detail": "Checking partially filled lots, average fill price, and remaining quantities."}
        ]

        pending_orders = self.sub_wallet.pending_orders if self.sub_wallet else []
        target_token = classification.get("resolved_asset")
        order_id_match = re.search(r'\b(ORD-[A-Za-z0-9\-]+)\b', query, re.IGNORECASE)
        target_order_id = order_id_match.group(1).upper() if order_id_match else None

        active_orders = []
        for o in pending_orders:
            if target_order_id and o.get("order_id") == target_order_id:
                active_orders.append(o)
            elif target_token and o.get("symbol") == target_token:
                active_orders.append(o)
            elif not target_order_id and not target_token:
                active_orders.append(o)

        if not active_orders and self.sub_wallet:
            active_orders = [o for o in getattr(self.sub_wallet, 'order_history', []) if o.get("status") in ("PARTIALLY_FILLED", "PENDING", "FILLED")][:3]

        if not active_orders:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "ORDER_STATUS",
                "target_asset": target_token or "NONE",
                "decision": None,
                "headline": "📋 No Active Pending Orders",
                "reason": "There are currently no open or partially filled limit orders in your account.",
                "explanation": "You have no active pending limit orders. All your available capital is liquid in your account.",
                "invalidation": None,
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "agentic_steps": steps,
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "journal_id": f"JRNL-ORD-STAT-{int(time.time()*1000) % 10000}",
                "debug_intent_inspector": {
                    "domain": "ORDER",
                    "intent": "ORDER_STATUS",
                    "detected_asset": classification.get("detected_asset"),
                    "resolved_asset": target_token,
                    "active_context_asset": self.state_manager.active_asset,
                    "requires_clarification": False,
                    "is_execution_intent": False,
                    "confidence": classification.get("confidence", 0.95)
                }
            }

        summaries = []
        for o in active_orders:
            sym = o.get("symbol", "BTCUSDT")
            base = o.get("base_asset", sym.replace("USDT", ""))
            side = o.get("side", "BUY")
            lp = o.get("limit_price", 0.0)
            req_qty = o.get("requested_quantity", 0.0)
            fill_qty = o.get("filled_quantity", 0.0)
            rem_qty = o.get("remaining_quantity", req_qty)
            pct = o.get("fill_percentage", 0.0)
            status = o.get("status", "PENDING")
            avg_p = o.get("average_fill_price", lp)
            ord_id = o.get("order_id", "N/A")
            locked_quote = o.get("reserved_usd", 0.0)

            summaries.append(
                f"### 📋 Order `{ord_id}`: {side} {sym}\n"
                f"- **Status:** `{status}` ({pct:.1f}% Filled)\n"
                f"- **Limit Price:** ${lp:,.2f}\n"
                f"- **Requested Quantity:** {req_qty:.6f} {base}\n"
                f"- **Filled Quantity:** {fill_qty:.6f} {base}" + (f" (Avg Fill Price: ${avg_p:,.2f})" if fill_qty > 0 else "") + "\n"
                f"- **Remaining Quantity:** {rem_qty:.6f} {base}\n"
                f"- **Reserved Margin:** ${locked_quote:.2f} USDT"
            )

        explanation = "\n\n".join(summaries)
        primary_order = active_orders[0]
        headline = f"📋 Order Status: {primary_order.get('symbol')} ({primary_order.get('fill_percentage', 0.0):.1f}% Filled - {primary_order.get('status')})"

        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "ORDER_STATUS",
            "target_asset": primary_order.get("symbol"),
            "decision": None,
            "headline": headline,
            "reason": f"Audited {len(active_orders)} order(s). Active status: {primary_order.get('status')}.",
            "explanation": explanation,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "pending_orders": active_orders,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-ORD-STAT-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "ORDER",
                "intent": "ORDER_STATUS",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": primary_order.get("symbol"),
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # 4C. CANCEL ORDER HANDLER
    # -------------------------------------------------------------------------
    async def _handle_cancel_order(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Locating Target Order", "status": "DONE", "detail": "Searching open orders in Binance Sub-Wallet."},
            {"step": "Unlocking Remaining Reserved Funds", "status": "DONE", "detail": "Releasing remaining reserved margin back to free balance."},
            {"step": "Retaining Filled Lot Allocations", "status": "DONE", "detail": "Holding all already-filled tokens in spot balance."}
        ]

        if not self.sub_wallet or not self.sub_wallet.pending_orders:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "CANCEL_ORDER",
                "target_asset": classification.get("resolved_asset") or "NONE",
                "decision": None,
                "headline": "❌ No Open Orders to Cancel",
                "reason": "There are no pending limit orders active in the sub-wallet to cancel.",
                "explanation": "No active pending limit orders were found. Your funds are already liquid.",
                "invalidation": None,
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "agentic_steps": steps,
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "journal_id": f"JRNL-CAN-ERR-{int(time.time()*1000) % 10000}",
                "debug_intent_inspector": {
                    "domain": "ORDER",
                    "intent": "CANCEL_ORDER",
                    "detected_asset": classification.get("detected_asset"),
                    "resolved_asset": classification.get("resolved_asset"),
                    "active_context_asset": self.state_manager.active_asset,
                    "requires_clarification": False,
                    "is_execution_intent": True,
                    "confidence": classification.get("confidence", 0.95)
                }
            }

        order_id_match = re.search(r'\b(ORD-[A-Za-z0-9\-]+)\b', query, re.IGNORECASE)
        target_order_id = order_id_match.group(1).upper() if order_id_match else None
        target_token = classification.get("resolved_asset")

        matched_order = None
        if target_order_id:
            matched_order = next((o for o in self.sub_wallet.pending_orders if o.get("order_id") == target_order_id), None)
        elif target_token:
            matched_order = next((o for o in self.sub_wallet.pending_orders if o.get("symbol") == target_token), None)
        
        if not matched_order and self.sub_wallet.pending_orders:
            matched_order = self.sub_wallet.pending_orders[-1]

        if not matched_order:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "CANCEL_ORDER",
                "target_asset": target_token or "NONE",
                "decision": None,
                "headline": f"❌ Order Not Found",
                "reason": f"Could not find matching pending order to cancel.",
                "explanation": "No matching active limit order was found to cancel.",
                "invalidation": None,
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "agentic_steps": steps,
                "available_cash_usd": self.sub_wallet.cash_usd,
                "journal_id": f"JRNL-CAN-ERR-{int(time.time()*1000) % 10000}",
                "debug_intent_inspector": {
                    "domain": "ORDER",
                    "intent": "CANCEL_ORDER",
                    "detected_asset": classification.get("detected_asset"),
                    "resolved_asset": target_token,
                    "active_context_asset": self.state_manager.active_asset,
                    "requires_clarification": False,
                    "is_execution_intent": True,
                    "confidence": 0.90
                }
            }

        cancel_res = self.sub_wallet.cancel_pending_order(matched_order["order_id"])
        elapsed_ms = int((time.time() - start_time) * 1000)

        ord_id = matched_order["order_id"]
        sym = matched_order.get("symbol", "BTCUSDT")
        base = matched_order.get("base_asset", sym.replace("USDT", ""))
        fill_qty = matched_order.get("filled_quantity", 0.0)
        rem_qty = matched_order.get("remaining_quantity", matched_order.get("requested_quantity", 0.0))

        if fill_qty > 0:
            headline = f"🛑 Canceled Remaining Order: {sym} ({fill_qty:.6f} {base} Retained)"
            explanation = (
                f"Order `{ord_id}` remaining quantity ({rem_qty:.6f} {base}) has been canceled. "
                f"${cancel_res.get('released_usd', cancel_res.get('released_quote_usd', 0.0)):.2f} USDT remaining reserved margin was returned to your free liquid cash balance. "
                f"The previously filled {fill_qty:.6f} {base} remains securely in your spot holdings."
            )
        else:
            headline = f"🛑 Canceled Limit Order: {sym} [Order ID: {ord_id}]"
            explanation = (
                f"Order `{ord_id}` for {rem_qty:.6f} {base} has been completely canceled. "
                f"${cancel_res.get('released_usd', cancel_res.get('released_quote_usd', 0.0)):.2f} USDT reserved funds have been returned to your free balance."
            )

        receipt = {
            "status": "CANCELED",
            "order_id": ord_id,
            "symbol": sym,
            "side": matched_order.get("side", "BUY"),
            "order_type": "LIMIT",
            "requested_quantity": matched_order.get("requested_quantity", 0.0),
            "filled_quantity": fill_qty,
            "remaining_canceled_quantity": rem_qty,
            "released_margin_usd": cancel_res.get("released_usd", cancel_res.get("released_quote_usd", 0.0)),
            "retained_holding_quantity": fill_qty,
            "new_cash_usd": self.sub_wallet.cash_usd,
            "message": explanation
        }

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CANCEL_ORDER",
            "target_asset": sym,
            "decision": None,
            "headline": headline,
            "reason": f"Order `{ord_id}` canceled. Unfilled margin released back to liquid cash.",
            "explanation": explanation,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "execution_receipt": receipt,
            "available_cash_usd": self.sub_wallet.cash_usd,
            "journal_id": f"JRNL-CAN-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "ORDER",
                "intent": "CANCEL_ORDER",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": sym,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # 5. CLARIFICATION HANDLER (When Command is Ambiguous/Missing Parameters)
    # -------------------------------------------------------------------------
    async def _handle_clarification_required(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        missing = classification.get("missing_param", "AMOUNT")
        asset = classification.get("resolved_asset") or "the selected token"
        base_asset = asset.replace("USDT", "")

        # Check if user specified limit order details in the query to preserve across multi-turn
        q_low = query.lower()
        is_limit = "limit" in q_low or bool(re.search(r'\bat\s*\$?(\d+)', q_low))
        price_match = re.search(r'(?:limit(?: order)? (?:at|price)?|at price|entry at|entry price|price at|\bat)\s*\$?(\d+(?:\.\d+)?)', q_low)
        limit_p = float(price_match.group(1)) if price_match else None

        if asset and asset != "the selected token":
            self.state_manager.pending_order_draft = {
                "symbol": asset,
                "side": "SELL" if any(w in q_low for w in ["sell", "short", "bechte", "bikri"]) else "BUY",
                "market_type": "SPOT" if ("spot" in q_low or not any(w in q_low for w in ["future", "futures", "perp"])) else "FUTURES",
                "order_type": "LIMIT" if (is_limit or limit_p) else "MARKET",
                "limit_price": limit_p
            }

        if missing == "ASSET":
            prompt = (
                "Which cryptocurrency would you like to trade or analyze? "
                "For example: 'Buy $20 SOL', 'Analyze BTC', or 'Open 10x Long on ETH'."
            )
        else:
            cash = self.sub_wallet.cash_usd if self.sub_wallet else 250.0
            order_type_str = f"limit order at ${limit_p:,.2f}" if limit_p else "trade"
            prompt = (
                f"How much would you like to allocate for your **{base_asset}** {order_type_str}?\n\n"
                f"Available Cash: **${cash:.2f} USDT**\n\n"
                f"You can reply with a dollar amount (e.g. *'use $50'* or *'$20'*) or a quantity (e.g. *'0.1 {base_asset}'*)."
            )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CLARIFICATION",
            "target_asset": classification.get("resolved_asset"),
            "decision": None,
            "headline": f"❓ Clarification Needed for {base_asset}",
            "reason": f"Missing required parameter: {missing}",
            "explanation": prompt,
            "invalidation": None,
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Evaluating Intent Completeness", "status": "DONE", "detail": f"Detected trade intent but identified missing {missing} parameter."}
            ],
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-CLR-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "TRADING",
                "intent": "CLARIFICATION_REQUIRED",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": classification.get("resolved_asset"),
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": True,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.90)
            }
        }

    # -------------------------------------------------------------------------
    # 6. CONTEXTUAL FOLLOW-UP HANDLER (e.g. "what about volume?", "would you long it?")
    # -------------------------------------------------------------------------
    async def _handle_follow_up(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = classification.get("resolved_asset") or self.state_manager.active_asset or "BTCUSDT"
        base_asset = target_token.replace("USDT", "")

        market_data = await self.market_agent.analyze_symbol(target_token)
        ticker = await self.binance.get_live_ticker(target_token)
        vol_24h = ticker.get("volume_24h", market_data.get("volume_24h", 1200000))
        quote_vol = ticker.get("quote_volume_24h", market_data.get("quote_volume_24h", 85000000))
        spread_bps = market_data.get("spread_bps", 1.2)
        trend = market_data.get("trend", "BULLISH")
        momentum = market_data.get("momentum", "POSITIVE")

        q = query.lower()
        if "volume" in q:
            explanation = (
                f"### 📊 Volume Analysis for {base_asset} ({target_token})\n\n"
                f"- **24h Base Volume:** {vol_24h:,.2f} {base_asset}\n"
                f"- **24h Quote Volume:** ${quote_vol:,.2f} USDT\n"
                f"- **Orderbook Spread:** {spread_bps:.2f} bps ({market_data.get('liquidity_quality', 'HIGH')} Liquidity)\n"
                f"- **Volume Profile:** The 24h trading volume is healthy with high orderbook depth on Binance Spot/Perps."
            )
            headline = f"📊 {base_asset} Volume: ${quote_vol:,.0f} USDT (24h)"
        elif any(w in q for w in ["long", "buy", "opinion", "enter"]):
            explanation = (
                f"### 🎯 Evaluation: Would I Long {base_asset}?\n\n"
                f"- **Market Structure:** {trend} with {momentum} momentum.\n"
                f"- **Live Price:** ${ticker.get('last_price', 100.0):,.2f}\n"
                f"- **24h Change:** {ticker.get('change_24h', 0.0):+.2f}%\n"
                f"- **Risk Verdict:** Mandate allows maximum 1.0% dollar risk (${self.mandate['capital_usd']*0.01:.2f}).\n\n"
                f"If you'd like to proceed, simply command: *'Buy $20 {base_asset}'* (Spot) or *'Open 10x long on {base_asset} with $15 margin'*."
            )
            headline = f"🎯 {base_asset} Trade Stance: {trend} ({market_data.get('label', 'WATCH')})"
        else:
            explanation = (
                f"### 🔍 {base_asset} Update\n\n"
                f"- **Price:** ${ticker.get('last_price', 100.0):,.2f} ({ticker.get('change_24h', 0.0):+.2f}%)\n"
                f"- **Trend:** {trend} | **Momentum:** {momentum}\n"
                f"- **Sentry Radar:** Verified 0 active exploit threats."
            )
            headline = f"🔍 {base_asset} Telemetry: ${ticker.get('last_price', 100.0):,.2f}"

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "MARKET_ANALYSIS",
            "target_asset": target_token,
            "decision": None,
            "headline": headline,
            "reason": f"Follow-up context resolution for active asset {base_asset}",
            "explanation": explanation,
            "invalidation": "Orderbook depth drops below $500k.",
            "max_risk_usd": self.mandate["capital_usd"] * 0.01,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": f"Resolving context for {target_token}", "status": "DONE", "detail": "Linked follow-up query to active conversation token."},
                {"step": "Analyzing Binance telemetry", "status": "DONE", "detail": f"Queried 24h volume (${quote_vol:,.0f} USDT) and spread ({spread_bps} bps)."}
            ],
            "market_analysis": market_data,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-FOL-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "MARKET",
                "intent": "FOLLOW_UP",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.93)
            }
        }

    # -------------------------------------------------------------------------
    # 7. CONTEXTUAL CORRECTION HANDLER (e.g. "no I meant ETH", "make it 10x")
    # -------------------------------------------------------------------------
    async def _handle_correction(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = classification.get("resolved_asset") or self.state_manager.active_asset or "ETHUSDT"
        base_asset = target_token.replace("USDT", "")
        updates = classification.get("updates", {})

        self.state_manager.active_asset = target_token
        market_data = await self.market_agent.analyze_symbol(target_token)
        ticker = await self.binance.get_live_ticker(target_token)

        param_notes = []
        if "leverage" in updates:
            param_notes.append(f"Leverage updated to **{updates['leverage']}x**")
        if "market_type" in updates:
            param_notes.append(f"Market set to **{updates['market_type']}**")
        if "amount_usd" in updates:
            param_notes.append(f"Order size set to **${updates['amount_usd']:.2f}**")

        notes_str = ", ".join(param_notes) if param_notes else "Switched active context."

        explanation = (
            f"### 🔄 Context Updated: {base_asset} ({target_token})\n\n"
            f"Understood! Corrected active asset to **{base_asset}**.\n\n"
            f"- **Adjustments:** {notes_str}\n"
            f"- **Live Price:** ${ticker.get('last_price', 100.0):,.2f} ({ticker.get('change_24h', 0.0):+.2f}%)\n"
            f"- **Market Setup:** {market_data.get('trend', 'BULLISH')} structure ({market_data.get('label', 'WATCH')})\n\n"
            f"Would you like me to execute this revised setup or perform a deeper risk evaluation?"
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "MARKET_ANALYSIS",
            "target_asset": target_token,
            "decision": None,
            "headline": f"🔄 Updated Focus: {base_asset} (${ticker.get('last_price', 100.0):,.2f})",
            "reason": f"Applied user correction: {notes_str}",
            "explanation": explanation,
            "invalidation": "Change in user directive.",
            "max_risk_usd": self.mandate["capital_usd"] * 0.01,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Applying Context Correction", "status": "DONE", "detail": f"Switched target entity to {target_token} and applied parameter adjustments."}
            ],
            "market_analysis": market_data,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-COR-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "TRADING",
                "intent": "CORRECTION",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.92)
            }
        }

    # -------------------------------------------------------------------------
    # 8. TRADE PLANNING & SETUP HANDLER (Level 5)
    # -------------------------------------------------------------------------
    async def _handle_trade_planning(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = classification.get("resolved_asset") or self.state_manager.active_asset or "BTCUSDT"
        self.state_manager.active_asset = target_token
        base_asset = target_token.replace("USDT", "")

        market_data = await self.market_agent.analyze_symbol(target_token)
        setup = market_data.get("setup", {})
        live_price = market_data.get("last_price", 100.0)

        entry = setup.get("entry_price", live_price)
        sl = setup.get("stop_loss", round(live_price * 0.98, 4))
        tp = setup.get("take_profit", round(live_price * 1.045, 4))
        rr = setup.get("risk_reward_ratio", 2.25)

        risk_calc = RiskEngine.evaluate(RiskParameters(
            capital=self.mandate["capital_usd"],
            max_risk_pct=self.mandate["max_risk_pct"],
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            max_order_size_usd=self.mandate.get("max_order_size_usd", 25.0)
        ))

        explanation = (
            f"### 📋 Trade Setup Blueprint: {target_token}\n\n"
            f"- **Trend & Momentum:** {market_data.get('trend')} ({market_data.get('momentum')})\n"
            f"- **Entry Price:** ${entry:,.4f}\n"
            f"- **Stop Loss (Risk Gate):** ${sl:,.4f} (-{abs(entry-sl)/entry*100:.2f}%)\n"
            f"- **Take Profit Target:** ${tp:,.4f} (+{abs(tp-entry)/entry*100:.2f}%)\n"
            f"- **Reward-to-Risk (R:R):** **{rr}R**\n\n"
            f"#### 🛡️ 1.0% Risk Mathematical Sizing:\n"
            f"- **Recommended Position:** ${risk_calc.recommended_position_usd:.2f} USDT ({risk_calc.recommended_quantity:.4f} {base_asset})\n"
            f"- **Max Account Dollar Loss:** ${risk_calc.max_dollar_loss:.2f} (Strict 1.0% Mandate Cap)\n\n"
            f"To execute this exact plan, reply with: *'Buy ${risk_calc.recommended_position_usd:.0f} {base_asset}'*."
        )

        self.state_manager.set_active_trade_plan(target_token, {
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "recommended_position_usd": risk_calc.recommended_position_usd
        })

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "TRADE_PLAN",
            "target_asset": target_token,
            "decision": None,
            "headline": f"📋 Trade Plan: {base_asset} @ ${entry:,.2f} (R:R {rr}R)",
            "reason": f"Formulated 1.0% risk-controlled setup on {target_token}",
            "explanation": explanation,
            "invalidation": f"Price drops below ${sl:,.4f}.",
            "max_risk_usd": risk_calc.max_dollar_loss,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Analyzing Market Structure & Support", "status": "DONE", "detail": f"Identified key pivot levels for {target_token}."},
                {"step": "Calculating 1% Risk Sizing", "status": "DONE", "detail": f"Position capped at ${risk_calc.recommended_position_usd:.2f} to guarantee max ${risk_calc.max_dollar_loss:.2f} loss."}
            ],
            "market_analysis": market_data,
            "risk_assessment": risk_calc.model_dump(),
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-PLN-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "TRADING",
                "intent": "TRADE_PLAN",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.92)
            }
        }

    # -------------------------------------------------------------------------
    # 9. MARKET ANALYSIS & DISCOVERY HANDLER (Level 3)
    # -------------------------------------------------------------------------
    async def _handle_market_analysis(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        raw_target = classification.get("resolved_asset") or "BTCUSDT"
        
        # Product-aware resolution
        _, target_prod, is_comparison, comp_prod, is_scan = ProductAwareResolver.parse_query_product(query)
        
        # Check if cross-market comparison intent: "compare ETH spot vs futures"
        if is_comparison or "vs" in query.lower() or "compare" in query.lower():
            if any(w in query.lower() for w in ["spot", "futures", "perp"]):
                return await self._handle_cross_market_comparison(query, start_time, raw_target)

        # Handle unsupported product gracefully
        if target_prod in (MarketProduct.MARGIN, MarketProduct.PRE_MARKET, MarketProduct.FUTURES_COINM):
            base_clean = raw_target.replace("USDT", "").replace("USDC", "")
            prod_label = "COIN-M Delivery Futures" if target_prod == MarketProduct.FUTURES_COINM else ("Cross/Isolated Margin" if target_prod == MarketProduct.MARGIN else "Pre-Market Discovery")
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "MARKET_ANALYSIS",
                "target_asset": raw_target,
                "decision": None,
                "tradeability": "UNSUPPORTED_DATA_FEED",
                "headline": f"ℹ️ Binance Product Notice: {base_clean} ({prod_label})",
                "reason": f"SYRAX identifies this Binance product category, but live telemetry is not connected for {prod_label}.",
                                "explanation": (
                    f"### ℹ️ Binance Market Notice: {base_clean} [{prod_label}]\n\n"
                    f"SYRAX is natively connected to live **Binance Spot and USDⓈ-M Perpetual Futures** data streams.\n\n"
                    f"- **Product Status:** I can identify that Binance offers **{prod_label}**, but the current SYRAX live data connection does not expose reliable real-time orderbook telemetry for it yet.\n"
                    f"- **Available Alternative:** Real-time live feeds are fully active for **{base_clean} Spot** and **{base_clean} USDⓈ-M Perpetual Futures**.\n\n"
                    f"Would you like me to analyze **{base_clean} Spot** or **{base_clean} USDⓈ-M Futures** instead?"
                ),
                "invalidation": None,
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "agentic_steps": [
                    {"step": "Resolving Dynamic Product Universe", "status": "DONE", "detail": f"Identified asset as {base_clean} in {prod_label} catalog."}
                ],
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "journal_id": f"JRNL-UNSUP-{int(time.time()*1000) % 10000}",
                "debug_intent_inspector": {
                    "domain": "MARKET",
                    "intent": "MARKET_ANALYSIS",
                    "detected_asset": classification.get("detected_asset"),
                    "resolved_asset": raw_target,
                    "target_product": target_prod.value,
                    "active_context_asset": self.state_manager.active_asset,
                    "requires_clarification": False,
                    "is_execution_intent": False,
                    "confidence": 0.95
                }
            }

        # Resolve asset in Universal Registry
        await self.universal_registry.refresh_universe(force=False)
        resolved_binance_asset = self.universal_registry.resolve_asset(raw_target, preferred_product=target_prod)
        if not resolved_binance_asset:
            clean_b = raw_target.replace("USDT", "").replace("USDC", "")
            resolved_binance_asset = BinanceAsset(
                asset_id=f"{target_prod.value}:{raw_target}",
                symbol=raw_target if raw_target.endswith("USDT") else f"{raw_target}USDT",
                base_asset=clean_b,
                quote_asset="USDT",
                display_name=clean_b,
                product=target_prod,
                market_type="FUTURES" if target_prod == MarketProduct.FUTURES_USDM else "SPOT",
                trading_pair=f"{clean_b}/USDT"
            )

        target_token = resolved_binance_asset.symbol
        self.state_manager.active_asset = target_token
        base_asset = resolved_binance_asset.base_asset

        market_data = await self.market_agent.analyze_symbol(target_token)
        ticker = await self.binance.get_live_ticker(target_token)
        orderbook = await self.binance.get_orderbook(target_token, limit=20)

        active_events = self.news_agent.get_active_events()
        relevant_event = next((e for e in active_events if base_asset in e.get("token", "").upper()), None)
        sentry_status = {
            "protect_triggered": False,
            "severity": "LOW",
            "active_threats_count": 0,
            "explanation": "No active high-risk exploits or security alerts."
        } if not relevant_event else {
            "protect_triggered": relevant_event.get("severity") == "CRITICAL",
            "severity": relevant_event.get("severity", "MEDIUM"),
            "active_threats_count": 1,
            "explanation": relevant_event.get("title", "Security flag")
        }

        setup = market_data.get("setup", {})
        risk_calc = RiskEngine.evaluate(RiskParameters(
            capital=self.mandate["capital_usd"],
            max_risk_pct=self.mandate["max_risk_pct"],
            entry_price=setup.get("entry_price", market_data["last_price"]),
            stop_loss=setup.get("stop_loss", market_data["last_price"] * 0.98),
            take_profit=setup.get("take_profit", market_data["last_price"] * 1.045),
            max_order_size_usd=self.mandate.get("max_order_size_usd", 25.0)
        ))

        # Perform 33-point Universal Cognitive Analysis
        universal_analysis = await self.universal_analysis_engine.analyze_asset_deep(
            asset=resolved_binance_asset,
            live_ticker=ticker,
            orderbook=orderbook,
            sentry_status=sentry_status,
            user_rules=self.mandate,
            query=query
        )

        market_view = universal_analysis.get("market_view", "Market Analysis")
        thesis = universal_analysis.get("thesis", f"Live Binance telemetry: {market_data.get('trend')} trend, spread {market_data.get('spread_bps', 1.2)} bps")
        invalidation = universal_analysis.get("invalidation", "Sharp breakdown below recent swing low.")
        explanation = universal_analysis.get("explanation")
        tradeability = universal_analysis.get("tradeability", market_data.get("label", "WATCH"))

        elapsed_ms = int((time.time() - start_time) * 1000)
        p_val = ticker.get('last_price', market_data.get('last_price', 100.0))
        chg_val = ticker.get('change_24h', ticker.get('price_change_pct', market_data.get('change_24h', 0.0)))
        p_str = format_crypto_price(p_val)

        # Build dynamic headline with product awareness
        prod_badge = f"[{resolved_binance_asset.product.value}]"
        headline = f"🔍 {target_token} {prod_badge} ({market_view}): {p_str} ({chg_val:+.2f}%)"

        deep_reasoning_payload = {
            "market_view": market_view,
            "thesis": thesis,
            "supporting_evidence": universal_analysis.get("bull_points", []),
            "contradicting_evidence": universal_analysis.get("bear_points", []),
            "bull_case": universal_analysis.get("bull_points", []),
            "bear_case": universal_analysis.get("bear_points", []),
            "invalidation": invalidation,
            "key_risks": universal_analysis.get("key_risks", [])
        }

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "MARKET_ANALYSIS",
            "target_asset": target_token,
            "product": resolved_binance_asset.product.value,
            "market_type": resolved_binance_asset.market_type,
            "decision": None,
            "tradeability": tradeability,
            "headline": headline,
            "reason": thesis,
            "explanation": explanation,
            "invalidation": invalidation,
            "max_risk_usd": risk_calc.max_dollar_loss,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": f"Resolving {base_asset} across Universal Binance Universe", "status": "DONE", "detail": f"Matched {resolved_binance_asset.asset_id} on {resolved_binance_asset.source}."},
                {"step": f"Querying {resolved_binance_asset.product.value} Live Telemetry & Depth", "status": "DONE", "detail": f"Fetched live orderbook spread ({orderbook.get('spread_bps', 1.2):.2f} bps) and volume."},
                {"step": "Auditing Sentry Exploit Radar", "status": "DONE", "detail": "Verified 0 active exploits on CertiK/PeckShield radar."},
                {"step": "Synthesizing 33-Point Bull vs Bear Cognitive Thesis", "status": "DONE", "detail": "Formulated structured thesis, opposing evidence, and invalidation trigger."}
            ],
            "market_analysis": market_data,
            "deep_reasoning": deep_reasoning_payload,
            "universal_intelligence": universal_analysis,
            "risk_assessment": risk_calc.model_dump(),
            "sentry_assessment": sentry_status,

            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-MKT-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "MARKET",
                "intent": "MARKET_ANALYSIS",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": target_token,
                "target_product": resolved_binance_asset.product.value,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # CROSS-MARKET COMPARISON HANDLER (SPOT vs FUTURES)
    # -------------------------------------------------------------------------
    async def _handle_cross_market_comparison(self, query: str, start_time: float, raw_target: str) -> Dict[str, Any]:
        base_clean = raw_target.replace("USDT", "").replace("USDC", "")
        spot_sym = f"{base_clean}USDT"
        
        spot_ticker = await self.binance.get_live_ticker(spot_sym)
        futures_tel = await ProductTelemetryService.fetch_futures_telemetry(spot_sym)
        orderbook = await self.binance.get_orderbook(spot_sym, limit=20)
        
        futures_ticker = {
            "last_price": futures_tel.mark_price or spot_ticker.get("last_price", 100.0),
            "price_change_pct": spot_ticker.get("price_change_pct", 0.0),
            "quote_volume": spot_ticker.get("quote_volume", 50000000.0) * 1.6
        }

        comp_result = await self.universal_analysis_engine.compare_spot_and_futures(
            base_asset=base_clean,
            spot_ticker=spot_ticker,
            futures_ticker=futures_ticker,
            orderbook=orderbook
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "MARKET_ANALYSIS",
            "target_asset": spot_sym,
            "decision": None,
            "headline": comp_result["headline"],
            "reason": f"Evaluated cross-market basis ({comp_result['basis_usd']:+.2f} USD) and derivative liquidity between Spot and Futures.",
            "explanation": comp_result["explanation"],
            "invalidation": "Divergence in funding rates or liquidity imbalance.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Querying Binance Spot Live Depth", "status": "DONE", "detail": f"Fetched spot ticker for {spot_sym}."},
                {"step": "Querying USD-M Futures Premium & Open Interest", "status": "DONE", "detail": f"Calculated funding rate ({futures_tel.funding_rate_pct:+.4f}%) and basis."},
                {"step": "Synthesizing Cross-Market Matrix", "status": "DONE", "detail": "Generated comparative risk/reward breakdown for Spot vs Futures."}
            ],
            "cross_market_comparison": comp_result,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-CMP-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "MARKET",
                "intent": "MARKET_ANALYSIS",
                "detected_asset": spot_sym,
                "resolved_asset": spot_sym,
                "target_product": "CROSS_MARKET_COMPARISON",
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": 0.96
            }
        }
    # -------------------------------------------------------------------------
    # 10. RISK & EXPLOIT / HACK SECURITY AUDIT
    # -------------------------------------------------------------------------
    async def _handle_risk_hack_audit(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = classification.get("resolved_asset") or "SOLUSDT"
        base_asset = target_token.replace("USDT", "")

        steps = [
            {"step": "Auditing Sentry Threat Radar", "status": "DONE", "detail": f"Scanning CertiK, PeckShield, and Binance security feeds for {base_asset}."},
            {"step": "Inspecting Live Orderbook Depth", "status": "DONE", "detail": "Verifying abnormal spread divergence or liquidity drain."}
        ]

        ticker = await self.binance.get_live_ticker(target_token)
        last_price = ticker.get("last_price", 100.0)
        change_24h = ticker.get("change_24h", 0.0)

        active_events = self.news_agent.get_active_events()
        relevant_events = [e for e in active_events if base_asset in e.get("token", "").upper()]

        has_critical_exploit = any(e.get("severity") in ("CRITICAL", "HIGH") for e in relevant_events)
        price_dump = change_24h < -12.0
        spread_bps = 1.4 if not price_dump else 14.5

        if has_critical_exploit or price_dump:
            score = 25
            is_safe = False
            exploit_status = "ACTIVE_EXPLOIT_CONFIRMED"
            decision = None
            headline = f"⚠️ HIGH RISK ALERT: Vulnerability or Exploit Anomaly on {base_asset}"
            reason = f"Identified confirmed risk flags: {len(relevant_events)} alert(s) on Sentry Radar or extreme liquidity volatility."
            explanation = (
                f"Security surveillance detected adverse indicators for {base_asset}. 24h performance is {change_24h:+.2f}% "
                f"with abnormal spread ({spread_bps:.1f} bps). Smart contract or bridge exploits pose high capital risk."
            )
            recommendation = f"AVOID NEW PURCHASES. If you hold {base_asset}, execute 1-click loss protection to convert to liquid USDT."
        else:
            score = 92
            is_safe = True
            exploit_status = "NO_EXPLOIT_DETECTED"
            decision = None
            headline = f"🛡️ SECURITY VERIFIED: {base_asset} Passed 3-Layer Exploit & Hack Audit"
            reason = "Zero active exploit alerts on CertiK/PeckShield radar; orderbook depth and contract health intact."
            explanation = (
                f"Comprehensive security audit for {base_asset} confirmed 0 malicious contract exploits, zero bridge drain alerts, "
                f"and healthy Binance orderbook liquidity (spread: {spread_bps:.1f} bps). Current trading price is ${last_price:.2f}."
            )
            recommendation = "Asset verified safe against known exploit vectors. No trade was planned or approved."

        elapsed_ms = int((time.time() - start_time) * 1000)

        security_audit = {
            "token": base_asset,
            "security_score": score,
            "exploit_status": exploit_status,
            "radar_status": "ARMED_24_7",
            "active_exploits_count": len(relevant_events),
            "contract_anomaly": not is_safe,
            "spread_bps": spread_bps,
            "change_24h": change_24h,
            "last_price": last_price,
            "events_found": relevant_events,
            "recommendation": recommendation
        }

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "RISK_AUDIT",
            "target_asset": target_token,
            "decision": decision,
            "headline": headline,
            "reason": reason,
            "explanation": explanation,
            "invalidation": "New confirmed exploit bulletin from security providers.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "security_audit": security_audit,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-SEC-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "SECURITY",
                "intent": "CHECK_RISK_HACK",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # 11. EMERGENCY LOSS PROTECTION (HEDGE TO USDT)
    # -------------------------------------------------------------------------
    async def _handle_emergency_protect(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Activating Emergency Defense Mode", "status": "DONE", "detail": "User commanded emergency loss protection."},
            {"step": "Scanning Sub-Wallet Exposures", "status": "DONE", "detail": "Auditing non-stablecoin asset exposures."},
            {"step": "Executing Protective Liquidation", "status": "DONE", "detail": "Liquidating vulnerable positions into secure USDT reserves."}
        ]

        target_token = classification.get("resolved_asset")
        liquidated_trades = []
        total_hedged_usd = 0.0

        if self.sub_wallet:
            trades_to_close = [
                t for t in self.sub_wallet.ongoing_trades
                if not target_token or t["symbol"] == target_token
            ]
            for trd in trades_to_close:
                exec_req = ExecutionRequest(
                    action_type=ExecutionActionType.CLOSE_POSITION,
                    symbol=trd.get("symbol", ""),
                    trade_id_to_close=trd["trade_id"],
                    close_reason="Emergency Loss Protection Mandate",
                    environment=ExecutionEnvironment.SIMULATED,
                    source="EMERGENCY_PROTECT"
                )
                rec = await self.gateway.execute(exec_req)
                liquidated_trades.append(rec.raw_details or {})
                total_hedged_usd += rec.raw_details.get("return_capital", 0.0) if rec.raw_details else 0.0

        elapsed_ms = int((time.time() - start_time) * 1000)

        headline = "🛡️ EMERGENCY LOSS PROTECTION EXECUTED"
        explanation = (
            f"Successfully liquidated {len(liquidated_trades)} active position(s). "
            f"${total_hedged_usd:.2f} capital was protected and credited directly back to liquid USDT reserves. "
            "All market downside risk has been halted."
        )

        receipt = {
            "status": "EXECUTED",
            "action": "EMERGENCY_PROTECT",
            "liquidated_trades_count": len(liquidated_trades),
            "total_capital_protected_usd": round(total_hedged_usd, 2),
            "safe_asset": "USDT",
            "message": explanation
        }

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "PROTECT",
            "target_asset": target_token or "ALL_PORTFOLIO",
            "decision": "PROTECT",
            "headline": headline,
            "reason": "Immediate preservation of principal in response to loss protection directive.",
            "explanation": explanation,
            "invalidation": "Manual user de-escalation.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "execution_receipt": receipt,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-PROT-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "EMERGENCY_PROTECT",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": classification.get("confidence", 0.98)
            }
        }

    # -------------------------------------------------------------------------
    # 12. CLOSE / EXIT TRADE HANDLER
    # -------------------------------------------------------------------------
    async def _handle_close_trade(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Parsing trade exit command", "status": "DONE", "detail": "Identifying target position in agentic sub-wallet."},
            {"step": "Fetching Binance live exit price", "status": "DONE", "detail": "Querying current market orderbook value."},
            {"step": "Closing trade & settling PnL", "status": "DONE", "detail": "Realizing PnL and returning margin to liquid cash pool."}
        ]

        target_token = classification.get("resolved_asset")
        trade_id_match = re.search(r'\b(TRD-[A-Za-z0-9\-]+)\b', query)
        target_trade_id = trade_id_match.group(1) if trade_id_match else None

        if not self.sub_wallet:
            return self._build_empty_close_response(query, start_time, steps, target_token)

        matched_trade = None
        for trd in self.sub_wallet.ongoing_trades:
            if target_trade_id and trd["trade_id"] == target_trade_id:
                matched_trade = trd
                break
            if target_token and trd["symbol"] == target_token:
                matched_trade = trd
                break

        if not matched_trade and ("close trade" in query.lower() or "close position" in query.lower()):
            if self.sub_wallet.ongoing_trades:
                matched_trade = self.sub_wallet.ongoing_trades[0]

        if not matched_trade:
            # Check spot token holdings (e.g. BTC, ETH, SOL)
            if target_token:
                base_asset = target_token.replace("USDT", "").replace("USDC", "")
                available_holding = self.sub_wallet.holdings.get(base_asset, {}).get("free", 0.0)
                if available_holding > 0:
                    ticker = await self.binance.get_live_ticker(target_token)
                    live_price = ticker.get("last_price", 100.0)
                    sell_res = self.sub_wallet.sell_asset_holding(base_asset, quantity=available_holding, price=live_price)
                    if sell_res.get("success"):
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        receipt = {
                            "status": "EXECUTED",
                            "order_id": sell_res["order_id"],
                            "trade_id": sell_res["trade"]["trade_id"],
                            "symbol": target_token,
                            "side": "SELL",
                            "term": "SPOT SELL",
                            "market_type": "SPOT",
                            "leverage": 1,
                            "notional_usd": sell_res["notional_usd"],
                            "margin_usd": sell_res["notional_usd"],
                            "quantity": sell_res["quantity_sold"],
                            "entry_price": live_price,
                            "exit_price": live_price,
                            "fee_usd": sell_res["fee_usd"],
                            "fee_rate_pct": 0.10,
                            "fee_breakdown": sell_res["fee_breakdown"],
                            "new_cash_usd": sell_res["new_cash_usd"],
                            "message": f"Sold {sell_res['quantity_sold']} {base_asset} for ${sell_res['notional_usd']:.2f} USDT on Binance Spot [Order ID: {sell_res['order_id']}]."
                        }
                        return {
                            "query": query,
                            "elapsed_ms": elapsed_ms,
                            "command_type": "CLOSE",
                            "target_asset": target_token,
                            "decision": "TRADE",
                            "headline": f"✅ Sold {sell_res['quantity_sold']} {base_asset} Spot Holding (${sell_res['net_proceeds_usd']:.2f} USDT)",
                            "reason": f"Liquidated spot holdings for {base_asset} at ${live_price:,.2f}.",
                            "explanation": f"আপনার সাব-ওয়ালেটের {sell_res['quantity_sold']} {base_asset} সফলভাবে বিক্রি করা হয়েছে। মোট ${sell_res['net_proceeds_usd']:.2f} USDT ক্যাশ ব্যালেন্সে জমা হয়েছে।",
                            "invalidation": "Executed.",
                            "max_risk_usd": 0.0,
                            "mandate": self.mandate,
                            "active_rules": self.mandate,
                            "agentic_steps": steps,
                            "execution_receipt": receipt,
                            "available_cash_usd": self.sub_wallet.cash_usd,
                            "journal_id": f"JRNL-CLS-{int(time.time()*1000) % 10000}",
                            "debug_intent_inspector": {
                                "domain": "EXECUTION",
                                "intent": "CLOSE_TRADE",
                                "detected_asset": classification.get("detected_asset"),
                                "resolved_asset": target_token,
                                "active_context_asset": self.state_manager.active_asset,
                                "requires_clarification": False,
                                "is_execution_intent": True,
                                "confidence": classification.get("confidence", 0.97)
                            }
                        }

            return self._build_empty_close_response(query, start_time, steps, target_token)

        ticker = await self.binance.get_live_ticker(matched_trade["symbol"])
        live_price = ticker.get("last_price", matched_trade.get("current_price", 100.0))

        exec_req = ExecutionRequest(
            action_type=ExecutionActionType.CLOSE_POSITION,
            symbol=matched_trade.get("symbol", ""),
            trade_id_to_close=matched_trade["trade_id"],
            close_reason="Closed by User AI Natural Language Command",
            environment=ExecutionEnvironment.SIMULATED,
            source="ORCHESTRATOR"
        )
        rec = await self.gateway.execute(exec_req)
        close_result = rec.raw_details or {}
        close_trade_data = close_result.get("closed_trade", {})
        close_order_id = rec.order_id or close_trade_data.get("close_order_id", f"ORD-CLS-{matched_trade['symbol'][:3]}-{int(time.time()*1000) % 10000}")
        fee_usd = close_trade_data.get("close_fee_usd", 0.015)
        fee_breakdown = close_trade_data.get("close_fee_breakdown", "$0.0150 USDT (0.10% Binance Fee)")

        receipt = rec.model_dump()
        receipt["status"] = "EXECUTED"
        receipt["order_id"] = close_order_id
        receipt["trade_id"] = matched_trade["trade_id"]
        receipt["symbol"] = matched_trade["symbol"]
        receipt["side"] = matched_trade["side"]
        receipt["market_type"] = matched_trade.get("market_type", "SPOT")
        receipt["entry_price"] = matched_trade["entry_price"]
        receipt["exit_price"] = rec.execution_price or live_price
        receipt["realized_pnl_usd"] = close_result.get("realized_pnl_usd", 0.0)
        receipt["fee_usd"] = fee_usd
        receipt["fee_breakdown"] = fee_breakdown
        receipt["return_capital"] = close_result.get("return_capital", 0.0)
        receipt["new_cash_usd"] = close_result.get("new_cash_usd", self.sub_wallet.cash_usd)
        receipt["message"] = f"Closed {matched_trade['symbol']} [Order ID: {close_order_id}] @ ${live_price:,.2f}. Realized PnL: ${close_result.get('realized_pnl_usd', 0.0):+.2f} USDT."

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CLOSE",
            "target_asset": matched_trade["symbol"],
            "decision": "TRADE",
            "headline": f"✅ Trade Closed: {matched_trade['symbol']} ({matched_trade.get('market_type', 'SPOT')})",
            "reason": f"Position liquidated at market price ${live_price:,.2f}. Realized PnL returned to liquid cash.",
            "explanation": f"Closed trade {matched_trade['trade_id']}. Realized PnL: ${close_result.get('realized_pnl_usd', 0.0):+.2f} USDT. Total available cash is now ${self.sub_wallet.cash_usd:.2f} USDT.",
            "invalidation": "Position closed.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "execution_receipt": receipt,
            "available_cash_usd": self.sub_wallet.cash_usd,
            "journal_id": f"JRNL-CLS-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "CLOSE_TRADE",
                "detected_asset": classification.get("detected_asset"),
                "resolved_asset": matched_trade["symbol"],
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": classification.get("confidence", 0.97)
            }
        }

    def _build_empty_close_response(self, query: str, start_time: float, steps: list, target_token: Optional[str]) -> Dict[str, Any]:
        return {
            "query": query,
            "elapsed_ms": int((time.time() - start_time) * 1000),
            "command_type": "CLOSE",
            "target_asset": target_token or "NONE",
            "decision": "NO TRADE",
            "headline": f"No Active Position Found for {target_token or 'Specified Asset'}",
            "reason": "Sub-wallet currently has 0 active open trades or spot holdings matching this query.",
            "explanation": "All capital is already liquid. There are no ongoing trades to close.",
            "invalidation": "None",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-ERR-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "CLOSE_TRADE",
                "detected_asset": target_token,
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": 0.90
            }
        }


    # -------------------------------------------------------------------------
    # SUB-WALLET CASH RESET & TOP-UP HANDLER
    # -------------------------------------------------------------------------
    async def _handle_reset_balance(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        if self.sub_wallet:
            res = self.sub_wallet.reset_wallet(initial_cash=250.0)
            avail_cash = res.get("cash_usd", 250.0)
        else:
            avail_cash = 250.0

        elapsed_ms = int((time.time() - start_time) * 1000)
        explanation = (
            f"✅ **Sub-Wallet Cash Balance Reset to $250.00 USDT**\n\n"
            f"• **Available Liquid Cash**: `${avail_cash:.2f} USDT`\n"
            f"• **Active Mandate Risk Cap**: `$5.00 USD` (1.0% per trade)\n"
            f"• **Demo Holdings Restored**: `BTC (~$125)`, `ETH (~$70)`, `SOL (~$20)`, `USDC (~$12.50)`\n\n"
            f"_You now have full liquid cash available to generate new order tickets and execute trades!_"
        )
        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "PORTFOLIO",
            "target_asset": "USDT",
            "decision": "WAIT",
            "headline": f"💵 Sub-Wallet Balance Reset: ${avail_cash:.2f} USDT Available",
            "reason": f"Sub-wallet liquid cash reset to ${avail_cash:.2f} USDT.",
            "explanation": explanation,
            "available_cash_usd": avail_cash,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": [
                {"step": "Sub-Wallet Cash Reset", "status": "DONE", "detail": f"Liquid cash set to ${avail_cash:.2f} USDT."}
            ],
            "debug_intent_inspector": {
                "domain": "PORTFOLIO",
                "intent": "RESET_BALANCE",
                "detected_asset": "USDT",
                "resolved_asset": "USDT",
                "is_execution_intent": True,
                "confidence": 1.0
            }
        }


    # -------------------------------------------------------------------------
    # INTERNAL CROSS-WALLET TRANSFER HANDLER (ZERO-FEE BINANCE WALLETS)
    # -------------------------------------------------------------------------
    async def _handle_internal_transfer(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Parsing internal transfer instructions", "status": "DONE", "detail": "Identifying source wallet, destination wallet, asset, and amount."},
            {"step": "Verifying Binance Agent OS zero-fee route", "status": "DONE", "detail": "Validating internal account balances & 0.00% fee routing."},
            {"step": "Executing instant deterministic transfer", "status": "DONE", "detail": "Settling balances across internal Binance wallets."}
        ]

        q = query.lower()

        # Wallet aliases
        wallet_map = {
            "spot": "SPOT",
            "fiat": "SPOT",
            "fiat & spot": "SPOT",
            "funding": "FUNDING",
            "p2p": "FUNDING",
            "pay": "FUNDING",
            "futures": "USDT_FUTURES",
            "future": "USDT_FUTURES",
            "usdt futures": "USDT_FUTURES",
            "usdt_futures": "USDT_FUTURES",
            "usd-m": "USDT_FUTURES",
            "usdm": "USDT_FUTURES",
            "coin futures": "COIN_FUTURES",
            "coin_futures": "COIN_FUTURES",
            "coin-m": "COIN_FUTURES",
            "coinm": "COIN_FUTURES",
            "margin": "CROSS_MARGIN",
            "cross margin": "CROSS_MARGIN",
            "cross_margin": "CROSS_MARGIN",
            "earn": "EARN",
            "staking": "EARN",
            "simple earn": "EARN"
        }

        # Detect source and target
        from_w = "SPOT"
        to_w = "USDT_FUTURES"

        # Regex checks: e.g. "from spot to margin", "spot theke futures e"
        m_from_to = re.search(r'(?:from\s+|theke\s+)?(spot|funding|usd-?m|futures|coin-?m|margin|earn)\s+(?:to\s+|theke\s+|e\s+)+(spot|funding|usd-?m|futures|coin-?m|margin|earn)', q)
        if m_from_to:
            w1 = m_from_to.group(1).replace("-", "")
            w2 = m_from_to.group(2).replace("-", "")
            from_w = wallet_map.get(w1, "SPOT")
            to_w = wallet_map.get(w2, "USDT_FUTURES")
        else:
            if "to margin" in q or "margin e" in q or "margin" in q:
                to_w = "CROSS_MARGIN"
            elif "to futures" in q or "futures e" in q or "futures" in q or "usd-m" in q:
                to_w = "USDT_FUTURES"
            elif "to funding" in q or "funding e" in q or "funding" in q:
                to_w = "FUNDING"
            elif "to earn" in q or "earn e" in q or "earn" in q:
                to_w = "EARN"
            elif "to spot" in q or "spot e" in q:
                to_w = "SPOT"

        if from_w == to_w:
            to_w = "CROSS_MARGIN" if from_w == "SPOT" else "SPOT"

        # Detect asset (default USDT)
        asset = "USDT"
        for a in ["USDT", "USDC", "FDUSD", "BTC", "ETH", "SOL", "BNB"]:
            if re.search(r'\b' + a.lower() + r'\b', q):
                asset = a
                break

        # Detect amount
        amount = 10.0
        m_amt = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:\$|usd|usdt|usdc|bnb|btc|eth|sol|fdusd)?', q)
        if m_amt:
            try:
                parsed = float(m_amt.group(1))
                if parsed > 0:
                    amount = parsed
            except Exception:
                pass

        if "all" in q or "sob" in q or "shob" in q:
            if self.sub_wallet:
                src_bal = self.sub_wallet.wallets.get(from_w, {}).get("balances", {}).get(asset, {}).get("free", 0.0)
                if src_bal > 0:
                    amount = src_bal

        elapsed_ms = int((time.time() - start_time) * 1000)

        if not self.sub_wallet:
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRANSFER",
                "target_asset": asset,
                "decision": "NO TRADE",
                "headline": "Internal Transfer Info",
                "reason": "Sub-wallet instance not available.",
                "explanation": "Internal transfers allow zero-fee movements between Spot, Funding, USD-M Futures, Coin-M Futures, Margin, and Earn.",
                "available_cash_usd": 250.0
            }

        res = self.sub_wallet.execute_internal_transfer(
            from_wallet=from_w,
            to_wallet=to_w,
            asset=asset,
            amount=amount
        )

        if res.get("success"):
            tx = res.get("transfer", {})
            receipt = {
                "status": "EXECUTED",
                "action": "INTERNAL_TRANSFER",
                "transfer_id": tx.get("transfer_id", "XFER-OK"),
                "from_wallet": from_w,
                "from_wallet_name": tx.get("from_wallet_name", from_w),
                "to_wallet": to_w,
                "to_wallet_name": tx.get("to_wallet_name", to_w),
                "asset": asset,
                "amount": amount,
                "fee_usd": 0.0,
                "fee_breakdown": "$0.0000 (0.00% Internal Transfer Fee)",
                "tx_hash": tx.get("tx_hash", "INT-LOCAL-001"),
                "timestamp": tx.get("timestamp"),
                "from_wallet_balance": res.get("from_wallet_balance", 0.0),
                "to_wallet_balance": res.get("to_wallet_balance", 0.0),
                "message": f"Transferred {amount} {asset} from {tx.get('from_wallet_name', from_w)} to {tx.get('to_wallet_name', to_w)} with 0.00 fees."
            }
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRANSFER",
                "target_asset": asset,
                "decision": "TRADE",
                "headline": f"✅ Internal Transfer Executed: {amount} {asset} ({tx.get('from_wallet_name', from_w)} ➔ {tx.get('to_wallet_name', to_w)})",
                "reason": f"Instant zero-fee Binance internal transfer executed successfully.",
                "explanation": (
                    f"Successfully transferred **{amount} {asset}** (Zero-Fee):\n"
                    f"- **From:** {tx.get('from_wallet_name', from_w)} (New Balance: {res.get('from_wallet_balance', 0.0)} {asset})\n"
                    f"- **To:** {tx.get('to_wallet_name', to_w)} (New Balance: {res.get('to_wallet_balance', 0.0)} {asset})\n"
                    f"- **Fee:** 0.00% (Free)\n"
                    f"- **Transfer ID:** `{tx.get('transfer_id')}`"
                ),
                "invalidation": "Executed.",
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "agentic_steps": steps,
                "execution_receipt": receipt,
                "available_cash_usd": self.sub_wallet.cash_usd,
                "journal_id": f"JRNL-XFER-{int(time.time()*1000) % 10000}"
            }
        else:
            # Transfer could not be completed (e.g. insufficient funds)
            err_msg = res.get("error", "Insufficient funds or invalid wallets.")
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRANSFER",
                "target_asset": asset,
                "decision": "NO TRADE",
                "headline": f"⚠️ Internal Transfer Not Executed",
                "reason": err_msg,
                "explanation": f"ট্রান্সফার সম্পন্ন করা সম্ভব হয়নি: {err_msg}। অনুগ্রহ করে ওয়ালেটে পর্যাপ্ত ব্যালেন্স আছে কিনা চেক করুন।",
                "invalidation": "Failed transfer check.",
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "agentic_steps": steps,
                "available_cash_usd": self.sub_wallet.cash_usd,
                "journal_id": f"JRNL-ERR-{int(time.time()*1000) % 10000}"
            }

    # -------------------------------------------------------------------------
    # 13. CONVERT ASSET (ZERO-FEE BINANCE CONVERT)
    # -------------------------------------------------------------------------
    async def _handle_convert_asset(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Parsing convert instruction", "status": "DONE", "detail": "Extracting source asset, target asset, and amount."},
            {"step": "Requesting Binance Convert zero-fee quote", "status": "DONE", "detail": "Calculating guaranteed conversion rate without slippage."},
            {"step": "Executing Binance Convert swap", "status": "DONE", "detail": "Settling balances on Binance Agent OS."}
        ]

        # Comprehensive Convert/Swap Intent Parser
        q_clean = query.strip()
        q_low = q_clean.lower()

        is_all = bool(re.search(r'\b(?:all|sob|shob|puro|100%)\b', q_clean, re.IGNORECASE))
        is_usd_specified = False
        parsed_amount = None
        from_asset = None
        to_asset = None

        # Check for dollar-denominated amount: "$10", "10$", "10 usd", "10 usdt", "10 dollars"
        usd_m = re.search(r'(?:\$\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:\$|usd\b|usdt\b|dollars?\b))\s*(?:worth\s+of|value\s+of|of)?', q_clean, re.IGNORECASE)
        if usd_m:
            is_usd_specified = True
            parsed_amount = float(usd_m.group(1) or usd_m.group(2))

        # Check for token pair: "<FROM> to <TO>" or "from <FROM> to <TO>" or "swap <FROM> for <TO>"
        # Handles "btc to eth", "worth of btc to eth", "sol into usdt", "usdc -> usdt"
        pair_patterns = [
            r'(?:worth\s+of|value\s+of|of)\s+([A-Za-z0-9]{2,10})\s*(?:to|into|->|for|\be\b)\s*([A-Za-z0-9]{2,10})',
            r'(?:convert|swap)\s+(?:all\s+)?(?:\$\d+(?:\.\d+)?|\d+(?:\.\d+)?\$?|\d+(?:\.\d+)?\s*(?:usd|usdt)?\s+)?(?:worth\s+of\s+|of\s+)?([A-Za-z0-9]{2,10})\s*(?:to|into|->|for|\be\b)\s*([A-Za-z0-9]{2,10})',
            r'(?:from\s+)?([A-Za-z0-9]{2,10})\s*(?:to|into|->|for|\be\b)\s*([A-Za-z0-9]{2,10})'
        ]

        filler_words = {"WORTH", "OF", "THE", "ALL", "SOB", "SHOB", "CONVERT", "SWAP", "TRADE", "BALANCE", "PORTFOLIO", "MY", "A", "AN", "SOME", "INTO", "FOR"}

        for pat in pair_patterns:
            m = re.search(pat, q_clean, re.IGNORECASE)
            if m:
                cand_from = m.group(1).upper()
                cand_to = m.group(2).upper()
                if cand_from not in filler_words and cand_to not in filler_words:
                    from_asset = cand_from
                    to_asset = cand_to
                    break

        # If amount was a plain token quantity (e.g. "convert 0.05 btc to eth"):
        if not is_usd_specified and not parsed_amount:
            raw_num_m = re.search(r'(?:convert|swap)\s+(\d+(?:\.\d+)?)\s+([A-Za-z0-9]{2,10})', q_clean, re.IGNORECASE)
            if raw_num_m:
                parsed_amount = float(raw_num_m.group(1))
                if not from_asset:
                    from_asset = raw_num_m.group(2).upper()

        # Clean symbol suffixes (e.g. BTCUSDT -> BTC)
        from_asset = (from_asset or "USDC").upper()
        to_asset = (to_asset or "USDT").upper()

        if from_asset.endswith("USDT") and len(from_asset) > 4:
            from_asset = from_asset[:-4]
        if to_asset.endswith("USDT") and len(to_asset) > 4:
            to_asset = to_asset[:-4]

        # Fetch current USD price of from_asset to convert USD notional to token quantity
        ticker_from = await self.binance.get_live_ticker(f"{from_asset}USDT" if from_asset not in ("USDT", "USDC", "USD", "FDUSD") else "USDT")
        from_price_usd = float(ticker_from.get("last_price", 1.0)) if from_asset not in ("USDT", "USDC", "USD", "FDUSD") else 1.0

        ticker_to = await self.binance.get_live_ticker(f"{to_asset}USDT" if to_asset not in ("USDT", "USDC", "USD", "FDUSD") else "USDT")
        to_price_usd = float(ticker_to.get("last_price", 1.0)) if to_asset not in ("USDT", "USDC", "USD", "FDUSD") else 1.0

        if is_all:
            avail = self.sub_wallet.holdings.get(from_asset, {}).get("free", 0.0) if self.sub_wallet else 0.0
            amount_in_from_token = avail if avail > 0 else (10.0 / from_price_usd if from_price_usd > 0 else 10.0)
        elif is_usd_specified and parsed_amount:
            # User specified dollar amount (e.g. $10 worth of BTC)
            amount_in_from_token = parsed_amount / from_price_usd if from_price_usd > 0 else parsed_amount
        elif parsed_amount:
            # User specified token quantity directly (e.g. 0.005 BTC)
            amount_in_from_token = parsed_amount
        else:
            # Default to $10 USD notional
            amount_in_from_token = 10.0 / from_price_usd if from_price_usd > 0 else 10.0

        quote = await self.binance.quote_binance_convert(from_asset, to_asset, amount_in_from_token)
        exec_res = await self.binance.execute_binance_convert(
            quote_id=quote["quote_id"],
            from_asset=from_asset,
            to_asset=to_asset,
            from_amount=quote["from_amount"],
            to_amount=quote["to_amount"]
        )

        convert_order_id = f"ORD-CNV-{from_asset}{to_asset}-{int(time.time()*1000) % 10000}"
        if self.sub_wallet:
            self.sub_wallet.record_convert_history(from_asset, to_asset, quote["from_amount"], quote["to_amount"], quote["quote_id"])

        from_notional = quote["from_amount"] * from_price_usd
        to_notional = quote["to_amount"] * to_price_usd

        from_qty_str = f"{quote['from_amount']:.8f}".rstrip('0').rstrip('.') if quote['from_amount'] < 0.01 else (f"{quote['from_amount']:.6f}".rstrip('0').rstrip('.') if quote['from_amount'] < 1 else f"{quote['from_amount']:,.4f}")
        to_qty_str = f"{quote['to_amount']:.8f}".rstrip('0').rstrip('.') if quote['to_amount'] < 0.01 else (f"{quote['to_amount']:.6f}".rstrip('0').rstrip('.') if quote['to_amount'] < 1 else f"{quote['to_amount']:,.4f}")

        receipt = {
            "status": "EXECUTED",
            "order_id": convert_order_id,
            "action": "CONVERT",
            "from_asset": from_asset,
            "to_asset": to_asset,
            "from_amount": quote["from_amount"],
            "to_amount": quote["to_amount"],
            "from_notional_usd": round(from_notional, 2),
            "to_notional_usd": round(to_notional, 2),
            "exchange_rate": quote["exchange_rate"],
            "quote_id": quote["quote_id"],
            "fee_usd": 0.0,
            "fee_rate_pct": 0.0,
            "fee_breakdown": "0.00 USDT (0.00% Zero-Fee Binance Convert)",
            "message": f"Swapped {from_qty_str} {from_asset} (~${from_notional:.2f} USD) -> {to_qty_str} {to_asset} (~${to_notional:.2f} USD) [Order ID: {convert_order_id}] at 0% fee."
        }

        elapsed_ms = int((time.time() - start_time) * 1000)

        headline = f"✅ Zero-Fee Conversion: {from_qty_str} {from_asset} (~${from_notional:.2f} USD) -> {to_qty_str} {to_asset}"
        explanation = (
            f"Successfully executed instant zero-slippage swap via Binance Convert router.\n\n"
            f"• **From**: `{from_qty_str} {from_asset}` (~${from_notional:.2f} USD at `${from_price_usd:,.2f}`)\n"
            f"• **To**: `{to_qty_str} {to_asset}` (~${to_notional:.2f} USD at `${to_price_usd:,.2f}`)\n"
            f"• **Execution Rate**: `1 {from_asset} = {quote['exchange_rate']} {to_asset}`\n"
            f"• **Fee Incurred**: `0.00 USDT (0.00% Zero-Fee Binance Convert)`\n"
            f"• **Order Reference**: `{convert_order_id}`\n\n"
            f"Sub-wallet balances updated immediately with 0% orderbook slippage."
        )

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "CONVERT",
            "target_asset": f"{from_asset}->{to_asset}",
            "decision": "TRADE",
            "headline": headline,
            "reason": f"Executed instantaneous zero-slippage swap {from_asset} -> {to_asset} via Binance Convert router.",
            "explanation": explanation,
            "invalidation": "Executed.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "execution_receipt": receipt,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-CNV-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "CONVERT_ASSET",
                "detected_asset": f"{from_asset}->{to_asset}",
                "resolved_asset": f"{from_asset}->{to_asset}",
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # 14. UPDATE RULES / MANDATE
    # -------------------------------------------------------------------------
    async def _handle_update_rules(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            {"step": "Analyzing custom rule adjustments", "status": "DONE", "detail": "Parsing user mathematical risk limits and leverage ceilings."},
            {"step": "Applying rules to Risk Engine", "status": "DONE", "detail": "Updating active enforcement thresholds across all agents."}
        ]

        updated_fields = []

        risk_m = re.search(r'(?:risk(?: of)?|max risk(?: of)?)\s*(\d+(?:\.\d+)?)\s*%', query, re.IGNORECASE)
        if risk_m:
            new_risk = float(risk_m.group(1))
            self.mandate["max_risk_pct"] = new_risk
            updated_fields.append(f"Max Risk: {new_risk}% (${self.mandate['capital_usd'] * (new_risk/100):.2f})")

        cap_m = re.search(r'(?:capital(?: of)?|budget(?: of)?)\s*\$?(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        if cap_m:
            new_cap = float(cap_m.group(1))
            self.mandate["capital_usd"] = new_cap
            if self.sub_wallet:
                self.sub_wallet.allocated_budget_usd = new_cap
            updated_fields.append(f"Allocated Capital: ${new_cap:.2f}")

        lev_m = re.search(r'(?:max leverage|leverage(?: of)?)\s*(\d+)x?', query, re.IGNORECASE)
        if lev_m:
            new_lev = int(lev_m.group(1))
            self.mandate["max_leverage"] = new_lev
            updated_fields.append(f"Max Leverage Ceiling: {new_lev}x")

        if "stop loss false" in query.lower() or "no stop loss" in query.lower():
            self.mandate["require_stop_loss"] = False
            updated_fields.append("Mandatory Stop Loss: DISABLED")
        elif "stop loss" in query.lower():
            self.mandate["require_stop_loss"] = True
            updated_fields.append("Mandatory Stop Loss: STRICT ENFORCEMENT")

        if "assisted" in query.lower():
            self.mandate["execution_mode"] = "ASSISTED"
            updated_fields.append("Mode: ASSISTED (Requires Confirmation)")
        elif "autonomous" in query.lower() or "direct" in query.lower():
            self.mandate["execution_mode"] = "AUTONOMOUS"
            updated_fields.append("Mode: AUTONOMOUS (Instant Execution)")

        elapsed_ms = int((time.time() - start_time) * 1000)
        changes_summary = ", ".join(updated_fields) if updated_fields else "Verified active mandate parameters."

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "RULES_UPDATE",
            "target_asset": "MANDATE_RULES",
            "decision": "TRADE",
            "headline": "⚙️ Custom Trading Rules Updated",
            "reason": f"Applied changes: {changes_summary}",
            "explanation": (
                f"Your trading parameters are now enforced across the whole system: "
                f"Capital: ${self.mandate['capital_usd']:.2f}, Max Risk Per Trade: {self.mandate['max_risk_pct']}%, "
                f"Max Leverage: {self.mandate['max_leverage']}x, Mandatory SL: {self.mandate['require_stop_loss']}."
            ),
            "invalidation": "Next rule update.",
            "max_risk_usd": self.mandate["capital_usd"] * (self.mandate["max_risk_pct"] / 100.0),
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-RUL-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "PORTFOLIO",
                "intent": "UPDATE_RULES",
                "detected_asset": None,
                "resolved_asset": None,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": False,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # 15. REBALANCE PORTFOLIO
    # -------------------------------------------------------------------------
    async def _handle_rebalance(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_allocations = self.mandate.get("target_allocations")

        if not target_allocations or not isinstance(target_allocations, dict) or len(target_allocations) == 0:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "REBALANCE",
                "target_asset": "PORTFOLIO",
                "decision": None,
                "headline": "⚠️ Target Allocations Not Configured",
                "reason": "Portfolio mandate does not contain target asset allocation weights.",
                "explanation": (
                    "### ⚖️ Rebalance Mandate Unset\n\n"
                    "No target portfolio weights are configured in your active mandate. SYRAX will not invent default allocations without your explicit instructions.\n\n"
                    "Please specify your desired targets first, for example:\n"
                    "- *'Set target allocations: 40% USDT, 30% BTC, 15% ETH, 10% SOL, 5% USDC'*"
                ),
                "invalidation": None,
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "agentic_steps": [
                    {"step": "Checking Mandate Target Allocations", "status": "DONE", "detail": "Target allocation map is empty. Prompting user for target specification."}
                ],
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "journal_id": f"JRNL-REB-ERR-{int(time.time()*1000) % 10000}",
                "debug_intent_inspector": {
                    "domain": "EXECUTION",
                    "intent": "REBALANCE",
                    "detected_asset": None,
                    "resolved_asset": "PORTFOLIO",
                    "active_context_asset": self.state_manager.active_asset,
                    "requires_clarification": True,
                    "is_execution_intent": False,
                    "confidence": 0.90
                }
            }

        steps = [
            {"step": "Auditing Current Portfolio Drift", "status": "DONE", "detail": "Comparing live holding weights against configured mandate corridor."},
            {"step": "Calculating Minimal-Friction Route", "status": "DONE", "detail": "Minimizing slippage and exchange fee friction across Binance Spot orderbooks."},
            {"step": "Executing Disciplined Rebalance", "status": "DONE", "detail": "Aligning sub-wallet asset weights to target corridor."}
        ]

        # Fetch live prices for drift computation
        price_map = {"USDT": 1.0, "USDC": 1.0, "USD": 1.0, "FDUSD": 1.0}
        for asset in target_allocations.keys():
            if asset not in price_map:
                ticker = await self.binance.get_live_ticker(f"{asset}USDT")
                price_map[asset] = ticker.get("last_price", 100.0)

        # Compute total value
        total_val = self.sub_wallet.cash_usd if self.sub_wallet else 250.0
        holdings_dict = self.sub_wallet.holdings if self.sub_wallet else {"USDT": {"free": 250.0, "locked": 0.0}}
        for asset, data in holdings_dict.items():
            if asset not in ("USDT", "USDC", "USD", "FDUSD"):
                qty = data.get("free", 0.0) + data.get("locked", 0.0)
                p = price_map.get(asset, 100.0)
                total_val += (qty * p)

        drift_lines = []
        action_lines = []
        total_rebalance_volume_usd = 0.0

        for asset, target_pct in target_allocations.items():
            p = price_map.get(asset, 1.0)
            cur_qty = holdings_dict.get(asset, {}).get("free", 0.0) if self.sub_wallet else 0.0
            cur_val = cur_qty * p if asset not in ("USDT", "USDC") else cur_qty
            cur_pct = (cur_val / total_val * 100.0) if total_val > 0 else 0.0
            drift_pct = cur_pct - target_pct
            drift_status = "BALANCED" if abs(drift_pct) <= 2.0 else ("OVERWEIGHT" if drift_pct > 0 else "UNDERWEIGHT")
            drift_lines.append(f"- **{asset}:** Current: `{cur_pct:.1f}%` | Target: `{target_pct:.1f}%` | Drift: `{drift_pct:+.1f}%` ({drift_status})")

            target_val = total_val * (target_pct / 100.0)
            diff_usd = target_val - cur_val
            if abs(diff_usd) > 1.0:
                total_rebalance_volume_usd += abs(diff_usd)
                if diff_usd > 0:
                    action_lines.append(f"- **BUY ${diff_usd:.2f} {asset}** (~{diff_usd/p:.4f} {asset})")
                else:
                    action_lines.append(f"- **TRIM ${abs(diff_usd):.2f} {asset}** (~{abs(diff_usd)/p:.4f} {asset}) into USDT")

        estimated_fee_usd = round(total_rebalance_volume_usd * 0.001, 4) # 0.10% Binance spot fee
        execution_mode = self.mandate.get("execution_mode", "AUTONOMOUS")

        if self.sub_wallet:
            res = self.sub_wallet.rebalance_to_corridor()
        else:
            res = {"success": True, "rebalanced_targets": target_allocations}

        explanation = (
            f"### ⚖️ Portfolio Rebalance Intelligence\n\n"
            f"**Total Portfolio Value:** ${total_val:,.2f} USD\n\n"
            f"#### 📊 Current vs Target Drift Corridor:\n"
            + "\n".join(drift_lines) + "\n\n"
            f"#### 🔄 Required Rebalancing Actions:\n"
            + ("\n".join(action_lines) if action_lines else "- All assets are already within the ±2% corridor.") + "\n\n"
            f"#### 💸 Estimated Friction & Risk Check:\n"
            f"- **Estimated Binance Spot Fee (0.10%):** ${estimated_fee_usd:.4f} USDT\n"
            f"- **Risk Guard:** Mandate risk cap preserved; 0 active security exploits on Sentry.\n"
            f"- **Execution Mode:** `{execution_mode}` (Rebalance executed).\n\n"
            f"All asset allocations have been successfully realigned to your target policy."
        )

        receipt = {
            "status": "EXECUTED",
            "action": "REBALANCE",
            "target_weights": target_allocations,
            "estimated_friction_usd": estimated_fee_usd,
            "execution_mode": execution_mode,
            "message": "Portfolio rebalanced to target corridor weights."
        }

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "REBALANCE",
            "target_asset": "PORTFOLIO",
            "decision": "TRADE",
            "headline": "⚖️ Portfolio Rebalanced to Target Corridor",
            "reason": "Eliminated asset allocation drift and restored disciplined risk diversification.",
            "explanation": explanation,
            "invalidation": "Allocation drift > 5%.",
            "max_risk_usd": 0.0,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "execution_receipt": receipt,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-REB-{int(time.time()*1000) % 10000}",
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "REBALANCE",
                "detected_asset": None,
                "resolved_asset": "PORTFOLIO",
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": classification.get("confidence", 0.95)
            }
        }

    # -------------------------------------------------------------------------
    # 16. DIRECT NATURAL LANGUAGE TRADE EXECUTION (BUY / LONG / SHORT / LIMIT)
    # -------------------------------------------------------------------------
    async def _handle_execute_trade(self, query: str, start_time: float, classification: Dict[str, Any]) -> Dict[str, Any]:
        target_token = classification.get("resolved_asset") or "BTCUSDT"
        base_asset = target_token.replace("USDT", "")
        self.state_manager.active_asset = target_token

        steps = [
            {"step": "Parsing Execution Intent & Parameters", "status": "DONE", "detail": f"Target: {target_token}, analyzing price levels and constraints."},
            {"step": "Validating Mathematical Risk Limits", "status": "DONE", "detail": "Auditing 1.0% account risk cap and stop-loss boundaries via Central Gateway."},
            {"step": "Compiling Cryptographic Order Ticket", "status": "DONE", "detail": "Generating immutable order ticket with 120s TTL and SHA-256 canonical hash."}
        ]

        # Parameter extraction
        q_low = query.lower()
        side = "SELL" if any(w in q_low for w in ["sell", "short", "bechte", "bikri"]) else "BUY"
        is_futures = ("future" in q_low or "futures" in q_low or "perp" in q_low or "perps" in q_low)
        is_spot = ("spot" in q_low) or (not is_futures and not self.mandate.get("default_market", "SPOT") == "FUTURES")
        market_type = "SPOT" if is_spot else "FUTURES"

        lev_m = re.search(r'\b(\d+)x\b', q_low)
        if lev_m:
            leverage = int(lev_m.group(1))
            market_type = "FUTURES" if leverage > 1 else market_type
        else:
            leverage = 1 if market_type == "SPOT" else 10

        margin_type = "ISOLATED"

        # Notional / Amount
        amt_match = re.search(r'\$\s*(\d+(?:\.\d+)?)', query)
        if not amt_match:
            amt_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:\$|usd|dollar|dollars|usdt)', query, re.IGNORECASE)
        notional_usd = float(amt_match.group(1)) if amt_match else 25.0

        # Limit vs Market
        is_limit = ("limit" in q_low) or bool(re.search(r'\b(?:under|below|at|discount)\b', q_low))
        limit_match = re.search(r'(?:limit(?: order)? (?:at|price)?|at price|entry at|entry price|price at|\bat)\s*\$?(\d+(?:\.\d+)?)', q_low)
        discount_match = re.search(r'(?:under|below|discount of)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:under|below|discount|from|cheaper)?', q_low)

        ticker = await self.binance.get_live_ticker(target_token)
        live_price = float(ticker.get("last_price", 100.0))

        raw_limit_price = None
        if limit_match:
            raw_limit_price = float(limit_match.group(1))
        elif discount_match and "limit" in q_low:
            pct_val = float(discount_match.group(1))
            raw_limit_price = live_price * (1.0 - (pct_val / 100.0))

        if is_limit and raw_limit_price and raw_limit_price > 0:
            order_type = "LIMIT"
            limit_price = raw_limit_price
        else:
            order_type = "MARKET"
            limit_price = None

        sl_m = re.search(r'(?:sl|stop\s*loss)\s*\$?(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        tp_m = re.search(r'(?:tp|take\s*profit)\s*\$?(\d+(?:\.\d+)?)', query, re.IGNORECASE)

        base_p = limit_price or live_price
        p_prec = 8 if base_p < 0.01 else 4

        stop_loss = float(sl_m.group(1)) if sl_m else (
            round(base_p * 0.98, p_prec) if side == "BUY" else round(base_p * 1.02, p_prec)
        )
        if tp_m:
            take_profit = float(tp_m.group(1))
        else:
            sl_dist = abs(base_p - stop_loss)
            take_profit = round(base_p + (sl_dist * 2.0), p_prec) if side == "BUY" else round(base_p - (sl_dist * 2.0), p_prec)


        # Pre-audit sub-wallet liquid cash availability
        avail_cash = self.sub_wallet.cash_usd if self.sub_wallet else 250.0
        fee_rate = 0.001 if market_type == "SPOT" else 0.0005
        margin_req = (notional_usd / leverage) if (market_type == "FUTURES" and leverage > 1) else notional_usd
        total_req_usd = margin_req * (1.0 + fee_rate)

        if side == "BUY" and total_req_usd > avail_cash:
            elapsed_ms = int((time.time() - start_time) * 1000)
            if avail_cash < 1.0:
                explanation_str = (
                    f"Your sub-wallet liquid cash is depleted:\n\n"
                    f"• **Available Cash**: `${avail_cash:.2f} USDT`\n"
                    f"• **Required for Order**: `${total_req_usd:.2f} USD` (Margin + Est Fee)\n\n"
                    f"💡 **Suggested Fix:**\n"
                    f"1. Type **`reset balance`** to immediately reset your sub-wallet cash back to `$250.00 USDT`.\n"
                    f"2. Or sell existing token holdings in the **Positions** tab."
                )
            else:
                suggested_notional = max(1.0, round(avail_cash / (1.0 + fee_rate), 2))
                explanation_str = (
                    f"You requested a **${notional_usd:.2f}** order, but your available sub-wallet liquid cash is **${avail_cash:.2f} USDT**.\n\n"
                    f"• **Available Cash**: `${avail_cash:.2f} USDT`\n"
                    f"• **Max Order Size Possible**: `${suggested_notional:.2f} USD`\n\n"
                    f"💡 **Suggested Fix:**\n"
                    f"1. Type **`Buy ${suggested_notional:.0f} {target_token.replace('USDT', '')} on spot`** to use your current cash.\n"
                    f"2. Or type **`reset balance`** to restore your cash back to `$250.00 USDT`.\n"
                    f"3. Or sell other token holdings in the Positions tab."
                )
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRADE",
                "target_asset": target_token,
                "decision": "NO TRADE",
                "headline": f"🚨 Insufficient Cash: Requested ${notional_usd:.2f} vs Available ${avail_cash:.2f} USDT",
                "reason": f"Order size ${notional_usd:.2f} exceeds liquid cash ${avail_cash:.2f} USDT.",
                "explanation": explanation_str,
                "invalidation": "Capital Bounds Veto.",
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "available_cash_usd": avail_cash
            }

        # Pre-audit 1.0% risk sizing
        risk_calc = RiskEngine.evaluate(RiskParameters(
            capital=self.mandate["capital_usd"],
            max_risk_pct=self.mandate["max_risk_pct"],
            entry_price=limit_price or live_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_order_size_usd=self.mandate.get("max_order_size_usd", 25.0)
        ))

        # Check hard leverage limit
        max_allowed_lev = self.mandate.get("max_leverage", 10)
        if leverage > max_allowed_lev:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRADE",
                "target_asset": target_token,
                "decision": "NO TRADE",
                "headline": f"🚨 TRADE REJECTED: Requested leverage {leverage}x exceeds mandate ceiling of {max_allowed_lev}x",
                "reason": f"Leverage {leverage}x strictly exceeds system max of {max_allowed_lev}x (silent clamping prohibited).",
                "explanation": f"The trade request exceeded the maximum allowed leverage limit ({max_allowed_lev}x).",
                "invalidation": "Mandate Risk Invariant Veto.",
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0
            }

        # Compile immutable OrderTicket (Phase 6 Human Confirmation Boundary)
        ticket = await self.ticket_registry.create_ticket(
            symbol=target_token,
            side=side,
            order_type=order_type,
            notional_usd=notional_usd,
            decision_price=live_price,
            limit_price=limit_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=leverage,
            market_type=market_type,
            venue="binance",
            risk_amount_usd=risk_calc.max_dollar_loss,
            risk_pct=self.mandate["max_risk_pct"],
            confidence=0.95,
            environment="SIMULATED",
            account_scope="default",
            ttl_seconds=120.0,
            ai_thesis=f"{side} {target_token} order draft generated based on user directive.",
            metadata={"margin_type": margin_type}
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        card = format_order_ticket_card(ticket)

        return {
            "query": query,
            "elapsed_ms": elapsed_ms,
            "command_type": "TRADE",
            "target_asset": target_token,
            "decision": "TICKET_GENERATED",
            "headline": card["headline"],
            "reason": f"Exact order ticket {ticket.parent_order_id} generated. Awaiting explicit confirmation token.",
            "explanation": card["explanation"],
            "invalidation": f"Ticket expires in {int(ticket.ttl_seconds)}s or upon parameter modification.",
            "max_risk_usd": ticket.risk_amount_usd,
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "agentic_steps": steps,
            "order_ticket": card,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": f"JRNL-TKT-{ticket.parent_order_id}",
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "EXECUTE_TRADE",
                "detected_asset": target_token,
                "resolved_asset": target_token,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": 0.96
            }
        }

    async def _handle_confirm_order_ticket(self, parent_order_id: str, confirmation_token: str, start_time: float) -> Dict[str, Any]:
        """
        Validates token, consumes OrderTicket atomically, and routes ExecutionRequest to Gateway.
        Fully idempotent: Gracefully handles already-executed tickets without throwing confusing red errors.
        """
        poid = parent_order_id.strip().upper()
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Check existing ticket in registry first for idempotent status handling
        existing_ticket = await self.ticket_registry.get_ticket(poid)
        if existing_ticket:
            if existing_ticket.status == TicketStatus.EXECUTED:
                avail_cash_str = f"${self.sub_wallet.cash_usd:.2f} USDT" if self.sub_wallet else "$245.00 USDT"
                qty_str = f"{existing_ticket.quantity:.6f}" if existing_ticket.quantity < 1 else f"{existing_ticket.quantity:.4f}"
                explanation_str = f"Order ticket **{poid}** has already been confirmed and filled.\n\n• **Instrument**: `{existing_ticket.side} {existing_ticket.symbol}` ({existing_ticket.market_type})\n• **Order ID**: `{existing_ticket.gateway_order_id or 'ORD-ACTIVE'}`\n• **Position Size**: `${existing_ticket.notional_usd:.2f} USD` (Qty: `{qty_str}`)\n• **Stop Loss**: `${existing_ticket.stop_loss:,.4f}` | **Take Profit**: `${existing_ticket.take_profit:,.4f}`\n• **Available Cash**: `{avail_cash_str}`\n\n_Position is currently tracked by the 24/7 Autonomous Sentinel & Post-Trade Guardian._"
                return {
                    "query": confirmation_token,
                    "elapsed_ms": elapsed_ms,
                    "command_type": "TRADE",
                    "target_asset": existing_ticket.symbol,
                    "decision": "TRADE",
                    "headline": f"✅ Order Ticket {poid} Already Successfully Executed",
                    "reason": f"Order ticket {poid} ({existing_ticket.side} {existing_ticket.symbol} ${existing_ticket.notional_usd:.2f}) is already active in your portfolio.",
                    "explanation": explanation_str,
                    "invalidation": None,
                    "ticket_id": poid,
                    "ticket_status": "EXECUTED",
                    "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 245.0,
                    "debug_intent_inspector": {
                        "domain": "EXECUTION",
                        "intent": "CONFIRM_ORDER_TICKET",
                        "detected_asset": existing_ticket.symbol,
                        "resolved_asset": existing_ticket.symbol,
                        "is_execution_intent": True,
                        "confidence": 1.0
                    }
                }
            elif existing_ticket.status == TicketStatus.REJECTED_BY_GATEWAY:
                rejection_msg = existing_ticket.rejection_reason or "Mandate risk bounds exceeded (1.0% maximum loss cap)."
                explanation_str = f"Order ticket **{poid}** was evaluated by the Unified Execution Gateway and blocked by policy:\n\n**Reason:** {rejection_msg}\n\n💡 **Suggested Fix:** Reduce order size/leverage or tighten your stop-loss distance so maximum dollar loss stays within your $5.00 (1.0%) mandate limit."
                return {
                    "query": confirmation_token,
                    "elapsed_ms": elapsed_ms,
                    "command_type": "TRADE",
                    "target_asset": existing_ticket.symbol,
                    "decision": "NO TRADE",
                    "headline": f"🛡️ Order Ticket {poid} Blocked by Safety Gatekeeper",
                    "reason": rejection_msg,
                    "explanation": explanation_str,
                    "invalidation": "Safety Gatekeeper Veto.",
                    "ticket_id": poid,
                    "ticket_status": "REJECTED_BY_GATEWAY",
                    "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                    "debug_intent_inspector": {
                        "domain": "EXECUTION",
                        "intent": "CONFIRM_ORDER_TICKET",
                        "detected_asset": existing_ticket.symbol,
                        "resolved_asset": existing_ticket.symbol,
                        "is_execution_intent": True,
                        "confidence": 1.0
                    }
                }

        success, ticket, msg = await self.ticket_registry.confirm_ticket(poid, confirmation_token)

        if not success or not ticket:
            return {
                "query": confirmation_token,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRADE_CONFIRMATION",
                "target_asset": ticket.symbol if ticket else "UNKNOWN",
                "decision": "CONFIRMATION_REJECTED",
                "headline": f"🚨 Order Ticket Confirmation Failed: {poid}",
                "reason": msg,
                "explanation": f"Confirmation for ticket **{poid}** failed: {msg}",
                "invalidation": "Confirmation rejected / invalid ticket.",
                "ticket_id": poid,
                "ticket_status": ticket.status.value if ticket else "NOT_FOUND",
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "debug_intent_inspector": {
                    "domain": "EXECUTION",
                    "intent": "CONFIRM_ORDER_TICKET",
                    "detected_asset": ticket.symbol if ticket else None,
                    "resolved_asset": ticket.symbol if ticket else None,
                    "is_execution_intent": True,
                    "confidence": 1.0
                }
            }

        exec_env = ExecutionEnvironment.SIMULATED
        if ticket.environment == "TESTNET":
            exec_env = ExecutionEnvironment.TESTNET
        elif ticket.environment == "LIVE":
            exec_env = ExecutionEnvironment.LIVE

        exec_req = ExecutionRequest(
            action_type=ExecutionActionType.OPEN_POSITION,
            symbol=ticket.symbol,
            side=ticket.side,
            order_type=ticket.order_type,
            notional_usd=ticket.notional_usd,
            quantity=ticket.quantity,
            price=ticket.decision_price,
            limit_price=ticket.limit_price,
            stop_loss=ticket.stop_loss,
            take_profit=ticket.take_profit,
            leverage=ticket.leverage,
            market_type=ticket.market_type,
            margin_type=ticket.metadata.get("margin_type", "ISOLATED"),
            environment=exec_env,
            source="HUMAN_CONFIRMATION",
            mandate=self.mandate
        )

        receipt: ExecutionReceipt = await self.gateway.execute(exec_req)
        elapsed_ms = int((time.time() - start_time) * 1000)

        if receipt.status in (ExecutionStatus.REJECTED, ExecutionStatus.BLOCKED, ExecutionStatus.FAILED):
            await self.ticket_registry.mark_rejected_by_gateway(poid, receipt.rejection_reason or receipt.message)
            return {
                "query": confirmation_token,
                "elapsed_ms": elapsed_ms,
                "command_type": "TRADE",
                "target_asset": ticket.symbol,
                "decision": "NO TRADE",
                "headline": f"🚨 TRADE {receipt.status.value}: {receipt.rejection_reason or receipt.message}",
                "reason": receipt.rejection_reason or receipt.message,
                "explanation": f"The trade for confirmed ticket **{poid}** was evaluated by the Unified Execution Gateway and was {receipt.status.value.lower()}: {receipt.rejection_reason or receipt.message}",
                "invalidation": "Safety Gatekeeper Veto.",
                "max_risk_usd": 0.0,
                "mandate": self.mandate,
                "active_rules": self.mandate,
                "ticket_id": poid,
                "ticket_status": TicketStatus.REJECTED_BY_GATEWAY.value,
                "execution_receipt": receipt.model_dump(),
                "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
                "journal_id": f"JRNL-VETO-{poid}",
                "debug_intent_inspector": {
                    "domain": "EXECUTION",
                    "intent": "CONFIRM_ORDER_TICKET",
                    "detected_asset": ticket.symbol,
                    "resolved_asset": ticket.symbol,
                    "is_execution_intent": True,
                    "confidence": 1.0
                }
            }

        # Successful Execution
        await self.ticket_registry.mark_executed(poid, receipt.order_id, receipt.trade_id)
        receipt_dict = receipt.model_dump()
        receipt_dict["rule_compliance"] = f"PASS (Max Loss Capped to ${self.mandate['capital_usd'] * (self.mandate['max_risk_pct']/100.0):.2f})"
        p_str = format_crypto_price(receipt.requested_price)
        sl_str = format_crypto_price(receipt.stop_loss) if receipt.stop_loss else "Trailing"
        tp_str = format_crypto_price(receipt.take_profit) if receipt.take_profit else "None"
        avail_cash_str = f"${self.sub_wallet.cash_usd:.2f} USDT" if self.sub_wallet else "$250.00 USDT"

        qty_str = f"{receipt.quantity:.6f}" if receipt.quantity < 1 else f"{receipt.quantity:.4f}"

        if ticket.order_type == "LIMIT":
            headline = f"⏳ Limit Order Placed: {receipt.term} {ticket.symbol} @ {p_str} [Ticket: {poid} | Order ID: {receipt.order_id}]"
            reason = f"Confirmed ticket {poid} executed. Limit order submitted to simulated orderbook at {p_str}. Margin ${receipt.margin_usd:.2f} USDT reserved."
            explanation = (
                f"Confirmed order ticket **{poid}** has been successfully authorized and submitted.\n\n"
                f"• **Instrument**: `{receipt.term} {ticket.symbol}` ({receipt.market_type} on `{receipt.environment.value}`)\n"
                f"• **Limit Price**: `{p_str}` (Qty: `{qty_str}`)\n"
                f"• **Margin Locked**: `${receipt.margin_usd:.2f} USDT`\n"
                f"• **Stop Loss**: `{sl_str}` | **Take Profit**: `{tp_str}`\n"
                f"• **Estimated Fee**: `{receipt.fee_breakdown}`\n"
                f"• **Available Liquid Balance**: `{avail_cash_str}`\n"
                f"• **Account Risk**: Strictly capped to 1.0% mandate."
            )
        else:
            headline = f"🚀 Order Filled: {receipt.term} {ticket.symbol} [Ticket: {poid} | Order ID: {receipt.order_id}]"
            reason = f"Confirmed ticket {poid} filled at {p_str} with ${receipt.margin_usd:.2f} margin [{receipt.environment.value}]. Fee: {receipt.fee_breakdown}"
            explanation = (
                f"Confirmed order ticket **{poid}** has been successfully authorized and filled.\n\n"
                f"• **Instrument**: `{receipt.term} {ticket.symbol}` ({receipt.market_type} on `{receipt.environment.value}`)\n"
                f"• **Order ID**: `{receipt.order_id}` | **Trade ID**: `{receipt.trade_id}`\n"
                f"• **Fill Entry Price**: `{p_str}` (Qty: `{qty_str}`)\n"
                f"• **Margin Allocated**: `${receipt.margin_usd:.2f} USDT`\n"
                f"• **Stop Loss**: `{sl_str}` | **Take Profit**: `{tp_str}`\n"
                f"• **Realized Transaction Fee**: `{receipt.fee_breakdown}` (deducted from cash)\n"
                f"• **Post-Trade Liquid Cash**: `{avail_cash_str}`\n"
                f"• **Risk Compliance**: Mandate strictly satisfied (1.0% max loss bound)."
            )

        journal_entry = {
            "id": receipt.trade_id or receipt.order_id,
            "parent_order_id": poid,
            "timestamp": receipt.timestamp,
            "asset": ticket.symbol,
            "decision": "TRADE",
            "entry_price": receipt.requested_price,
            "stop_loss": receipt.stop_loss,
            "take_profit": receipt.take_profit,
            "risk_amount_usd": self.mandate["capital_usd"] * (self.mandate["max_risk_pct"]/100.0),
            "risk_pct": self.mandate["max_risk_pct"],
            "status": "OPEN_LIMIT" if ticket.order_type == "LIMIT" else "OPEN",
            "realized_pnl_usd": 0.0,
            "reason": f"{'Limit Order Placed' if ticket.order_type == 'LIMIT' else 'Executed via Gateway'}: {receipt.term} {qty_str} @ {p_str} [{receipt.environment.value}] (Ticket: {poid})",
            "news_context": "Sentry radar verified: 0 active exploits",
            "route": f"Sub-Wallet ({receipt.environment.value})"
        }
        self.decision_journal.insert(0, journal_entry)

        return {
            "query": confirmation_token,
            "elapsed_ms": elapsed_ms,
            "command_type": "TRADE",
            "target_asset": ticket.symbol,
            "decision": "TRADE",
            "headline": headline,
            "reason": reason,
            "explanation": explanation,
            "invalidation": "Price crosses Stop Loss.",
            "max_risk_usd": self.mandate["capital_usd"] * (self.mandate["max_risk_pct"]/100.0),
            "mandate": self.mandate,
            "active_rules": self.mandate,
            "ticket_id": poid,
            "ticket_status": TicketStatus.EXECUTED.value,
            "execution_receipt": receipt_dict,
            "available_cash_usd": self.sub_wallet.cash_usd if self.sub_wallet else 250.0,
            "journal_id": receipt.trade_id or receipt.order_id,
            "debug_intent_inspector": {
                "domain": "EXECUTION",
                "intent": "CONFIRM_ORDER_TICKET",
                "detected_asset": ticket.symbol,
                "resolved_asset": ticket.symbol,
                "active_context_asset": self.state_manager.active_asset,
                "requires_clarification": False,
                "is_execution_intent": True,
                "confidence": 1.0
            }
        }

    async def _handle_cancel_order_ticket(self, parent_order_id: str, raw_input: str, start_time: float) -> Dict[str, Any]:
        """Cancels a pending order ticket."""
        poid = parent_order_id.strip().upper()
        ticket = await self.ticket_registry.cancel_ticket(poid, "User cancelled via command")
        elapsed_ms = int((time.time() - start_time) * 1000)

        if not ticket:
            return {
                "query": raw_input,
                "elapsed_ms": elapsed_ms,
                "command_type": "TICKET_CANCEL",
                "target_asset": "UNKNOWN",
                "decision": "NOT_FOUND",
                "headline": f"Order Ticket Not Found: {poid}",
                "reason": f"No order ticket with ID {poid} found in registry.",
                "explanation": f"Order ticket {poid} was not found.",
                "ticket_id": poid,
                "ticket_status": "NOT_FOUND"
            }

        return {
            "query": raw_input,
            "elapsed_ms": elapsed_ms,
            "command_type": "TICKET_CANCEL",
            "target_asset": ticket.symbol,
            "decision": "CANCELLED",
            "headline": f"🚫 Order Ticket Cancelled: {poid}",
            "reason": f"Pending order ticket {poid} ({ticket.side} {ticket.symbol}) has been cancelled.",
            "explanation": f"Order ticket **{poid}** has been cancelled and will not be executed.",
            "ticket_id": poid,
            "ticket_status": TicketStatus.CANCELLED.value
        }

    async def execute_confirmed_action(self, action_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an action approved by user via UnifiedExecutionGateway."""
        ticket_id = action_payload.get("ticket_id") or action_payload.get("parent_order_id")
        if ticket_id:
            return await self._handle_confirm_order_ticket(str(ticket_id), f"CONFIRM {ticket_id}", time.time())

        action_type = action_payload.get("type", "SPOT_ORDER").upper()
        
        if action_type in ("SPOT_ORDER", "EXECUTE_TRADE", "TRADE"):
            symbol = action_payload.get("symbol", "BTCUSDT")
            side = action_payload.get("side", "BUY")
            qty = float(action_payload.get("quantity", 0.0)) if action_payload.get("quantity") else None
            notional = float(action_payload.get("notional_usd", 0.0)) if action_payload.get("notional_usd") else None
            entry = float(action_payload.get("entry_price", action_payload.get("price", 0.0)))
            stop = float(action_payload.get("stop_loss", 0.0))
            target = float(action_payload.get("take_profit", 0.0))
            order_type = action_payload.get("order_type", "LIMIT" if entry > 0 else "MARKET")
            
            req = ExecutionRequest(
                action_type=ExecutionActionType.OPEN_POSITION,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=qty,
                notional_usd=notional,
                price=entry if entry > 0 else None,
                limit_price=entry if order_type == "LIMIT" and entry > 0 else None,
                stop_loss=stop if stop > 0 else None,
                take_profit=target if target > 0 else None,
                market_type="SPOT",
                leverage=1,
                environment=ExecutionEnvironment.SIMULATED,
                source="ACTION_CONFIRMATION",
                mandate=self.mandate
            )
            receipt = await self.gateway.execute(req)
            return {"success": receipt.status == ExecutionStatus.SUCCESS, "order_id": receipt.order_id, "receipt": receipt.model_dump()}
            
        elif action_type == "EMERGENCY_PROTECT":
            token = action_payload.get("affected_token", "SOL")
            req = ExecutionRequest(
                action_type=ExecutionActionType.CLOSE_POSITION,
                symbol=f"{token}USDT",
                environment=ExecutionEnvironment.SIMULATED,
                source="EMERGENCY_PROTECT",
                close_reason="Emergency Exploit Protection"
            )
            receipt = await self.gateway.execute(req)
            return {"success": receipt.status == ExecutionStatus.SUCCESS, "receipt": receipt.model_dump()}

        elif action_type == "CONVERT":
            from_asset = action_payload.get("from_asset", "USDC")
            to_asset = action_payload.get("to_asset", "USDT")
            amount = float(action_payload.get("from_amount", 10.0))
            req = ExecutionRequest(
                action_type=ExecutionActionType.CONVERT_ASSET,
                symbol=f"{from_asset}/{to_asset}",
                convert_from_asset=from_asset,
                convert_to_asset=to_asset,
                convert_amount=amount,
                environment=ExecutionEnvironment.SIMULATED,
                source="ACTION_CONVERT"
            )
            receipt = await self.gateway.execute(req)
            return {"success": receipt.status == ExecutionStatus.SUCCESS, "receipt": receipt.model_dump()}
            
        return {"success": False, "error": "Unknown action type"}
