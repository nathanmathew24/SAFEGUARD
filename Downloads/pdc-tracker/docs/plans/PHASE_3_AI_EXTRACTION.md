# Phase 3 — AI Extraction Agent
**Project:** DocFlow — UAE Document Intelligence & Payment Management System
**Owner:** Farzeel Fazir / Funoon.ai
**Date:** 2026-07-02
**Status:** AWAITING APPROVAL

---

## 1. What We Are Building

Phase 3 wires the AI document pipeline. A user uploads a photo, scan, or PDF of a business
document; the system classifies it, extracts all fields via Claude, scores confidence per
field, and either auto-creates the Phase 2 record or routes it to a human review queue.

**No manual data entry required for inbound documents.**

---

## 2. End-to-End Flow

```
POST /api/upload  (multipart/form-data)
  → validate MIME type, extension, size (10MB max)
  → store file encrypted at rest (AES-256, Fernet)
  → return { upload_id, filename, size }

POST /api/extractions  (trigger extraction on an uploaded file)
  → load file, decrypt
  → pre-process: PDF → text via pdfplumber; image → OCR via pytesseract
  → sanitize extracted text (strip null bytes, limit length)
  → classifier agent: call Claude → identify document type
  → extractor agent: call Claude with type-specific schema → fields + confidence scores
  → validate extracted fields (required fields, numeric amounts, date formats)
  → if ALL critical fields confidence >= 0.85:
       auto-create Phase 2 document record → return { document_id, status: "created" }
  → else:
       create ExtractionReview record → return { review_id, status: "pending_review",
         low_confidence_fields: [...] }

GET  /api/extractions/pending        (Finance Manager+ — human review queue)
GET  /api/extractions/{id}           (Finance Manager+ — see extracted fields + confidence)
POST /api/extractions/{id}/approve   (Finance Manager+ — confirm/correct fields, create doc)
POST /api/extractions/{id}/reject    (Finance Manager+ — discard extraction)
```

---

## 3. New Dependencies

| Package | Version | Purpose |
|---|---|---|
| `anthropic` | `>=0.40.0` | Claude API client |
| `pdfplumber` | `>=0.11.0` | PDF text extraction (no OCR needed for text PDFs) |
| `pytesseract` | `>=0.3.13` | OCR for scanned images/PDFs |
| `Pillow` | `>=11.0.0` | Image pre-processing before OCR |
| `pdf2image` | `>=1.17.0` | Convert PDF pages to images for OCR fallback |
| `filetype` | `>=1.2.0` | MIME type detection from file bytes (not extension) |
| `cryptography` | `>=44.0.0` | AES-256 Fernet file encryption at rest |

**Note:** `pytesseract` requires Tesseract OCR binary installed on the system.
Docker image will install it via `apt-get install tesseract-ocr`.

---

## 4. New Models

### 4.1 `UploadedFile`

```
id                  SERIAL PK
company_id          FK → companies
original_filename   VARCHAR(255)
stored_filename     VARCHAR(255)   — UUID-based, no relation to original
file_size           INTEGER        — bytes
mime_type           VARCHAR(100)
storage_path        TEXT           — relative path inside uploads dir
is_encrypted        BOOLEAN DEFAULT true
uploaded_by         FK → users
uploaded_at         TIMESTAMP UTC
extraction_status   ENUM(pending, processing, completed, failed) DEFAULT pending
```

### 4.2 `ExtractionReview`

```
id                  SERIAL PK
upload_id           FK → uploaded_files
company_id          FK → companies
document_type       VARCHAR(50)    — classified type
raw_text            TEXT           — sanitized OCR/PDF text (stored for re-extraction)
extracted_fields    JSONB          — {field: {value, confidence}}
low_confidence_fields  JSONB       — list of field names with confidence < 0.85
status              ENUM(pending, approved, rejected) DEFAULT pending
reviewed_by         FK → users NULL
reviewed_at         TIMESTAMP UTC NULL
rejection_reason    TEXT NULL
created_document_id INTEGER NULL   — set when approved
created_at          TIMESTAMP UTC
updated_at          TIMESTAMP UTC
```

### 4.3 `ExtractionLog`

```
id                  SERIAL PK
upload_id           FK → uploaded_files
agent_step          VARCHAR(50)    — 'classify' | 'extract'
model_used          VARCHAR(100)   — e.g. claude-sonnet-4-6
input_tokens        INTEGER
output_tokens       INTEGER
truncated_input     TEXT           — first 500 chars only (no full financial data)
truncated_output    TEXT           — first 500 chars only
duration_ms         INTEGER
success             BOOLEAN
error_message       TEXT NULL
created_at          TIMESTAMP UTC
```

---

## 5. Agents

### 5.1 `app/agents/classifier.py`

