from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.ejercicios import Ejercicio
from app.models.rutinas import Rutinas
from app.models.usuarios import User
from app.schemas.rutina import (
    RutinaCreate,
    RutinaEjerciciosAssign,
    RutinaUpdate,
)


class RutinaError(Exception):
    pass


class RutinaNotFoundError(RutinaError):
    pass


class RutinaNameExistsError(RutinaError):
    pass


class UserNotFoundError(RutinaError):
    pass


class EjercicioNotFoundError(RutinaError):
    pass


class EjercicioAlreadyAssignedError(RutinaError):
    pass


class RutinaService:

    @staticmethod
    def _name_exists(
        db: Session, nombre: str, exclude_id: int | None = None
    ) -> bool:
        stmt = select(Rutinas.cod_rutina).where(
            func.lower(Rutinas.nombre) == nombre.lower()
        )
        if exclude_id is not None:
            stmt = stmt.where(Rutinas.cod_rutina != exclude_id)
        return db.scalar(stmt.limit(1)) is not None

    @staticmethod
    def list_rutinas(
        db: Session,
        *,
        search: str | None,
        id_usuario: int | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Rutinas], int]:
        filters = []

        if search:
            filters.append(Rutinas.nombre.ilike(f"%{search.strip()}%"))
        if id_usuario is not None:
            filters.append(Rutinas.id_usuario == id_usuario)

        total = (
            db.scalar(select(func.count(Rutinas.cod_rutina)).where(*filters))
            or 0
        )

        items = db.scalars(
            select(Rutinas)
            .where(*filters)
            .order_by(Rutinas.cod_rutina.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total

    @staticmethod
    def get_rutina(db: Session, cod_rutina: int) -> Rutinas:
        rutina = db.get(Rutinas, cod_rutina)
        if rutina is None:
            raise RutinaNotFoundError("Rutina no encontrada.")
        return rutina

    @staticmethod
    def create_rutina(db: Session, data: RutinaCreate) -> Rutinas:
        if RutinaService._name_exists(db, data.nombre):
            raise RutinaNameExistsError("Ya existe una rutina con ese nombre.")

        if data.id_usuario is not None:
            if db.get(User, data.id_usuario) is None:
                raise UserNotFoundError("Cliente no encontrado.")

        rutina = Rutinas(
            nombre=data.nombre,
            objetivo=data.objetivo,
            id_usuario=data.id_usuario,
            ejercicios=[],
        )

        try:
            db.add(rutina)
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(rutina)
        return rutina

    @staticmethod
    def update_rutina(
        db: Session, cod_rutina: int, data: RutinaUpdate
    ) -> Rutinas:
        rutina = RutinaService.get_rutina(db, cod_rutina)
        changes = data.model_dump(exclude_unset=True)

        new_nombre = changes.get("nombre")
        if new_nombre is not None and RutinaService._name_exists(
            db, new_nombre, exclude_id=rutina.cod_rutina
        ):
            raise RutinaNameExistsError("Ya existe una rutina con ese nombre.")

        if "id_usuario" in changes and changes["id_usuario"] is not None:
            if db.get(User, changes["id_usuario"]) is None:
                raise UserNotFoundError("Cliente no encontrado.")

        for field, value in changes.items():
            setattr(rutina, field, value)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(rutina)
        return rutina

    @staticmethod
    def delete_rutina(db: Session, cod_rutina: int) -> None:
        rutina = RutinaService.get_rutina(db, cod_rutina)
        try:
            db.delete(rutina)
            db.commit()
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def assign_ejercicios(
        db: Session, cod_rutina: int, data: RutinaEjerciciosAssign
    ) -> Rutinas:
        rutina = RutinaService.get_rutina(db, cod_rutina)
        current_list = list(rutina.ejercicios or [])
        existing_ids = {item["ejercicio_id"] for item in current_list}

        for item in data.ejercicios:
            ejercicio = db.get(Ejercicio, item.ejercicio_id)
            if ejercicio is None:
                raise EjercicioNotFoundError(
                    f"El ejercicio con id {item.ejercicio_id} no existe."
                )

            if item.ejercicio_id in existing_ids:
                raise EjercicioAlreadyAssignedError(
                    f"El ejercicio '{ejercicio.nombre}' ya está asignado a esta rutina."
                )

            existing_ids.add(item.ejercicio_id)
            current_list.append(
                {
                    "ejercicio_id": item.ejercicio_id,
                    "nombre_ejercicio": ejercicio.nombre,
                    "grupo_muscular": ejercicio.grupo_muscular,
                    "series": item.series,
                    "repeticiones": item.repeticiones,
                    "descanso_segundos": item.descanso_segundos,
                    "orden": item.orden,
                    "notas": item.notas,
                }
            )

        current_list.sort(key=lambda x: x.get("orden", 1))
        rutina.ejercicios = current_list
        flag_modified(rutina, "ejercicios")

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(rutina)
        return rutina

    @staticmethod
    def assign_to_client(
        db: Session, cod_rutina: int, id_usuario: int
    ) -> Rutinas:
        rutina = RutinaService.get_rutina(db, cod_rutina)
        user = db.get(User, id_usuario)
        if user is None:
            raise UserNotFoundError("Cliente no encontrado.")

        rutina.id_usuario = user.id_usuario
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(rutina)
        return rutina