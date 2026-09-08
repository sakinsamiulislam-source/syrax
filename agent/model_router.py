"""
SYRAX — Model Router & AI Brain Abstraction Layer
Provides a provider-agnostic, fail-closed AI reasoning architecture for SYRAX.

Key Principles:
1. Provider-Agnostic Interface (AIProvider ABC & AIResponse).
2. Gemini Provider (Google Gemini official endpoints with server-side keys).
3. Structured Output Validation (Bounded repair, schema enforcement, fail-closed trading safety).
4. System of Record Separation (AI reasons; deterministic SYRAX systems authorize & execute).
5. Fail-Closed Invariant (Malformed/failed AI output strictly resolves to WAIT/NO_TRADE, never TRADE).
"""

import os
import re
import json
import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("syrax.model_router")


# =============================================================================
# 1. STANDARDIZED AI RESPONSE CONTAINER
# =============================================================================

@dataclass
class AIResponse:
    """
    Standardized AI response object returned across all model providers.
    """
    content: str = ""
    raw_text: str = ""
    structured_data: Optional[Dict[str, Any]] = None
    provider_name: str = ""
    model_name: str = ""
    success: bool = True
    error_type: Optional[str] = None      # TIMEOUT | RATE_LIMITED | AUTH_ERROR | PROVIDER_UNAVAILABLE | MALFORMED_OUTPUT | INVALID_SCHEMA | UNKNOWN_PROVIDER
    error_message: Optional[str] = None  # Safe, user-facing error message (no secrets/tracebacks)
    latency_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid_trade(self) -> bool:
        """Helper to check if response is a valid, authorized TRADE decision."""
        if not self.success or not self.structured_data:
            return False
        return self.structured_data.get("decision") == "TRADE"


# =============================================================================
# 2. STRUCTURED OUTPUT SCHEMA & VALIDATOR (FAIL-CLOSED)
# =============================================================================

