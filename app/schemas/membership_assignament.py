from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.asignacion_membresias import MembershipAssignmentStatus


class MembershipAssignmentCreate(BaseModel):
    user_id: int
    membership_id: int
    # Si no se envía, se usa hoy.
    start_date: date | None = None
    # Si no se envía, se usa el precio del plan.
    price_paid: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    notes: str | None = None


class MembershipAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    membership_id: int
    start_date: date
    end_date: date
    status: MembershipAssignmentStatus
    price_paid: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime