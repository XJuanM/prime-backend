from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.models.usuarios import utc_now_naive


class Ejercicio(Base):
    __tablename__ = "ejercicios"

    # Identificador único del ejercicio
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Nombre del ejercicio (ej. Press de banca, Sentadillas)
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )

    # Descripción o instrucciones de ejecución
    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Grupo muscular principal (ej. Pecho, Piernas, Espalda)
    grupo_muscular: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # Nivel de dificultad (ej. Principiante, Intermedio, Avanzado)
    dificultad: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    # Fecha de creación del registro
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now_naive,
        server_default=func.current_timestamp()
    )