import logging
import time
import redis
import hashlib
from django.core.cache import cache
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _token_identifier_and_exp(token: str):
    """
    Return a (redis_key, exp_timestamp) tuple.
    - Prefer token 'jti' claim if present: key = "jwt:blacklist:jti:{jti}"
    - Otherwise fall back to SHA256(token): key = "jwt:blacklist:hash:{sha256}"
    - exp_timestamp is integer POSIX seconds or 0 if unknown.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = int(payload.get("exp", 0)) if payload.get("exp") else 0
        jti = payload.get("jti")
        if jti:
            key = f"jwt:blacklist:jti:{jti}"
            return key, exp

    except Exception as e:
        exp = 0
        logger.debug("Failed to decode token for metadata: %s", exc)

    h = hashlib.sha256(token.encode('utf-8')).hexdigest()
    key = f"jwt:blacklist:hash:{h}"
    return key, exp


def blacklist_token(token: str) -> int:
    """
    Add token to redis blacklist with TTL equal to (exp - now) if exp exists,
    otherwise use JWT_BLACKLIST_DEFAULT_TTL.
    Returns TTL set (in seconds).
    """
    key, exp = _token_identifier_and_exp(token)
    now = int(time.time())
    if exp and exp > now:
        ttl = exp - now

    try:
        redis_client.setex(key, ttl, "blacklisted")
        logger.info("Blacklisted token key=%s ttl=%s", key, ttl)
    except Exception as exc:
        logger.exception("Failed to blacklist token in Redis: %s", exc)
        raise
    return ttl

def is_token_blacklisted(token: str) -> bool:
    key, _ = _token_identifier_and_exp(token)
    try:
        exists = redis_client.exists(key) == 1
        logger.info("Checked blacklist for key=%s exists=%s", key, exists)
        return exists
    except Exception as exc:
        logger.exception("Redis error while checking blacklist: %s", exc)
        return False