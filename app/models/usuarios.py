from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Computed,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.domain.enums.user_role import Roles
from app.infrastructure.database.base import Base


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "usuarios"

    __table_args__ = (
        UniqueConstraint("super_admin_slot", name="uq_users_single_super_admin"),
        Index("ix_users_role_active", "tipo_rol", "is_active"),
    )

    id_usuario: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    tipo_rol: Mapped[Roles] = mapped_column(
        SAEnum(
            Roles,
            values_callable=lambda cls: [roles.value for roles in cls],
            native_enum=False,
            create_constraint=True,
            length=30,
            name="ck_usuarios_tipo_rol",
        )
    )

    nombre: Mapped[str | None] = mapped_column(String(50))
    apellido: Mapped[str | None] = mapped_column(String(50))
    telefono: Mapped[str | None] = mapped_column(String(50))
    direccion: Mapped[str | None] = mapped_column(String(50))
    correo: Mapped[str | None] = mapped_column(String(60))

    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
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

    super_admin_slot: Mapped[int | None] = mapped_column(
        Integer,
        Computed(
            "CASE WHEN tipo_rol = 'Super Administrador' THEN 1 ELSE NULL END",
            persisted=True,
        ),
        nullable=True,
    )

    # Alias en inglés usados por servicios, schemas y routers
    id = synonym("id_usuario")
    role = synonym("tipo_rol")
    email = synonym("correo")
    first_name = synonym("nombre")
    last_name = synonym("apellido")
    phone = synonym("telefono")

    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    rutinas: Mapped[list["Rutinas"]] = relationship(
        "Rutinas",
        back_populates="usuario",
    )

    membership_assignments: Mapped[list["MembershipAssignment"]] = relationship(
        "MembershipAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    client_profile = relationship(
        "ClientProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    trainer_profile = relationship(
        "TrainerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
