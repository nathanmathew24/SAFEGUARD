from flask import Flask
from dotenv import load_dotenv

from app.extensions import db, migrate, bcrypt, jwt, limiter
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
    jwt.init_app(app)
    limiter.init_app(app)

    # Import all models so Alembic detects them
    with app.app_context():
        import app.models  # noqa: F401

    # Blueprints
    from app.api.health import health_bp
    from app.api.auth import auth_bp
    from app.api.documents import docs_bp
    from app.api.pdc import pdc_bp
    from app.api.extraction import extraction_bp
    from app.api.anomaly import anomaly_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(pdc_bp)
    app.register_blueprint(extraction_bp)
    app.register_blueprint(anomaly_bp)

    # Global error handlers (including PermissionError → 423, ValueError → 400)
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)

    return app
