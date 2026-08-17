from uuid import UUID

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_current_user, get_locale, require_client, require_psychologist
from app.i18n import t
from app.models import Client, Message
from app.schemas import MessageCreate, MessageOut

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/{client_id}", response_model=list[MessageOut])
async def list_messages(
    client_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    if user.role == "psychologist":
        client_result = await db.execute(
            select(Client).where(Client.id == client_id, Client.psychologist_id == user.id)
        )
    else:
        client_result = await db.execute(select(Client).where(Client.id == user.id))

    if not client_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))

    actual_client_id = client_id if user.role == "psychologist" else user.id
    result = await db.execute(
        select(Message).where(Message.client_id == actual_client_id).order_by(Message.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{client_id}", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    client_id: UUID,
    data: MessageCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    if user.role == "psychologist":
        client_result = await db.execute(
            select(Client).where(Client.id == client_id, Client.psychologist_id == user.id)
        )
        client = client_result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))
        psychologist_id = user.id
        actual_client_id = client_id
        sender_role = "psychologist"
    else:
        if client_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))
        client_result = await db.execute(select(Client).where(Client.id == user.id))
        client = client_result.scalar_one_or_none()
        psychologist_id = client.psychologist_id
        actual_client_id = user.id
        sender_role = "client"

    message = Message(
        psychologist_id=psychologist_id,
        client_id=actual_client_id,
        sender_role=sender_role,
        body=data.body,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message
