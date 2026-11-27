from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums.muscle_group import MuscleGroup
from app.infrastructure.database.base import Base


class ProgressRecord(Base):
    """Una SESIÓN de entrenamiento de un músculo dentro de una semana.

    Máximo 3 sesiones por (usuario, músculo, año, mes, semana).
    Cada mes tiene 4 semanas (week_of_month = 1..4).
    """

    __tablename__ = "progreso_semanal"

    __table_args__ = (
        UniqueConstraint(
            "id_usuario",
            "muscle_group",
            "year",
            "month",
            "week_of_month",
            "session_number",
            name="uq_progress_user_muscle_session",
        ),
        CheckConstraint(
            "session_number BETWEEN 1 AND 3", name="ck_progress_session_max_3"
        ),
        CheckConstraint("week_of_month BETWEEN 1 AND 4", name="ck_progress_week_1_4"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_progress_month"),
        CheckConstraint("weight_kg > 0", name="ck_progress_weight_positive"),
        CheckConstraint("repetitions > 0", name="ck_progress_reps_positive"),
        Index("ix_progress_user_period", "id_usuario", "year", "month"),
    )

    id_progreso: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    muscle_group: Mapped[MuscleGroup] = mapped_column(
        SAEnum(
            MuscleGroup,
            values_callable=lambda cls: [m.value for m in cls],
            native_enum=False,
            create_constraint=True,
            length=30,
            name="ck_progress_muscle_group",
        ),
        nullable=False,
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    week_of_month: Mapped[int] = mapped_column(Integer, nullable=False)
    session_number: Mapped[int] = mapped_column(Integer, nullable=False)

    weight_kg: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship("User")

    @property
    def volume(self) -> float:
        """Volumen de la sesión = peso x repeticiones."""
        return float(self.weight_kg) * self.repetitions
