from enum import Enum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.database.base import Base


class Roles(str, Enum):
    SUPER_ADMIN = 'Super Administrador'
    ADMINISTRADOR = 'Administrador'
    ENTRENADOR = 'Entrenador'
    CLIENTE = 'Cliente'
