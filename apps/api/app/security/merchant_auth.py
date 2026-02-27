from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from ..models import MerchantKey
from .passwords import verify_password
from .signing import verify_signature
from .replay import validate_timestamp, nonce_seen

def get_merchant_secret(db: Session, key_id: str) -> tuple[int, str]:
    mk = db.query(MerchantKey).filter(MerchantKey.key_id == key_id, MerchantKey.status == "active").first()
    if not mk:
        raise HTTPException(401, "Invalid API key")

    # For demo: store secret hash with bcrypt and validate by comparing provided secret directly
    # In real systems you wouldn't send secret each call; you'd store the secret securely.
    # Here we keep it simple: use the secret as HMAC key, but validate key_id exists.
    return mk.merchant_id, mk.key_secret_hash  # we'll use hash as "secret" for demo purposes

def require_signed_merchant(request: Request, db: Session):
    """
    Enforces:
    - X-Key-Id
    - X-Timestamp (int)
    - X-Nonce
    - X-Signature (HMAC)
    """
    key_id = request.headers.get("X-Key-Id")
    ts = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")
    sig = request.headers.get("X-Signature")

    if not all([key_id, ts, nonce, sig]):
        raise HTTPException(401, "Missing merchant auth headers")

    try:
        ts_int = int(ts)
    except ValueError:
        raise HTTPException(401, "Bad timestamp")

    if not validate_timestamp(ts_int):
        raise HTTPException(401, "Stale timestamp")

    merchant_id, secret = get_merchant_secret(db, key_id)

    if nonce_seen(merchant_id, nonce):
        raise HTTPException(401, "Replay detected (nonce reused)")

    # Read raw body
    body = request.state.raw_body if hasattr(request.state, "raw_body") else b""
    ok = verify_signature(
        provided_sig=sig,
        secret=secret,
        method=request.method,
        path=request.url.path,
        ts=ts,
        nonce=nonce,
        body=body,
    )
    if not ok:
        raise HTTPException(401, "Bad signature")

    return merchant_id