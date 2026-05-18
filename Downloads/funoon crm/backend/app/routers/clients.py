from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.client import Client, ClientNote, ClientStageHistory
from app.schemas.client import (
    ClientCreate,
    ClientDetail,
    ClientNoteCreate,
    ClientNoteOut,
    ClientOut,
    ClientStageMove,
    ClientUpdate,
)
from app.services.ai_service import complete

router = APIRouter()

VALID_STAGES = [
    "inbound", "qualifying", "proposal_sent",
    "negotiating", "closed_won", "live", "churned",
]

SYSTEM_PROMPT = """You are Funoon's internal operations assistant. Funoon is an AI automation agency based in the UAE.
Tone: direct, specific, low-word-count. No filler phrases."""


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ClientOut])
async def list_clients(
    stage: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Client).order_by(Client.updated_at.desc())
    if stage:
        q = q.where(Client.stage == stage)
    result = await db.execute(q)
    return result.scalars().all()


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(body: ClientCreate, db: AsyncSession = Depends(get_db)):
    client = Client(**body.model_dump())
    db.add(client)
    history = ClientStageHistory(client=client, from_stage=None, to_stage="inbound")
    db.add(history)
    await db.commit()
    await db.refresh(client)
    return client


# ── Get one ───────────────────────────────────────────────────────────────────

@router.get("/{client_id}", response_model=ClientDetail)
async def get_client(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .options(
            selectinload(Client.notes),
            selectinload(Client.stage_history),
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: str,
    body: ClientUpdate,
    db: AsyncSession = Depends(get_db),
):
    client = await _get_or_404(client_id, db)
    for field, value in body.model_dump(exclude_unset=True, exclude={"stage"}).items():
        setattr(client, field, value)
    client.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(client)
    return client


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: str, db: AsyncSession = Depends(get_db)):
    client = await _get_or_404(client_id, db)
    await db.delete(client)
    await db.commit()


# ── Stage move ────────────────────────────────────────────────────────────────

@router.post("/{client_id}/stage", response_model=ClientOut)
async def move_stage(
    client_id: str,
    body: ClientStageMove,
    db: AsyncSession = Depends(get_db),
):
    if body.to_stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {body.to_stage}")
    client = await _get_or_404(client_id, db)
    prev = client.stage
    client.stage = body.to_stage
    client.updated_at = datetime.now(timezone.utc)
    history = ClientStageHistory(
        client_id=client_id,
        from_stage=prev,
        to_stage=body.to_stage,
        note=body.note,
    )
    db.add(history)
    await db.commit()
    await db.refresh(client)
    return client


# ── Notes ─────────────────────────────────────────────────────────────────────

@router.post("/{client_id}/notes", response_model=ClientNoteOut, status_code=status.HTTP_201_CREATED)
async def add_note(
    client_id: str,
    body: ClientNoteCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_or_404(client_id, db)
    note = ClientNote(client_id=client_id, body=body.body)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


# ── AI: summarise notes ───────────────────────────────────────────────────────

@router.post("/{client_id}/ai/summarise", response_model=dict)
async def ai_summarise(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.notes))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client.notes:
        return {"summary": "No notes yet."}

    notes_text = "\n".join(f"- {n.body}" for n in client.notes)
    response = await complete(
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Summarise these notes about {client.name} in 3 bullet points:\n{notes_text}",
        }],
        max_tokens=256,
    )
    summary = response.content[0].text
    client.ai_context = summary
    client.ai_context_updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"summary": summary}


# ── AI: draft follow-up ───────────────────────────────────────────────────────

@router.post("/{client_id}/ai/followup", response_model=dict)
async def ai_followup(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.notes))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    context = client.ai_context or (
        "\n".join(f"- {n.body}" for n in client.notes[-5:]) if client.notes else "No notes."
    )
    response = await complete(
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Draft a WhatsApp follow-up message for {client.name} "
                f"(stage: {client.stage}, enquiry: {client.enquiry or 'unknown'}).\n"
                f"Context:\n{context}\n\n"
                "Funoon brand voice: restrained, operational, specific. "
                "No exclamation marks. No buzzwords. Short sentences. Under 80 words."
            ),
        }],
        max_tokens=200,
    )
    return {"message": response.content[0].text}


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_or_404(client_id: str, db: AsyncSession) -> Client:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
