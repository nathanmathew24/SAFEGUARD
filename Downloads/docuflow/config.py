import os
from datetime import timedelta


class Config:
    # Secrets — MUST come from environment; no fallback default reaching production
    SECRET_KEY = os.environ["SECRET_KEY"]
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]

    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://redis:6379/0")

    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "memory://")
    RATELIMIT_DEFAULT = "200 per minute"
    RATELIMIT_HEADERS_ENABLED = True

    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
    UPLOAD_MAX_BYTES = int(os.environ.get("UPLOAD_MAX_BYTES", 10 * 1024 * 1024))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Werkzeug hard cap

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    EXTRACTION_MODEL = os.environ.get("EXTRACTION_MODEL", "claude-opus-4-5-20251101")

    EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "smtp")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "DocuFlow <no-reply@example.com>")
    POSTMARK_SERVER_TOKEN = os.environ.get("POSTMARK_SERVER_TOKEN", "")
    POSTMARK_FROM = os.environ.get("POSTMARK_FROM", "DocuFlow <no-reply@example.com>")

    WHATSAPP_BSP_PROVIDER = os.environ.get("WHATSAPP_BSP_PROVIDER", "")
    WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "")
    WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
    WHATSAPP_FROM_NUMBER = os.environ.get("WHATSAPP_FROM_NUMBER", "")

    # Anomaly detection thresholds (tunable via env)
    ANOMALY_PRICE_DEVIATION_PCT = float(os.environ.get("ANOMALY_PRICE_DEVIATION_PCT", 25.0))
    ANOMALY_QTY_STDDEV_FACTOR = float(os.environ.get("ANOMALY_QTY_STDDEV_FACTOR", 3.0))
    ANOMALY_PRICE_MIN_SAMPLES = int(os.environ.get("ANOMALY_PRICE_MIN_SAMPLES", 3))
    ANOMALY_QTY_MIN_SAMPLES = int(os.environ.get("ANOMALY_QTY_MIN_SAMPLES", 5))

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    BCRYPT_LOG_ROUNDS = 12


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False

    @classmethod
    def _check_secrets(cls):
        pass  # allow placeholder values locally


class TestingConfig(Config):
    TESTING = True
    SESSION_COOKIE_SECURE = False
    BCRYPT_LOG_ROUNDS = 4
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False
    ANTHROPIC_API_KEY = "test-key-not-real"
    UPLOAD_DIR = "test_uploads"


class ProductionConfig(Config):
    DEBUG = False


_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return _map.get(env, DevelopmentConfig)
