# app/llm/runtime.py
from __future__ import annotations

import os
from dotenv import load_dotenv
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
import json
import re  # ✅ AJOUT
import asyncio

import random
from dataclasses import dataclass
from httpx import Timeout


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v

# =========================
# Prompt caps (chars)
# =========================
STATE_BLOCK_MAX   = 5_000
PLAYBOOK_MAX      = 8_000
DOCS_CHUNKS_MAX   = 6_000
CTX_SUMMARY_MAX   = 6_000
USER_TEXT_MAX     = 16_000

# Filet de sécurité: cap global par message (si sections introuvables)
# (On laisse respirer un peu, mais on évite les prompts délirants)
USER_MESSAGE_HARD_MAX   = 20_000
SYSTEM_MESSAGE_HARD_MAX = 14_000

# =========================
# Retry / timeouts
# =========================
DEFAULT_CONNECT_TIMEOUT_S = float(_env("LLM_CONNECT_TIMEOUT_S", "10"))
DEFAULT_READ_TIMEOUT_S    = float(_env("LLM_READ_TIMEOUT_S", "35"))
DEFAULT_WRITE_TIMEOUT_S   = float(_env("LLM_WRITE_TIMEOUT_S", "20"))
DEFAULT_POOL_TIMEOUT_S    = float(_env("LLM_POOL_TIMEOUT_S", "10"))

RETRY_BASE_SLEEP_S        = float(_env("LLM_RETRY_BASE_SLEEP_S", "0.6"))
RETRY_MAX_SLEEP_S         = float(_env("LLM_RETRY_MAX_SLEEP_S", "4.0"))
RETRY_JITTER_S            = float(_env("LLM_RETRY_JITTER_S", "0.25"))

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass
class CapMeta:
    applied: bool = False
    system_before: int = 0
    system_after: int = 0
    user_before: int = 0
    user_after: int = 0
    sections_hit: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied": self.applied,
            "system_before": self.system_before,
            "system_after": self.system_after,
            "user_before": self.user_before,
            "user_after": self.user_after,
            "sections_hit": self.sections_hit or [],
        }


