"""
Document type classifier agent.
Calls Claude to determine which of the 9 document types a text belongs to.
"""
import json
import time
from flask import current_app

_KNOWN_TYPES = {
    "invoice", "purchase_invoice", "lpo", "quotation",
    "credit_note", "debit_note", "delivery_note", "pdc", "receipt_voucher",
}

_SYSTEM_PROMPT = (
    "You are a UAE business document classifier. "
    "You only return valid JSON. Never include explanations outside the JSON."
)

_USER_TEMPLATE = """\
<document_content>
{text}
</document_content>
<task>
Classify this business document into exactly one category.
Return JSON only, no other text:
{{"document_type": "invoice|purchase_invoice|lpo|quotation|credit_note|debit_note|delivery_note|pdc|receipt_voucher|unknown", "confidence": 0.0}}
confidence is 0.0 to 1.0.
</task>"""


def classify(sanitized_text: str, upload_id: int) -> dict:
    """
    Returns {"document_type": str, "confidence": float}.
    Logs the call to ExtractionLog. Never raises — returns unknown on failure.
    """
    from app.models.extraction_log import ExtractionLog
    from app.extensions import db

    model = current_app.config.get("EXTRACTION_MODEL", "claude-sonnet-4-6")
    prompt = _USER_TEMPLATE.format(text=sanitized_text[:3000])

    start = time.monotonic()
    success = False
    raw_output = ""
    input_tokens = output_tokens = None
    error_msg = None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=model,
            max_tokens=256,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_output = message.content[0].text.strip()
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        result = _parse_classify_response(raw_output)
        success = True
        return result

    except Exception as exc:
        error_msg = str(exc)[:500]
        return {"document_type": "unknown", "confidence": 0.0}

    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        log = ExtractionLog(
            upload_id=upload_id,
            agent_step="classify",
            model_used=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            truncated_input=prompt[:500],
            truncated_output=raw_output[:500],
            duration_ms=duration_ms,
            success=success,
            error_message=error_msg,
        )
        db.session.add(log)
        db.session.flush()


def _parse_classify_response(raw: str) -> dict:
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    doc_type = str(data.get("document_type", "unknown")).lower()
    if doc_type not in _KNOWN_TYPES:
        doc_type = "unknown"
    confidence = float(data.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))
    return {"document_type": doc_type, "confidence": confidence}
