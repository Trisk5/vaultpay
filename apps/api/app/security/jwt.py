from datetime import datetime, timedelta, timezone
from jose import jwt
from ..config import settings

ALGO = "HS256"

def create_access_token(*, sub: str, scopes: list[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": sub,
        "scopes": scopes,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.jwt_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGO)

def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[ALGO],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )