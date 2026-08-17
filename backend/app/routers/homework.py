from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_current_user, get_locale, require_psychologist
from app.i18n import t
from app.models import Client, Homework, HomeworkStatus
from app.schemas import HomeworkCreate, HomeworkOut

router = APIRouter(prefix="/homework", tags=["homework"])


@router.post("", response_model=HomeworkOut, status_code=status.HTTP_201_CREATED)
async def create_homework(
    data: HomeworkCreate,
    user: AuthUser = Depends(require_psychologist),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(
        select(Client).where(Client.id == data.client_id, Client.psychologist_id == user.id, Client.is_active.is_(True))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    homework = Homework(
        client_id=data.client_id,
        psychologist_id=user.id,
        title=data.title,
        description=data.description,
        due_at=data.due_at,
        status=HomeworkStatus.assigned,
    )
    db.add(homework)
    await db.commit()
    await db.refresh(homework)
    return homework


@router.get("/client/{client_id}", response_model=list[HomeworkOut])
async def list_homework(
    client_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    if user.role == "psychologist":
        client_check = await db.execute(
            select(Client).where(Client.id == client_id, Client.psychologist_id == user.id)
        )
        if not client_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))
        target_id = client_id
    else:
        if client_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))
        target_id = user.id

    result = await db.execute(
        select(Homework).where(Homework.client_id == target_id).order_by(Homework.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{homework_id}/complete", response_model=HomeworkOut)
async def complete_homework(
    homework_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    result = await db.execute(select(Homework).where(Homework.id == homework_id))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    if user.role == "client" and homework.client_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))
    if user.role == "psychologist" and homework.psychologist_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))

    homework.status = HomeworkStatus.completed
    await db.commit()
    await db.refresh(homework)
    return homework
