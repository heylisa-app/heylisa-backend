# app/llm/runtime.py
from __future__ import annotations

import os
from dotenv import load_dotenv
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx


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

    def _headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _chat_url(self, base_url: str) -> str:
        # Accept both ".../v1" and root base URLs
        if base_url.endswith("/v1"):
            return f"{base_url}/chat/completions"
        return f"{base_url}/v1/chat/completions"

    async def chat_text(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 800,
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
        return text, meta

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        *,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
        max_tokens: int = 900,
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
        return obj, meta


    async def _call_with_fallback(
        self,
        *,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        last_err: Optional[Exception] = None

        for provider in self.providers:
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
                # On tente le fallback immédiatement
                continue

        raise LLMCallError(f"All LLM providers failed. Last error: {last_err}")

    async def _call_one(
        self,
        *,
        provider: Dict[str, Any],
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        url = self._chat_url(provider["base_url"])
        headers = self._headers(provider["api_key"])

        body: Dict[str, Any] = {
            "model": provider["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
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