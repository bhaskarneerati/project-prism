import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.api.routers.proxy as proxy_module
from app.core.config import settings
from app.db.base import Base
from app.db.models import api_key, quota, rejected_request, request_log, route, user  # noqa: F401
from app.db.session import get_db
from app.main import app

test_engine = create_async_engine(settings.TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

# Background tasks in proxy.py (request logging, quota increment) call
# async_session_factory directly instead of going through the get_db
# dependency, so FastAPI's dependency_overrides never reaches them. Patch
# the module-level reference directly so they use the test database too.
proxy_module.async_session_factory = TestSessionLocal


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def auth_headers(client):
    payload = {"email": "testuser@example.com", "password": "secret123"}
    await client.post("/v1/auth/register", json=payload)
    response = await client.post("/v1/auth/login", json=payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
