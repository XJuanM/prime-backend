from enum import Enum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.database.base import Base


class Roles(str, Enum):
    SUPER_ADMIN = 'Super Administrador'
    ADMINISTRADOR = 'Administrador'
    ENTRENADOR = 'Entrenador'
    CLIENTE = 'Cliente'


class Role(Base):
    __tablename__ = "roles"

    tipo_rol: Mapped[str] = mapped_column(String(30), primary_key=True)