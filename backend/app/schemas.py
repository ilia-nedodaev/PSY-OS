from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import HomeworkStatus, Locale, NoteSourceType, SessionStatus, SosStatus


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    locale: str


class PsychologistRegister(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)
    locale: Locale = Locale.uk


class PsychologistLogin(BaseModel):
    email: EmailStr
    password: str


class ClientLogin(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str


class ClientCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = None
    locale: Locale = Locale.uk


class ClientOut(BaseModel):
    id: UUID
    username: str
    first_name: str
    last_name: str
    phone: str | None
    locale: Locale
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    client_id: UUID
    scheduled_at: datetime
    duration_minutes: int = 50


class SessionOut(BaseModel):
    id: UUID
    client_id: UUID
    scheduled_at: datetime
    duration_minutes: int
    status: SessionStatus

    model_config = {"from_attributes": True}


class NoteCreateText(BaseModel):
    client_id: UUID
    session_id: UUID | None = None
    content_text: str = Field(min_length=1)


class NoteOut(BaseModel):
    id: UUID
    client_id: UUID
    session_id: UUID | None
    source_type: NoteSourceType
    content_text: str | None
    transcript: str | None
    ai_summary: str | None
    ai_homework: str | None
    ai_next_plan: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class MessageOut(BaseModel):
    id: UUID
    sender_role: str
    body: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HomeworkCreate(BaseModel):
    client_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    due_at: datetime | None = None


class HomeworkOut(BaseModel):
    id: UUID
    client_id: UUID
    title: str
    description: str
    due_at: datetime | None
    status: HomeworkStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class SosCreate(BaseModel):
    message: str | None = Field(default=None, max_length=1000)


class SosOut(BaseModel):
    id: UUID
    status: SosStatus
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentStubCreate(BaseModel):
    session_id: UUID | None = None
    amount_cents: int = Field(gt=0)


class PaymentStubOut(BaseModel):
    id: UUID
    status: str
    amount_cents: int
    currency: str
    message_key: str = "payment.stub_message"
    title_key: str = "payment.stub_title"


class PreBriefOut(BaseModel):
    brief: str


class AiInsightOut(BaseModel):
    id: UUID
    insight_type: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
