from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_current_user, get_locale, require_psychologist
from app.i18n import t
from app.models import Client, Psychologist
from app.schemas_profile import UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserProfile)
async def get_me(
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    if user.role == "psychologist":
        result = await db.execute(select(Psychologist).where(Psychologist.id == user.id))
        psych = result.scalar_one_or_none()
        if not psych:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.unauthorized", locale))
        return UserProfile(
            id=psych.id,
            role="psychologist",
            locale=psych.locale.value,
            first_name=psych.first_name,
            last_name=psych.last_name,
            email=psych.email,
            phone=psych.phone,
        )

    result = await db.execute(select(Client).where(Client.id == user.id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.unauthorized", locale))
    return UserProfile(
        id=client.id,
        role="client",
        locale=client.locale.value,
        first_name=client.first_name,
        last_name=client.last_name,
        username=client.username,
        phone=client.phone,
    )
