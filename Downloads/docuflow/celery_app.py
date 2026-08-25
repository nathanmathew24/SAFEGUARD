from celery import Celery


def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        worker_prefetch_multiplier=1,
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# Module-level instance used by workers; populated by create_app
celery = Celery(__name__)
