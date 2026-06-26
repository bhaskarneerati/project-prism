import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routers import admin, analytics, api_keys, auth, proxy, routes
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = structlog.get_logger()

app = FastAPI(title="Prism")

app.include_router(auth.router, prefix="/v1")
app.include_router(api_keys.router, prefix="/v1")
app.include_router(routes.router, prefix="/v1")
app.include_router(analytics.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")
app.include_router(proxy.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        logger.info("request_started", method=request.method, path=request.url.path)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_finished", status_code=response.status_code)
        structlog.contextvars.clear_contextvars()
        return response


app.add_middleware(RequestIDMiddleware)

@app.get("/")
async def root():
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
