import asyncio

from app.cache.redis_client import RedisCache
from app.main import app
from fastapi.testclient import TestClient


class FakeRedisClient:
    def __init__(self):
        self.values = {}
        self.closed = False

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex):
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)

    async def ping(self):
        return True

    async def aclose(self):
        self.closed = True


def test_request_id_is_preserved_or_generated():
    client = TestClient(app)
    supplied = client.get("/health/live", headers={"X-Request-ID": "request-123"})
    assert supplied.status_code == 200
    assert supplied.headers["X-Request-ID"] == "request-123"

    generated = client.get("/health/live")
    assert generated.status_code == 200
    assert generated.headers["X-Request-ID"]


def test_redis_cache_round_trip(monkeypatch):
    fake = FakeRedisClient()
    monkeypatch.setattr(
        "app.cache.redis_client.Redis.from_url",
        lambda url, decode_responses=True: fake,
    )
    cache = RedisCache()

    async def exercise():
        await cache.set_json("product:1", {"id": 1, "sku": "SKU-1"})
        assert await cache.get_json("product:1") == {"id": 1, "sku": "SKU-1"}
        await cache.delete("product:1")
        assert await cache.get_json("product:1") is None
        assert await cache.ping() is True
        await cache.close()

    asyncio.run(exercise())
    assert fake.closed is True


def test_readiness_reports_dependency_failure(monkeypatch):
    import app.api.health as health

    class BrokenSession:
        def execute(self, query):
            raise RuntimeError("database down")

        def close(self):
            pass

    class BrokenRedis:
        @classmethod
        def from_url(cls, url):
            return cls()

        async def ping(self):
            raise RuntimeError("redis down")

        async def aclose(self):
            pass

    async def broken_rabbitmq(url):
        raise RuntimeError("rabbitmq down")

    monkeypatch.setattr(health, "SessionLocal", lambda: BrokenSession())
    monkeypatch.setattr(health, "Redis", BrokenRedis)
    monkeypatch.setattr(health.aio_pika, "connect_robust", broken_rabbitmq)

    response = TestClient(app).get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "checks": {
            "database": "down",
            "redis": "down",
            "rabbitmq": "down",
        },
    }
