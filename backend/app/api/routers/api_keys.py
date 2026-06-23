import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.api_key_repository import ApiKeyRepository
from app.schemas.api_key import (
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    CreateApiKeyRequest,
    UpdateApiKeyRequest,
)
from app.services.api_key_service import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyResponse])
async def list_keys(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ApiKeyService(ApiKeyRepository(db))
    return await service.list_keys(current_user.id)


@router.post("", response_model=ApiKeyCreatedResponse)
async def create_key(
    payload: CreateApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ApiKeyService(ApiKeyRepository(db))
    api_key, raw_key = await service.create_key(current_user.id, payload.name)
    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )


@router.patch("/{key_id}", response_model=ApiKeyResponse)
async def update_key(
    key_id: uuid.UUID,
    payload: UpdateApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ApiKeyService(ApiKeyRepository(db))
    return await service.update_key_name(current_user.id, key_id, payload.name)


@router.delete("/{key_id}", response_model=ApiKeyResponse)
async def revoke_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ApiKeyService(ApiKeyRepository(db))
    return await service.revoke_key(current_user.id, key_id)
