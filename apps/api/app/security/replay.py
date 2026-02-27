import time
from ..redis_client import redis_client
from ..config import settings

def validate_timestamp(ts: int) -> bool:
    now = int(time.time())
    return abs(now - ts) <= settings.replay_window_seconds

def nonce_seen(merchant_id: int, nonce: str) -> bool:
    key = f"nonce:{merchant_id}:{nonce}"
    # SETNX for replay protection
    ok = redis_client.set(key, "1", nx=True, ex=settings.replay_window_seconds)
    return ok is None  # if None => already existed