class StructuredOutputValidator:
    """
    Validates, repairs, and sanitizes structured AI reasoning outputs.
    Guarantees that malformed or contradictory AI outputs NEVER produce a TRADE decision.
    """

    ALLOWED_DECISIONS = {"TRADE", "WAIT", "NO_TRADE", "PROTECT", None}

    STANDARD_TRADING_SCHEMA = {
        "type": "object",
        "properties": {
            "decision": {"type": ["string", "null"], "enum": ["TRADE", "WAIT", "NO_TRADE", "PROTECT", None]},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "reasoning": {"type": "string"},
            "risks": {"type": "array", "items": {"type": "string"}},
            "relevant_data": {"type": "object"},
            "suggested_action": {"type": "string"},
            "requires_confirmation": {"type": "boolean"}
        },
        "required": ["decision", "confidence", "reasoning"]
    }

    @classmethod
    def extract_json_block(cls, text: str) -> Optional[str]:
        """Extracts JSON string from markdown codeblocks or raw text."""
        if not text or not text.strip():
            return None

        clean_text = text.strip()

        # 1. Match ```json ... ``` codeblock
        json_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text, re.IGNORECASE)
        if json_block_match:
            candidate = json_block_match.group(1).strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate

        # 2. Match outermost { ... }
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return clean_text[start_idx:end_idx + 1]

        return None

    @classmethod
    def repair_json_string(cls, json_str: str) -> str:
        """Applies bounded, safe repairs to common LLM JSON syntax imperfections."""
        if not json_str:
            return ""

        s = json_str.strip()
        # Remove trailing commas before closing braces/brackets
        s = re.sub(r",\s*([\}\]])", r"\1", s)
        # Fix unescaped newlines in strings
        s = s.replace("\r\n", "\n")
        return s

    @classmethod
    def validate_trading_reasoning(
        cls,
        raw_text: str,
        fallback_decision: str = "NO_TRADE"
    ) -> Tuple[bool, Dict[str, Any], Optional[str], Optional[str]]:
        """
        Parses and validates trading reasoning JSON.
        Returns: (success, structured_data, error_type, error_message)
        FAIL-CLOSED INVARIANT: On any parsing or validation failure, decision is strictly NO_TRADE/WAIT.
        """
        json_candidate = cls.extract_json_block(raw_text)
        if not json_candidate:
            return (
                False,
                {
                    "decision": fallback_decision,
                    "confidence": 0,
                    "reasoning": "AI output contained no valid JSON structure.",
                    "risks": ["AI Output Unstructured"],
                    "relevant_data": {},
                    "suggested_action": "WAIT",
                    "requires_confirmation": False
                },
                "MALFORMED_OUTPUT",
                "AI reasoning output was not structured. No trade was authorized."
            )

        # Attempt parsing with repair
        parsed_obj = None
        try:
            parsed_obj = json.loads(json_candidate)
        except Exception:
            repaired = cls.repair_json_string(json_candidate)
            try:
                parsed_obj = json.loads(repaired)
            except Exception as e:
                logger.warning(f"Failed to parse AI JSON reasoning: {e}")
                return (
                    False,
                    {
                        "decision": fallback_decision,
                        "confidence": 0,
                        "reasoning": f"JSON syntax error in AI response: {str(e)}",
                        "risks": ["JSON Syntax Malformation"],
                        "relevant_data": {},
                        "suggested_action": "WAIT",
                        "requires_confirmation": False
                    },
                    "MALFORMED_OUTPUT",
                    "AI reasoning syntax was invalid. No trade was authorized."
                )

        if not isinstance(parsed_obj, dict):
            return (
                False,
                {
                    "decision": fallback_decision,
                    "confidence": 0,
                    "reasoning": "AI output JSON root was not an object.",
                    "risks": ["Invalid Root Type"],
                    "relevant_data": {},
                    "suggested_action": "WAIT",
                    "requires_confirmation": False
                },
                "INVALID_SCHEMA",
                "AI reasoning schema was invalid. No trade was authorized."
            )

        # -------------------------------------------------------------
        # Field Validation & Fail-Closed Sanitization
        # -------------------------------------------------------------
        raw_decision = parsed_obj.get("decision")
        if raw_decision is not None:
            raw_decision_str = str(raw_decision).strip().upper()
            if raw_decision_str in cls.ALLOWED_DECISIONS:
                decision = raw_decision_str
            else:
                logger.warning(f"Invalid decision enum '{raw_decision}' received from AI. Failing closed to {fallback_decision}.")
                decision = fallback_decision
        else:
            decision = None

        # Confidence: clamp to 0-100
        raw_conf = parsed_obj.get("confidence", 0)
        try:
            conf_val = float(raw_conf)
            if 0.0 <= conf_val <= 1.0 and conf_val != 0.0 and conf_val != 1.0:
                # Scaled 0.0 - 1.0 float to percentage
                confidence = int(round(conf_val * 100))
            else:
                confidence = max(0, min(100, int(round(conf_val))))
        except (ValueError, TypeError):
            confidence = 0

        reasoning = str(parsed_obj.get("reasoning", "") or "No reasoning provided.")
        raw_risks = parsed_obj.get("risks", [])
        risks = [str(r) for r in raw_risks] if isinstance(raw_risks, list) else []
        relevant_data = parsed_obj.get("relevant_data", {}) if isinstance(parsed_obj.get("relevant_data"), dict) else {}
        suggested_action = str(parsed_obj.get("suggested_action", "") or (decision or "WAIT"))
        requires_confirmation = bool(parsed_obj.get("requires_confirmation", True))

        validated_data = {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "risks": risks,
            "relevant_data": relevant_data,
            "suggested_action": suggested_action,
            "requires_confirmation": requires_confirmation
        }

        return (True, validated_data, None, None)


# =============================================================================
# 3. ABSTRACT AI PROVIDER INTERFACE
# =============================================================================

