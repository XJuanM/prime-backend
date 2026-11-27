from datetime import date, datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.reportes import ReporteTipo

_NON_NULLABLE_FIELDS = ("titulo", "tipo", "fecha_inicio", "fecha_fin")


def _clean_titulo(value: str | None) -> str | None:
    if value is None:
        return value
    value = " ".join(value.split())
    if not value:
        raise ValueError("El título no puede estar vacío.")
    return value


class ReporteCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    tipo: ReporteTipo
    fecha_inicio: date
    fecha_fin: date
    descripcion: str | None = None

    _normalize_titulo = field_validator("titulo")(_clean_titulo)

    @model_validator(mode="after")
    def _validate_dates(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError(
                "La fecha fin no puede ser anterior a la fecha inicio."
            )
        return self


class ReporteUpdate(BaseModel):
    """Actualización parcial: solo se modifican los campos enviados."""

    titulo: str | None = Field(default=None, min_length=1, max_length=150)
    tipo: ReporteTipo | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    descripcion: str | None = None

    _normalize_titulo = field_validator("titulo")(_clean_titulo)

    @model_validator(mode="after")
    def _reject_null_on_required_fields(self):
        for field in _NON_NULLABLE_FIELDS:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"El campo '{field}' no puede ser nulo.")
        return self


class ReporteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    tipo: ReporteTipo
    fecha_inicio: date
    fecha_fin: date
    descripcion: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class ReporteContenido(BaseModel):
    """Datos calculados del reporte en el momento de la consulta."""

    indicadores: dict[str, Any]
    columnas: list[str]
    filas: list[list[Any]]


class ReporteDetalleResponse(ReporteResponse):
    contenido: ReporteContenido


class ReporteListResponse(BaseModel):
    items: list[ReporteResponse]
    total: int
    page: int
    page_size: int