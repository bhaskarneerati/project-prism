import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.route_repository import RouteRepository
from app.schemas.route import CreateRouteRequest, RouteResponse
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteResponse])
async def list_routes(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = RouteService(RouteRepository(db))
    return await service.list_routes(current_user.id)


@router.post("", response_model=RouteResponse)
async def create_route(
    payload: CreateRouteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(RouteRepository(db))
    return await service.create_route(current_user.id, payload.slug, payload.target_url)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(RouteRepository(db))
    await service.delete_route(current_user.id, route_id)
