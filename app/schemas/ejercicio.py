from pydantic import BaseModel, ConfigDict, Field


class EjercicioBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    musculo_enfoque: str = Field(..., min_length=1, max_length=100)


class EjercicioCreate(EjercicioBase):
    pass


class EjercicioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    musculo_enfoque: str | None = Field(default=None, min_length=1, max_length=100)


class EjercicioResponse(EjercicioBase):
    id_ejercicio: int

    model_config = ConfigDict(from_attributes=True)


class EjercicioListResponse(BaseModel):
    items: list[EjercicioResponse]
    total: int
    page: int
    page_size: int