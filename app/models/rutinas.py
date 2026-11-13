from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base

class Rutinas(Base):
    __tablename__ = "rutinas"

    cod_rutina: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id_usuario"))
    nombre: Mapped[Optional[str]] = mapped_column(String(30))
    objetivo: Mapped[Optional[str]] = mapped_column(String(30))

    usuario: Mapped[Optional["User"]] = relationship(back_populates="rutinas")