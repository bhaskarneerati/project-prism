import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.api_key import ApiKey


class ApiKeyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[ApiKey]:
        result = await self.db.execute(select(ApiKey).where(ApiKey.user_id == user_id))
        return list(result.scalars().all())

    async def get_by_id(self, key_id: uuid.UUID, user_id: uuid.UUID) -> ApiKey | None:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self.db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, name: str, key_hash: str) -> ApiKey:
        api_key = ApiKey(user_id=user_id, name=name, key_hash=key_hash)
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def update_name(self, api_key: ApiKey, name: str) -> ApiKey:
        api_key.name = name
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def revoke(self, api_key: ApiKey) -> ApiKey:
        api_key.is_active = False
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key
