from ..redis_client import redis_client
from ..config import settings

def ratelimit_or_429(key: str) -> bool:
    """
    Returns True if allowed, False if limit exceeded.
    """
    bucket = f"rl:{key}"
    # fixed window per minute (simple + acceptable for portfolio)
    count = redis_client.incr(bucket)
    if count == 1:
        redis_client.expire(bucket, 60)
    return count <= settings.rate_limit_per_minute