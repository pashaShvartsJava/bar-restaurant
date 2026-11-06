import stripe
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_algorithm: str
    jwt_public_key_path: str
    internal_token: str

    stripe_secret_key_subscriptions: str
    stripe_webhook_secret_subscriptions: str

    STRIPE_CONNECT_WEBHOOK_SECRET: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
stripe.api_key = settings.stripe_secret_key_subscriptions