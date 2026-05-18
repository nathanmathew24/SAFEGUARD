from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project import Project, ProjectBlocker, ProjectNote
from app.schemas.project import (
    BlockerCreate,
    BlockerOut,
    ProjectCreate,
    ProjectDetail,
    ProjectNoteCreate,
    ProjectNoteOut,
    ProjectOut,
    ProjectUpdate,
)
from app.services.ai_service import complete

router = APIRouter()

SYSTEM_PROMPT = """You are Funoon's internal operations assistant. Tone: direct, specific, low-word-count."""


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ProjectOut])
async def list_projects(
    health: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Project).order_by(Project.health, Project.updated_at.desc())
    if health:
        q = q.where(Project.health == health)
    result = await db.execute(q)
    return result.scalars().all()


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(**body.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


# ── Get one ───────────────────────────────────────────────────────────────────

@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.blockers), selectinload(Project.notes))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    project = await _get_or_404(project_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    project.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(project)
    return project


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await _get_or_404(project_id, db)
    await db.delete(project)
    await db.commit()


# ── Blockers ──────────────────────────────────────────────────────────────────

@router.post("/{project_id}/blockers", response_model=BlockerOut, status_code=status.HTTP_201_CREATED)
async def add_blocker(
    project_id: str,
    body: BlockerCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_or_404(project_id, db)
    blocker = ProjectBlocker(project_id=project_id, **body.model_dump())
    db.add(blocker)
    await db.commit()
    await db.refresh(blocker)
    return blocker


@router.patch("/{project_id}/blockers/{blocker_id}/resolve", response_model=BlockerOut)
async def resolve_blocker(
    project_id: str,
    blocker_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProjectBlocker).where(
            ProjectBlocker.id == blocker_id,
            ProjectBlocker.project_id == project_id,
        )
    )
    blocker = result.scalar_one_or_none()
    if not blocker:
        raise HTTPException(status_code=404, detail="Blocker not found")
    blocker.resolved = True
    blocker.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(blocker)
    return blocker


@router.delete("/{project_id}/blockers/{blocker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blocker(
    project_id: str,
    blocker_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProjectBlocker).where(
            ProjectBlocker.id == blocker_id,
            ProjectBlocker.project_id == project_id,
        )
    )
    blocker = result.scalar_one_or_none()
    if not blocker:
        raise HTTPException(status_code=404, detail="Blocker not found")
    await db.delete(blocker)
    await db.commit()


# ── Notes ─────────────────────────────────────────────────────────────────────

@router.post("/{project_id}/notes", response_model=ProjectNoteOut, status_code=status.HTTP_201_CREATED)
async def add_note(
    project_id: str,
    body: ProjectNoteCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_or_404(project_id, db)
    note = ProjectNote(project_id=project_id, body=body.body)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


# ── AI: summarise for new team member ────────────────────────────────────────

@router.post("/{project_id}/ai/summarise", response_model=dict)
async def ai_summarise(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.notes), selectinload(Project.blockers))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    notes_text = "\n".join(f"- {n.body}" for n in project.notes) or "No notes."
    blockers_text = "\n".join(
        f"- {b.body} (owner: {b.owner or 'unassigned'}, due: {b.due_date or 'no date'})"
        for b in project.blockers if not b.resolved
    ) or "No open blockers."

    response = await complete(
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Write a plain-language briefing for a new team member joining project '{project.name}'.\n"
                f"Stack: {', '.join(project.stack_tags or []) or 'unknown'}\n"
                f"Health: {project.health}\n"
                f"Notes:\n{notes_text}\n"
                f"Open blockers:\n{blockers_text}"
            ),
        }],
        max_tokens=400,
    )
    return {"summary": response.content[0].text}


# ── AI: draft client update ───────────────────────────────────────────────────

@router.post("/{project_id}/ai/client-update", response_model=dict)
async def ai_client_update(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.notes))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    recent_notes = "\n".join(f"- {n.body}" for n in project.notes[-5:]) or "No recent notes."
    response = await complete(
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Draft a WhatsApp status update for the client of project '{project.name}'.\n"
                f"Recent activity:\n{recent_notes}\n\n"
                "Funoon brand voice: restrained, operational, specific. No exclamation marks. Under 80 words."
            ),
        }],
        max_tokens=200,
    )
    return {"message": response.content[0].text}


# ── Auto-flag logic (called by scheduler) ────────────────────────────────────

async def run_auto_flag(db: AsyncSession) -> None:
    today = date.today()
    result = await db.execute(select(Project).options(selectinload(Project.blockers), selectinload(Project.notes)))
    projects = result.scalars().all()

    for project in projects:
        new_health = "green"

        # No activity in 7 days → amber
        if project.notes:
            last_note = max(n.created_at for n in project.notes)
            days_since = (datetime.now(timezone.utc) - last_note).days
            if days_since >= 7:
                new_health = "amber"

        # Open blocker past due date → amber
        for blocker in project.blockers:
            if not blocker.resolved and blocker.due_date and blocker.due_date < today:
                new_health = "amber"
                break

        # Renewal within 14 days → amber
        if project.renewal_date and (project.renewal_date - today).days <= 14:
            new_health = "amber"

        if new_health != project.health and project.health != "red":
            project.health = new_health
            project.updated_at = datetime.now(timezone.utc)

    await db.commit()


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
