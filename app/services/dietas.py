from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dietas import Dieta
from app.schemas.dietas import DietaCreate, DietaUpdate


class DietaNoEncontrada(Exception):
    pass


def obtener(db: Session, cod_dieta: int, id_usuario: int) -> Dieta:
    dieta = db.scalar(
        select(Dieta).where(Dieta.cod_dieta == cod_dieta, Dieta.id_usuario == id_usuario)
    )
    if dieta is None:
        raise DietaNoEncontrada()
    return dieta


def listar(db: Session, id_usuario: int, skip: int, limit: int) -> list[Dieta]:
    stmt = (
        select(Dieta)
        .where(Dieta.id_usuario == id_usuario)
        .order_by(Dieta.cod_dieta)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def crear(db: Session, data: DietaCreate, id_usuario: int) -> Dieta:
    dieta = Dieta(**data.model_dump(), id_usuario=id_usuario)
    db.add(dieta)
    db.commit()
    db.refresh(dieta)
    return dieta


def actualizar(db: Session, cod_dieta: int, id_usuario: int, data: DietaUpdate) -> Dieta:
    dieta = obtener(db, cod_dieta, id_usuario)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(dieta, campo, valor)
    db.commit()
    db.refresh(dieta)
    return dieta


def eliminar(db: Session, cod_dieta: int, id_usuario: int) -> None:
    dieta = obtener(db, cod_dieta, id_usuario)
    db.delete(dieta)
    db.commit()