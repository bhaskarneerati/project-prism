from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    REDIS_URL: str
    JWT_SECRET: str
    JWT_EXPIRY_MINUTES: int = 1440
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    ADMIN_EMAIL: str = "admin@prism.local"
    ADMIN_PASSWORD: str = "change-this-admin-password"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
