from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from app.domain.enums.user_role import Roles


class ClientProfileCreate(BaseModel):
    birth_date: date | None = None
    address: str | None = Field(default=None, max_length=255)
    emergency_contact_name: str | None = Field(
        default=None, max_length=150
    )
    emergency_contact_phone: str | None = Field(
        default=None, max_length=30
    )
    notes: str | None = None


class TrainerProfileCreate(BaseModel):
    job_title: str = Field(min_length=2, max_length=100)
    specialty: str | None = Field(default=None, max_length=150)
    hire_date: date | None = None
    is_available: bool = True
    notes: str | None = None


class UserCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8)
    role: Roles
    client_profile: ClientProfileCreate | None = None
    trainer_profile: TrainerProfileCreate | None = None

    @model_validator(mode="after")
    def validate_role_profiles(self):
        if self.role == Roles.SUPER_ADMIN:
            raise ValueError(
                "El SUPER ADMIN no se puede crear desde este endpoint."
            )

        if self.role == Roles.CLIENTE:
            if self.client_profile is None:
                raise ValueError(
                    "El cliente debe tener un perfil de cliente"
                )

            if self.trainer_profile is not None:
                raise ValueError(
                    "El cliente no puede tener un perfil de entrenador"
                )

        elif self.role in (Roles.ADMINISTRADOR, Roles.ENTRENADOR):
            if self.trainer_profile is None:
                raise ValueError(
                    "El Entrenador o Administrador debe tener un perfil de entrenador"
                )

            if self.client_profile is not None:
                raise ValueError(
                    "Un Entrenador o Administrador no puede tener un perfil de cliente"
                )

        return self


# Datos permitidos para actualizar
class UserUpdate(BaseModel):
    first_name: str | None = Field(
        default=None, min_length=2, max_length=100
    )
    last_name: str | None = Field(
        default=None, min_length=2, max_length=100
    )
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


# Cambio de estado de la cuenta
class UserStatusUpdate(BaseModel):
    is_active: bool


class UserResponse(BaseModel):
    """
    Información pública de un usuario.

    No incluye password_hash ni otros datos privados.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str | None
    last_name: str | None
    email: EmailStr | None
    phone: str | None
    role: Roles
    is_active: bool
    created_at: datetime
    updated_at: datetime
