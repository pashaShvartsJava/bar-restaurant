import stripe
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_algorithm: str
    jwt_public_key_path: str
    internal_token: str
    cookie_secret_key: str

    STRIPE_SECRET_KEY_SUBSCRIPTIONS: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    BASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
stripe.api_key = settings.STRIPE_SECRET_KEY_SUBSCRIPTIONS