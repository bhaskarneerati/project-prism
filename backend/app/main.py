from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth
from app.core.config import settings

app = FastAPI(title="Prism")

app.include_router(auth.router, prefix="/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