```python
# Classifies document type from raw text
# Returns: { "document_type": "invoice", "confidence": 0.95 }
# Prompt structure:
<document_content>{sanitized_text[:3000]}</document_content>
<task>
Classify this business document. Return JSON only:
{"document_type": "invoice|purchase_invoice|lpo|quotation|credit_note|
  debit_note|delivery_note|pdc|receipt_voucher|unknown", "confidence": 0.0-1.0}
</task>
```

### 5.2 `app/agents/document_extractor.py`

```python
# Extracts fields per document type schema
# Returns: { "fields": { field: { "value": ..., "confidence": 0.0-1.0 } }, "payment_method_needed": bool }
# Prompt structure:
<document_type>{doc_type}</document_type>
<document_content>{sanitized_text[:4000]}</document_content>
<task>
Extract fields for a {doc_type}. Return JSON only per schema below.
For each field return {"value": ..., "confidence": 0.0-1.0}.
Flag uncertain fields with confidence < 0.85.
Schema: {type_schema}
</task>
```

### 5.3 `app/agents/validator.py`

```python
# Validates extracted fields without calling Claude (pure Python)
# Checks: required fields present, amounts numeric and > 0,
#         dates parseable, strings not empty
# Returns: { "valid": bool, "errors": [...] }
```

### 5.4 `app/utils/ocr.py`

```python
# Pre-processing pipeline:
# 1. PDF with text layer → pdfplumber (fast, no OCR needed)
# 2. PDF without text / image files → pdf2image → pytesseract
# 3. Sanitize: strip null bytes, normalize whitespace, limit to 8000 chars
# Returns: sanitized_text: str
```

### 5.5 `app/utils/file_store.py`

```python
# Handles upload storage:
# - save_file(file_bytes, original_name) → (stored_path, stored_name)
# - load_file(stored_path) → file_bytes
# - Fernet symmetric encryption (key from ENCRYPTION_KEY env var)
# - Files stored at: uploads/{company_id}/{uuid4}.enc
```

---

## 6. Type Schemas for Extraction

Each document type has a schema that tells the extractor which fields to extract.

```python
SCHEMAS = {
    "invoice": {
        "critical": ["party_name", "document_date", "total_amount"],
        "fields": ["party_name", "party_trn", "document_date", "due_date",
                   "invoice_type", "subtotal_amount", "tax_amount", "total_amount",
                   "reference_number", "payment_method"]
    },
    "purchase_invoice": {
        "critical": ["party_name", "document_date", "total_amount"],
        "fields": ["party_name", "party_trn", "document_date", "due_date",
                   "supplier_invoice_number", "subtotal_amount", "tax_amount",
                   "total_amount", "reference_number"]
    },
    "pdc": {
        "critical": ["party_name", "cheque_number", "cheque_date", "amount", "bank_name"],
        "fields": ["party_name", "cheque_number", "bank_name", "cheque_date", "amount"]
    },
    "lpo": {
        "critical": ["party_name", "document_date"],
        "fields": ["party_name", "document_date", "due_date", "reference_number",
                   "delivery_expected_date"]
    },
    "quotation": {
        "critical": ["party_name", "document_date", "total_amount"],
        "fields": ["party_name", "document_date", "valid_until", "total_amount",
                   "subtotal_amount", "tax_amount", "reference_number"]
    },
    "credit_note": {
        "critical": ["party_name", "document_date", "total_amount", "reason"],
        "fields": ["party_name", "document_date", "total_amount", "reason",
                   "reference_number"]
    },
    "debit_note": {
        "critical": ["party_name", "document_date", "total_amount", "reason"],
        "fields": ["party_name", "document_date", "total_amount", "reason",
                   "reference_number"]
    },
    "delivery_note": {
        "critical": ["party_name", "document_date"],
        "fields": ["party_name", "document_date", "delivery_date", "received_by",
                   "items_description", "reference_number"]
    },
    "receipt_voucher": {
        "critical": ["received_from", "document_date", "amount", "payment_method"],
        "fields": ["received_from", "document_date", "amount", "payment_method",
                   "bank_reference", "reference_number"]
    },
}
```

---

## 7. Security Rules (from CLAUDE.md)

- **Never pass raw file bytes to Claude** — only sanitized text
- **System prompt injection prevention** — user content wrapped in `<document_content>` tags, never concatenated raw
- **PII handling** — TRN numbers extracted for storage but NOT included in Claude API prompts by default; only included when the extraction schema explicitly requires it
- **Audit all Claude calls** — ExtractionLog records every call with truncated I/O
- **File validation order**: (1) size check, (2) MIME from bytes (`filetype` lib, not extension), (3) extension whitelist, (4) re-check after decrypt

---

## 8. API Endpoints

### POST /api/upload
```
Auth: JWT required, any authenticated role
Body: multipart/form-data, field "file"
Validation:
  - Size <= 10MB
  - MIME type in: application/pdf, image/png, image/jpeg, image/webp
  - Extension in: .pdf, .png, .jpg, .jpeg, .webp
Response 201: { "upload_id": 1, "filename": "invoice.pdf", "size": 204800 }
Response 422: { "error": { "code": "INVALID_FILE", "message": "..." } }
```