def _truncate(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    # on coupe proprement et on laisse une note
    return text[: max_chars - 80] + "\n\n[... tronqué ...]\n"


def _cap_section(text: str, *, label: str, max_chars: int, start_patterns: List[str], end_patterns: List[str]) -> Tuple[str, bool]:
    """
    Tronque une section délimitée par des marqueurs (regex) si trouvée.
    Retourne (text_modifié, found?)
    """
    if not text:
        return text, False

    # On cherche un start
    start_match = None
    for sp in start_patterns:
        m = re.search(sp, text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            start_match = m
            break
    if not start_match:
        return text, False

    start_idx = start_match.start()

    # On cherche un end après start
    end_idx = None
    for ep in end_patterns:
        m2 = re.search(ep, text[start_match.end():], flags=re.IGNORECASE | re.DOTALL)
        if m2:
            end_idx = start_match.end() + m2.start()
            break

    if end_idx is None:
        # section jusqu'à fin
        end_idx = len(text)

    section = text[start_match.start():end_idx]
    if len(section) <= max_chars:
        return text, True

    capped = _truncate(section, max_chars)
    new_text = text[:start_match.start()] + capped + text[end_idx:]
    return new_text, True


def _cap_user_content(user_text: str) -> Tuple[str, List[str]]:
    """
    Cap “intelligent” : on tronque les sections si on les reconnaît, puis filet hard max.
    Renvoie (user_text_cappé, sections_hit)
    """
    sections_hit: List[str] = []

    # Heuristique markers (à matcher sur tes prompts actuels)
    # -> Ajustables sans toucher au reste.
    user_text, hit = _cap_section(
        user_text,
        label="STATE_BLOCK",
        max_chars=STATE_BLOCK_MAX,
        start_patterns=[
            r"\[RW_STATE_BLOCK\]",               # vu dans tes logs
            r"^STATE\b",                         # certains prompts
            r"STATE\s*\(",                       # "STATE (SOURCE DE VÉRITÉ"
        ],
        end_patterns=[
            r"^\s*PLAYBOOK\b",
            r"^\s*DOCS?\b",
            r"^\s*CONTEXT\b",
            r"^\s*RÈGLES\b",
            r"^\s*---",
        ],
    )
    if hit: sections_hit.append("STATE_BLOCK")

    user_text, hit = _cap_section(
        user_text,
        label="PLAYBOOK",
        max_chars=PLAYBOOK_MAX,
        start_patterns=[
            r"\bPLAYBOOK\b",
            r"\bAGENT\s+PLAYBOOK\b",
            r"playbook[_\s]attached",
        ],
        end_patterns=[
            r"^\s*DOCS?\b",
            r"^\s*CONTEXT\b",
            r"^\s*STATE\b",
            r"^\s*---",
        ],
    )
    if hit: sections_hit.append("PLAYBOOK")

    user_text, hit = _cap_section(
        user_text,
        label="DOCS_CHUNKS",
        max_chars=DOCS_CHUNKS_MAX,
        start_patterns=[
            r"\bDOCS?\b",
            r"\bDOCS[_\s]CHUNKS\b",
            r"\bKNOWLEDGE\b",
        ],
        end_patterns=[
            r"^\s*CONTEXT\b",
            r"^\s*STATE\b",
            r"^\s*PLAYBOOK\b",
            r"^\s*---",
        ],
    )
    if hit: sections_hit.append("DOCS_CHUNKS")

    user_text, hit = _cap_section(
        user_text,
        label="CTX_SUMMARY",
        max_chars=CTX_SUMMARY_MAX,
        start_patterns=[
            r"\bCTX\b",
            r"\bCONTEXT\b",
            r"\bCTX[_\s]SUMMARY\b",
        ],
        end_patterns=[
            r"^\s*STATE\b",
            r"^\s*PLAYBOOK\b",
            r"^\s*DOCS?\b",
            r"^\s*---",
        ],
    )
    if hit: sections_hit.append("CTX_SUMMARY")

    # USER_TEXT (WhatsApp) : on cap par pattern faible risque.
    # Si introuvable, le hard max prendra le relais.
    user_text, hit = _cap_section(
        user_text,
        label="USER_TEXT",
        max_chars=USER_TEXT_MAX,
        start_patterns=[
            r"\bMessage utilisateur\b",
            r"\bUser message\b",
            r"\bRAW_USER_MESSAGE\b",
        ],
        end_patterns=[
            r"^\s*STATE\b",
            r"^\s*PLAYBOOK\b",
            r"^\s*DOCS?\b",
            r"^\s*CONTEXT\b",
            r"^\s*---",
        ],
    )
    if hit: sections_hit.append("USER_TEXT")

    # Filet global
    user_text = _truncate(user_text, USER_MESSAGE_HARD_MAX)
    return user_text, sections_hit


def _normalize_and_cap_messages(messages: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], CapMeta]:
    """
    Cap au runtime, sans dépendre du code des agents.
    - cap system hard max
    - cap user via sections + hard max
    """
    meta = CapMeta(applied=False, sections_hit=[])
    if not isinstance(messages, list) or not messages:
        return messages, meta

    new_msgs: List[Dict[str, str]] = []
    for m in messages:
        role = (m.get("role") or "").lower()
        content = m.get("content") or ""
        if role == "system":
            meta.system_before += len(content)
            capped = _truncate(content, SYSTEM_MESSAGE_HARD_MAX)
            meta.system_after += len(capped)
            if len(capped) != len(content):
                meta.applied = True
            new_msgs.append({**m, "content": capped})
        elif role == "user":
            meta.user_before += len(content)
            capped, hits = _cap_user_content(content)
            meta.sections_hit.extend([h for h in hits if h not in (meta.sections_hit or [])])
            meta.user_after += len(capped)
            if len(capped) != len(content):
                meta.applied = True
            new_msgs.append({**m, "content": capped})
        else:
            # assistant/tool/etc : on ne touche pas
            new_msgs.append(m)

    return new_msgs, meta


def _is_retryable_exc(e: Exception) -> bool:
    return isinstance(e, (
        httpx.ReadTimeout,
        httpx.ConnectTimeout,
        httpx.RemoteProtocolError,
        httpx.WriteTimeout,
        httpx.PoolTimeout,
        httpx.NetworkError,
    ))


def _backoff_sleep_s(attempt_idx: int) -> float:
    # attempt_idx: 0,1,2...
    base = RETRY_BASE_SLEEP_S * (2 ** attempt_idx)
    base = min(base, RETRY_MAX_SLEEP_S)
    jitter = random.random() * RETRY_JITTER_S
    return base + jitter





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

        def _extract_first_json_object(s: str) -> Optional[str]:
            # récupère le premier {...} “raisonnable”
            m = re.search(r"\{.*\}", s, flags=re.DOTALL)
            return m.group(0) if m else None

        try:
            obj = json.loads(content)
        except Exception:
            extracted = _extract_first_json_object(content or "")
            if extracted:
                try:
                    obj = json.loads(extracted)
                except Exception as e2:
                    raise LLMCallError(
                        f"LLM returned non-JSON content from {provider['name']}: {content[:180]}"
                    ) from e2
            else:
                raise LLMCallError(
                    f"LLM returned non-JSON content from {provider['name']}: {content[:180]}"
                )

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

        # ✅ Cap prompts (system/user) + sections
        messages, cap_meta = _normalize_and_cap_messages(messages)

        if self._trace_enabled():
            print("[LLM_TRACE] prompt_caps", cap_meta.to_dict())

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

        # ✅ Perplexity: response_format "json_object" n'est pas supporté.
        # On n'envoie pas response_format du tout (on force le JSON via le prompt côté web_search_json).
        if response_format is not None:
            if provider["name"] != "perplexity":
                body["response_format"] = response_format
            else:
                if self._trace_enabled():
                    print("[LLM_TRACE] perplexity_skip_response_format", {"requested": response_format})

        timeout = Timeout(
            connect=DEFAULT_CONNECT_TIMEOUT_S,
            read=DEFAULT_READ_TIMEOUT_S,
            write=DEFAULT_WRITE_TIMEOUT_S,
            pool=DEFAULT_POOL_TIMEOUT_S,
        )

        attempts = max(1, int(self.max_retries) + 1)

        last_exc: Optional[Exception] = None
        t0 = time.time()

        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(attempts):
                try:
                    r = await client.post(url, headers=headers, json=body)

                    # Retry sur statuts "transient"
                    if r.status_code in RETRYABLE_STATUS:
                        if attempt < attempts - 1:
                            if self._trace_enabled():
                                print("[LLM_TRACE] retry_status", {
                                    "provider": provider["name"],
                                    "status": r.status_code,
                                    "attempt": attempt + 1,
                                    "attempts": attempts,
                                })
                            sleep_s = _backoff_sleep_s(attempt)
                            await asyncio.sleep(sleep_s)
                            continue

                    # Erreur non retryable
                    if r.status_code < 200 or r.status_code >= 300:
                        raise LLMCallError(f"{provider['name']} HTTP_{r.status_code} {r.text[:180]}")

                    duration_ms = int((time.time() - t0) * 1000)
                    data = r.json()
                    data["_meta"] = {"duration_ms": duration_ms}
                    return data, provider

                except Exception as e:
                    last_exc = e

                    retryable = _is_retryable_exc(e)
                    if self._trace_enabled():
                        print("[LLM_TRACE] retry_exc", {
                            "provider": provider["name"],
                            "error_type": type(e).__name__,
                            "retryable": retryable,
                            "attempt": attempt + 1,
                            "attempts": attempts,
                        })

                    if (attempt < attempts - 1) and retryable:
                        sleep_s = _backoff_sleep_s(attempt)
                        await asyncio.sleep(sleep_s)
                        continue

                    break

        # si on sort de la boucle, c'est qu'on a échoué
        raise last_exc if isinstance(last_exc, LLMCallError) else LLMCallError(str(last_exc)[:200])