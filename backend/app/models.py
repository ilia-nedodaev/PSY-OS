import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Locale(str, enum.Enum):
    uk = "uk"
    en = "en"


class SessionStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class NoteSourceType(str, enum.Enum):
    text = "text"
    voice = "voice"
    file = "file"


class HomeworkStatus(str, enum.Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class SosStatus(str, enum.Enum):
    pending = "pending"
    viewed = "viewed"
    responded = "responded"


class PaymentStatus(str, enum.Enum):
    stub = "stub"
    pending = "pending"
    paid = "paid"
    failed = "failed"


class AiInsightType(str, enum.Enum):
    memory = "memory"
    pre_brief = "pre_brief"
    post_summary = "post_summary"
    homework_pattern = "homework_pattern"
    topic = "topic"


class Psychologist(Base):
    __tablename__ = "psychologists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    locale: Mapped[Locale] = mapped_column(Enum(Locale), default=Locale.uk)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clients: Mapped[list["Client"]] = relationship(back_populates="psychologist")
    sessions: Mapped[list["TherapySession"]] = relationship(back_populates="psychologist")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("psychologist_id", "username", name="uq_client_username_per_psychologist"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    username: Mapped[str] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    locale: Mapped[Locale] = mapped_column(Enum(Locale), default=Locale.uk)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    psychologist: Mapped["Psychologist"] = relationship(back_populates="clients")
    sessions: Mapped[list["TherapySession"]] = relationship(back_populates="client")
    notes: Mapped[list["SessionNote"]] = relationship(back_populates="client")
    homework_items: Mapped[list["Homework"]] = relationship(back_populates="client")
    messages: Mapped[list["Message"]] = relationship(back_populates="client")
    life_events: Mapped[list["LifeEvent"]] = relationship(back_populates="client")


class TherapySession(Base):
    __tablename__ = "therapy_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.scheduled)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    psychologist: Mapped["Psychologist"] = relationship(back_populates="sessions")
    client: Mapped["Client"] = relationship(back_populates="sessions")
    notes: Mapped[list["SessionNote"]] = relationship(back_populates="session")


class SessionNote(Base):
    __tablename__ = "session_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("therapy_sessions.id", ondelete="SET NULL"), nullable=True)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[NoteSourceType] = mapped_column(Enum(NoteSourceType), default=NoteSourceType.text)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_homework: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_next_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["TherapySession | None"] = relationship(back_populates="notes")
    client: Mapped["Client"] = relationship(back_populates="notes")
    chunks: Mapped[list["NoteChunk"]] = relationship(back_populates="note")


class NoteChunk(Base):
    __tablename__ = "note_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("session_notes.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536), nullable=True)

    note: Mapped["SessionNote"] = relationship(back_populates="chunks")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    sender_role: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped["Client"] = relationship(back_populates="messages")


class Homework(Base):
    __tablename__ = "homework"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[HomeworkStatus] = mapped_column(Enum(HomeworkStatus), default=HomeworkStatus.assigned)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped["Client"] = relationship(back_populates="homework_items")


class SosEvent(Base):
    __tablename__ = "sos_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SosStatus] = mapped_column(Enum(SosStatus), default=SosStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("therapy_sessions.id", ondelete="SET NULL"), nullable=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="UAH")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.stub)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LifeEvent(Base):
    __tablename__ = "life_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    title: Mapped[str] = mapped_column(String(255))
    emoji: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped["Client"] = relationship(back_populates="life_events")


class AiInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    psychologist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    insight_type: Mapped[AiInsightType] = mapped_column(Enum(AiInsightType))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
