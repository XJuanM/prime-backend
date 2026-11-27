from typing import Optional

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class Rutinas(Base):
    __tablename__ = "rutinas"

    cod_rutina: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id_usuario"), nullable=True
    )
    nombre: Mapped[Optional[str]] = mapped_column(String(30))
    objetivo: Mapped[Optional[str]] = mapped_column(String(30))
    ejercicios: Mapped[Optional[list[dict]]] = mapped_column(
        JSON, nullable=True, default=list
    )

    usuario: Mapped[Optional["User"]] = relationship(back_populates="rutinas")