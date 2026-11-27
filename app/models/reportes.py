from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ReporteTipo(str, Enum):
    MEMBRESIAS = "membresias"  # asignaciones e ingresos por plan
    USUARIOS = "usuarios"      # altas de usuarios por rol


class Reporte(Base):
    __tablename__ = "reportes"

    __table_args__ = (
        CheckConstraint(
            "fecha_fin >= fecha_inicio",
            name="ck_reportes_fechas_validas",
        ),
        Index("ix_reportes_tipo_created_at", "tipo", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    titulo: Mapped[str] = mapped_column(String(150), nullable=False)

    tipo: Mapped[ReporteTipo] = mapped_column(
        SAEnum(
            ReporteTipo,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            native_enum=False,
            create_constraint=True,
            length=20,
            name="ck_reportes_tipo",
        ),
        nullable=False,
    )

    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)

    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )