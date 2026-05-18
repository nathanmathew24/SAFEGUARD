"""
Funoon CRM Telegram Bot
Natural language interface to create invoices, deals, notes and check status.
Claude parses intent → executes CRM actions → replies with result + PDF if needed.
"""
import io
import json
import logging
import os
from datetime import date

import structlog
from telegram import Bot, Update
from telegram.constants import ParseMode

from app.config import settings

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are the Funoon CRM assistant running inside a Telegram bot.
Farzeel sends you natural language messages. Parse the intent and respond with a JSON action.

Available actions:
1. create_invoice — create an invoice and send the PDF
2. create_deal    — add a new client deal to the pipeline
3. add_note       — add a note to a client or project
4. get_status     — look up status of a client/project/financials
5. list_overdue   — list overdue invoices
6. unknown        — message doesn't match any action, reply conversationally

Respond ONLY with valid JSON in this exact format:

For create_invoice:
{
  "action": "create_invoice",
  "client_name": "Al Wathba Auto",
  "line_items": [
    {"description": "WhatsApp bot — monthly retainer", "qty": 1, "unit_price": 1500}
  ],
  "due_days": 30,
  "notes": "optional note"
}

For create_deal:
{
  "action": "create_deal",
  "company": "Client Co",
  "contact_name": "Name",
  "whatsapp": "+971...",
  "enquiry": "what they need",
  "estimated_mrr": 2000,
  "source": "referral"
}

For add_note:
{
  "action": "add_note",
  "target_type": "client",
  "target_name": "Al Wathba",
  "note": "text of note"
}

For get_status:
{
  "action": "get_status",
  "query": "original query text"
}

For list_overdue:
{
  "action": "list_overdue"
}

For unknown:
{
  "action": "unknown",
  "reply": "conversational reply text"
}

