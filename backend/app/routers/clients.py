from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_locale, require_psychologist
from app.i18n import t
from app.models import Client
from app.schemas import ClientCreate, ClientOut
from app.services.security import hash_password

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    existing = await db.execute(
        select(Client).where(Client.psychologist_id == user.id, Client.username == data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=t("auth.username_taken", locale))

    client = Client(
        psychologist_id=user.id,
        username=data.username,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        locale=data.locale,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("", response_model=list[ClientOut])
async def list_clients(
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Client).where(Client.psychologist_id == user.id, Client.is_active.is_(True)).order_by(Client.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: UUID,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.psychologist_id == user.id, Client.is_active.is_(True))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))
    return client
