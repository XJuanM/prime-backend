from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.asignacion_membresias import MembershipAssignmentStatus
from app.models.membresias import Membresias_periodo

# Campos que no admiten NULL en la base de datos.
_NON_NULLABLE_FIELDS = ("name", "period", "duration_days", "price", "is_active")


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return value
    value = " ".join(value.split())
    if not value:
        raise ValueError("El nombre no puede estar vacío.")
    return value


class MembershipCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    period: Membresias_periodo
    # Si no se envía, se calcula según el periodo (30, 90, 180 o 365 días).
    duration_days: int | None = Field(default=None, gt=0)
    description: str | None = None
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    is_active: bool = True

    _normalize_name = field_validator("name")(_clean_name)


class MembershipUpdate(BaseModel):
    """Actualización parcial: solo se modifican los campos enviados."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    period: Membresias_periodo | None = None
    duration_days: int | None = Field(default=None, gt=0)
    description: str | None = None
    price: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    is_active: bool | None = None

    _normalize_name = field_validator("name")(_clean_name)

    @model_validator(mode="after")
    def _reject_null_on_required_fields(self):
        for field in _NON_NULLABLE_FIELDS:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"El campo '{field}' no puede ser nulo.")
        return self


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    period: Membresias_periodo
    duration_days: int
    description: str | None
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MembershipListResponse(BaseModel):
    items: list[MembershipResponse]
    total: int
    page: int
    page_size: int


class AssignmentCreate(BaseModel):
    user_id: int
    start_date: date | None = None  # por defecto, hoy
    price_paid: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )  # por defecto, el precio del plan
    notes: str | None = None


class AssignmentResponse(BaseModel):
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
