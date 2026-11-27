from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums.muscle_group import MuscleGroup

# Los nombres internos se mantienen (modelo/servicio); la API expone
# los alias en español tanto al recibir como al responder.


class ProgressCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    muscle_group: MuscleGroup = Field(alias="grupo_muscular")
    year: int = Field(alias="anio", ge=2000, le=2100)
    month: int = Field(alias="mes", ge=1, le=12)
    week_of_month: int = Field(
        alias="semana_del_mes", ge=1, le=4, description="Semana del mes (1 a 4)"
    )
    weight_kg: float = Field(
        alias="peso_kg", gt=0, le=1000, description="Peso utilizado en kg"
    )
    repetitions: int = Field(
        alias="repeticiones", gt=0, le=10000, description="Repeticiones realizadas"
    )


class ProgressUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    weight_kg: float | None = Field(
        default=None, alias="peso_kg", gt=0, le=1000
    )
    repetitions: int | None = Field(
        default=None, alias="repeticiones", gt=0, le=10000
    )


class ProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_progreso: int
    id_usuario: int
    muscle_group: MuscleGroup = Field(serialization_alias="grupo_muscular")
    year: int = Field(serialization_alias="anio")
    month: int = Field(serialization_alias="mes")
    week_of_month: int = Field(serialization_alias="semana_del_mes")
    session_number: int = Field(serialization_alias="numero_sesion")
    weight_kg: float = Field(serialization_alias="peso_kg")
    repetitions: int = Field(serialization_alias="repeticiones")
    volume: float = Field(
        serialization_alias="volumen", description="Peso x repeticiones"
    )
    created_at: datetime = Field(serialization_alias="creado_en")
    updated_at: datetime = Field(serialization_alias="actualizado_en")


class WeekVariation(BaseModel):
    week_of_month: int = Field(serialization_alias="semana_del_mes")
    sessions: int = Field(serialization_alias="sesiones")
    avg_session_volume: float = Field(
        serialization_alias="volumen_promedio_sesion",
        description="Promedio de peso x repeticiones por sesión",
    )
    change_vs_previous_pct: float | None = Field(
        default=None,
        serialization_alias="variacion_vs_semana_anterior_pct",
    )


class MonthlyProgressResponse(BaseModel):
    user_id: int = Field(serialization_alias="usuario_id")
    muscle_group: MuscleGroup = Field(serialization_alias="grupo_muscular")
    year: int = Field(serialization_alias="anio")
    month: int = Field(serialization_alias="mes")
    initial_volume: float = Field(serialization_alias="volumen_inicial")
    final_volume: float = Field(serialization_alias="volumen_final")
    progress_pct: float = Field(
        serialization_alias="porcentaje_progreso",
        description="(semana 4 - semana 1) / semana 1 * 100",
    )
    average_weekly_change_pct: float = Field(
        serialization_alias="variacion_semanal_promedio_pct"
    )
    weeks: list[WeekVariation] = Field(serialization_alias="semanas")
