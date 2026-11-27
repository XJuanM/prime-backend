from pydantic import BaseModel, ConfigDict, Field


class AlimentoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    proteinas: float = Field(..., ge=0)
    calorias: float = Field(..., ge=0)


class AlimentoCreate(AlimentoBase):
    pass


class AlimentoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    proteinas: float | None = Field(default=None, ge=0)
    calorias: float | None = Field(default=None, ge=0)


class AlimentoResponse(AlimentoBase):
    id_alimento: int

    model_config = ConfigDict(from_attributes=True)


class AlimentoListResponse(BaseModel):
    items: list[AlimentoResponse]
    total: int
    page: int
    page_size: int