# app/services/auth.py
import httpx
import logging
from app.settings import settings

logger = logging.getLogger("uvicorn.error")

class AuthError(Exception):
    pass

async def get_auth_user_id_from_bearer(authorization: str | None) -> str | None:
    if not authorization:
        if settings.environment.lower() == "dev":
            return None
        raise AuthError("Missing Authorization header")

    if not authorization.lower().startswith("bearer "):
        raise AuthError("Invalid Authorization header (expected Bearer token)")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise AuthError("Empty Bearer token")

    if not settings.supabase_url or not settings.supabase_anon_key:
        if settings.environment.lower() == "dev":
            return None
        raise AuthError("Supabase auth env missing (SUPABASE_URL / SUPABASE_ANON_KEY)")

    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"

    # ✅ logs Railway-friendly
    logger.info("[AUTHDBG] env=%s", settings.environment)
    logger.info("[AUTHDBG] supabase_url=%s", settings.supabase_url)
    logger.info("[AUTHDBG] anon_prefix=%s", (settings.supabase_anon_key or "")[:12])
    logger.info("[AUTHDBG] token_prefix=%s", token[:16])
    logger.info("[AUTHDBG] user_url=%s", url)

    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_anon_key,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, headers=headers)

    if r.status_code != 200:
        # ✅ log la réponse Supabase (très utile)
        logger.warning("[AUTHDBG] supabase /user failed: %s %s", r.status_code, (r.text or "")[:180])
        raise AuthError(f"Supabase auth failed: HTTP {r.status_code}")

    data = r.json()
    auth_user_id = data.get("id")
    if not auth_user_id:
        raise AuthError("Supabase auth response missing id")

    return str(auth_user_id)