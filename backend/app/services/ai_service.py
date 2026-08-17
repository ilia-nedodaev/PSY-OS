import hashlib
import re
from datetime import UTC, datetime

import redis.asyncio as redis

from app.config import settings

_redis: redis.Redis | None = None
_redis_unavailable = False


async def get_redis() -> redis.Redis | None:
    global _redis, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis is None:
        try:
            client = redis.from_url(settings.redis_url, decode_responses=True)
            await client.ping()
            _redis = client
        except Exception:
            _redis_unavailable = True
            return None
    return _redis


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= max_chars:
            current = f"{current}\n{paragraph}".strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks or [text[:max_chars]]


def cache_key(prefix: str, *parts: str) -> str:
    raw = ":".join(parts)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"psyos:{prefix}:{digest}"


async def check_ai_rate_limit(psychologist_id: str) -> bool:
    client = await get_redis()
    if not client:
        return True
    key = f"psyos:ai:count:{psychologist_id}:{datetime.now(UTC).date().isoformat()}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, 86400)
    return count <= settings.ai_max_requests_per_psychologist_per_day


async def get_cached_ai(key: str) -> str | None:
    client = await get_redis()
    if not client:
        return None
    return await client.get(key)


async def set_cached_ai(key: str, value: str) -> None:
    client = await get_redis()
    if not client:
        return
    ttl = settings.ai_cache_ttl_hours * 3600
    await client.setex(key, ttl, value)
