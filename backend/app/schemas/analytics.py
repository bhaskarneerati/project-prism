import uuid
from datetime import date, datetime

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_requests: int
    avg_latency_ms: float
    error_rate: float


class RequestsOverTimeEntry(BaseModel):
    date: date
    request_count: int


class TopRouteResponse(BaseModel):
    route_id: uuid.UUID
    slug: str
    request_count: int


class LogEntry(BaseModel):
    id: uuid.UUID
    route_id: uuid.UUID
    api_key_id: uuid.UUID
    timestamp: datetime
    latency_ms: int
    status_code: int
    request_method: str

    class Config:
        from_attributes = True


class RejectionBreakdownEntry(BaseModel):
    reason: str
    count: int


class PaginatedLogsResponse(BaseModel):
    page: int
    page_size: int
    total: int
    logs: list[LogEntry]
