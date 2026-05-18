from datetime import datetime

from pydantic import BaseModel


class ClientNoteOut(BaseModel):
    id: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StageHistoryOut(BaseModel):
    id: str
    from_stage: str | None
    to_stage: str
    note: str | None
    moved_at: datetime

    model_config = {"from_attributes": True}


class ClientBase(BaseModel):
    name: str
    contact_name: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    source: str | None = None
    enquiry: str | None = None
    estimated_mrr: int | None = None
    next_action: str | None = None
    next_action_due: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = None
    contact_name: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    source: str | None = None
    enquiry: str | None = None
    estimated_mrr: int | None = None
    next_action: str | None = None
    next_action_due: str | None = None
    stage: str | None = None


class ClientOut(ClientBase):
    id: str
    stage: str
    ai_context: str | None = None
    ai_context_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientDetail(ClientOut):
    notes: list[ClientNoteOut] = []
    stage_history: list[StageHistoryOut] = []


class ClientStageMove(BaseModel):
    to_stage: str
    note: str | None = None


class ClientNoteCreate(BaseModel):
    body: str
