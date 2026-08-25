"""
Provider-agnostic email service.

EMAIL_PROVIDER=smtp  → uses stdlib smtplib (no extra dependency)
EMAIL_PROVIDER=postmark → uses Postmark HTTP API (requests)

Adding a provider: implement the _send_* function and add it to _PROVIDERS.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests
from flask import current_app


class EmailError(Exception):
    pass


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
):
    provider = current_app.config.get("EMAIL_PROVIDER", "smtp")
    try:
        if provider == "postmark":
            _send_postmark(to, subject, html_body, text_body)
        else:
            _send_smtp(to, subject, html_body, text_body)
    except EmailError:
        raise
    except Exception as exc:
        raise EmailError(f"Email send failed ({provider}): {exc}") from exc


def _send_smtp(to, subject, html_body, text_body):
    cfg = current_app.config
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["SMTP_FROM"]
    msg["To"] = to
    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"]) as server:
            server.starttls(context=context)
            server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            server.sendmail(cfg["SMTP_FROM"], to, msg.as_string())
    except smtplib.SMTPException as exc:
        raise EmailError(str(exc)) from exc


def _send_postmark(to, subject, html_body, text_body):
    cfg = current_app.config
    payload = {
        "From": cfg["POSTMARK_FROM"],
        "To": to,
        "Subject": subject,
        "HtmlBody": html_body,
    }
    if text_body:
        payload["TextBody"] = text_body

    resp = requests.post(
        "https://api.postmarkapp.com/email",
        json=payload,
        headers={
            "X-Postmark-Server-Token": cfg["POSTMARK_SERVER_TOKEN"],
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise EmailError(f"Postmark returned {resp.status_code}: {resp.text}")
