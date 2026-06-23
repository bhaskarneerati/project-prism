import uuid

from fastapi import HTTPException, status

from app.db.models.route import Route
from app.repositories.route_repository import RouteRepository


class RouteService:
    def __init__(self, route_repo: RouteRepository):
        self.route_repo = route_repo

    async def create_route(self, user_id: uuid.UUID, slug: str, target_url: str) -> Route:
        existing = await self.route_repo.get_by_slug(slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already in use"
            )
        return await self.route_repo.create(user_id=user_id, slug=slug, target_url=target_url)

    async def list_routes(self, user_id: uuid.UUID) -> list[Route]:
        return await self.route_repo.get_by_user_id(user_id)

    async def delete_route(self, user_id: uuid.UUID, route_id: uuid.UUID) -> None:
        route = await self.route_repo.get_by_id(route_id, user_id)
        if route is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
        await self.route_repo.delete(route)
