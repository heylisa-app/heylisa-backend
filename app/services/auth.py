import httpx
from app.settings import settings


class AuthError(Exception):
    pass


async def get_auth_user_id_from_bearer(authorization: str | None) -> str | None:
    """
    Returns auth_user_id (UUID as str) from Supabase Auth /user endpoint.

    DEV behavior:
      - if ENVIRONMENT=dev and no Authorization => returns None (permissive)
    PROD behavior (later):
      - we will require Authorization
    """
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
        # In dev we tolerate; in prod we’ll enforce
        if settings.environment.lower() == "dev":
            return None
        raise AuthError("Supabase auth env missing (SUPABASE_URL / SUPABASE_ANON_KEY)")

    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_anon_key,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, headers=headers)

    if r.status_code != 200:
        raise AuthError(f"Supabase auth failed: HTTP {r.status_code}")

    data = r.json()
    auth_user_id = data.get("id")
    if not auth_user_id:
        raise AuthError("Supabase auth response missing id")

    return str(auth_user_id)