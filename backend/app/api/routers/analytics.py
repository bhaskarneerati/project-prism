import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.log_repository import LogRepository
from app.schemas.analytics import (
    OverviewResponse,
    PaginatedLogsResponse,
    RejectionBreakdownEntry,
    RequestsOverTimeEntry,
    TopRouteResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = AnalyticsService(LogRepository(db))
    return await service.get_overview(current_user.id)


@router.get("/requests-over-time", response_model=list[RequestsOverTimeEntry])
async def requests_over_time(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(LogRepository(db))
    return await service.get_requests_over_time(current_user.id, days)


@router.get("/top-routes", response_model=list[TopRouteResponse])
async def top_routes(
    limit: int = Query(5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(LogRepository(db))
    return await service.get_top_routes(current_user.id, limit)


@router.get("/rejections", response_model=list[RejectionBreakdownEntry])
async def rejections(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = AnalyticsService(LogRepository(db))
    return await service.get_rejection_breakdown(current_user.id)


@router.get("/logs", response_model=PaginatedLogsResponse)
async def logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    route_id: uuid.UUID | None = None,
    status_code: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(LogRepository(db))
    log_rows, total = await service.get_logs(
        current_user.id, page, page_size, route_id, status_code, from_date, to_date
    )
    return PaginatedLogsResponse(page=page, page_size=page_size, total=total, logs=log_rows)
