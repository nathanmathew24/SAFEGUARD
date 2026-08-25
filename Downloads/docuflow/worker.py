"""Celery worker entrypoint."""
from app import create_app
from celery_app import make_celery, celery as _celery

flask_app = create_app()
celery = make_celery(flask_app)

# Patch the module-level celery instance so tasks bind correctly
import celery_app as _module
_module.celery.__dict__.update(celery.__dict__)

# Import task modules so Celery discovers them
import app.tasks.extraction_tasks  # noqa: F401
import app.tasks.reminder_tasks    # noqa: F401
