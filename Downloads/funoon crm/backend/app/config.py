from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379"

    admin_username: str
    admin_password_hash: str
    jwt_secret: str
    jwt_expire_days: int = 7

    anthropic_api_key: str

    meta_phone_number_id: str = ""
    meta_access_token: str = ""
    farzeel_whatsapp: str = ""

    environment: str = "development"
    frontend_url: str = "http://localhost:5173"

    standup_enabled: bool = True
    standup_hour: int = 9
    standup_minute: int = 0

    telegram_bot_token: str = ""
    telegram_allowed_chat_id: str = ""  # your personal chat ID — only you can use the bot


settings = Settings()
