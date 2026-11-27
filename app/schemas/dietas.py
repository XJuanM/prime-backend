from pydantic import BaseModel, ConfigDict, Field


class DietaBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    objetivo: str | None = Field(default=None, max_length=150)
    tipo_dieta: str | None = Field(default=None, max_length=100)
    duracion: str | None = Field(default=None, max_length=50)
    calorias_objetivo: int | None = Field(default=None, gt=0)
    observaciones: str | None = None


class DietaCreate(DietaBase):
    pass


class DietaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    objetivo: str | None = Field(default=None, max_length=150)
    tipo_dieta: str | None = Field(default=None, max_length=100)
    duracion: str | None = Field(default=None, max_length=50)
    calorias_objetivo: int | None = Field(default=None, gt=0)
    observaciones: str | None = None


class DietaOut(DietaBase):
    model_config = ConfigDict(from_attributes=True)

    cod_dieta: int
    id_usuario: int