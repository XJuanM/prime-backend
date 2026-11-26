from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Ejercicio(Base):
    __tablename__ = "ejercicios"

    # Si en tu base de datos la columna se llama "id" (o distinto), cámbialo aquí:
    # mapped_column("id", Integer, primary_key=True, autoincrement=True)
    id_ejercicio: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    musculo_enfoque: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )