import uuid
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import AuthUser, get_locale, require_psychologist
from app.i18n import t
from app.models import Client, NoteChunk, NoteSourceType, SessionNote, TherapySession
from app.schemas import NoteCreateText, NoteOut, PreBriefOut
from app.services.openai_client import AIService

router = APIRouter(prefix="/notes", tags=["notes"])
ai_service = AIService()


async def _verify_client(db: AsyncSession, psychologist_id: UUID, client_id: UUID) -> Client:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.psychologist_id == psychologist_id, Client.is_active.is_(True))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", "uk"))
    return client


@router.post("/text", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_text_note(
    data: NoteCreateText,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    await _verify_client(db, user.id, data.client_id)

    if data.session_id:
        session_result = await db.execute(
            select(TherapySession).where(
                TherapySession.id == data.session_id,
                TherapySession.psychologist_id == user.id,
                TherapySession.client_id == data.client_id,
            )
        )
        if not session_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    ai_result = await ai_service.process_note(str(user.id), str(data.client_id), data.content_text, user.locale)

    note = SessionNote(
        session_id=data.session_id,
        psychologist_id=user.id,
        client_id=data.client_id,
        source_type=NoteSourceType.text,
        content_text=data.content_text,
        transcript=data.content_text,
        ai_summary=ai_result.get("summary") or None,
        ai_homework=ai_result.get("homework") or None,
        ai_next_plan=ai_result.get("next_plan") or None,
    )
    db.add(note)
    await db.flush()

    chunks = ai_result.get("chunks", [])
    embeddings = await ai_service.embed_chunks(chunks)
    for index, chunk in enumerate(chunks):
        db.add(
            NoteChunk(
                note_id=note.id,
                chunk_index=index,
                chunk_text=chunk,
                embedding=embeddings[index] if index < len(embeddings) else None,
            )
        )

    await db.commit()
    await db.refresh(note)
    return note


@router.post("/upload", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def upload_note_file(
    client_id: UUID = Form(...),
    session_id: UUID | None = Form(default=None),
    source_type: NoteSourceType = Form(default=NoteSourceType.file),
    content_text: str | None = Form(default=None),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    await _verify_client(db, user.id, client_id)

    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "upload.bin").suffix
    filename = f"{uuid.uuid4()}{ext}"
    dest = upload_root / filename

    size = 0
    async with aiofiles.open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
            await out.write(chunk)

    note_text = content_text or f"[Uploaded file: {file.filename}]"
    ai_result = await ai_service.process_note(str(user.id), str(client_id), note_text, user.locale)

    note = SessionNote(
        session_id=session_id,
        psychologist_id=user.id,
        client_id=client_id,
        source_type=source_type,
        content_text=content_text,
        file_path=str(dest),
        transcript=note_text,
        ai_summary=ai_result.get("summary") or None,
        ai_homework=ai_result.get("homework") or None,
        ai_next_plan=ai_result.get("next_plan") or None,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/client/{client_id}", response_model=list[NoteOut])
async def list_client_notes(
    client_id: UUID,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    await _verify_client(db, user.id, client_id)
    result = await db.execute(
        select(SessionNote).where(SessionNote.client_id == client_id, SessionNote.psychologist_id == user.id).order_by(SessionNote.created_at.desc())
    )
    return result.scalars().all()


@router.post("/client/{client_id}/pre-brief", response_model=PreBriefOut)
async def pre_session_brief(
    client_id: UUID,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    await _verify_client(db, user.id, client_id)
    result = await db.execute(
        select(SessionNote)
        .where(SessionNote.client_id == client_id, SessionNote.psychologist_id == user.id)
        .order_by(SessionNote.created_at.desc())
        .limit(12)
    )
    notes = result.scalars().all()
    texts = [n.transcript or n.content_text or "" for n in notes if (n.transcript or n.content_text)]
    brief = await ai_service.pre_session_brief(str(user.id), str(client_id), texts, user.locale)
    return PreBriefOut(brief=brief)
