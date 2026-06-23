import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.api_key import ApiKey
from app.db.models.rejected_request import RejectedRequest
from app.db.models.request_log import RequestLog
from app.db.models.route import Route


class LogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _user_logs_query(self, user_id: uuid.UUID):
        return select(RequestLog).join(ApiKey, RequestLog.api_key_id == ApiKey.id).where(
            ApiKey.user_id == user_id
        )

    async def get_overview(self, user_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(
                func.count(RequestLog.id),
                func.avg(RequestLog.latency_ms),
                func.sum(case((RequestLog.status_code >= 400, 1), else_=0)),
            )
            .join(ApiKey, RequestLog.api_key_id == ApiKey.id)
            .where(ApiKey.user_id == user_id)
        )
        total_requests, avg_latency, error_count = result.one()
        total_requests = total_requests or 0
        error_count = error_count or 0
        error_rate = (error_count / total_requests * 100) if total_requests else 0.0
        return {
            "total_requests": total_requests,
            "avg_latency_ms": round(float(avg_latency), 2) if avg_latency else 0.0,
            "error_rate": round(error_rate, 2),
        }

    async def get_requests_over_time(self, user_id: uuid.UUID, days: int = 30) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        day_col = func.date_trunc("day", RequestLog.timestamp)
        result = await self.db.execute(
            select(day_col, func.count(RequestLog.id))
            .join(ApiKey, RequestLog.api_key_id == ApiKey.id)
            .where(ApiKey.user_id == user_id, RequestLog.timestamp >= since)
            .group_by(day_col)
            .order_by(day_col)
        )
        return [{"date": row[0].date(), "request_count": row[1]} for row in result.all()]

    async def get_top_routes(self, user_id: uuid.UUID, limit: int = 5) -> list[dict]:
        result = await self.db.execute(
            select(Route.id, Route.slug, func.count(RequestLog.id).label("request_count"))
            .join(RequestLog, RequestLog.route_id == Route.id)
            .join(ApiKey, RequestLog.api_key_id == ApiKey.id)
            .where(ApiKey.user_id == user_id)
            .group_by(Route.id, Route.slug)
            .order_by(func.count(RequestLog.id).desc())
            .limit(limit)
        )
        return [
            {"route_id": row[0], "slug": row[1], "request_count": row[2]} for row in result.all()
        ]

    async def get_rejection_breakdown(self, user_id: uuid.UUID) -> list[dict]:
        # Rejections with no api_key_id (e.g. missing X-API-Key header) have
        # no way to attribute them to a user, so they're excluded here by the join.
        result = await self.db.execute(
            select(RejectedRequest.reason, func.count(RejectedRequest.id))
            .join(ApiKey, RejectedRequest.api_key_id == ApiKey.id)
            .where(ApiKey.user_id == user_id)
            .group_by(RejectedRequest.reason)
            .order_by(func.count(RejectedRequest.id).desc())
        )
        return [{"reason": row[0], "count": row[1]} for row in result.all()]

    async def get_logs_paginated(
        self,
        user_id: uuid.UUID,
        page: int,
        page_size: int,
        route_id: uuid.UUID | None = None,
        status_code: int | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[RequestLog], int]:
        query = self._user_logs_query(user_id)
        if route_id is not None:
            query = query.where(RequestLog.route_id == route_id)
        if status_code is not None:
            query = query.where(RequestLog.status_code == status_code)
        if from_date is not None:
            query = query.where(RequestLog.timestamp >= from_date)
        if to_date is not None:
            query = query.where(RequestLog.timestamp <= to_date)

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        paginated_query = (
            query.order_by(RequestLog.timestamp.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(paginated_query)
        logs = list(result.scalars().all())
        return logs, total
