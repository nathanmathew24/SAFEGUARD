from datetime import datetime

from pydantic import BaseModel


class SOPOut(BaseModel):
    id: str
    title: str
    category: str | None
    content: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class SOPCreate(BaseModel):
    title: str
    category: str | None = None
    content: str


class SOPUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    content: str | None = None


class IncidentOut(BaseModel):
    id: str
    project_id: str | None
    severity: str
    description: str
    root_cause: str | None
    resolution: str | None
    time_to_resolve: int | None
    occurred_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    project_id: str | None = None
    severity: str
    description: str
    root_cause: str | None = None
    resolution: str | None = None
    time_to_resolve: int | None = None


class AskAIRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class AskAIResponse(BaseModel):
    reply: str
    conversation_id: str
