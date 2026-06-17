from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    SECRET_KEY: SecretStr
    algorithm: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    max_upload_size_bytes: int = 5*1024*1024

    posts_per_page: int = 10


settings = Settings()     # type: ignore[call-arg]  # loaded from .env file
