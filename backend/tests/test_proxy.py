import pytest

from app.api.routers import proxy as proxy_module
from app.core.redis import get_redis
from app.main import app


class FakeRedisPipeline:
    def __init__(self, store):
        self.store = store
        self.ops = []

    def zremrangebyscore(self, key, min_, max_):
        self.ops.append(("zremrangebyscore", key, min_, max_))
        return self

    def zadd(self, key, mapping):
        self.ops.append(("zadd", key, mapping))
        return self

    def zcard(self, key):
        self.ops.append(("zcard", key))
        return self

    def expire(self, key, seconds):
        self.ops.append(("expire", key, seconds))
        return self

    async def execute(self):
        results = []
        for op in self.ops:
            kind, key = op[0], op[1]
            zset = self.store.setdefault(key, {})
            if kind == "zremrangebyscore":
                _, _, min_, max_ = op
                for member in [m for m, s in zset.items() if min_ <= s <= max_]:
                    del zset[member]
                results.append(None)
            elif kind == "zadd":
                _, _, mapping = op
                zset.update(mapping)
                results.append(len(mapping))
            elif kind == "zcard":
                results.append(len(zset))
            elif kind == "expire":
                results.append(True)
        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeRedis:
    def __init__(self):
        self.store = {}

    def pipeline(self, transaction=True):
        return FakeRedisPipeline(self.store)


class FakeHttpResponse:
    def __init__(self, status_code=200, content=b'{"ok": true}'):
        self.status_code = status_code
        self.content = content
        self.headers = {"content-type": "application/json"}


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture(autouse=True)
def override_redis(fake_redis):
    app.dependency_overrides[get_redis] = lambda: fake_redis
    yield
    app.dependency_overrides.pop(get_redis, None)


async def _create_key_and_route(client, auth_headers, slug="test-route"):
    key_response = await client.post(
        "/v1/api-keys", json={"name": "Proxy Test Key"}, headers=auth_headers
    )
    raw_key = key_response.json()["raw_key"]
    await client.post(
        "/v1/routes",
        json={"slug": slug, "target_url": "https://example.com/get"},
        headers=auth_headers,
    )
    return raw_key


async def test_proxy_missing_api_key(client):
    response = await client.get("/proxy/some-slug")
    assert response.status_code == 401


async def test_proxy_forwards_request(client, auth_headers, monkeypatch):
    raw_key = await _create_key_and_route(client, auth_headers, slug="forward-test")

    async def fake_forward(method, url, headers, content):
        return FakeHttpResponse()

    monkeypatch.setattr(proxy_module, "_forward_to_upstream", fake_forward)

    response = await client.get("/proxy/forward-test", headers={"X-API-Key": raw_key})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


async def test_proxy_unknown_route(client, auth_headers):
    raw_key = await _create_key_and_route(client, auth_headers, slug="known-route")
    response = await client.get("/proxy/unknown-route", headers={"X-API-Key": raw_key})
    assert response.status_code == 404


async def test_proxy_rate_limit(client, auth_headers, monkeypatch):
    raw_key = await _create_key_and_route(client, auth_headers, slug="rate-limit-test")

    async def fake_forward(method, url, headers, content):
        return FakeHttpResponse()

    monkeypatch.setattr(proxy_module, "_forward_to_upstream", fake_forward)
    monkeypatch.setattr(proxy_module, "RATE_LIMIT_PER_MINUTE", 3)

    statuses = []
    for _ in range(5):
        response = await client.get("/proxy/rate-limit-test", headers={"X-API-Key": raw_key})
        statuses.append(response.status_code)

    assert statuses[:3] == [200, 200, 200]
    assert statuses[3:] == [429, 429]
