from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Alimento(Base):
    __tablename__ = "alimentos"

    # Si en tu base de datos la columna primaria se llama distinto (por ejemplo "id"),
    # puedes mapearla así: mapped_column("id", Integer, primary_key=True, autoincrement=True)
    id_alimento: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    proteinas: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    calorias: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )