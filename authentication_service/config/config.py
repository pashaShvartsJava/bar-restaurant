from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    jwt_algorithm: str
    jwt_access_token_expire_minutes: int

    jwt_private_key_path: str
    jwt_public_key_path: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()