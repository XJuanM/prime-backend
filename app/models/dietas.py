from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.models.usuarios import utc_now_naive


class Dieta(Base):
    __tablename__ = "dietas"

    # Identificador único de la dieta
    cod_dieta: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Usuario propietario de la dieta
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Nombre de la dieta (ej. Dieta de volumen, Plan de definición)
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Objetivo de la dieta (ej. Perder grasa, Ganar masa muscular)
    objetivo: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    # Tipo de dieta (ej. Hipocalórica, Cetogénica, Vegetariana)
    tipo_dieta: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Duración de la dieta (ej. 4 semanas, 3 meses)
    duracion: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # Calorías diarias objetivo
    calorias_objetivo: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # Observaciones adicionales
    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Fecha de creación del registro
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now_naive,
        server_default=func.current_timestamp()
    )