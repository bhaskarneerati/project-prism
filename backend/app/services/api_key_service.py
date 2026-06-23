import uuid
from datetime import datetime

from fastapi import HTTPException, status

from app.core.security import generate_api_key
from app.db.models.api_key import ApiKey
from app.repositories.api_key_repository import ApiKeyRepository


class ApiKeyService:
    def __init__(self, api_key_repo: ApiKeyRepository):
        self.api_key_repo = api_key_repo

    async def create_key(
        self, user_id: uuid.UUID, name: str, expires_at: datetime | None = None
    ) -> tuple[ApiKey, str]:
        raw_key, key_hash = generate_api_key()
        api_key = await self.api_key_repo.create(
            user_id=user_id, name=name, key_hash=key_hash, expires_at=expires_at
        )
        return api_key, raw_key

    async def list_keys(self, user_id: uuid.UUID) -> list[ApiKey]:
        return await self.api_key_repo.get_by_user_id(user_id)

    async def update_key_name(self, user_id: uuid.UUID, key_id: uuid.UUID, name: str) -> ApiKey:
        api_key = await self.api_key_repo.get_by_id(key_id, user_id)
        if api_key is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        return await self.api_key_repo.update_name(api_key, name)

    async def revoke_key(self, user_id: uuid.UUID, key_id: uuid.UUID) -> ApiKey:
        api_key = await self.api_key_repo.get_by_id(key_id, user_id)
        if api_key is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        return await self.api_key_repo.revoke(api_key)
