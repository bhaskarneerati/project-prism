import uuid

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    request_count: int


class AdminResetPasswordRequest(BaseModel):
    new_password: str
