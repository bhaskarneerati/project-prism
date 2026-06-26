import uuid

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.api_key import ApiKey
from app.db.models.quota import Quota
from app.db.models.rejected_request import RejectedRequest
from app.db.models.request_log import RequestLog
from app.db.models.route import Route
from app.db.models.user import User


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_users_with_request_counts(self) -> list[dict]:
        result = await self.db.execute(
            select(User.id, User.email, func.count(RequestLog.id))
            .outerjoin(ApiKey, ApiKey.user_id == User.id)
            .outerjoin(RequestLog, RequestLog.api_key_id == ApiKey.id)
            .group_by(User.id, User.email)
            .order_by(User.email)
        )
        return [
            {"id": row[0], "email": row[1], "request_count": row[2]} for row in result.all()
        ]

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def set_password_hash(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self.db.commit()

    async def delete_user_cascade(self, user_id: uuid.UUID) -> None:
        key_ids_result = await self.db.execute(select(ApiKey.id).where(ApiKey.user_id == user_id))
        key_ids = [row[0] for row in key_ids_result.all()]

        route_ids_result = await self.db.execute(select(Route.id).where(Route.user_id == user_id))
        route_ids = [row[0] for row in route_ids_result.all()]

        await self.db.execute(
            delete(RequestLog).where(
                or_(RequestLog.api_key_id.in_(key_ids), RequestLog.route_id.in_(route_ids))
            )
        )
        await self.db.execute(
            delete(RejectedRequest).where(RejectedRequest.api_key_id.in_(key_ids))
        )
        await self.db.execute(delete(ApiKey).where(ApiKey.user_id == user_id))
        await self.db.execute(delete(Route).where(Route.user_id == user_id))
        await self.db.execute(delete(Quota).where(Quota.user_id == user_id))
        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()
