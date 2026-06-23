import uuid
from datetime import datetime

from app.repositories.log_repository import LogRepository


class AnalyticsService:
    def __init__(self, log_repo: LogRepository):
        self.log_repo = log_repo

    async def get_overview(self, user_id: uuid.UUID) -> dict:
        return await self.log_repo.get_overview(user_id)

    async def get_requests_over_time(self, user_id: uuid.UUID, days: int = 30) -> list[dict]:
        return await self.log_repo.get_requests_over_time(user_id, days)

    async def get_top_routes(self, user_id: uuid.UUID, limit: int = 5) -> list[dict]:
        return await self.log_repo.get_top_routes(user_id, limit)

    async def get_rejection_breakdown(self, user_id: uuid.UUID) -> list[dict]:
        return await self.log_repo.get_rejection_breakdown(user_id)

    async def get_logs(
        self,
        user_id: uuid.UUID,
        page: int,
        page_size: int,
        route_id: uuid.UUID | None = None,
        status_code: int | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        logs, total = await self.log_repo.get_logs_paginated(
            user_id, page, page_size, route_id, status_code, from_date, to_date
        )
        return logs, total
