from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AuthUser, get_current_user, get_locale
from app.i18n import t
from app.models import Client, Payment, PaymentStatus, TherapySession
from app.schemas import PaymentStubCreate, PaymentStubOut

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/stub", response_model=PaymentStubOut, status_code=status.HTTP_201_CREATED)
async def create_payment_stub(
    data: PaymentStubCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    locale: str = Depends(get_locale),
):
    if user.role == "client":
        client_result = await db.execute(select(Client).where(Client.id == user.id))
        client = client_result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))
        client_id = client.id
        psychologist_id = client.psychologist_id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden", locale))

    if data.session_id:
        session_result = await db.execute(
            select(TherapySession).where(
                TherapySession.id == data.session_id,
                TherapySession.client_id == client_id,
            )
        )
        if not session_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t("auth.forbidden", locale))

    payment = Payment(
        session_id=data.session_id,
        client_id=client_id,
        psychologist_id=psychologist_id,
        amount_cents=data.amount_cents,
        status=PaymentStatus.stub,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentStubOut(
        id=payment.id,
        status=payment.status.value,
        amount_cents=payment.amount_cents,
        currency=payment.currency,
    )
