
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.workspace import AIConversation, IncidentLog, SOP
from app.schemas.workspace import (
    AskAIRequest,
    AskAIResponse,
    IncidentCreate,
    IncidentOut,
    SOPCreate,
    SOPOut,
    SOPUpdate,
)
from app.services.ai_service import complete

router = APIRouter()

WORKSPACE_SYSTEM = """You are Funoon's internal operations assistant. Funoon is an AI automation agency based in the UAE, founded by Farzeel Fazir.

You have read access to the full CRM: clients, projects, finances, AI ops metrics, and the automation component library. Use the provided tools to fetch data before answering. Never make up numbers or statuses — always fetch them.

You do NOT have write access. If Farzeel asks you to do something that requires writing (send a message, update a record), draft the content or explain the steps, but make clear he needs to action it.

Tone: direct, specific, low-word-count. You sound like a sharp colleague, not a customer service bot. No filler phrases. No "Great question!" No "Certainly!". Just the answer.

If asked to draft a message (WhatsApp, email, proposal), write in Funoon's brand voice: restrained, operational, specific. No exclamation marks. No buzzwords. Short sentences.

When Farzeel asks about a project or client by name, always fetch the live data first — never answer from memory."""

# Tool definitions for Ask AI
AI_TOOLS = [
    {
        "name": "list_clients",
        "description": "List clients filtered by stage or search all. Returns name, stage, MRR, next action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "Filter by stage (optional)"},
            },
        },
    },
    {
        "name": "list_projects",
        "description": "List all projects with current health status, stack tags, and renewal dates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "health": {"type": "string", "description": "Filter by health: green, amber, red (optional)"},
            },
        },
    },
    {
        "name": "get_financial_summary",
        "description": "Get MRR, ARR, infra costs, and revenue at risk.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_overdue_invoices",
        "description": "List all invoices with overdue status.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_open_blockers",
        "description": "List all unresolved blockers across all projects.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "search_components",
        "description": "Search the automation library by name, category, or tech tag.",
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search query"},
            },
        },
    },
]


async def _execute_tool(tool_name: str, tool_input: dict, db: AsyncSession) -> str:
    from app.models.client import Client
    from app.models.financial import Invoice
    from app.models.library import Component
    from app.models.project import Project, ProjectBlocker
    from app.routers.financial import run_invoice_overdue_check

    if tool_name == "list_clients":
        q = select(Client).order_by(Client.updated_at.desc())
        if tool_input.get("stage"):
            q = q.where(Client.stage == tool_input["stage"])
        result = await db.execute(q)
        clients = result.scalars().all()
        lines = [
            f"- {c.name} | stage: {c.stage} | MRR: AED {c.estimated_mrr or 0} | next: {c.next_action or 'none'}"
            for c in clients
        ]
        return "\n".join(lines) or "No clients found."

    elif tool_name == "list_projects":
        q = select(Project).order_by(Project.health)
        if tool_input.get("health"):
            q = q.where(Project.health == tool_input["health"])
        result = await db.execute(q)
        projects = result.scalars().all()
        lines = [
            f"- {p.name} | health: {p.health} | stack: {', '.join(p.stack_tags or [])} | renewal: {p.renewal_date or 'none'}"
            for p in projects
        ]
        return "\n".join(lines) or "No projects found."

    elif tool_name == "get_financial_summary":
        from app.models.financial import BillingRecord, InfraCost
        from datetime import date
        active = await db.execute(select(BillingRecord).where(BillingRecord.status == "active"))
        mrr = sum(b.amount for b in active.scalars().all())
        today = date.today()
        costs = await db.execute(select(InfraCost).where(InfraCost.month == today.replace(day=1)))
        infra = sum(c.amount for c in costs.scalars().all())
        return f"MRR: AED {mrr} | ARR: AED {mrr * 12} | Infra cost this month: AED {infra} | Margin: AED {mrr - infra}"

    elif tool_name == "list_overdue_invoices":
        result = await db.execute(select(Invoice).where(Invoice.status == "overdue"))
        invoices = result.scalars().all()
        lines = [
            f"- Invoice {i.number or i.id} | AED {i.amount} | due: {i.due_date}"
            for i in invoices
        ]
        return "\n".join(lines) or "No overdue invoices."

    elif tool_name == "list_open_blockers":
        result = await db.execute(
            select(ProjectBlocker).where(ProjectBlocker.resolved == False)  # noqa: E712
        )
        blockers = result.scalars().all()
        lines = [
            f"- {b.body} | owner: {b.owner or 'unassigned'} | due: {b.due_date or 'no date'}"
            for b in blockers
        ]
        return "\n".join(lines) or "No open blockers."

    elif tool_name == "search_components":
        from sqlalchemy import or_
        q_str = tool_input.get("q", "")
        q = select(Component)
        if q_str:
            q = q.where(or_(
                Component.name.ilike(f"%{q_str}%"),
                Component.description.ilike(f"%{q_str}%"),
            ))
        result = await db.execute(q)
        components = result.scalars().all()
        lines = [
            f"- {c.name} [{c.category}] v{c.version or '?'} | status: {c.status} | tags: {', '.join(c.tech_tags or [])}"
            for c in components
        ]
        return "\n".join(lines) or "No components found."

    return f"Unknown tool: {tool_name}"


