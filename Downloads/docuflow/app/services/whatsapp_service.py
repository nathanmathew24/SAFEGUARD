"""
Provider-agnostic WhatsApp service — paid add-on only.

GATE: every public function checks company.whatsapp_addon_enabled.
If the flag is False the call is a no-op (logged, not an error).

WHATSAPP_BSP_PROVIDER controls which transport is used:
  twilio    → Twilio Content API
  wati      → Wati send-template endpoint
  360dialog → 360dialog Cloud API (Meta-compatible)
  (blank)   → disabled, all calls are no-ops regardless of addon flag

To add a BSP: implement _send_<name> and register it in _PROVIDERS.
"""
from flask import current_app


class WhatsAppError(Exception):
    pass


def send_whatsapp(company, to_number: str, body: str) -> bool:
    """
    Send a WhatsApp message. Returns True if sent, False if add-on is not enabled.
    Raises WhatsAppError on provider failure.
    """
    if not company.whatsapp_addon_enabled:
        current_app.logger.debug(
            "WhatsApp add-on not enabled for company %s — skipping send", company.id
        )
        return False

    provider = current_app.config.get("WHATSAPP_BSP_PROVIDER", "").lower()
    if not provider:
        current_app.logger.warning("WHATSAPP_BSP_PROVIDER not configured — skipping send")
        return False

    sender = _PROVIDERS.get(provider)
    if sender is None:
        raise WhatsAppError(f"Unknown BSP provider: {provider!r}")

    sender(to_number, body)
    return True


def _send_twilio(to_number: str, body: str):
    import requests
    cfg = current_app.config
    api_url = cfg["WHATSAPP_API_URL"]
    resp = requests.post(
        api_url,
        data={"From": f"whatsapp:{cfg['WHATSAPP_FROM_NUMBER']}", "To": f"whatsapp:{to_number}", "Body": body},
        auth=(cfg.get("TWILIO_ACCOUNT_SID", ""), cfg["WHATSAPP_API_TOKEN"]),
        timeout=10,
    )
    if resp.status_code not in (200, 201):
        raise WhatsAppError(f"Twilio error {resp.status_code}: {resp.text}")


def _send_wati(to_number: str, body: str):
    import requests
    cfg = current_app.config
    resp = requests.post(
        f"{cfg['WHATSAPP_API_URL']}/api/v1/sendSessionMessage/{to_number}",
        json={"messageText": body},
        headers={"Authorization": f"Bearer {cfg['WHATSAPP_API_TOKEN']}"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise WhatsAppError(f"Wati error {resp.status_code}: {resp.text}")


def _send_360dialog(to_number: str, body: str):
    import requests
    cfg = current_app.config
    resp = requests.post(
        f"{cfg['WHATSAPP_API_URL']}/v1/messages",
        json={
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": body},
        },
        headers={
            "D360-API-KEY": cfg["WHATSAPP_API_TOKEN"],
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise WhatsAppError(f"360dialog error {resp.status_code}: {resp.text}")


_PROVIDERS = {
    "twilio": _send_twilio,
    "wati": _send_wati,
    "360dialog": _send_360dialog,
}
