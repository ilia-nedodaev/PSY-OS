from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models import Locale


class UserProfile(BaseModel):
    id: UUID
    role: str
    locale: str
    first_name: str
    last_name: str
    email: str | None = None
    username: str | None = None
    phone: str | None = None


class LifeEventCreate(BaseModel):
    client_id: UUID
    event_date: datetime
    title: str
    emoji: str | None = None


class LifeEventOut(BaseModel):
    id: UUID
    client_id: UUID
    event_date: datetime
    title: str
    emoji: str | None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
