from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.financial import BillingRecord, Expense, InfraCost, Invoice
from app.schemas.financial import (
    BillingRecordCreate,
    BillingRecordOut,
    BillingRecordUpdate,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    FinancialSummary,
    InfraCostCreate,
    InfraCostOut,
    InvoiceCreate,
    InvoiceOut,
    InvoiceUpdate,
    PLSummary,
)

router = APIRouter()


# ── Financial summary ─────────────────────────────────────────────────────────

@router.get("/summary", response_model=FinancialSummary)
async def financial_summary(db: AsyncSession = Depends(get_db)):
    active = await db.execute(select(BillingRecord).where(BillingRecord.status == "active"))
    mrr = sum(b.amount for b in active.scalars().all())

    at_risk = await db.execute(
        select(BillingRecord).where(BillingRecord.status.in_(["churned", "paused"]))
    )
    revenue_at_risk = sum(b.amount for b in at_risk.scalars().all())

    today = date.today()
    month_start = today.replace(day=1).isoformat()

    costs = await db.execute(select(InfraCost).where(InfraCost.month == month_start))
    infra_cost_month = sum(c.amount for c in costs.scalars().all())

    expenses = await db.execute(select(Expense).where(Expense.month == month_start))
    expense_total_month = sum(e.amount for e in expenses.scalars().all())

    invoices_paid = await db.execute(
        select(Invoice).where(
            Invoice.status == "paid",
            Invoice.paid_date >= month_start,
        )
    )
    revenue_collected_month = sum(i.amount for i in invoices_paid.scalars().all())

    return FinancialSummary(
        mrr=mrr,
        arr=mrr * 12,
        infra_cost_month=infra_cost_month,
        expense_total_month=expense_total_month,
        total_cost_month=infra_cost_month + expense_total_month,
        net_margin_month=mrr - infra_cost_month - expense_total_month,
        revenue_at_risk=revenue_at_risk,
        revenue_collected_month=revenue_collected_month,
    )


# ── P&L summary ───────────────────────────────────────────────────────────────

@router.get("/pl", response_model=PLSummary)
async def pl_summary(months: int = 6, db: AsyncSession = Depends(get_db)):
    """Returns month-by-month P&L for the last N months."""
    today = date.today()
    rows = []

    for i in range(months - 1, -1, -1):
        # Calculate month
        month_num = today.month - i
        year = today.year
        while month_num <= 0:
            month_num += 12
            year -= 1
        month_str = f"{year}-{month_num:02d}-01"
        label = f"{year}-{month_num:02d}"

        infra_r = await db.execute(select(InfraCost).where(InfraCost.month == month_str))
        infra = sum(c.amount for c in infra_r.scalars().all())

        exp_r = await db.execute(select(Expense).where(Expense.month == month_str))
        exp = sum(e.amount for e in exp_r.scalars().all())

        inv_r = await db.execute(
            select(Invoice).where(Invoice.status == "paid", Invoice.paid_date >= month_str,
                                  Invoice.paid_date < f"{year}-{month_num:02d}-32")
        )
        revenue = sum(inv.amount for inv in inv_r.scalars().all())

        rows.append({
            "month": label,
            "revenue": revenue,
            "infra_cost": infra,
            "expenses": exp,
            "total_cost": infra + exp,
            "net": revenue - infra - exp,
        })

    return PLSummary(rows=rows)


# ── Monthly revenue history ────────────────────────────────────────────────────

@router.get("/revenue-history")
async def revenue_history(months: int = 12, db: AsyncSession = Depends(get_db)):
    today = date.today()
    result = []
    for i in range(months - 1, -1, -1):
        month_num = today.month - i
        year = today.year
        while month_num <= 0:
            month_num += 12
            year -= 1
        month_str = f"{year}-{month_num:02d}-01"
        label = f"{year}-{month_num:02d}"

        inv_r = await db.execute(
            select(Invoice).where(Invoice.status == "paid", Invoice.paid_date >= month_str,
                                  Invoice.paid_date < f"{year}-{month_num:02d}-32")
        )
        revenue = sum(inv.amount for inv in inv_r.scalars().all())
        result.append({"month": label, "revenue": revenue})
    return result


# ── Per-project margin ─────────────────────────────────────────────────────────

@router.get("/project-margins")
async def project_margins(db: AsyncSession = Depends(get_db)):
    from app.models.client import Client
    from app.models.project import Project

    projects = (await db.execute(select(Project))).scalars().all()
    today = date.today()
    month_str = today.replace(day=1).isoformat()

    margins = []
    for p in projects:
        infra_r = await db.execute(
            select(InfraCost).where(InfraCost.project_id == p.id, InfraCost.month == month_str)
        )
        infra = sum(c.amount for c in infra_r.scalars().all())

        mrr = 0
        if p.client_id:
            billing_r = await db.execute(
                select(BillingRecord).where(
                    BillingRecord.client_id == p.client_id,
                    BillingRecord.status == "active",
                )
            )
            mrr = sum(b.amount for b in billing_r.scalars().all())

        margins.append({
            "project_id": p.id,
            "project_name": p.name,
            "mrr": mrr,
            "infra_cost": infra,
            "margin": mrr - infra,
            "margin_pct": round((mrr - infra) / mrr * 100, 1) if mrr else 0,
        })

    return sorted(margins, key=lambda x: x["margin"], reverse=True)


# ── Billing records ───────────────────────────────────────────────────────────

@router.get("/billing", response_model=list[BillingRecordOut])
async def list_billing(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BillingRecord)
        .options(selectinload(BillingRecord.client))
        .order_by(BillingRecord.status, BillingRecord.amount.desc())
    )
    records = result.scalars().all()
    out = []
    for r in records:
        d = BillingRecordOut.model_validate(r)
        d.client_name = r.client.name if r.client else None
        out.append(d)
    return out


