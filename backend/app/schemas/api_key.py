import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateApiKeyRequest(BaseModel):
    name: str
    expires_at: datetime | None = None


class UpdateApiKeyRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    expires_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str
