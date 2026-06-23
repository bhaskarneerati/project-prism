import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.quota import Quota

DEFAULT_MONTHLY_LIMIT = 10_000


def _next_month_start() -> datetime:
    now = datetime.now(timezone.utc)
    if now.month == 12:
        return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


class QuotaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> Quota | None:
        result = await self.db.execute(select(Quota).where(Quota.user_id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, monthly_limit: int = DEFAULT_MONTHLY_LIMIT) -> Quota:
        quota = Quota(
            user_id=user_id,
            monthly_limit=monthly_limit,
            current_usage=0,
            reset_date=_next_month_start(),
        )
        self.db.add(quota)
        await self.db.commit()
        await self.db.refresh(quota)
        return quota

    async def increment_usage(self, quota: Quota) -> None:
        quota.current_usage += 1
        await self.db.commit()
