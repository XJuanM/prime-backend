from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alimentos import Alimento
from app.schemas.alimento import AlimentoCreate, AlimentoUpdate


class AlimentoNotFoundError(Exception):
    """Se lanza cuando no existe un alimento con ese ID."""


class AlimentoNameExistsError(Exception):
    """Se lanza cuando ya existe un alimento con ese mismo nombre."""


class AlimentoService:
    @staticmethod
    def list_alimentos(
        db: Session,
        *,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Alimento], int]:
        stmt = select(Alimento)
        count_stmt = select(func.count()).select_from(Alimento)

        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(Alimento.nombre.ilike(pattern))
            count_stmt = count_stmt.where(Alimento.nombre.ilike(pattern))

        total = db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        items = list(
            db.scalars(
                stmt.order_by(Alimento.id_alimento.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return items, total

    @staticmethod
    def get_alimento(db: Session, alimento_id: int) -> Alimento:
        alimento = db.get(Alimento, alimento_id)
        if not alimento:
            raise AlimentoNotFoundError(f"No se encontró el alimento con id {alimento_id}.")
        return alimento

    @staticmethod
    def create_alimento(db: Session, data: AlimentoCreate) -> Alimento:
        nombre_clean = data.nombre.strip()

        existing = db.scalar(
            select(Alimento).where(func.lower(Alimento.nombre) == nombre_clean.lower())
        )
        if existing:
            raise AlimentoNameExistsError(
                f"Ya existe un alimento llamado '{nombre_clean}'."
            )

        nuevo = Alimento(
            nombre=nombre_clean,
            proteinas=data.proteinas,
            calorias=data.calorias,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo

    @staticmethod
    def update_alimento(
        db: Session, alimento_id: int, data: AlimentoUpdate
    ) -> Alimento:
        alimento = AlimentoService.get_alimento(db, alimento_id)
        updates = data.model_dump(exclude_unset=True)

        if "nombre" in updates and updates["nombre"] is not None:
            nombre_clean = updates["nombre"].strip()
            duplicate = db.scalar(
                select(Alimento).where(
                    func.lower(Alimento.nombre) == nombre_clean.lower(),
                    Alimento.id_alimento != alimento_id,
                )
            )
            if duplicate:
                raise AlimentoNameExistsError(
                    f"Ya existe otro alimento llamado '{nombre_clean}'."
                )
            alimento.nombre = nombre_clean

        if "proteinas" in updates and updates["proteinas"] is not None:
            alimento.proteinas = updates["proteinas"]

        if "calorias" in updates and updates["calorias"] is not None:
            alimento.calorias = updates["calorias"]

        db.commit()
        db.refresh(alimento)
        return alimento

    @staticmethod
    def delete_alimento(db: Session, alimento_id: int) -> None:
        alimento = AlimentoService.get_alimento(db, alimento_id)
        db.delete(alimento)
        db.commit()