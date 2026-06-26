import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.db.session import get_db
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import (
    AdminLoginRequest,
    AdminResetPasswordRequest,
    AdminTokenResponse,
    AdminUserResponse,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(payload: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    service = AdminService(AdminRepository(db))
    token = service.login(payload.email, payload.password)
    return AdminTokenResponse(access_token=token)


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    _admin: str = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    service = AdminService(AdminRepository(db))
    return await service.list_users()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    _admin: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(AdminRepository(db))
    await service.delete_user(user_id)


@router.patch("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(
    user_id: uuid.UUID,
    payload: AdminResetPasswordRequest,
    _admin: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(AdminRepository(db))
    await service.reset_user_password(user_id, payload.new_password)
