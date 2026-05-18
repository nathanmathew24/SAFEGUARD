import hashlib
import hmac
import os
import re
import secrets

import structlog
from fastapi import APIRouter, Header, HTTPException, Request
from telegram import Bot, Update

from app.config import settings

router = APIRouter()
logger = structlog.get_logger()

# A random secret token we generate once and register with Telegram.
# Telegram sends it back in X-Telegram-Bot-Api-Secret-Token on every request.
# Stored in .env as TELEGRAM_WEBHOOK_SECRET.
_WEBHOOK_SECRET_KEY = "TELEGRAM_WEBHOOK_SECRET"


def _get_bot() -> Bot:
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")
    return Bot(token=settings.telegram_bot_token)


def _get_webhook_secret() -> str:
    """Read from env — generated once during /configure."""
    return os.environ.get(_WEBHOOK_SECRET_KEY, "")


def _verify_telegram_request(secret_token_header: str | None) -> bool:
    """
    Telegram sends the secret token we registered in X-Telegram-Bot-Api-Secret-Token.
    Constant-time compare to prevent timing attacks.
    """
    expected = _get_webhook_secret()
    if not expected:
        # Not configured yet — reject
        return False
    if not secret_token_header:
        return False
    return hmac.compare_digest(expected, secret_token_header)


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    """
    Receive updates from Telegram via webhook.
    Protected by a secret token that only Telegram knows.
    Any request without the correct token is silently dropped with 200
    (so attackers get no information about whether the endpoint exists).
    """
    if not _verify_telegram_request(x_telegram_bot_api_secret_token):
        # Return 200 so the caller learns nothing — just drop the request
        logger.warning("telegram_webhook_unauthorized")
        return {"ok": True}

    if not settings.telegram_bot_token:
        return {"ok": True}

    data = await request.json()
    update = Update.de_json(data, _get_bot())

    if not update.message or not update.message.text:
        return {"ok": True}

    chat_id = str(update.message.chat_id)
    text    = update.message.text.strip()

    # Double-check: only process messages from the configured chat ID
    if settings.telegram_allowed_chat_id and chat_id != settings.telegram_allowed_chat_id:
        logger.warning("telegram_unknown_chat", chat_id=chat_id)
        return {"ok": True}

    import asyncio
    asyncio.create_task(_process(chat_id, text))
    return {"ok": True}


async def _process(chat_id: str, text: str):
    from app.services.telegram_bot import handle_message, send_responses
    try:
        bot       = _get_bot()
        responses = await handle_message(text, chat_id)
        await send_responses(bot, chat_id, responses)
    except Exception as e:
        logger.error("telegram_process_failed", error=str(e))
        try:
            await _get_bot().send_message(chat_id=chat_id, text="Something went wrong. Try again.")
        except Exception:
            pass


@router.post("/set-webhook")
async def set_webhook(webhook_url: str):
    """Register webhook URL with Telegram, including the secret token."""
    bot    = _get_bot()
    secret = _get_webhook_secret()
    if not secret:
        raise HTTPException(status_code=400, detail="Run /configure first to generate the webhook secret.")
    url    = f"{webhook_url.rstrip('/')}/telegram/webhook"
    result = await bot.set_webhook(url=url, secret_token=secret)
    return {"ok": result, "webhook_url": url}


@router.get("/webhook-info")
async def webhook_info():
    bot = _get_bot()
    info = await bot.get_webhook_info()
    return {
        "url": info.url,
        "pending_updates": info.pending_update_count,
        "last_error": info.last_error_message,
    }


@router.post("/send-test")
async def send_test():
    """Send a test message to the configured chat ID."""
    if not settings.telegram_allowed_chat_id:
        raise HTTPException(status_code=400, detail="TELEGRAM_ALLOWED_CHAT_ID not set")
    bot = _get_bot()
    await bot.send_message(
        chat_id=settings.telegram_allowed_chat_id,
        text=(
            "✓ Funoon CRM bot connected.\n\n"
            "Try:\n"
            "• invoice Al Wathba 1500 for WhatsApp bot\n"
            "• new deal Kandy Cars, chatbot, 2000/month\n"
            "• status of Al Wathba\n"
            "• show overdue invoices"
        ),
    )
    return {"ok": True}


@router.post("/configure")
async def configure_telegram(token: str, chat_id: str):
    """
    Save token + chat ID to .env and generate a webhook secret.
    The secret is a random string Telegram will send back on every webhook call
    so we know the request is genuinely from Telegram.
    """
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if not os.path.exists(env_path):
        raise HTTPException(status_code=500, detail=".env file not found")

    # Generate a webhook secret (max 256 chars, alphanumeric + _ -)
    webhook_secret = secrets.token_urlsafe(32)

    with open(env_path, "r") as f:
        content = f.read()

    def _set(text, key, value):
        pattern = rf"^{key}=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, text, re.MULTILINE):
            return re.sub(pattern, replacement, text, flags=re.MULTILINE)
        return text + f"\n{replacement}"

    content = _set(content, "TELEGRAM_BOT_TOKEN",        token)
    content = _set(content, "TELEGRAM_ALLOWED_CHAT_ID",  chat_id)
    content = _set(content, _WEBHOOK_SECRET_KEY,          webhook_secret)

    with open(env_path, "w") as f:
        f.write(content)

    # Apply in-process immediately (no restart needed)
    settings.telegram_bot_token         = token
    settings.telegram_allowed_chat_id   = chat_id
    os.environ[_WEBHOOK_SECRET_KEY]     = webhook_secret

    return {"ok": True}
