# Phase 2 — Document Models
**Project:** DocFlow — UAE Document Intelligence & Payment Management System  
**Owner:** Farzeel Fazir / Funoon.ai  
**Date:** 2026-07-02  
**Status:** AWAITING APPROVAL

---

## 1. What We Are Building

Phase 2 introduces all business document models and their CRUD API endpoints. No AI extraction yet (Phase 3). The goal is a clean, audited, RBAC-enforced data layer that Phase 3 will populate via AI.

### Document types

| # | Model | Direction | Has Line Items |
|---|---|---|---|
| 1 | `Invoice` | Outbound (we issue to customer) | Yes |
| 2 | `PurchaseInvoice` | Inbound (supplier issues to us) | Yes |
| 3 | `LPO` | Outbound (we issue to supplier) | Yes |
| 4 | `Quotation` | Outbound (we issue to customer) | Yes |
| 5 | `CreditNote` | Outbound (we issue to customer) | Yes |
| 6 | `DebitNote` | Outbound (we issue to customer) | Yes |
| 7 | `DeliveryNote` | Outbound (we issue to customer) | No |
| 8 | `PDC` | Inbound (cheque received from customer) | No |
| 9 | `ReceiptVoucher` | Outbound (we issue to customer) | No |

---

## 2. Schema Design

### 2.1 Shared fields (all document models inherit via mixin)

```
id                  SERIAL PK
company_id          FK → companies (NOT NULL)
document_number     VARCHAR(50) UNIQUE per company (auto-generated)
status              ENUM(draft, confirmed, voided) DEFAULT draft
party_name          VARCHAR(255) NOT NULL
party_trn           VARCHAR(50) NULL  — UAE Tax Registration Number
document_date       DATE NOT NULL
due_date            DATE NULL
reference_number    VARCHAR(100) NULL  — external ref (e.g. customer PO no.)
notes               TEXT NULL
is_voided           BOOLEAN DEFAULT false
void_reason         TEXT NULL
voided_by           FK → users NULL
voided_at           TIMESTAMP UTC NULL
created_by          FK → users NOT NULL
created_at          TIMESTAMP UTC NOT NULL
updated_at          TIMESTAMP UTC NOT NULL
```

### 2.2 LineItem model (shared across Invoice, PurchaseInvoice, LPO, Quotation, CreditNote, DebitNote)

```
id                  SERIAL PK
document_id         INTEGER NOT NULL
document_type       VARCHAR(50) NOT NULL   — discriminator ('invoice', 'purchase_invoice', etc.)
description         VARCHAR(500) NOT NULL
quantity            INTEGER NOT NULL       — whole units (e.g. 5 boxes)
unit_price          INTEGER NOT NULL       — fils (AED × 100)
discount_amount     INTEGER DEFAULT 0      — fils
tax_rate_bp         INTEGER DEFAULT 500    — basis points (500 = 5% UAE VAT)
line_total          INTEGER NOT NULL       — fils, computed: (qty × unit_price) - discount + tax
sort_order          INTEGER DEFAULT 0
```

No FK polymorphism — discriminator column + compound index on (document_type, document_id).

### 2.3 Invoice (Sales Invoice)

```
+ invoice_type      ENUM(standard, proforma, tax_invoice) DEFAULT tax_invoice
+ subtotal_amount   INTEGER NOT NULL  — fils, sum of line totals before tax
+ tax_amount        INTEGER NOT NULL  — fils
+ total_amount      INTEGER NOT NULL  — fils
+ payment_method    ENUM(cash, bank_transfer, cheque, pdc) NULL
+ payment_status    ENUM(unpaid, partial, paid) DEFAULT unpaid
+ amount_paid       INTEGER DEFAULT 0  — fils
```

### 2.4 PurchaseInvoice (Supplier invoice received by us)

```
+ supplier_invoice_number  VARCHAR(100) NULL
+ subtotal_amount          INTEGER NOT NULL  — fils
+ tax_amount               INTEGER NOT NULL  — fils
+ total_amount             INTEGER NOT NULL  — fils
+ payment_method           ENUM(cash, bank_transfer, cheque, pdc) NULL
+ payment_status           ENUM(unpaid, partial, paid) DEFAULT unpaid
+ amount_paid              INTEGER DEFAULT 0  — fils
```

### 2.5 LPO (Local Purchase Order — we issue to supplier)

