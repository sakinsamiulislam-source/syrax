# SYRAX — Model Router & AI Brain Abstraction Specification

## 1. Overview
The **Model Router** is SYRAX's provider-agnostic cognitive orchestration layer. It decouples the trading agent and conversational logic from specific LLM implementations, enforcing strict fail-closed safety, deterministic routing, and structured reasoning schema validation.

```text
USER / TRADER
      ↓
SEMANTIC BRAIN (TALK / THINK / ACT Classification & Multi-Turn Memory)
      ↓
MODEL ROUTER (Deterministic Provider Selection & Failover)
      ├── GeminiProvider (Primary official Google Gemini API)
      └── OpenRouterProvider (Secondary optional provider)
      ↓
STRUCTURED OUTPUT VALIDATOR (Bounded JSON Repair, Schema Enforcement, Fail-Closed)
      ↓
DETERMINISTIC SYRAX SYSTEMS (Hard Gatekeeper)
      ├── Market Scanner (Live Orderbook, Liquidity, Spreads)
      ├── Risk Engine (1.0% Account Risk Cap, Mandatory SL)
      ├── Sentry Radar (Smart Contract Exploit & Threat Monitor)
      ├── Sub-Wallet Manager (Balances, Margins, Reserves)
      └── Execution Gateway (Binance Order Router)
```

---

## 2. Core Architectural Invariant: System of Record Separation

| Domain | Responsible Subsystem | Authority & Capabilities |
| :--- | :--- | :--- |
| **Reasoning & Natural Synthesis** | `ModelRouter` / `AIProvider` | Synthesizes context, interprets user inquiries, generates educational breakdowns, formats watchlists. |
| **Account State & Balances** | `SubWalletManager` | Sole source of truth for liquid cash, reserved margin, and asset allocations. |
| **Market Data & Spreads** | `MarketAgent` / `BinanceAgentOS` | Live Binance Spot & USDⓈ-M Futures orderbook tickers and depth. |
| **Mathematical Risk Limits** | `RiskEngine` | Invariant 1.0% dollar loss cap, mandatory stop-loss calculation, position sizing math. |
| **Exploit Defense** | `NewsSentryAgent` | Live CertiK/PeckShield exploit feeds and token blacklist enforcement. |
| **Order Placement** | `BinanceAgentOS` | Direct exchange API execution. |

> **Critical Rule:** The AI Model is NEVER the source of truth for balances, market prices, positions, risk limits, or execution authorization. AI output can never bypass deterministic safety gates.

---

## 3. Provider Abstraction Contract

All providers implement the `AIProvider` abstract base class (`agent/model_router.py`):

```python
class AIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g. 'gemini')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if credentials are valid and server is online."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Returns telemetry dictionary (name, model, error, latency)."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.3,
        model_override: Optional[str] = None,
        timeout: float = 10.0,
        **kwargs
    ) -> AIResponse:
        """Generates freeform natural text response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.2,
        model_override: Optional[str] = None,
        timeout: float = 10.0,
        fallback_decision: str = "NO_TRADE",
        **kwargs
    ) -> AIResponse:
        """Generates schema-validated structured response."""
        pass
```

---

## 4. Standardized `AIResponse` Container

```python
@dataclass
class AIResponse:
    content: str = ""
    raw_text: str = ""
    structured_data: Optional[Dict[str, Any]] = None
    provider_name: str = ""
    model_name: str = ""
    success: bool = True
    error_type: Optional[str] = None      # TIMEOUT | RATE_LIMITED | AUTH_ERROR | PROVIDER_UNAVAILABLE | MALFORMED_OUTPUT | INVALID_SCHEMA | UNKNOWN_PROVIDER
    error_message: Optional[str] = None  # Safe, user-friendly message (no secret leaks)
    latency_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid_trade(self) -> bool:
        """Helper checking if response is a successful, authorized TRADE."""
        return self.success and bool(self.structured_data and self.structured_data.get("decision") == "TRADE")
```

---

## 5. Structured Output & Fail-Closed Safety

For trading and reasoning tasks (`THINK`), SYRAX uses a standardized structured reasoning schema:

```json
{
  "decision": "TRADE | WAIT | NO_TRADE | PROTECT | null",
  "confidence": 0-100,
  "reasoning": "Detailed market setup and risk analysis rationale",
  "risks": ["Risk factor 1", "Risk factor 2"],
  "relevant_data": {},
  "suggested_action": "Action summary",
  "requires_confirmation": true
}
```

### Fail-Closed Invariants:
1. **Invalid Enum Rejection:** If the AI outputs an unrecognized decision (e.g. `BUY_NOW`, `YOLO`), it is strictly coerced to `NO_TRADE` or `WAIT`. Never `TRADE`.
2. **Confidence Clamping:** Confidence is automatically clamped to `[0, 100]`. Float probabilities `[0.0, 1.0]` are auto-scaled to integer percentages.
3. **Corrupted Output:** If the provider returns broken JSON or non-JSON text, `StructuredOutputValidator` flags `MALFORMED_OUTPUT`, `success=False`, and sets `decision="NO_TRADE"`.
4. **Execution Gate:** Downstream execution systems strictly check `resp.is_valid_trade()`. AI failure never triggers trade execution.

---

## 6. Configuration & Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `gemini` | Configured active provider (`gemini` or `openrouter`). |
| `GEMINI_API_KEY` | *(Required)* | Google Gemini API key (Server-side ONLY). |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model endpoint for reasoning. |
| `OPENROUTER_API_KEY` | *(Optional)* | Secondary API key for OpenRouter fallback. |
| `OPENROUTER_MODEL` | `google/gemma-4-31b-it:free` | Model target for OpenRouter. |

> **Security Mandate:** API keys are read server-side only. They are never transmitted to the frontend, logged in telemetry, or serialized in API receipts.

---

## 7. How to Add a Future Model Provider

To add a new provider (e.g. Anthropic Claude, OpenAI, Local Ollama):
1. Create a class subclassing `AIProvider` in `agent/model_router.py`:
   ```python
   class ClaudeProvider(AIProvider):
       @property
       def name(self) -> str:
           return "claude"
       # Implement is_available, get_status, generate, generate_structured
   ```
2. Register it in `ModelRouter.__init__`:
   ```python
   self.claude = ClaudeProvider()
   self.register_provider("claude", self.claude)
   ```
3. Set `AI_PROVIDER=claude` in `.env`. No changes required to existing conversational or trading workflows.