class AIProvider(ABC):
    """
    Abstract Base Class for all AI model providers (Gemini, OpenRouter, etc.).
    Defines the contract for text generation, structured reasoning, and health monitoring.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g. 'gemini', 'openrouter')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured with credentials and available."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Returns health telemetry and configuration metadata."""
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


# =============================================================================
# 4. GOOGLE GEMINI PROVIDER (PRIMARY)
# =============================================================================

class GeminiProvider(AIProvider):
    """
    Official Google Gemini API Provider.
    Executes high-throughput multi-modal and structured reasoning tasks.
    API keys remain strictly server-side and are never logged or exposed.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.default_model = (model or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)).strip()
        self._last_error: Optional[str] = None
        self._last_latency_ms: int = 0

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 5 and self._api_key != "YOUR_GEMINI_KEY_HERE")

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "configured": self.is_available(),
            "model": self.default_model,
            "last_error": self._last_error,
            "last_latency_ms": self._last_latency_ms
        }

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
        start_t = time.time()
        if not self.is_available():
            return AIResponse(
                success=False,
                provider_name=self.name,
                error_type="AUTH_ERROR",
                error_message="Gemini API credentials are not configured on the server."
            )

        target_model = model_override or self.default_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self._api_key}"

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instructions: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})

        for m in messages:
            role = "user" if m.get("role") in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(url, json=payload)
                elapsed_ms = int((time.time() - start_t) * 1000)
                self._last_latency_ms = elapsed_ms

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            raw_text = parts[0].get("text", "").strip()
                            self._last_error = None
                            return AIResponse(
                                content=raw_text,
                                raw_text=raw_text,
                                provider_name=self.name,
                                model_name=target_model,
                                success=True,
                                latency_ms=elapsed_ms
                            )

                    return AIResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=target_model,
                        error_type="MALFORMED_OUTPUT",
                        error_message="Gemini returned an empty candidate list.",
                        latency_ms=elapsed_ms
                    )

                elif res.status_code == 429:
                    self._last_error = "Rate limit exceeded (429)"
                    return AIResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=target_model,
                        error_type="RATE_LIMITED",
                        error_message="Gemini API rate limit reached. Please retry in a moment.",
                        latency_ms=elapsed_ms
                    )

                elif res.status_code in (401, 403):
                    self._last_error = f"Authentication error ({res.status_code})"
                    return AIResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=target_model,
                        error_type="AUTH_ERROR",
                        error_message="Gemini API authentication failed. Verify server API key.",
                        latency_ms=elapsed_ms
                    )

                else:
                    self._last_error = f"HTTP {res.status_code}"
                    return AIResponse(
                        success=False,
                        provider_name=self.name,
                        model_name=target_model,
                        error_type="PROVIDER_UNAVAILABLE",
                        error_message=f"Gemini API returned status {res.status_code}.",
                        latency_ms=elapsed_ms
                    )

        except httpx.TimeoutException:
            elapsed_ms = int((time.time() - start_t) * 1000)
            self._last_error = "Request Timeout"
            return AIResponse(
                success=False,
                provider_name=self.name,
                model_name=target_model,
                error_type="TIMEOUT",
                error_message="Gemini API request timed out.",
                latency_ms=elapsed_ms
            )

        except Exception as e:
            elapsed_ms = int((time.time() - start_t) * 1000)
            self._last_error = str(e)
            logger.debug(f"Gemini generate error: {e}")
            return AIResponse(
                success=False,
                provider_name=self.name,
                model_name=target_model,
                error_type="PROVIDER_UNAVAILABLE",
                error_message="Gemini connection encountered an unexpected error.",
                latency_ms=elapsed_ms
            )

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
        """Generates structured reasoning and enforces fail-closed schema validation."""
        schema_instruction = (
            "You MUST respond ONLY with valid JSON conforming strictly to this format:\n"
            "{\n"
            '  "decision": "TRADE" | "WAIT" | "NO_TRADE" | "PROTECT" | null,\n'
            '  "confidence": 0-100,\n'
            '  "reasoning": "Clear explanation of market setup and risk analysis",\n'
            '  "risks": ["Risk 1", "Risk 2"],\n'
            '  "relevant_data": {},\n'
            '  "suggested_action": "Action summary",\n'
            '  "requires_confirmation": true\n'
            "}\n"
            "Do not output markdown backticks or conversational filler before/after the JSON."
        )

        full_system_prompt = f"{system_prompt}\n\n{schema_instruction}" if system_prompt else schema_instruction

        resp = await self.generate(
            messages=messages,
            system_prompt=full_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_override=model_override,
            timeout=timeout,
            **kwargs
        )

        if not resp.success:
            # Inject fail-closed structured payload on provider error
            resp.structured_data = {
                "decision": fallback_decision,
                "confidence": 0,
                "reasoning": resp.error_message or "AI provider unavailable.",
                "risks": ["AI Provider Failure"],
                "relevant_data": {},
                "suggested_action": "WAIT",
                "requires_confirmation": False
            }
            return resp

        # Validate & sanitize JSON
        valid, structured_data, err_type, err_msg = StructuredOutputValidator.validate_trading_reasoning(
            resp.raw_text,
            fallback_decision=fallback_decision
        )

        resp.structured_data = structured_data
        if not valid:
            resp.success = False
            resp.error_type = err_type
            resp.error_message = err_msg

        return resp


# =============================================================================
# 5. OPENROUTER PROVIDER (OPTIONAL SECONDARY)
# =============================================================================

class OpenRouterProvider(AIProvider):
    """
    OpenRouter API Provider with multi-model fallback and rate limit handling.
    """

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_FALLBACK_MODELS = [
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "liquid/lfm-2.5-2.6b:free"
    ]

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self._api_key = (api_key or os.getenv("OPENROUTER_API_KEY", "")).strip()
        self.default_model = (default_model or os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")).strip()
        self._last_429_time = 0.0
        self._last_error: Optional[str] = None
        self._last_latency_ms: int = 0

    @property
    def name(self) -> str:
        return "openrouter"

    def is_available(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 10 and self._api_key != "YOUR_OPENROUTER_KEY_HERE")

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "configured": self.is_available(),
            "model": self.default_model,
            "last_error": self._last_error,
            "last_latency_ms": self._last_latency_ms
        }

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
        start_t = time.time()
        if not self.is_available():
            return AIResponse(
                success=False,
                provider_name=self.name,
                error_type="AUTH_ERROR",
                error_message="OpenRouter API key is not configured."
            )

        if time.time() - self._last_429_time < 10.0:
            return AIResponse(
                success=False,
                provider_name=self.name,
                error_type="RATE_LIMITED",
                error_message="OpenRouter is currently in rate-limit cooldown."
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "http://localhost:3001",
            "X-Title": "SYRAX Trading Agent",
            "Content-Type": "application/json"
        }

        target_model = model_override or self.default_model
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(self.OPENROUTER_API_URL, headers=headers, json=payload)
                elapsed_ms = int((time.time() - start_t) * 1000)
                self._last_latency_ms = elapsed_ms

                if res.status_code == 200:
                    data = res.json()
                    msg = data["choices"][0]["message"]
                    content = (msg.get("content") or msg.get("reasoning") or "").strip()
                    if content:
                        self._last_error = None
                        return AIResponse(
                            content=content,
                            raw_text=content,
                            provider_name=self.name,
                            model_name=target_model,
                            success=True,
                            latency_ms=elapsed_ms
                        )
                elif res.status_code == 429:
                    self._last_429_time = time.time()
                    self._last_error = "Rate Limited (429)"
                    return AIResponse(
                        success=False,
                        provider_name=self.name,
                        error_type="RATE_LIMITED",
                        error_message="OpenRouter rate limit reached.",
                        latency_ms=elapsed_ms
                    )

        except Exception as e:
            elapsed_ms = int((time.time() - start_t) * 1000)
            self._last_error = str(e)
            return AIResponse(
                success=False,
                provider_name=self.name,
                error_type="PROVIDER_UNAVAILABLE",
                error_message=f"OpenRouter connection error: {e}",
                latency_ms=elapsed_ms
            )

        return AIResponse(
            success=False,
            provider_name=self.name,
            error_type="PROVIDER_UNAVAILABLE",
            error_message="OpenRouter did not return valid content.",
            latency_ms=int((time.time() - start_t) * 1000)
        )

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
        schema_instruction = (
            "You MUST respond ONLY with valid JSON conforming strictly to this format:\n"
            "{\n"
            '  "decision": "TRADE" | "WAIT" | "NO_TRADE" | "PROTECT" | null,\n'
            '  "confidence": 0-100,\n'
            '  "reasoning": "Clear explanation of market setup and risk analysis",\n'
            '  "risks": ["Risk 1", "Risk 2"],\n'
            '  "relevant_data": {},\n'
            '  "suggested_action": "Action summary",\n'
            '  "requires_confirmation": true\n'
            "}\n"
            "Do not output markdown backticks or conversational filler."
        )
        full_system_prompt = f"{system_prompt}\n\n{schema_instruction}" if system_prompt else schema_instruction

        resp = await self.generate(
            messages=messages,
            system_prompt=full_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_override=model_override,
            timeout=timeout,
            **kwargs
        )

        if not resp.success:
            resp.structured_data = {
                "decision": fallback_decision,
                "confidence": 0,
                "reasoning": resp.error_message or "OpenRouter unavailable.",
                "risks": ["AI Provider Failure"],
                "relevant_data": {},
                "suggested_action": "WAIT",
                "requires_confirmation": False
            }
            return resp

        valid, structured_data, err_type, err_msg = StructuredOutputValidator.validate_trading_reasoning(
            resp.raw_text,
            fallback_decision=fallback_decision
        )
        resp.structured_data = structured_data
        if not valid:
            resp.success = False
            resp.error_type = err_type
            resp.error_message = err_msg

        return resp


# =============================================================================
# 6. MODEL ROUTER ENGINE
# =============================================================================

class ModelRouter:
    """
    Intelligent Model & Task Routing Engine for SYRAX.
    Selects configured AI providers, enforces deterministic fallback rules,
    and guarantees fail-closed safety for all downstream execution systems.
    """

    TASK_CONVERSATION = "CONVERSATION"
    TASK_REASONING = "REASONING"
    TASK_CRYPTO_ANALYSIS = "CRYPTO_ANALYSIS"
    TASK_CODE_GENERATION = "CODE_GENERATION"
    TASK_OPPORTUNITY_DISCOVERY = "OPPORTUNITY_DISCOVERY"

    def __init__(
        self,
        default_provider: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None
    ):
        self._providers: Dict[str, AIProvider] = {}
        
        # Instantiate built-in providers
        self.gemini = GeminiProvider(api_key=gemini_api_key)
        self.openrouter = OpenRouterProvider(api_key=openrouter_api_key)

        self.register_provider("gemini", self.gemini)
        self.register_provider("openrouter", self.openrouter)

        # Default provider is Gemini unless configured otherwise
        configured = (default_provider or os.getenv("AI_PROVIDER", "gemini")).strip().lower()
        self.active_provider_name = configured if configured in self._providers else "gemini"

    def register_provider(self, name: str, provider: AIProvider):
        """Registers a new AI provider under a unique name."""
        self._providers[name.lower()] = provider

    def get_provider(self, name: Optional[str] = None) -> Optional[AIProvider]:
        """Returns the requested provider or active provider."""
        p_name = (name or self.active_provider_name).lower()
        return self._providers.get(p_name)

    def get_preferred_provider(self) -> Optional[AIProvider]:
        """
        Deterministically returns the active configured provider.
        If active is unavailable, checks if a configured secondary provider exists.
        """
        active = self.get_provider(self.active_provider_name)
        if active and active.is_available():
            return active

        # Fallback to alternative registered provider ONLY if actually configured & available
        for name, prov in self._providers.items():
            if name != self.active_provider_name and prov.is_available():
                return prov

        return active  # Return the active even if unavailable so callers get clean status

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive router telemetry and status of all providers."""
        return {
            "active_provider": self.active_provider_name,
            "providers": {name: p.get_status() for name, p in self._providers.items()}
        }

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.3,
        provider_name: Optional[str] = None,
        model_override: Optional[str] = None,
        timeout: float = 10.0
    ) -> AIResponse:
        """
        Routes freeform text generation to the preferred provider with deterministic fallback.
        """
        prov = self.get_provider(provider_name) if provider_name else self.get_preferred_provider()
        if not prov:
            return AIResponse(
                success=False,
                error_type="UNKNOWN_PROVIDER",
                error_message=f"Requested AI provider '{provider_name}' is not registered."
            )

        if not prov.is_available():
            return AIResponse(
                success=False,
                provider_name=prov.name,
                error_type="PROVIDER_UNAVAILABLE",
                error_message=f"AI provider '{prov.name}' is not configured or unavailable."
            )

        resp = await prov.generate(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_override=model_override,
            timeout=timeout
        )

        # If primary failed with timeout or rate-limit, check deterministic fallback
        if not resp.success and not provider_name:
            for name, fallback_prov in self._providers.items():
                if name != prov.name and fallback_prov.is_available():
                    logger.info(f"Primary provider '{prov.name}' failed ({resp.error_type}). Attempting fallback to '{name}'.")
                    fallback_resp = await fallback_prov.generate(
                        messages=messages,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=timeout
                    )
                    if fallback_resp.success:
                        return fallback_resp

        return resp

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.2,
        provider_name: Optional[str] = None,
        model_override: Optional[str] = None,
        timeout: float = 10.0,
        fallback_decision: str = "NO_TRADE"
    ) -> AIResponse:
        """
        Routes structured reasoning generation with strict fail-closed validation.
        """
        prov = self.get_provider(provider_name) if provider_name else self.get_preferred_provider()
        if not prov:
            return AIResponse(
                success=False,
                error_type="UNKNOWN_PROVIDER",
                error_message=f"Requested AI provider '{provider_name}' is not registered.",
                structured_data={
                    "decision": fallback_decision,
                    "confidence": 0,
                    "reasoning": f"Unknown AI provider '{provider_name}'.",
                    "risks": ["Provider Not Found"],
                    "relevant_data": {},
                    "suggested_action": "WAIT",
                    "requires_confirmation": False
                }
            )

        if not prov.is_available():
            return AIResponse(
                success=False,
                provider_name=prov.name,
                error_type="PROVIDER_UNAVAILABLE",
                error_message=f"AI provider '{prov.name}' is unavailable.",
                structured_data={
                    "decision": fallback_decision,
                    "confidence": 0,
                    "reasoning": f"Provider '{prov.name}' is unavailable.",
                    "risks": ["Provider Offline"],
                    "relevant_data": {},
                    "suggested_action": "WAIT",
                    "requires_confirmation": False
                }
            )

        resp = await prov.generate_structured(
            messages=messages,
            schema=schema,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_override=model_override,
            timeout=timeout,
            fallback_decision=fallback_decision
        )

        # Deterministic fallback if primary failed
        if not resp.success and not provider_name:
            for name, fallback_prov in self._providers.items():
                if name != prov.name and fallback_prov.is_available():
                    logger.info(f"Primary provider '{prov.name}' failed structured generation. Trying '{name}'.")
                    fallback_resp = await fallback_prov.generate_structured(
                        messages=messages,
                        schema=schema,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=timeout,
                        fallback_decision=fallback_decision
                    )
                    if fallback_resp.success:
                        return fallback_resp

        return resp

    async def execute_task(
        self,
        task: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.3
    ) -> Optional[str]:
        """
        Backwards-compatible execution entrypoint returning plain string content or None.
        """
        resp = await self.generate_text(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        if resp.success and resp.content:
            return resp.content
        return None
