import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.route import Route


class RouteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[Route]:
        result = await self.db.execute(select(Route).where(Route.user_id == user_id))
        return list(result.scalars().all())

    async def get_by_id(self, route_id: uuid.UUID, user_id: uuid.UUID) -> Route | None:
        result = await self.db.execute(
            select(Route).where(Route.id == route_id, Route.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Route | None:
        result = await self.db.execute(select(Route).where(Route.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, slug: str, target_url: str) -> Route:
        route = Route(user_id=user_id, slug=slug, target_url=target_url)
        self.db.add(route)
        await self.db.commit()
        await self.db.refresh(route)
        return route

    async def delete(self, route: Route) -> None:
        await self.db.delete(route)
        await self.db.commit()
