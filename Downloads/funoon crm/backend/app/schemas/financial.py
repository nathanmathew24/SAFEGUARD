from datetime import datetime

from pydantic import BaseModel


# ── Billing ───────────────────────────────────────────────────────────────────

class BillingRecordOut(BaseModel):
    id: str
    client_id: str
    client_name: str | None = None
    amount: int
    cycle: str
    status: str
    started_at: str | None
    ended_at: str | None
    notes: str | None = None

    model_config = {"from_attributes": True}


class BillingRecordCreate(BaseModel):
    client_id: str
    amount: int
    cycle: str = "monthly"
    status: str = "active"
    started_at: str | None = None
    ended_at: str | None = None
    notes: str | None = None


class BillingRecordUpdate(BaseModel):
    amount: int | None = None
    cycle: str | None = None
    status: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    notes: str | None = None


# ── Invoices ──────────────────────────────────────────────────────────────────

class LineItem(BaseModel):
    description: str
    qty: int = 1
    unit_price: int


class InvoiceOut(BaseModel):
    id: str
    client_id: str | None
    client_name: str | None = None
    number: str | None
    amount: int
    issued_date: str | None
    due_date: str | None
    paid_date: str | None = None
    status: str
    doc_type: str = "invoice"
    notes: str | None
    line_items: list[LineItem] | None = None

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    client_id: str | None = None
    number: str | None = None
    amount: int
    issued_date: str | None = None
    due_date: str | None = None
    status: str = "draft"
    doc_type: str = "invoice"   # invoice | receipt | quote
    notes: str | None = None
    line_items: list[LineItem] | None = None


class InvoiceUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    number: str | None = None
    due_date: str | None = None
    issued_date: str | None = None
    paid_date: str | None = None
    line_items: list[LineItem] | None = None


# ── Infra costs ───────────────────────────────────────────────────────────────

class InfraCostOut(BaseModel):
    id: str
    project_id: str | None
    service: str
    amount: int
    month: str
    notes: str | None

    model_config = {"from_attributes": True}


class InfraCostCreate(BaseModel):
    project_id: str | None = None
    service: str
    amount: int
    month: str
    notes: str | None = None


# ── Expenses ──────────────────────────────────────────────────────────────────

class ExpenseOut(BaseModel):
    id: str
    category: str
    description: str
    amount: int
    month: str
    recurring: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseCreate(BaseModel):
    category: str
    description: str
    amount: int
    month: str
    recurring: bool = False
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    category: str | None = None
    description: str | None = None
    amount: int | None = None
    month: str | None = None
    recurring: bool | None = None
    notes: str | None = None


# ── Summaries ─────────────────────────────────────────────────────────────────

class FinancialSummary(BaseModel):
    mrr: int
    arr: int
    infra_cost_month: int
    expense_total_month: int
    total_cost_month: int
    net_margin_month: int
    revenue_at_risk: int
    revenue_collected_month: int


class PLRow(BaseModel):
    month: str
    revenue: int
    infra_cost: int
    expenses: int
    total_cost: int
    net: int


class PLSummary(BaseModel):
    rows: list[PLRow]
