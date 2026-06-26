import secrets
import uuid

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_admin_access_token, hash_password
from app.repositories.admin_repository import AdminRepository


class AdminService:
    def __init__(self, admin_repo: AdminRepository):
        self.admin_repo = admin_repo

    def login(self, email: str, password: str) -> str:
        email_matches = secrets.compare_digest(email, settings.ADMIN_EMAIL)
        password_matches = secrets.compare_digest(password, settings.ADMIN_PASSWORD)
        if not (email_matches and password_matches):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials"
            )
        return create_admin_access_token(email)

    async def list_users(self) -> list[dict]:
        return await self.admin_repo.get_users_with_request_counts()

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self.admin_repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.admin_repo.delete_user_cascade(user_id)

    async def reset_user_password(self, user_id: uuid.UUID, new_password: str) -> None:
        user = await self.admin_repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.admin_repo.set_password_hash(user, hash_password(new_password))
