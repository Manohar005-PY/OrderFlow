import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings


class RedisCache:
    def __init__(self, url: str = settings.REDIS_URL):
        self.client: Redis = Redis.from_url(url, decode_responses=True)

    async def get_json(self, key: str) -> Any | None:
        value = await self.client.get(key)
        return json.loads(value) if value is not None else None

    async def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await self.client.set(key, json.dumps(value), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def ping(self) -> bool:
        return bool(await self.client.ping())

    async def close(self) -> None:
        await self.client.aclose()