Rules:
- Extract amounts as integers in AED (no decimals)
- If client name is ambiguous, use what was given
- due_days defaults to 30 if not specified
- Be precise — never add fields not in the schema
"""


async def handle_message(text: str, chat_id: str) -> list[dict]:
    """
    Parse the message with Claude, execute the action, return list of responses.
    Each response is {"type": "text"|"document", "content": ..., "filename": ...}
    """
    from app.services.ai_service import complete
    from app.database import SessionLocal

    # Security: only respond to allowed chat ID
    if settings.telegram_allowed_chat_id and str(chat_id) != str(settings.telegram_allowed_chat_id):
        return [{"type": "text", "content": "Unauthorised."}]

    # Parse intent with Claude
    response = await complete(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
        max_tokens=512,
    )
    raw = response.content[0].text.strip()

    try:
        # Strip markdown code fences if Claude adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        action = json.loads(raw)
    except Exception:
        return [{"type": "text", "content": f"Couldn't parse that. Raw: {raw[:200]}"}]

    async with SessionLocal() as db:
        return await _execute(action, db)


async def _execute(action: dict, db) -> list[dict]:
    from sqlalchemy import select
    from app.models.client import Client, ClientNote, ClientStageHistory
    from app.models.financial import Invoice
    from app.models.project import Project
    from app.models.settings import CompanySettings

    act = action.get("action")

    # ── create_invoice ────────────────────────────────────────────────────────
    if act == "create_invoice":
        client_name = action.get("client_name", "")
        line_items  = action.get("line_items", [])
        due_days    = int(action.get("due_days", 30))
        notes       = action.get("notes")

        if not line_items:
            return [{"type": "text", "content": "No line items found. Try: 'invoice Al Wathba 1500 for WhatsApp bot'"}]

        # Find client
        client_data = None
        if client_name:
            result = await db.execute(
                select(Client).where(Client.name.ilike(f"%{client_name}%")).limit(1)
            )
            c = result.scalar_one_or_none()
            if c:
                client_data = {
                    "name": c.name,
                    "contact_name": c.contact_name,
                    "email": c.email,
                    "whatsapp": c.whatsapp,
                }

        # Get company settings
        co_result = await db.execute(select(CompanySettings).limit(1))
        co = co_result.scalar_one_or_none()

        # Auto-generate invoice number
        count_result = await db.execute(select(Invoice))
        count = len(count_result.scalars().all()) + 1
        prefix = (co.invoice_prefix if co else None) or "INV"
        inv_number = f"{prefix}-{count:04d}"

        today     = date.today()
        due_date  = date(today.year, today.month, today.day)

        # Calculate total
        subtotal = sum(int(i.get("qty", 1)) * int(i.get("unit_price", 0)) for i in line_items)
        vat_rate = int(co.vat_rate if co else 5)
        total    = subtotal + round(subtotal * vat_rate / 100)

        # Save invoice to DB
        invoice = Invoice(
            client_id   = c.id if client_data and 'c' in dir() else None,
            number      = inv_number,
            amount      = total,
            issued_date = today.isoformat(),
            due_date    = date(today.year, today.month,
                               min(today.day + due_days, 28)).isoformat(),
            status      = "draft",
            doc_type    = "invoice",
            notes       = notes,
            line_items  = line_items,
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)

        # Generate PDF
        from app.services.invoice_pdf import generate_invoice_pdf
        from app.routers.settings_router import UPLOADS_DIR

        def _ap(f):
            if not f: return None
            p = os.path.join(UPLOADS_DIR, f)
            return p if os.path.exists(p) else None

        co_data = {}
        if co:
            co_data = {
                "company_name": co.company_name, "tagline": co.tagline,
                "address_line1": co.address_line1, "address_line2": co.address_line2,
                "email": co.email, "phone": co.phone, "website": co.website,
                "bank_name": co.bank_name, "bank_account_name": co.bank_account_name,
                "bank_iban": co.bank_iban, "bank_account_number": co.bank_account_number,
                "bank_swift": co.bank_swift, "bank_currency": co.bank_currency,
                "invoice_payment_terms": co.invoice_payment_terms,
                "vat_rate": int(co.vat_rate or 5),
                "signature_path": _ap(co.signature_path),
                "stamp_path": _ap(co.stamp_path),
                "letterhead_path": _ap(co.letterhead_path),
            }

        pdf_bytes = generate_invoice_pdf(
            invoice={
                "id": invoice.id, "number": invoice.number,
                "amount": invoice.amount, "issued_date": invoice.issued_date,
                "due_date": invoice.due_date, "status": invoice.status,
                "_doc_type": "INVOICE", "notes": invoice.notes,
                "line_items": line_items,
            },
            client=client_data,
            company=co_data,
        )

        summary = (
            f"✓ Invoice {inv_number} created\n"
            f"Client: {client_name or '—'}\n"
            f"Amount: AED {total:,} (incl. {vat_rate}% VAT)\n"
            f"Status: Draft"
        )
        return [
            {"type": "text", "content": summary},
            {"type": "document", "content": pdf_bytes, "filename": f"{inv_number}.pdf"},
        ]

    # ── create_deal ───────────────────────────────────────────────────────────
    elif act == "create_deal":
        company  = action.get("company", "Unknown")
        contact  = action.get("contact_name")
        whatsapp = action.get("whatsapp")
        enquiry  = action.get("enquiry")
        mrr      = action.get("estimated_mrr")
        source   = action.get("source", "inbound")

        client = Client(
            name=company, contact_name=contact, whatsapp=whatsapp,
            enquiry=enquiry, estimated_mrr=mrr, source=source,
            stage="inbound",
        )
        db.add(client)
        history = ClientStageHistory(client=client, from_stage=None, to_stage="inbound")
        db.add(history)
        await db.commit()

        return [{"type": "text", "content":
            f"✓ Deal created: {company}\n"
            f"Stage: Inbound\n"
            f"{'Est. MRR: AED ' + str(mrr) if mrr else ''}\n"
            f"{'Enquiry: ' + enquiry if enquiry else ''}"
        }]

    # ── add_note ──────────────────────────────────────────────────────────────
    elif act == "add_note":
        target_type = action.get("target_type", "client")
        target_name = action.get("target_name", "")
        note_text   = action.get("note", "")

        if target_type == "client":
            result = await db.execute(
                select(Client).where(Client.name.ilike(f"%{target_name}%")).limit(1)
            )
            c = result.scalar_one_or_none()
            if not c:
                return [{"type": "text", "content": f"Client '{target_name}' not found."}]
            note = ClientNote(client_id=c.id, body=note_text)
            db.add(note)
            await db.commit()
            return [{"type": "text", "content": f"✓ Note added to {c.name}"}]

        elif target_type == "project":
            from app.models.project import ProjectNote
            result = await db.execute(
                select(Project).where(Project.name.ilike(f"%{target_name}%")).limit(1)
            )
            p = result.scalar_one_or_none()
            if not p:
                return [{"type": "text", "content": f"Project '{target_name}' not found."}]
            note = ProjectNote(project_id=p.id, body=note_text)
            db.add(note)
            await db.commit()
            return [{"type": "text", "content": f"✓ Note added to {p.name}"}]

        return [{"type": "text", "content": "Specify client or project name."}]

    # ── get_status ────────────────────────────────────────────────────────────
    elif act == "get_status":
        query = action.get("query", "")
        from app.services.ai_service import complete as ai_complete
        from app.models.financial import BillingRecord

        # Build a context snapshot
        clients_r  = await db.execute(select(Client).order_by(Client.updated_at.desc()).limit(20))
        projects_r = await db.execute(select(Project).order_by(Project.health).limit(20))
        billing_r  = await db.execute(select(BillingRecord).where(BillingRecord.status == "active"))
        overdue_r  = await db.execute(select(Invoice).where(Invoice.status == "overdue"))

        clients  = clients_r.scalars().all()
        projects = projects_r.scalars().all()
        mrr      = sum(b.amount for b in billing_r.scalars().all())
        overdue  = overdue_r.scalars().all()

        ctx = (
            f"Clients ({len(clients)}):\n" +
            "\n".join(f"  {c.name} | {c.stage} | AED {c.estimated_mrr or 0}" for c in clients) +
            f"\n\nProjects ({len(projects)}):\n" +
            "\n".join(f"  {p.name} | {p.health}" for p in projects) +
            f"\n\nMRR: AED {mrr}" +
            (f"\nOverdue invoices: {len(overdue)}" if overdue else "")
        )

        resp = await ai_complete(
            system="You are Funoon's CRM assistant. Answer concisely in plain text. No markdown.",
            messages=[{"role": "user", "content": f"CRM data:\n{ctx}\n\nQuestion: {query}"}],
            max_tokens=300,
        )
        return [{"type": "text", "content": resp.content[0].text}]

    # ── list_overdue ──────────────────────────────────────────────────────────
    elif act == "list_overdue":
        result  = await db.execute(select(Invoice).where(Invoice.status == "overdue"))
        invoices = result.scalars().all()
        if not invoices:
            return [{"type": "text", "content": "No overdue invoices."}]
        lines = [f"Overdue invoices ({len(invoices)}):"]
        for inv in invoices:
            lines.append(f"  {inv.number or inv.id[:8]} — AED {inv.amount:,} — due {inv.due_date or '?'}")
        return [{"type": "text", "content": "\n".join(lines)}]

    # ── unknown ───────────────────────────────────────────────────────────────
    else:
        return [{"type": "text", "content": action.get("reply", "I didn't understand that. Try: 'invoice Al Wathba 1500 for bot retainer'")}]


async def send_responses(bot: Bot, chat_id: str, responses: list[dict]) -> None:
    for r in responses:
        try:
            if r["type"] == "text":
                await bot.send_message(chat_id=chat_id, text=r["content"])
            elif r["type"] == "document":
                await bot.send_document(
                    chat_id=chat_id,
                    document=io.BytesIO(r["content"]),
                    filename=r.get("filename", "invoice.pdf"),
                    caption=r.get("caption", ""),
                )
        except Exception as e:
            logger.error("telegram_send_failed", error=str(e))
