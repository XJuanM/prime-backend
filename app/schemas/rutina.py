from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_NON_NULLABLE_FIELDS = ("nombre", "objetivo")


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return value
    value = " ".join(value.split())
    if not value:
        raise ValueError("El campo no puede estar vacío.")
    return value


class RutinaEjercicioItem(BaseModel):
    ejercicio_id: int = Field(gt=0)
    series: int = Field(default=3, ge=1, le=20)
    repeticiones: str = Field(default="12", min_length=1, max_length=30)
    descanso_segundos: int | None = Field(default=60, ge=0, le=600)
    orden: int = Field(default=1, ge=1)
    notas: str | None = Field(default=None, max_length=255)


class RutinaEjerciciosAssign(BaseModel):
    ejercicios: list[RutinaEjercicioItem] = Field(min_length=1)


class RutinaEjercicioResponse(BaseModel):
    ejercicio_id: int
    nombre_ejercicio: str | None = None
    grupo_muscular: str | None = None
    series: int
    repeticiones: str
    descanso_segundos: int | None = None
    orden: int
    notas: str | None = None


class RutinaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=30)
    objetivo: str = Field(min_length=1, max_length=30)
    id_usuario: int | None = Field(default=None, gt=0)

    _normalize_nombre = field_validator("nombre")(_clean_text)
    _normalize_objetivo = field_validator("objetivo")(_clean_text)


class RutinaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=30)
    objetivo: str | None = Field(default=None, min_length=1, max_length=30)
    id_usuario: int | None = Field(default=None, gt=0)

    _normalize_nombre = field_validator("nombre")(_clean_text)
    _normalize_objetivo = field_validator("objetivo")(_clean_text)

    @model_validator(mode="after")
    def _reject_null_on_required_fields(self):
        for field in _NON_NULLABLE_FIELDS:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"El campo '{field}' no puede ser nulo.")
        return self


class RutinaAssignClient(BaseModel):
    id_usuario: int = Field(gt=0)


class RutinaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cod_rutina: int
    id_usuario: int | None
    nombre: str | None
    objetivo: str | None
    ejercicios: list[RutinaEjercicioResponse] = []


class RutinaListResponse(BaseModel):
    items: list[RutinaResponse]
    total: int
    page: int
    page_size: int