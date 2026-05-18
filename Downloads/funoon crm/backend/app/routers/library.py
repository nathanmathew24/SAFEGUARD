from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.library import Component
from app.schemas.library import ComponentCreate, ComponentOut, ComponentUpdate
from app.services.ai_service import complete

router = APIRouter()


@router.get("", response_model=list[ComponentOut])
async def list_components(
    category: str | None = None,
    status_filter: str | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Component).order_by(Component.name)
    if category:
        query = query.where(Component.category == category)
    if status_filter:
        query = query.where(Component.status == status_filter)
    if q:
        query = query.where(
            or_(
                Component.name.ilike(f"%{q}%"),
                Component.description.ilike(f"%{q}%"),
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ComponentOut, status_code=status.HTTP_201_CREATED)
async def create_component(body: ComponentCreate, db: AsyncSession = Depends(get_db)):
    component = Component(**body.model_dump())
    db.add(component)
    await db.commit()
    await db.refresh(component)
    return component


@router.get("/{component_id}", response_model=ComponentOut)
async def get_component(component_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Component).where(Component.id == component_id))
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@router.patch("/{component_id}", response_model=ComponentOut)
async def update_component(
    component_id: str,
    body: ComponentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Component).where(Component.id == component_id))
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(component, field, value)
    component.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(component)
    return component


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(component_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Component).where(Component.id == component_id))
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    await db.delete(component)
    await db.commit()


@router.post("/ai/suggest", response_model=dict)
async def ai_suggest_components(body: dict, db: AsyncSession = Depends(get_db)):
    description = body.get("description", "")
    if not description:
        raise HTTPException(status_code=400, detail="description required")

    result = await db.execute(select(Component).where(Component.status != "deprecated"))
    components = result.scalars().all()
    catalogue = "\n".join(
        f"- {c.name} [{c.category}] ({', '.join(c.tech_tags or [])}): {c.description or ''}"
        for c in components
    )

    response = await complete(
        system="You are Funoon's internal operations assistant. Tone: direct, specific, low-word-count.",
        messages=[{
            "role": "user",
            "content": (
                f"Based on this component library, which components would be needed to build: '{description}'?\n\n"
                f"Library:\n{catalogue or 'Empty library.'}\n\n"
                "List the relevant components and give a rough effort estimate."
            ),
        }],
        max_tokens=400,
    )
    return {"suggestion": response.content[0].text}
