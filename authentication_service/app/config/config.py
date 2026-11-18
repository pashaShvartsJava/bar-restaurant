from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    jwt_algorithm: str
    jwt_access_token_expire_minutes: int

    jwt_private_key_path: str
    jwt_public_key_path: str

    internal_token: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    PLATFORM_ADMIN_LOGIN: str
    PLATFORM_ADMIN_PASSWORD_HASH: str
    PLATFORM_ADMIN_KEY_HASH: str
    PLATFORM_ADMIN_JWT_SECRET: str


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()