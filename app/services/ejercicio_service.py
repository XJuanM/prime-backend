from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ejercicios import Ejercicio
from app.schemas.ejercicio import EjercicioCreate, EjercicioUpdate


class EjercicioNotFoundError(Exception):
    """Se lanza cuando no existe un ejercicio con ese ID."""


class EjercicioNameExistsError(Exception):
    """Se lanza cuando ya existe un ejercicio con ese mismo nombre."""


class EjercicioService:
    @staticmethod
    def list_ejercicios(
        db: Session,
        *,
        search: str | None = None,
        musculo_enfoque: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Ejercicio], int]:
        stmt = select(Ejercicio)
        count_stmt = select(func.count()).select_from(Ejercicio)

        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(Ejercicio.nombre.ilike(pattern))
            count_stmt = count_stmt.where(Ejercicio.nombre.ilike(pattern))

        if musculo_enfoque:
            musculo_clean = musculo_enfoque.strip()
            stmt = stmt.where(Ejercicio.musculo_enfoque.ilike(musculo_clean))
            count_stmt = count_stmt.where(Ejercicio.musculo_enfoque.ilike(musculo_clean))

        total = db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        items = list(
            db.scalars(
                stmt.order_by(Ejercicio.id_ejercicio.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return items, total

    @staticmethod
    def get_ejercicio(db: Session, ejercicio_id: int) -> Ejercicio:
        ejercicio = db.get(Ejercicio, ejercicio_id)
        if not ejercicio:
            raise EjercicioNotFoundError(f"No se encontró el ejercicio con id {ejercicio_id}.")
        return ejercicio

    @staticmethod
    def create_ejercicio(db: Session, data: EjercicioCreate) -> Ejercicio:
        nombre_clean = data.nombre.strip()
        musculo_clean = data.musculo_enfoque.strip()

        existing = db.scalar(
            select(Ejercicio).where(func.lower(Ejercicio.nombre) == nombre_clean.lower())
        )
        if existing:
            raise EjercicioNameExistsError(
                f"Ya existe un ejercicio llamado '{nombre_clean}'."
            )

        nuevo = Ejercicio(
            nombre=nombre_clean,
            musculo_enfoque=musculo_clean,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo

    @staticmethod
    def update_ejercicio(
        db: Session, ejercicio_id: int, data: EjercicioUpdate
    ) -> Ejercicio:
        ejercicio = EjercicioService.get_ejercicio(db, ejercicio_id)
        updates = data.model_dump(exclude_unset=True)

        if "nombre" in updates and updates["nombre"] is not None:
            nombre_clean = updates["nombre"].strip()
            duplicate = db.scalar(
                select(Ejercicio).where(
                    func.lower(Ejercicio.nombre) == nombre_clean.lower(),
                    Ejercicio.id_ejercicio != ejercicio_id,
                )
            )
            if duplicate:
                raise EjercicioNameExistsError(
                    f"Ya existe otro ejercicio llamado '{nombre_clean}'."
                )
            ejercicio.nombre = nombre_clean

        if "musculo_enfoque" in updates and updates["musculo_enfoque"] is not None:
            ejercicio.musculo_enfoque = updates["musculo_enfoque"].strip()

        db.commit()
        db.refresh(ejercicio)
        return ejercicio

    @staticmethod
    def delete_ejercicio(db: Session, ejercicio_id: int) -> None:
        ejercicio = EjercicioService.get_ejercicio(db, ejercicio_id)
        db.delete(ejercicio)
        db.commit()