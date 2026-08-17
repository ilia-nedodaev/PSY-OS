from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.i18n import t
from app.models import Client, Psychologist
from app.services.security import safe_decode_token

security = HTTPBearer(auto_error=False)


@dataclass
class AuthUser:
    id: UUID
    role: str
    locale: str = "uk"


def get_locale(
    accept_language: str | None = Header(default=None),
    x_locale: str | None = Header(default=None),
) -> str:
    if x_locale in ("uk", "en"):
        return x_locale
    if accept_language and accept_language.lower().startswith("en"):
        return "en"
    return "uk"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
) -> AuthUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.unauthorized", locale))

    payload = safe_decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.unauthorized", locale))

    user_id = payload.get("sub")
    role = payload.get("role")
    if not user_id or role not in ("psychologist", "client"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.unauthorized", locale))

    if role == "psychologist":
        result = await db.execute(select(Psychologist).where(Psychologist.id == user_id, Psychologist.is_active.is_(True)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.unauthorized", locale))
        return AuthUser(id=user.id, role="psychologist", locale=user.locale.value)

    result = await db.execute(select(Client).where(Client.id == user_id, Client.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t("auth.unauthorized", locale))
    return AuthUser(id=user.id, role="client", locale=user.locale.value)


def require_psychologist(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != "psychologist":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Psychologist access only")
    return user


def require_client(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != "client":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client access only")
    return user