# ── Ask AI ─────────────────────────────────────────────────────────────────────

@router.post("/ask", response_model=AskAIResponse)
async def ask_ai(body: AskAIRequest, db: AsyncSession = Depends(get_db)):
    # Load or create conversation
    conversation: AIConversation | None = None
    if body.conversation_id:
        result = await db.execute(
            select(AIConversation).where(AIConversation.id == body.conversation_id)
        )
        conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = AIConversation(messages=[])
        db.add(conversation)
        await db.flush()

    messages: list[dict] = list(conversation.messages)
    messages.append({"role": "user", "content": body.message})

    # Agentic tool-use loop
    reply_text = ""
    for _ in range(5):  # max 5 tool rounds
        response = await complete(
            system=WORKSPACE_SYSTEM,
            messages=messages,
            tools=AI_TOOLS,
            max_tokens=1024,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    reply_text = block.text
            messages.append({"role": "assistant", "content": reply_text})
            break

        if response.stop_reason == "tool_use":
            # Append assistant's tool-use turn
            messages.append({"role": "assistant", "content": response.content})  # type: ignore[arg-type]

            # Execute each tool and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_output = await _execute_tool(block.name, block.input, db)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_output,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            break

    conversation.messages = messages
    await db.commit()

    return AskAIResponse(reply=reply_text, conversation_id=conversation.id)


# ── SOPs ──────────────────────────────────────────────────────────────────────

@router.get("/sops", response_model=list[SOPOut])
async def list_sops(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SOP).order_by(SOP.title))
    return result.scalars().all()


@router.post("/sops", response_model=SOPOut, status_code=status.HTTP_201_CREATED)
async def create_sop(body: SOPCreate, db: AsyncSession = Depends(get_db)):
    sop = SOP(**body.model_dump())
    db.add(sop)
    await db.commit()
    await db.refresh(sop)
    return sop


@router.patch("/sops/{sop_id}", response_model=SOPOut)
async def update_sop(sop_id: str, body: SOPUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SOP).where(SOP.id == sop_id))
    sop = result.scalar_one_or_none()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(sop, field, value)
    await db.commit()
    await db.refresh(sop)
    return sop


@router.delete("/sops/{sop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sop(sop_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SOP).where(SOP.id == sop_id))
    sop = result.scalar_one_or_none()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")
    await db.delete(sop)
    await db.commit()


# ── Incidents ─────────────────────────────────────────────────────────────────

@router.get("/incidents", response_model=list[IncidentOut])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentLog).order_by(IncidentLog.occurred_at.desc()))
    return result.scalars().all()


@router.post("/incidents", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(body: IncidentCreate, db: AsyncSession = Depends(get_db)):
    incident = IncidentLog(**body.model_dump())
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident


@router.patch("/incidents/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: str,
    body: IncidentCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IncidentLog).where(IncidentLog.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    await db.commit()
    await db.refresh(incident)
    return incident
