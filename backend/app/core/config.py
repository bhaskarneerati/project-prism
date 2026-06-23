from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    REDIS_URL: str
    JWT_SECRET: str
    JWT_EXPIRY_MINUTES: int = 1440
    ENVIRONMENT: str = "development"


settings = Settings()
