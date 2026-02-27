from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str

    jwt_issuer: str = "vaultpay"
    jwt_audience: str = "vaultpay-api"
    jwt_secret: str
    jwt_ttl_seconds: int = 3600

    rate_limit_per_minute: int = 60
    replay_window_seconds: int = 300

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()