```
+ delivery_expected_date   DATE NULL
+ subtotal_amount          INTEGER NOT NULL  — fils
+ total_amount             INTEGER NOT NULL  — fils
```

### 2.6 Quotation (Proforma / quotation to customer)

```
+ valid_until              DATE NULL
+ subtotal_amount          INTEGER NOT NULL  — fils
+ tax_amount               INTEGER NOT NULL  — fils
+ total_amount             INTEGER NOT NULL  — fils
+ converted_to_invoice_id  FK → invoices NULL
```

### 2.7 CreditNote (Sales credit note to customer)

```
+ linked_invoice_id        FK → invoices NULL
+ reason                   TEXT NOT NULL
+ total_amount             INTEGER NOT NULL  — fils
```

### 2.8 DebitNote (Debit note to customer)

```
+ linked_invoice_id        FK → invoices NULL
+ reason                   TEXT NOT NULL
+ total_amount             INTEGER NOT NULL  — fils
```

### 2.9 DeliveryNote (Goods delivery / GRN)

```
+ linked_invoice_id        FK → invoices NULL
+ delivery_date            DATE NULL
+ received_by              VARCHAR(255) NULL
+ items_description        TEXT NULL  — free-form list of goods delivered
```

### 2.10 PDC (Post-Dated Cheque received from customer)

```
+ cheque_number            VARCHAR(100) NOT NULL
+ bank_name                VARCHAR(255) NOT NULL
+ cheque_date              DATE NOT NULL
+ amount                   INTEGER NOT NULL  — fils
+ submission_reminder_days INTEGER DEFAULT 3
+ pdc_status               ENUM(pending, submitted, cleared, bounced, cancelled) DEFAULT pending
+ linked_invoice_id        FK → invoices NULL
```

### 2.11 ReceiptVoucher (Payment receipt we issue to customer)

```
+ received_from            VARCHAR(255) NOT NULL
+ amount                   INTEGER NOT NULL  — fils
+ payment_method           ENUM(cash, bank_transfer, cheque) NOT NULL
+ linked_invoice_id        FK → invoices NULL
+ bank_reference           VARCHAR(100) NULL  — bank ref or cheque number
```

---

## 3. Document Number Auto-Generation

Format: `{PREFIX}-{YEAR}-{NNNN}` e.g. `INV-2026-0001`, `LPO-2026-0042`

Prefixes:
- Invoice → `INV`
- PurchaseInvoice → `PINV`
- LPO → `LPO`
- Quotation → `QTN`
- CreditNote → `CN`
- DebitNote → `DN`
- DeliveryNote → `DN-DEL` → actually `DLV`
- PDC → `PDC`
- ReceiptVoucher → `RV`

Sequence: per company, per doc type, per year. Stored as counter in a `document_sequences` table with `SELECT ... FOR UPDATE` to prevent gaps or duplicates under concurrency.

---

## 4. API Endpoints

Pattern: `POST|GET|PUT /api/{resource}` — no DELETE ever.

