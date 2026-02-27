import hashlib, hmac
from typing import Optional

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def make_canonical(method: str, path: str, ts: str, nonce: str, body_hash: str) -> str:
    return f"{method.upper()}|{path}|{ts}|{nonce}|{body_hash}"

def hmac_hex(secret: str, msg: str) -> str:
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())

def verify_signature(
    *,
    provided_sig: str,
    secret: str,
    method: str,
    path: str,
    ts: str,
    nonce: str,
    body: bytes,
) -> bool:
    body_hash = sha256_hex(body or b"")
    canonical = make_canonical(method, path, ts, nonce, body_hash)
    expected = hmac_hex(secret, canonical)
    return constant_time_eq(provided_sig, expected)