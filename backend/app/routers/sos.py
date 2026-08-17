from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_locale, require_client, require_psychologist
from app.i18n import t
from app.models import Client, SosEvent, SosStatus
from app.schemas import SosCreate, SosOut

router = APIRouter(prefix="/sos", tags=["sos"])


@router.post("", response_model=SosOut, status_code=status.HTTP_201_CREATED)
async def trigger_sos(
    data: SosCreate,
    user: AuthUser = Depends(require_client),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(select(Client).where(Client.id == user.id, Client.is_active.is_(True)))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    event = SosEvent(
        client_id=client.id,
        psychologist_id=client.psychologist_id,
        message=data.message,
        status=SosStatus.pending,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("", response_model=list[SosOut])
async def list_sos(
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SosEvent).where(SosEvent.psychologist_id == user.id).order_by(SosEvent.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{sos_id}/viewed", response_model=SosOut)
async def mark_sos_viewed(
    sos_id: UUID,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(
        select(SosEvent).where(SosEvent.id == sos_id, SosEvent.psychologist_id == user.id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    event.status = SosStatus.viewed
    event.viewed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(event)
    return event
