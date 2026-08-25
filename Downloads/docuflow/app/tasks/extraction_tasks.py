from celery_app import celery
from app.services.extraction_service import run_extraction


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def extract_document_task(self, job_id: int):
    try:
        run_extraction(job_id)
    except Exception as exc:
        raise self.retry(exc=exc)
