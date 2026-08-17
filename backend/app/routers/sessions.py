from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_locale, require_psychologist
from app.i18n import t
from app.models import Client, TherapySession
from app.schemas import SessionCreate, SessionOut

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _get_owned_client(db: AsyncSession, psychologist_id: UUID, client_id: UUID) -> Client | None:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.psychologist_id == psychologist_id, Client.is_active.is_(True))
    )
    return result.scalar_one_or_none()


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    client = await _get_owned_client(db, user.id, data.client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    session = TherapySession(
        psychologist_id=user.id,
        client_id=data.client_id,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    client_id: UUID | None = None,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
):
    query = select(TherapySession).where(TherapySession.psychologist_id == user.id)
    if client_id:
        query = query.where(TherapySession.client_id == client_id)
    query = query.order_by(TherapySession.scheduled_at.desc())
    result = await db.execute(query)
    return result.scalars().all()
