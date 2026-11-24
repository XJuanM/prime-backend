from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class MembershipAssignmentStatus(str, Enum):
    ACTIVA = "ACTIVA"
    VENCIDA = "VENCIDA"
    CANCELADA = "CANCELADA"
    SUSPENDIDA = "SUSPENDIDA"


class MembershipAssignment(Base):
    __tablename__ = "asignaciones_membresia"

    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="ck_asignaciones_membresia_valid_dates",
        ),
        CheckConstraint(
            "price_paid >= 0",
            name="ck_asignaciones_membresia_price_nonnegative",
        ),
        Index("ix_asignaciones_membresia_user_status", "user_id", "status"),
        Index("ix_asignaciones_membresia_plan_end_date", "membership_id", "end_date"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )

    membership_id: Mapped[int] = mapped_column(
        ForeignKey("membresias.id", ondelete="RESTRICT"),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[MembershipAssignmentStatus] = mapped_column(
        SAEnum(
            MembershipAssignmentStatus,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            native_enum=False,
            create_constraint=True,
            length=20,
            name="ck_asignaciones_membresia_status",
        ),
        nullable=False,
        default=MembershipAssignmentStatus.ACTIVA,
    )

    price_paid: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship(
        "User",
        back_populates="membership_assignments",
    )

    membership = relationship(
        "Membresias",
        back_populates="assignments",
    )