from flask import Flask
from dotenv import load_dotenv

from app.extensions import db, migrate, bcrypt, limiter
from config import get_config


def create_app(config_object=None):
    load_dotenv()

    app = Flask(__name__)

    if config_object is None:
        app.config.from_object(get_config())
    else:
        app.config.from_object(config_object)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    limiter.init_app(app)

    # Import models so Alembic/migrate detects them
    with app.app_context():
        from app.models import company, user, refresh_token, audit_log  # noqa: F401

    # Blueprints
    from app.api.health import health_bp
    from app.api.auth import auth_bp
    from app.api.audit import audit_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(audit_bp, url_prefix="/api")

    # Global error handlers — never expose internals
    from app.utils.errors import register_error_handlers

    register_error_handlers(app)

    return app
