from datetime import datetime

from pydantic import BaseModel


class ProjectNoteOut(BaseModel):
    id: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BlockerOut(BaseModel):
    id: str
    body: str
    owner: str | None
    due_date: str | None
    resolved: bool
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BlockerCreate(BaseModel):
    body: str
    owner: str | None = None
    due_date: str | None = None


class ProjectBase(BaseModel):
    name: str
    client_id: str | None = None
    health: str = "green"
    live_since: str | None = None
    renewal_date: str | None = None
    stack_tags: list[str] | None = None
    external_links: dict | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    health: str | None = None
    live_since: str | None = None
    renewal_date: str | None = None
    stack_tags: list[str] | None = None
    external_links: dict | None = None


class ProjectOut(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectOut):
    blockers: list[BlockerOut] = []
    notes: list[ProjectNoteOut] = []


class ProjectNoteCreate(BaseModel):
    body: str
