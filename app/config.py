from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    database_url: str = "/app/data/crypto_prices.db"
    fetch_interval: int = 60
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = ConfigDict(env_prefix="", env_file=".env")


settings = Settings()
