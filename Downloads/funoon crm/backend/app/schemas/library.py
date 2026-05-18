from datetime import datetime

from pydantic import BaseModel


class ComponentOut(BaseModel):
    id: str
    name: str
    category: str
    description: str | None
    tech_tags: list[str] | None
    status: str
    version: str | None
    github_path: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComponentCreate(BaseModel):
    name: str
    category: str
    description: str | None = None
    tech_tags: list[str] | None = None
    status: str = "stable"
    version: str | None = None
    github_path: str | None = None
    notes: str | None = None


class ComponentUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    tech_tags: list[str] | None = None
    status: str | None = None
    version: str | None = None
    github_path: str | None = None
    notes: str | None = None
