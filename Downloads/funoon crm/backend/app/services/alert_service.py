import structlog

from app.config import settings
from app.services.whatsapp_client import send_whatsapp_message

logger = structlog.get_logger()


async def alert_farzeel(message: str) -> None:
    if not settings.farzeel_whatsapp:
        logger.warning("alert_skipped_no_number")
        return
    try:
        await send_whatsapp_message(to=settings.farzeel_whatsapp, body=message)
    except Exception as e:
        logger.error("alert_send_failed", error=str(e))