### POST /api/extractions
```
Auth: JWT required, Finance Manager+
Body: { "upload_id": 1, "company_id": 1 }
Response 200: { "status": "created", "document_id": 42, "document_type": "invoice" }
         OR  { "status": "pending_review", "review_id": 7,
               "document_type": "invoice",
               "low_confidence_fields": ["party_trn", "due_date"] }
Response 422: extraction or validation failed
```

### GET /api/extractions/pending
```
Auth: Finance Manager+
Query: ?company_id=1&page=1&per_page=20
Response: paginated list of ExtractionReview records
```

### GET /api/extractions/{id}
```
Auth: Finance Manager+
Response: full ExtractionReview with extracted_fields + confidences
```

### POST /api/extractions/{id}/approve
```
Auth: Finance Manager+
Body: { corrected_fields: { ... } }  — optional corrections to extracted fields
Response: { "document_id": 42 }  — creates the Phase 2 document
```

### POST /api/extractions/{id}/reject
```
Auth: Finance Manager+
Body: { "reason": "Unreadable scan" }
Response: 200
```

---

## 9. Acceptance Criteria

- [ ] Upload endpoint rejects non-whitelisted file types (422)
- [ ] Upload endpoint rejects files > 10MB (422)
- [ ] MIME type validated from file bytes, not just extension
- [ ] Files stored encrypted (Fernet AES-256)
- [ ] PDF text extraction works for text-layer PDFs (pdfplumber)
- [ ] Image OCR works for PNG/JPG (pytesseract)
- [ ] Claude classifier returns one of the 9 known document types
- [ ] Claude extractor returns fields with confidence 0.0–1.0 per field
- [ ] Critical fields with confidence >= 0.85 → auto-create document
- [ ] Any critical field with confidence < 0.85 → ExtractionReview created
- [ ] Every Claude API call logged to ExtractionLog (truncated I/O only)
- [ ] No PII passed to Claude unless schema requires it
- [ ] Human review approve/reject endpoints work with RBAC
- [ ] Approve with corrected fields creates correct Phase 2 record
- [ ] Migration 003 applies and reverses cleanly
- [ ] Tests pass with >= 80% coverage on new code
- [ ] bandit 0 HIGH, pip-audit 0 CVEs

---

## 10. Test Plan (`tests/test_extraction.py`)

| Test | What it proves |
|---|---|
| `test_upload_pdf_success` | PDF accepted, upload_id returned |
| `test_upload_image_success` | PNG accepted |
| `test_upload_rejects_exe` | .exe returns 422 |
| `test_upload_rejects_wrong_mime` | PNG with .pdf extension rejected by byte-level MIME check |
| `test_upload_rejects_oversized` | >10MB returns 422 |
| `test_upload_requires_auth` | No token → 401 |
| `test_extract_high_confidence_creates_document` | All critical fields >= 0.85 → document created |
| `test_extract_low_confidence_creates_review` | One critical field < 0.85 → review record |
| `test_extraction_logged` | ExtractionLog entry written after each Claude call |
| `test_no_raw_text_in_claude_prompt` | Sanitizer strips injection attempts |
| `test_review_queue_list` | GET /api/extractions/pending returns pending reviews |
| `test_approve_creates_document` | POST .../approve creates Phase 2 doc |
| `test_approve_with_corrections` | Corrected fields override extracted fields |
| `test_reject_review` | POST .../reject sets status=rejected |
| `test_viewer_cannot_trigger_extraction` | 403 |
| `test_ops_staff_cannot_approve` | 403 |

Claude API calls will be **mocked** in tests (no live API calls in CI).

---

## 11. File Structure

```
app/
  agents/
    classifier.py         ← document type classifier (Claude API)
    document_extractor.py ← field extractor with confidence scoring
    validator.py          ← pure-Python field validation
  models/
    uploaded_file.py
    extraction_review.py
    extraction_log.py
  services/
    extraction_service.py ← orchestrates upload→OCR→classify→extract→validate→create/review
  utils/
    ocr.py                ← PDF text extraction + image OCR pipeline
    file_store.py         ← encrypted file save/load
  api/
    upload.py             ← POST /api/upload
    extractions.py        ← extraction trigger + review queue endpoints
migrations/
  versions/
    003_extraction_models.py
tests/
  test_extraction.py
  fixtures/
    sample_invoice.pdf    ← minimal PDF for tests (generated, not real)
    sample_invoice.png    ← minimal image for tests
docs/plans/
  PHASE_3_AI_EXTRACTION.md
```

---

## 12. Out of Scope for Phase 3

- WhatsApp notifications — Phase 4
- PDF generation — Phase 5
- Frontend — Phase 6
- Batch extraction — not in any phase
