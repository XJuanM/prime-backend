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


class EmployeeProfileCreate(BaseModel):
    # Ajusta los campos a tu modelo real de empleado/entrenador
    pass


class UserCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8)
    role: Roles
    client_profile: ClientProfileCreate | None = None
    employee_profile: EmployeeProfileCreate | None = None

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

            if self.employee_profile is not None:
                raise ValueError(
                    "El cliente no puede tener un perfil de empleado"
                )

        elif self.role in (Roles.ADMIN, Roles.ENTRENADOR):
            if self.employee_profile is None:
                raise ValueError(
                    "El Entrenador o Administrador debe tener un perfil de empleado"
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
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    role: Roles
    is_active: bool
    created_at: datetime
    updated_at: datetime
