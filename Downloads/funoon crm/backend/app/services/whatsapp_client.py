import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

WA_API_URL = "https://graph.facebook.com/v19.0"


async def send_whatsapp_message(to: str, body: str) -> dict:
    if not settings.meta_phone_number_id or not settings.meta_access_token:
        raise RuntimeError("WhatsApp credentials not configured")

    url = f"{WA_API_URL}/{settings.meta_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    headers = {"Authorization": f"Bearer {settings.meta_access_token}"}

    async with httpx.AsyncClient() as http:
        resp = await http.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logger.info("whatsapp_sent", to=to)
        return resp.json()