@router.post("/billing", response_model=BillingRecordOut, status_code=status.HTTP_201_CREATED)
async def create_billing(body: BillingRecordCreate, db: AsyncSession = Depends(get_db)):
    record = BillingRecord(**body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.patch("/billing/{record_id}", response_model=BillingRecordOut)
async def update_billing(record_id: str, body: BillingRecordUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BillingRecord).where(BillingRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Billing record not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/billing/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing(record_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BillingRecord).where(BillingRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Billing record not found")
    await db.delete(record)
    await db.commit()


# ── Invoices ──────────────────────────────────────────────────────────────────

@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.client))
        .order_by(Invoice.due_date.asc())
    )
    out = []
    for inv in result.scalars().all():
        d = InvoiceOut.model_validate(inv)
        d.client_name = inv.client.name if inv.client else None
        out.append(d)
    return out


@router.post("/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
async def create_invoice(body: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    invoice = Invoice(**body.model_dump())
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(invoice_id: str, body: InvoiceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Invoice).options(selectinload(Invoice.client)).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    updates = body.model_dump(exclude_unset=True)
    # Auto-set paid_date when marking paid
    if updates.get("status") == "paid" and not invoice.paid_date:
        updates["paid_date"] = date.today().isoformat()
    for field, value in updates.items():
        setattr(invoice, field, value)
    await db.commit()
    await db.refresh(invoice)
    d = InvoiceOut.model_validate(invoice)
    d.client_name = invoice.client.name if invoice.client else None
    return d


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.delete(invoice)
    await db.commit()


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Invoice).options(selectinload(Invoice.client)).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    from app.models.settings import CompanySettings
    from app.routers.settings_router import _get_or_create as _get_settings
    from app.services.invoice_pdf import generate_invoice_pdf

    company = await _get_settings(db)

    client_data = None
    if invoice.client:
        client_data = {
            "name": invoice.client.name,
            "contact_name": invoice.client.contact_name,
            "email": invoice.client.email,
            "whatsapp": invoice.client.whatsapp,
        }
    inv_data = {
        "id": invoice.id,
        "number": invoice.number,
        "amount": invoice.amount,
        "issued_date": invoice.issued_date,
        "due_date": invoice.due_date,
        "status": invoice.status,
        "doc_type": getattr(invoice, "doc_type", "invoice"),
        "_doc_type": (getattr(invoice, "doc_type", "invoice") or "invoice").upper(),
        "notes": invoice.notes,
        "line_items": invoice.line_items or [],
    }
    import os
    from app.routers.settings_router import UPLOADS_DIR

    letterhead_path = None
    if company.letterhead_path:
        full = os.path.join(UPLOADS_DIR, company.letterhead_path)
        if os.path.exists(full):
            letterhead_path = full

    def _asset_path(filename):
        if not filename:
            return None
        full = os.path.join(UPLOADS_DIR, filename)
        return full if os.path.exists(full) else None

    company_data = {
        "company_name": company.company_name,
        "signature_path": _asset_path(company.signature_path),
        "stamp_path": _asset_path(company.stamp_path),
        "address_line1": company.address_line1,
        "address_line2": company.address_line2,
        "trn": company.trn,
        "email": company.email,
        "website": company.website,
        "bank_name": company.bank_name,
        "bank_account_name": company.bank_account_name,
        "bank_iban": company.bank_iban,
        "bank_account_number": company.bank_account_number,
        "bank_swift": company.bank_swift,
        "bank_currency": company.bank_currency,
        "invoice_payment_terms": company.invoice_payment_terms,
        "vat_rate": int(company.vat_rate or "5"),
        "letterhead_path": letterhead_path,
    }
    pdf_bytes = generate_invoice_pdf(inv_data, client_data, company_data)
    filename = f"invoice-{invoice.number or invoice.id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Infra costs ───────────────────────────────────────────────────────────────

@router.get("/infra", response_model=list[InfraCostOut])
async def list_infra_costs(month: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(InfraCost).order_by(InfraCost.month.desc(), InfraCost.service)
    if month:
        q = q.where(InfraCost.month == month)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/infra", response_model=InfraCostOut, status_code=status.HTTP_201_CREATED)
async def create_infra_cost(body: InfraCostCreate, db: AsyncSession = Depends(get_db)):
    cost = InfraCost(**body.model_dump())
    db.add(cost)
    await db.commit()
    await db.refresh(cost)
    return cost


@router.delete("/infra/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_infra_cost(cost_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InfraCost).where(InfraCost.id == cost_id))
    cost = result.scalar_one_or_none()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")
    await db.delete(cost)
    await db.commit()


# ── Expenses ──────────────────────────────────────────────────────────────────

@router.get("/expenses", response_model=list[ExpenseOut])
async def list_expenses(month: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Expense).order_by(Expense.month.desc(), Expense.category)
    if month:
        q = q.where(Expense.month == month)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(body: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    expense = Expense(**body.model_dump())
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


@router.patch("/expenses/{expense_id}", response_model=ExpenseOut)
async def update_expense(expense_id: str, body: ExpenseUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    await db.commit()
    await db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()


# ── Invoice overdue check (called by scheduler) ───────────────────────────────

async def run_invoice_overdue_check(db: AsyncSession) -> list[Invoice]:
    today = date.today().isoformat()
    result = await db.execute(
        select(Invoice).where(Invoice.status == "sent", Invoice.due_date < today)
    )
    overdue = result.scalars().all()
    for inv in overdue:
        inv.status = "overdue"
    if overdue:
        await db.commit()
    return overdue
