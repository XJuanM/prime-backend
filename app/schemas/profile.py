from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.user import UserResponse


# ---------- Respuesta ----------

class ClientProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    birth_date: date | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None


class TrainerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_title: str
    specialty: str | None
    hire_date: date | None
    is_available: bool


class ProfileResponse(UserResponse):
    """Datos del usuario autenticado más su perfil según el rol."""

    client_profile: ClientProfileResponse | None = None
    trainer_profile: TrainerProfileResponse | None = None


# ---------- Edición ----------
# extra="forbid": si alguien envía role, email, is_active, password_hash...
# la API responde 422 en vez de ignorarlo en silencio.

class ClientProfileSelfUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    birth_date: date | None = None
    address: str | None = Field(default=None, max_length=255)
    emergency_contact_name: str | None = Field(
        default=None, max_length=150
    )
    emergency_contact_phone: str | None = Field(
        default=None, max_length=30
    )


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    first_name: str | None = Field(
        default=None, min_length=2, max_length=100
    )
    last_name: str | None = Field(
        default=None, min_length=2, max_length=100
    )
    phone: str | None = Field(default=None, max_length=30)
    client_profile: ClientProfileSelfUpdate | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def name_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("Este campo no puede ser nulo.")
        return value

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Debes enviar al menos un campo para actualizar.")
        return self
