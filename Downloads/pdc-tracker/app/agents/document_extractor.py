"""
Field extraction agent.
Given sanitized document text and classified type, extracts all fields
with per-field confidence scores using Claude.
"""
import json
import time
from flask import current_app

# Critical fields — if any have confidence < threshold, route to review queue
CRITICAL_FIELDS = {
    "invoice":          ["party_name", "document_date", "total_amount"],
    "purchase_invoice": ["party_name", "document_date", "total_amount"],
    "lpo":              ["party_name", "document_date"],
    "quotation":        ["party_name", "document_date", "total_amount"],
    "credit_note":      ["party_name", "document_date", "total_amount", "reason"],
    "debit_note":       ["party_name", "document_date", "total_amount", "reason"],
    "delivery_note":    ["party_name", "document_date"],
    "pdc":              ["party_name", "cheque_number", "cheque_date", "amount", "bank_name"],
    "receipt_voucher":  ["received_from", "document_date", "amount", "payment_method"],
}

# All extractable fields per type (TRN excluded from prompts — PII)
_SCHEMAS = {
    "invoice": [
        "party_name", "document_date", "due_date", "invoice_type",
        "subtotal_amount", "tax_amount", "total_amount",
        "payment_method", "reference_number",
    ],
    "purchase_invoice": [
        "party_name", "document_date", "due_date", "supplier_invoice_number",
        "subtotal_amount", "tax_amount", "total_amount", "reference_number",
    ],
    "lpo": [
        "party_name", "document_date", "due_date", "reference_number",
        "delivery_expected_date",
    ],
    "quotation": [
        "party_name", "document_date", "valid_until",
        "subtotal_amount", "tax_amount", "total_amount", "reference_number",
    ],
    "credit_note": [
        "party_name", "document_date", "total_amount", "reason", "reference_number",
    ],
    "debit_note": [
        "party_name", "document_date", "total_amount", "reason", "reference_number",
    ],
    "delivery_note": [
        "party_name", "document_date", "delivery_date",
        "received_by", "items_description", "reference_number",
    ],
    "pdc": [
        "party_name", "cheque_number", "bank_name", "cheque_date", "amount",
    ],
    "receipt_voucher": [
        "received_from", "document_date", "amount", "payment_method", "bank_reference",
    ],
}

_SYSTEM_PROMPT = (
    "You are a UAE business document data extractor. "
    "Return only valid JSON. All monetary amounts must be in fils (integer, AED × 100). "
    "Dates must be in YYYY-MM-DD format. Never include explanations outside the JSON."
)

_USER_TEMPLATE = """\
<document_type>{doc_type}</document_type>
<document_content>
{text}
</document_content>
<task>
Extract the following fields from this {doc_type} document.
Fields to extract: {fields}
For each field return an object with "value" and "confidence" (0.0 to 1.0).
All monetary amounts must be integers in fils (multiply AED by 100).
Return JSON only:
{{"fields": {{"field_name": {{"value": ..., "confidence": 0.0}}, ...}}}}
</task>"""


def extract(sanitized_text: str, doc_type: str, upload_id: int) -> dict:
    """
    Returns {"fields": {field: {"value": ..., "confidence": float}},
             "low_confidence_fields": [field_name, ...]}.
    Logs the call. Never raises — returns empty fields on failure.
    """
    from app.models.extraction_log import ExtractionLog
    from app.extensions import db

    schema_fields = _SCHEMAS.get(doc_type, [])
    model = current_app.config.get("EXTRACTION_MODEL", "claude-sonnet-4-6")
    threshold = current_app.config.get("CONFIDENCE_THRESHOLD", 0.85)
    prompt = _USER_TEMPLATE.format(
        doc_type=doc_type,
        text=sanitized_text[:4000],
        fields=", ".join(schema_fields),
    )

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
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_output = message.content[0].text.strip()
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        fields = _parse_extract_response(raw_output, schema_fields)
        success = True

    except Exception as exc:
        error_msg = str(exc)[:500]
        fields = {}

    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        log = ExtractionLog(
            upload_id=upload_id,
            agent_step="extract",
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

    critical = CRITICAL_FIELDS.get(doc_type, [])
    low_conf = [
        f for f in critical
        if f not in fields or fields[f].get("confidence", 0.0) < threshold
    ]

    return {"fields": fields, "low_confidence_fields": low_conf}


def _parse_extract_response(raw: str, schema_fields: list) -> dict:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    fields = data.get("fields", {})
    result = {}
    for field in schema_fields:
        if field in fields:
            entry = fields[field]
            if isinstance(entry, dict):
                value = entry.get("value")
                confidence = float(entry.get("confidence", 0.0))
                confidence = max(0.0, min(1.0, confidence))
                result[field] = {"value": value, "confidence": confidence}
    return result
