from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_current_user, get_locale, require_psychologist
from app.i18n import t
from app.models import Client, LifeEvent, TherapySession
from app.schemas import SessionOut
from app.schemas_profile import LifeEventCreate, LifeEventOut

router = APIRouter(tags=["timeline"])


@router.get("/sessions/my", response_model=list[SessionOut])
async def my_sessions(
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "psychologist":
        result = await db.execute(
            select(TherapySession).where(TherapySession.psychologist_id == user.id).order_by(TherapySession.scheduled_at.desc())
        )
    else:
        result = await db.execute(
            select(TherapySession).where(TherapySession.client_id == user.id).order_by(TherapySession.scheduled_at.desc())
        )
    return result.scalars().all()


@router.post("/timeline", response_model=LifeEventOut, status_code=status.HTTP_201_CREATED)
async def create_life_event(
    data: LifeEventCreate,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(
        select(Client).where(Client.id == data.client_id, Client.psychologist_id == user.id, Client.is_active.is_(True))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    event = LifeEvent(
        client_id=data.client_id,
        event_date=data.event_date,
        title=data.title,
        emoji=data.emoji,
        source="manual",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/timeline/client/{client_id}", response_model=list[LifeEventOut])
async def list_life_events(
    client_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    if user.role == "psychologist":
        check = await db.execute(
            select(Client).where(Client.id == client_id, Client.psychologist_id == user.id)
        )
        if not check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))
    elif user.id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))

    result = await db.execute(
        select(LifeEvent).where(LifeEvent.client_id == client_id).order_by(LifeEvent.event_date.desc())
    )
    return result.scalars().all()
