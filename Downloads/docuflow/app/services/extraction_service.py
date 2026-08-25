"""
Extraction service — runs inside a Celery task, never synchronously in a request.

Steps:
  1. Load the ExtractionJob from DB
  2. Prepare the input (text or image b64)
  3. Call Claude with a strict "return only JSON" system prompt
  4. Fuzzy-match each extracted line against the company's Product catalog
  5. Store matched_lines and set status = awaiting_confirmation
  6. Human confirmation endpoint (separate route) flips confirmed=True per line
     and then creates the real document — no auto-acceptance ever

Errors from Claude are wrapped as ExtractionError and stored on the job record.
"""
import base64
import json
from pathlib import Path

import anthropic
from rapidfuzz import process, fuzz

from app.extensions import db
from app.models.extraction_job import ExtractionJob
from app.models.product import Product


class ExtractionError(Exception):
    pass


_SYSTEM_PROMPT = """\
You are a document-line extraction assistant for a UAE trading company.
Extract line items from the input. Return ONLY valid JSON — no prose, no markdown.

Output format (JSON array):
[
  {"description": "item description", "quantity": 1.0, "unit_price": 100.0},
  ...
]

Rules:
- quantity and unit_price must be numbers (not strings)
- If you cannot determine quantity, use 1
- If you cannot determine unit_price, use 0
- Include every distinct product or service mentioned
- Return [] if no items found
"""


def run_extraction(job_id: int):
    job = db.session.get(ExtractionJob, job_id)
    if job is None:
        return

    job.status = "processing"
    db.session.commit()

    try:
        extracted = _call_claude(job)
        matched = _match_catalog(job.company_id, extracted)
        job.extracted_payload = extracted
        job.matched_lines = matched
        job.status = "awaiting_confirmation"
    except ExtractionError as exc:
        job.status = "failed"
        job.error_message = str(exc)

    db.session.commit()


def _call_claude(job: ExtractionJob) -> list:
    import os
    from flask import current_app

    api_key = current_app.config.get("ANTHROPIC_API_KEY", "")
    model = current_app.config.get("EXTRACTION_MODEL", "claude-opus-4-5-20251101")

    client = anthropic.Anthropic(api_key=api_key)

    if job.raw_input_type == "text":
        content = job.raw_input_ref or ""
        messages = [{"role": "user", "content": content}]
    else:
        # Image or PDF stored at raw_input_ref path
        file_path = Path(job.raw_input_ref or "")
        if not file_path.exists():
            raise ExtractionError(f"Input file not found: {file_path}")
        data = base64.standard_b64encode(file_path.read_bytes()).decode()
        media_type = "image/jpeg"
        if file_path.suffix.lower() == ".png":
            media_type = "image/png"
        elif file_path.suffix.lower() == ".pdf":
            media_type = "application/pdf"
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image" if "image" in media_type else "document",
                        "source": {"type": "base64", "media_type": media_type, "data": data},
                    },
                    {"type": "text", "text": "Extract all line items from this document."},
                ],
            }
        ]

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=messages,
        )
    except anthropic.APIError as exc:
        raise ExtractionError(f"Claude API error: {exc}") from exc

    raw_text = resp.content[0].text.strip()
    try:
        items = json.loads(raw_text)
        if not isinstance(items, list):
            raise ValueError("Expected a JSON array")
        return items
    except (json.JSONDecodeError, ValueError) as exc:
        raise ExtractionError(f"Claude returned non-JSON: {raw_text[:200]}") from exc


def _match_catalog(company_id: int, extracted: list) -> list:
    products = Product.query.filter_by(company_id=company_id, is_active=True).all()
    catalog = {p.id: p.name for p in products}
    catalog_names = list(catalog.values())
    catalog_ids = list(catalog.keys())

    matched = []
    for item in extracted:
        desc = str(item.get("description", ""))
        best_match = None
        best_score = 0.0
        best_product_id = None

        if catalog_names:
            result = process.extractOne(desc, catalog_names, scorer=fuzz.token_sort_ratio)
            if result:
                name, score, idx = result
                best_match = name
                best_score = score / 100.0
                best_product_id = catalog_ids[idx]

        matched.append({
            "description": desc,
            "quantity": item.get("quantity", 1),
            "unit_price": item.get("unit_price", 0),
            "matched_product_id": best_product_id,
            "matched_product_name": best_match,
            "confidence": best_score,
            "confirmed": False,   # must be set to True by a human before document creation
        })

    return matched


def confirm_job(job: ExtractionJob, confirmations: list[dict]):
    """
    Apply human confirmation to matched_lines.

    confirmations: [{"index": 0, "confirmed": true, "description": ..., "quantity": ..., "unit_price": ...}]

    Every line must be confirmed=True before the job can be used to create a document.
    There is no threshold-based auto-acceptance.
    """
    if job.status != "awaiting_confirmation":
        raise ExtractionError(f"Job {job.id} is not awaiting confirmation (status={job.status})")

    lines = list(job.matched_lines or [])
    idx_map = {c["index"]: c for c in confirmations}

    for i, line in enumerate(lines):
        conf = idx_map.get(i, {})
        line["confirmed"] = bool(conf.get("confirmed", False))
        # Allow human to override description/qty/price
        if "description" in conf:
            line["description"] = conf["description"]
        if "quantity" in conf:
            line["quantity"] = conf["quantity"]
        if "unit_price" in conf:
            line["unit_price"] = conf["unit_price"]

    unconfirmed = [i for i, l in enumerate(lines) if not l["confirmed"]]
    if unconfirmed:
        raise ExtractionError(
            f"Lines {unconfirmed} are not confirmed. Every line must be explicitly confirmed."
        )

    job.matched_lines = lines
    job.status = "confirmed"
