"""
WhatsApp Business Cloud API sender.
All sends are async (thread) so they never block the calling thread.
Logs: recipient phone + status only — message content is never logged.
"""
import logging
import os
import threading
import time

import requests

logger = logging.getLogger(__name__)

_API_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"
_RETRY_DELAY_SECONDS = 300  # 5 minutes


def _send_once(token: str, phone_number_id: str, to: str, body: str) -> bool:
    url = _API_URL.format(phone_number_id=phone_number_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        return resp.status_code == 200
    except requests.RequestException as exc:
        logger.error("WhatsApp HTTP error to %s: %s", to, type(exc).__name__)
        return False


def _send_with_retry(token: str, phone_number_id: str, to: str, body: str,
                     message_type: str) -> None:
    success = _send_once(token, phone_number_id, to, body)
    if success:
        logger.info("WhatsApp sent ok | to=%s type=%s", to, message_type)
        return

    logger.warning("WhatsApp send failed, retrying in %ds | to=%s type=%s",
                   _RETRY_DELAY_SECONDS, to, message_type)
    time.sleep(_RETRY_DELAY_SECONDS)
    success = _send_once(token, phone_number_id, to, body)
    if success:
        logger.info("WhatsApp retry ok | to=%s type=%s", to, message_type)
    else:
        logger.error("WhatsApp retry failed, giving up | to=%s type=%s", to, message_type)


def send_whatsapp(to: str, body: str, message_type: str = "notification") -> None:
    """
    Fire-and-forget WhatsApp send. Returns immediately; send happens in background thread.
    message_type is used for logging only — never put PII here.
    """
    token = os.environ.get("WHATSAPP_TOKEN", "")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_ID", "")

    if not token or not phone_number_id:
        logger.warning("WhatsApp not configured — WHATSAPP_TOKEN or WHATSAPP_PHONE_ID missing")
        return

    if not to:
        logger.warning("send_whatsapp called with empty recipient, skipping")
        return

    t = threading.Thread(
        target=_send_with_retry,
        args=(token, phone_number_id, to, body, message_type),
        daemon=True,
    )
    t.start()
