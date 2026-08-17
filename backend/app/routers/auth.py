from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_locale
from app.i18n import t
from app.models import Client, Psychologist
from app.schemas import (
    ClientLogin,
    PsychologistLogin,
    PsychologistRegister,
    TokenResponse,
)
from app.services.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/psychologist/register", response_model=TokenResponse)
async def register_psychologist(
    data: PsychologistRegister,
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    existing = await db.execute(select(Psychologist).where(Psychologist.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=t("auth.email_taken", locale))

    psychologist = Psychologist(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        locale=data.locale,
    )
    db.add(psychologist)
    await db.commit()
    await db.refresh(psychologist)

    sub = str(psychologist.id)
    return TokenResponse(
        access_token=create_access_token(sub, "psychologist"),
        refresh_token=create_refresh_token(sub, "psychologist"),
        role="psychologist",
        locale=psychologist.locale.value,
    )


@router.post("/psychologist/login", response_model=TokenResponse)
async def login_psychologist(
    data: PsychologistLogin,
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(select(Psychologist).where(Psychologist.email == data.email.lower()))
    psychologist = result.scalar_one_or_none()
    if not psychologist or not verify_password(data.password, psychologist.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.invalid_credentials", locale))

    sub = str(psychologist.id)
    return TokenResponse(
        access_token=create_access_token(sub, "psychologist"),
        refresh_token=create_refresh_token(sub, "psychologist"),
        role="psychologist",
        locale=psychologist.locale.value,
    )


@router.post("/client/login", response_model=TokenResponse)
async def login_client(
    data: ClientLogin,
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(select(Client).where(Client.username == data.username, Client.is_active.is_(True)))
    client = result.scalar_one_or_none()
    if not client or not verify_password(data.password, client.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.invalid_credentials", locale))

    sub = str(client.id)
    return TokenResponse(
        access_token=create_access_token(sub, "client", {"psychologist_id": str(client.psychologist_id)}),
        refresh_token=create_refresh_token(sub, "client"),
        role="client",
        locale=client.locale.value,
    )
