# app/llm/runtime.py
from __future__ import annotations

import os
from dotenv import load_dotenv
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
import json
import re  # ✅ AJOUT


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v


class LLMCallError(RuntimeError):
    pass


class LLMRuntime:
    """
    Simple runtime:
    - Provider #1: DeepSeek (prioritaire)
    - Provider #2: OpenAI (fallback)

    Assumption: both are OpenAI-compatible Chat Completions endpoints.
    If DeepSeek differs, you only change BASE_URL + headers/payload mapping here.
    """

    def __init__(self) -> None:
        load_dotenv()  # ✅ charge .env quand on lance un script standalone
        # Provider priority order
        self.providers: List[Dict[str, Any]] = [
            {
                "name": "deepseek",
                "base_url": _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                "api_key": _env("DEEPSEEK_API_KEY"),
                "model": _env("DEEPSEEK_MODEL", "deepseek-chat"),
            },
            {
                "name": "perplexity",
                "base_url": _env("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
                "api_key": _env("PERPLEXITY_API_KEY"),
                "model": _env("PERPLEXITY_MODEL", "sonar-pro"),
            },
            {
                "name": "openai",
                "base_url": _env("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "api_key": _env("OPENAI_API_KEY"),
                "model": _env("OPENAI_MODEL_FALLBACK", "gpt-4o-mini"),
            },
        ]

        # Safety: ensure at least one provider is configured
        if not any(p.get("api_key") for p in self.providers):
            raise RuntimeError(
                "No LLM API keys configured. Set DEEPSEEK_API_KEY and/or OPENAI_API_KEY."
            )

        self.timeout_s = float(_env("LLM_TIMEOUT_S", "20"))
        self.max_retries = int(_env("LLM_MAX_RETRIES", "0"))
        # ✅ Routing policies
        self.chat_provider_allowlist = {"deepseek", "openai"}      # jamais perplexity pour le chat
        self.websearch_provider_allowlist = {"perplexity"}        # web_search = perplexity only

    def _trace_enabled(self) -> bool:
        return str(_env("LLM_TRACE", "0")).strip() in {"1", "true", "True"}

    def _trace_store_enabled(self) -> bool:
        return str(_env("LLM_TRACE_STORE", "0")).strip() in {"1", "true", "True"}

    def _safe_preview(self, obj: Any, max_chars: int = 1200) -> str:
        try:
            s = json.dumps(obj, ensure_ascii=False, default=str)
        except Exception:
            s = str(obj)
        if len(s) <= max_chars:
            return s
        return s[: max_chars - 3] + "..."

    def _headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _chat_url(self, provider: Dict[str, Any]) -> str:
        base_url = provider["base_url"]
        name = provider["name"]

        # Perplexity → pas de /v1
        if name == "perplexity":
            return f"{base_url}/chat/completions"

        # Providers OpenAI-compatible classiques
        if base_url.endswith("/v1"):
            return f"{base_url}/chat/completions"

        return f"{base_url}/v1/chat/completions"

    async def chat_text(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 800,
        trace: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Returns (text, meta)
        meta includes: provider, model, duration_ms, raw (optional minimal)
        """
        payload_base, provider = await self._call_with_fallback(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=None,
            provider_allowlist=self.chat_provider_allowlist,
            raw_user_message=(trace or {}).get("raw_user_message"),  # ✅
            trace=trace,
        )

        text = (
            payload_base.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        ) or ""

        if not text.strip():
            raise LLMCallError(f"Empty LLM response from {provider['name']}")

        meta = {
            "provider": provider["name"],
            "model": provider["model"],
            "duration_ms": payload_base.get("_meta", {}).get("duration_ms"),
        }
        if self._trace_enabled():
            print(
                "[LLM_TRACE] chat_text",
                {
                    "provider": meta["provider"],
                    "model": meta["model"],
                    "duration_ms": meta["duration_ms"],
                    "trace": trace or {},
                    "messages_preview": self._safe_preview(messages, 800),
                    "response_preview": (text[:500] + "…") if len(text) > 500 else text,
                },
            )
        return text, meta

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        *,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
        max_tokens: int = 900,
        trace: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Returns (json_obj, meta)
        We request "response_format": {"type":"json_object"} for strict-ish JSON.
        If schema is provided, we pass it through as metadata only (for logging),
        and still rely on the agent prompt to enforce the schema.
        """
        response_format = {"type": "json_object"}

        payload, provider = await self._call_with_fallback(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            provider_allowlist=self.chat_provider_allowlist,
            raw_user_message=(trace or {}).get("raw_user_message"),
            trace=trace,
        )

        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        ) or ""

        # Parse JSON
        try:
            import json

            obj = json.loads(content)
        except Exception as e:
            raise LLMCallError(
                f"LLM returned non-JSON content from {provider['name']}: {content[:180]}"
            ) from e

        meta = {
            "provider": provider["name"],
            "model": provider["model"],
            "duration_ms": payload.get("_meta", {}).get("duration_ms"),
            "schema_hint": bool(json_schema),
        }

        if self._trace_enabled():
            print(
                "[LLM_TRACE] chat_json",
                {
                    "provider": meta["provider"],
                    "model": meta["model"],
                    "duration_ms": meta["duration_ms"],
                    "schema_hint": meta["schema_hint"],
                    "trace": trace or {},
                    "messages_preview": self._safe_preview(messages, 800),
                    "response_preview": self._safe_preview(obj, 500),
                },
            )
        return obj, meta


    async def web_search_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 900,
        trace: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Web search route:
        - Provider #1: Perplexity
        - Fallback: OpenAI (si API key présente)
        """
        payload, provider = await self._call_with_fallback(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            provider_allowlist={"perplexity", "openai"},
            preferred_order=["perplexity", "openai"],
        )

        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        ) or ""

        try:
            obj = json.loads(content)
        except Exception as e:
            raise LLMCallError(
                f"LLM returned non-JSON content from {provider['name']}: {content[:180]}"
            ) from e

        meta = {
            "provider": provider["name"],
            "model": provider["model"],
            "duration_ms": payload.get("_meta", {}).get("duration_ms"),
        }

        if self._trace_enabled():
            print(
                "[LLM_TRACE] web_search_json",
                {
                    "provider": meta["provider"],
                    "model": meta["model"],
                    "duration_ms": meta["duration_ms"],
                    "trace": trace or {},
                    "messages_preview": self._safe_preview(messages, 800),
                    "response_preview": self._safe_preview(obj, 500),
                },
            )

        return obj, meta


    def _last_user_content(self, messages: List[Dict[str, str]]) -> str:
        for m in reversed(messages):
            if (m.get("role") or "").lower() == "user":
                return (m.get("content") or "").strip()
        return ""

    def _word_count(self, text: str) -> int:
        # \w inclut les lettres accentuées en mode UNICODE
        return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))

    async def _call_with_fallback(
        self,
        *,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]],
        provider_allowlist: Optional[set] = None,
        preferred_order: Optional[List[str]] = None,
        raw_user_message: Optional[str] = None,
        trace: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        last_err: Optional[Exception] = None

        # --- Heuristique pour le chat (si allowlist = chat) ---
        if raw_user_message is not None:
            last_user = raw_user_message.strip()
        else:
            last_user = self._last_user_content(messages)

        wc = self._word_count(last_user)
        short_msg = wc > 0 and wc <= int(_env("LLM_SHORT_MSG_WORDS", "6"))

        # --- Exception: fastpath + smalltalk_intro => deepseek first (même si short msg) ---
        is_fastpath_smalltalk_intro = False
        try:
            rs = str((trace or {}).get("route_source") or "").strip().lower()
            st = str((trace or {}).get("runtime_state") or (trace or {}).get("state") or "").strip().lower()
            is_fastpath_smalltalk_intro = (rs == "fastpath" and st == "smalltalk_intro")
        except Exception:
            is_fastpath_smalltalk_intro = False

        # Base list
        providers_to_try = list(self.providers)

        # Apply allowlist (ex: chat only deepseek/openai OR websearch only perplexity)
        if provider_allowlist is not None:
            providers_to_try = [p for p in providers_to_try if p.get("name") in provider_allowlist]

        # Apply preferred order if provided
        if preferred_order:
            name_to_p = {p["name"]: p for p in providers_to_try}
            ordered = [name_to_p[n] for n in preferred_order if n in name_to_p]
            providers_to_try = ordered + [p for p in providers_to_try if p["name"] not in preferred_order]

        # ✅ Override: fastpath + smalltalk_intro => deepseek first (même si short msg)
        if (
            provider_allowlist == getattr(self, "chat_provider_allowlist", None)
            and is_fastpath_smalltalk_intro
        ):
            preferred = ["deepseek", "openai"]
            name_to_p = {p["name"]: p for p in providers_to_try}
            ordered = [name_to_p[n] for n in preferred if n in name_to_p]
            providers_to_try = ordered + [p for p in providers_to_try if p["name"] not in preferred]

        # If it's chat routing and message is short → openai first then deepseek
        # (Perplexity impossible ici car allowlist chat l’exclut)
        if (
            provider_allowlist == getattr(self, "chat_provider_allowlist", None)
            and short_msg
            and not is_fastpath_smalltalk_intro
        ):
            preferred = ["openai", "deepseek"]
            name_to_p = {p["name"]: p for p in providers_to_try}
            ordered = [name_to_p[n] for n in preferred if n in name_to_p]
            providers_to_try = ordered + [p for p in providers_to_try if p["name"] not in preferred]

        if self._trace_enabled():
            print(
                "[LLM_TRACE] provider_routing",
                {
                    "last_user_preview": (last_user[:80] + "…") if len(last_user) > 80 else last_user,
                    "word_count": wc,
                    "short_msg": short_msg,
                    "allowlist": sorted(list(provider_allowlist)) if provider_allowlist else None,
                    "providers_order": [p["name"] for p in providers_to_try if p.get("api_key")],
                },
            )

        for provider in providers_to_try:
            if not provider.get("api_key"):
                continue

            try:
                return await self._call_one(
                    provider=provider,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as e:
                last_err = e

                if self._trace_enabled():
                    print(
                        "[LLM_TRACE] provider_failed",
                        {
                            "provider": provider["name"],
                            "model": provider.get("model"),
                            "error_type": type(e).__name__,
                            "error_preview": str(e)[:200],
                        },
                    )

                continue

        if self._trace_enabled():
            print(
                "[LLM_TRACE] all_providers_failed",
                {
                    "last_error_type": type(last_err).__name__ if last_err else None,
                    "last_error_preview": str(last_err)[:300] if last_err else None,
                },
            )

        raise LLMCallError(f"All LLM providers failed. Last error: {last_err}")

    def _supports_store_param(self, provider_name: str) -> bool:
        # OpenAI Chat Completions supporte `store`
        # DeepSeek/Perplexity: pas garanti → on évite pour ne pas casser
        return provider_name == "openai"

    async def _call_one(
        self,
        *,
        provider: Dict[str, Any],
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        url = self._chat_url(provider)
        headers = self._headers(provider["api_key"])

        body: Dict[str, Any] = {
            "model": provider["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # ✅ Privacy hardening: do not store inputs/outputs (when supported)
        if self._supports_store_param(provider["name"]):
            body["store"] = False

            if self._trace_enabled():
                print("[LLM_TRACE] store_disabled", {"provider": provider["name"], "store": body.get("store")})

        if response_format is not None:
            body["response_format"] = response_format

        t0 = time.time()
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(url, headers=headers, json=body)

        duration_ms = int((time.time() - t0) * 1000)

        if r.status_code < 200 or r.status_code >= 300:
            raise LLMCallError(
                f"{provider['name']} HTTP_{r.status_code} {r.text[:180]}"
            )

        data = r.json()
        data["_meta"] = {"duration_ms": duration_ms}
        return data, provider