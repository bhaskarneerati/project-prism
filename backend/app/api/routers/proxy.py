import time
import uuid
from datetime import datetime, timezone

import httpx
import redis.asyncio as redis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.security import hash_api_key
from app.db.models.rejected_request import RejectedRequest
from app.db.models.request_log import RequestLog
from app.db.session import async_session_factory, get_db
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.quota_repository import QuotaRepository
from app.repositories.route_repository import RouteRepository

router = APIRouter()

RATE_LIMIT_PER_MINUTE = 60
HOP_BY_HOP_HEADERS = {"host", "x-api-key", "content-length", "content-encoding", "transfer-encoding"}


async def _write_request_log(
    route_id, api_key_id, latency_ms: int, status_code: int, method: str
) -> None:
    async with async_session_factory() as db:
        log = RequestLog(
            route_id=route_id,
            api_key_id=api_key_id,
            latency_ms=latency_ms,
            status_code=status_code,
            request_method=method,
        )
        db.add(log)
        await db.commit()


async def _increment_quota_usage(user_id) -> None:
    async with async_session_factory() as db:
        quota_repo = QuotaRepository(db)
        quota = await quota_repo.get_by_user_id(user_id)
        if quota:
            await quota_repo.increment_usage(quota)


async def _forward_to_upstream(method: str, url: str, headers: dict, content: bytes):
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.request(method=method, url=url, headers=headers, content=content)


async def _log_rejection(
    db: AsyncSession, api_key_id, slug: str, reason: str, status_code: int, method: str
) -> None:
    # Written synchronously (not as a background task): FastAPI drops
    # background tasks added before an HTTPException is raised, since the
    # exception handler builds a separate response that never carries them.
    rejection = RejectedRequest(
        api_key_id=api_key_id,
        slug=slug,
        reason=reason,
        status_code=status_code,
        request_method=method,
    )
    db.add(rejection)
    await db.commit()


@router.api_route("/proxy/{slug}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(
    slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    api_key_header = request.headers.get("X-API-Key")
    if not api_key_header:
        await _log_rejection(db, None, slug, "missing_api_key", status.HTTP_401_UNAUTHORIZED, request.method)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key header")

    key_hash = hash_api_key(api_key_header)
    api_key_repo = ApiKeyRepository(db)
    api_key = await api_key_repo.get_by_hash(key_hash)
    if api_key is None or not api_key.is_active:
        rejected_key_id = api_key.id if api_key else None
        await _log_rejection(
            db, rejected_key_id, slug, "invalid_api_key", status.HTTP_401_UNAUTHORIZED, request.method
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive API key")
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        await _log_rejection(
            db, api_key.id, slug, "expired_api_key", status.HTTP_403_FORBIDDEN, request.method
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key expired")

    now = time.time()
    window_start = now - 60
    rate_limit_key = f"rate_limit:{key_hash}"
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(rate_limit_key, 0, window_start)
        pipe.zadd(rate_limit_key, {f"{now}:{uuid.uuid4()}": now})
        pipe.zcard(rate_limit_key)
        pipe.expire(rate_limit_key, 60)
        _, _, request_count, _ = await pipe.execute()
    if request_count > RATE_LIMIT_PER_MINUTE:
        await _log_rejection(
            db, api_key.id, slug, "rate_limit_exceeded", status.HTTP_429_TOO_MANY_REQUESTS, request.method
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    quota_repo = QuotaRepository(db)
    quota = await quota_repo.get_by_user_id(api_key.user_id)
    if quota and quota.current_usage >= quota.monthly_limit:
        await _log_rejection(
            db, api_key.id, slug, "quota_exceeded", status.HTTP_429_TOO_MANY_REQUESTS, request.method
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Monthly quota exceeded")

    route_repo = RouteRepository(db)
    route = await route_repo.get_by_slug(slug)
    if route is None or route.user_id != api_key.user_id:
        await _log_rejection(
            db, api_key.id, slug, "route_not_found", status.HTTP_404_NOT_FOUND, request.method
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    body = await request.body()
    forward_headers = {
        k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
    }

    start_time = time.monotonic()
    try:
        upstream_response = await _forward_to_upstream(
            request.method, route.target_url, forward_headers, body
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Upstream target timed out")
    except httpx.RequestError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to reach upstream target")
    latency_ms = int((time.monotonic() - start_time) * 1000)

    background_tasks.add_task(
        _write_request_log, route.id, api_key.id, latency_ms, upstream_response.status_code, request.method
    )
    background_tasks.add_task(_increment_quota_usage, api_key.user_id)

    response_headers = {
        k: v for k, v in upstream_response.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )
