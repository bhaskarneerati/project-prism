import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateRouteRequest(BaseModel):
    slug: str
    target_url: str


class RouteResponse(BaseModel):
    id: uuid.UUID
    slug: str
    target_url: str
    created_at: datetime

    class Config:
        from_attributes = True