### 4.1 Endpoints per document type

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/invoices` | FM+ | Create invoice with line items |
| `GET` | `/api/invoices` | Viewer+ | List invoices (paginated, filterable) |
| `GET` | `/api/invoices/{id}` | Viewer+ | Get invoice with line items |
| `PUT` | `/api/invoices/{id}` | FM+ | Update draft invoice |
| `POST` | `/api/invoices/{id}/void` | FM+ | Void invoice (requires reason) |
| `POST` | `/api/invoices/{id}/confirm` | FM+ | Confirm draft → locks document |

Same pattern for: `purchase-invoices`, `lpos`, `quotations`, `credit-notes`, `debit-notes`, `delivery-notes`, `pdcs`, `receipt-vouchers`.

### 4.2 RBAC Matrix

| Action | Owner | Finance Manager | Operations Staff | Viewer |
|---|---|---|---|---|
| Create document | ✓ | ✓ | ✓ | ✗ |
| Read document | ✓ | ✓ | ✓ | ✓ |
| Update draft | ✓ | ✓ | ✓ | ✗ |
| Confirm document | ✓ | ✓ | ✗ | ✗ |
| Void document | ✓ | ✓ | ✗ | ✗ |
| Update confirmed | ✗ | ✗ | ✗ | ✗ |

Confirmed documents are immutable. Only void + re-issue is allowed.

### 4.3 Void semantics

```
POST /api/invoices/{id}/void
Body: {"reason": "Duplicate invoice"}
- Sets is_voided=true, void_reason, voided_by, voided_at
- Changes status to 'voided'
- Writes VOID audit log entry with old_values snapshot
- Returns 200 with updated document
- Cannot void an already-voided document → 409
```

---

## 5. Audit Trail

Every mutation writes to `audit_log`:

| Trigger | Action | old_values | new_values |
|---|---|---|---|
| Create | CREATE | null | full document dict (no secrets) |
| Update | UPDATE | pre-update snapshot | post-update snapshot |
| Confirm | UPDATE | {status: draft} | {status: confirmed} |
| Void | VOID | full document dict | {is_voided: true, void_reason: ...} |

Line item changes included in parent document snapshots.

---

## 6. Alembic Migration

One migration file: `002_document_models.py`

Creates tables in dependency order:
1. `document_sequences`
2. `invoices`, `purchase_invoices`, `lpos`, `quotations`
3. `credit_notes`, `debit_notes`, `delivery_notes`, `pdcs`, `receipt_vouchers`
4. `line_items`

All FKs enforced. Downgrade drops all tables + enums in reverse order.

---

## 7. Acceptance Criteria

- [ ] All 9 document models created with correct field types
- [ ] All monetary fields are INTEGER (fils) — zero floats
- [ ] All timestamps UTC
- [ ] `document_sequences` ensures no duplicate document numbers under concurrency
- [ ] No document can be deleted — only voided
- [ ] Confirmed documents cannot be updated
- [ ] RBAC enforced on all endpoints per matrix above
- [ ] Every create/update/void writes audit log entry
- [ ] Migration `002` applies and reverses cleanly
- [ ] `pytest` passes with ≥ 80% coverage on new code
- [ ] `bandit` zero HIGH findings
- [ ] `pip-audit` zero new CVEs

---

## 8. Test Plan

### `tests/test_documents.py`
| Test | What it proves |
|---|---|
| `test_create_invoice` | Invoice created with line items, document_number generated |
| `test_invoice_amounts_integer` | Total stored as INTEGER fils, never float |
| `test_duplicate_document_number_prevented` | Sequence generates unique numbers |
| `test_update_draft_invoice` | Draft invoice updatable, audit log written |
| `test_cannot_update_confirmed` | Returns 409 |
| `test_void_invoice` | is_voided=true, audit VOID entry written |
| `test_cannot_void_twice` | Returns 409 |
| `test_void_requires_reason` | Returns 422 without reason |
| `test_viewer_cannot_create` | Returns 403 |
| `test_viewer_can_read` | Returns 200 |
| `test_ops_staff_cannot_void` | Returns 403 |
| `test_finance_manager_can_confirm` | Returns 200 |
| `test_pdc_status_transitions` | pending → submitted → cleared |
| `test_quotation_convert_to_invoice` | linked invoice id set |
| `test_list_pagination` | page/per_page params work |
| `test_filter_by_status` | ?status=confirmed filters correctly |
| `test_soft_delete_not_exposed` | No DELETE endpoint exists |
| `test_audit_trail_on_create` | AuditLog entry with CREATE action |
| `test_audit_trail_on_update` | AuditLog entry with old/new values |
| `test_audit_trail_on_void` | AuditLog entry with VOID action |

---

## 9. File Structure

```
app/
  models/
    document_base.py        ← DocumentMixin (shared fields + void logic)
    document_sequence.py    ← DocumentSequence model + next_number()
    line_item.py            ← LineItem model
    invoice.py
    purchase_invoice.py
    lpo.py
    quotation.py
    credit_note.py
    debit_note.py
    delivery_note.py
    pdc.py
    receipt_voucher.py
  services/
    document_service.py     ← create/update/confirm/void logic, audit writes
  api/
    invoices.py             ← blueprint
    purchase_invoices.py
    lpos.py
    quotations.py
    credit_notes.py
    debit_notes.py
    delivery_notes.py
    pdcs.py
    receipt_vouchers.py
  schemas/                  ← NEW: request/response marshmallow-free validation
    document_schemas.py
migrations/
  versions/
    002_document_models.py
tests/
  test_documents.py
docs/plans/
  PHASE_2_DOCUMENT_MODELS.md   ← this file
```

---

## 10. What Is Out of Scope for Phase 2

- File upload / OCR — Phase 3
- AI extraction — Phase 3
- PDC reminder scheduler — Phase 4
- WhatsApp notifications — Phase 4
- PDF generation — Phase 5
- Frontend — Phase 6
