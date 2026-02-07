import json
import httpx
from app.settings import settings


class LlmError(Exception):
    pass


async def _call_openai_compatible(base_url: str, api_key: str, model: str, messages: list[dict]) -> str:
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.6,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=headers, content=json.dumps(payload))

    if r.status_code != 200:
        raise LlmError(f"LLM HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        raise LlmError("LLM response parse failed")


async def generate_reply(messages: list[dict]) -> tuple[str, dict]:
    """
    Returns (reply_text, provider_meta)
    """
    # 1) Try DeepSeek
    if settings.deepseek_api_key:
        try:
            txt = await _call_openai_compatible(
                base_url=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key,
                model=settings.deepseek_model,
                messages=messages,
            )
            return txt, {"primary": "deepseek", "fallback_used": False}
        except Exception:
            # fallback below
            pass

    # 2) Fallback OpenAI mini
    if settings.openai_api_key:
        txt = await _call_openai_compatible(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model_fallback,
            messages=messages,
        )
        return txt, {"primary": "openai", "fallback_used": True}

    raise LlmError("No LLM configured (missing DEEPSEEK_API_KEY and OPENAI_API_KEY)")