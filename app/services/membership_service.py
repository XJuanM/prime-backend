from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.asignacion_membresias import (
    MembershipAssignment,
    MembershipAssignmentStatus,
)
from app.models.membresias import Membresias, Membresias_periodo
from app.models.usuarios import User
from app.schemas.membership import (
    AssignmentCreate,
    MembershipCreate,
    MembershipUpdate,
)

DEFAULT_DURATION_DAYS = {
    Membresias_periodo.MENSUAL: 30,
    Membresias_periodo.TRIMESTRAL: 90,
    Membresias_periodo.SEMESTRAL: 180,
    Membresias_periodo.ANUAL: 365,
}


class MembershipError(Exception):
    pass


class MembershipNotFoundError(MembershipError):
    pass


class MembershipNameExistsError(MembershipError):
    pass


class MembershipInUseError(MembershipError):
    """La membresía tiene asignaciones y no se puede eliminar."""


class UserNotFoundError(MembershipError):
    pass


class MembershipInactiveError(MembershipError):
    pass


class ActiveAssignmentExistsError(MembershipError):
    pass


class MembershipService:

    @staticmethod
    def _name_exists(
        db: Session, name: str, exclude_id: int | None = None
    ) -> bool:
        stmt = select(Membresias.id).where(
            func.lower(Membresias.name) == name.lower()
        )
        if exclude_id is not None:
            stmt = stmt.where(Membresias.id != exclude_id)
        return db.scalar(stmt.limit(1)) is not None

    @staticmethod
    def list_memberships(
        db: Session,
        *,
        search: str | None,
        is_active: bool | None,
        period: Membresias_periodo | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Membresias], int]:
        filters = []

        if search:
            filters.append(Membresias.name.ilike(f"%{search.strip()}%"))
        if is_active is not None:
            filters.append(Membresias.is_active.is_(is_active))
        if period is not None:
            filters.append(Membresias.period == period)

        total = db.scalar(select(func.count(Membresias.id)).where(*filters)) or 0

        items = db.scalars(
            select(Membresias)
            .where(*filters)
            .order_by(Membresias.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total

    @staticmethod
    def get_membership(db: Session, membership_id: int) -> Membresias:
        membership = db.get(Membresias, membership_id)
        if membership is None:
            raise MembershipNotFoundError("Membresía no encontrada.")
        return membership

    @staticmethod
    def create_membership(db: Session, data: MembershipCreate) -> Membresias:
        if MembershipService._name_exists(db, data.name):
            raise MembershipNameExistsError(
                "Ya existe una membresía con ese nombre."
            )

        membership = Membresias(
            name=data.name,
            period=data.period,
            duration_days=data.duration_days
            or DEFAULT_DURATION_DAYS[data.period],
            description=data.description,
            price=data.price,
            is_active=data.is_active,
        )

        try:
            db.add(membership)
            db.commit()
        except IntegrityError:
            # Respaldo ante una carrera con el UNIQUE de la base de datos.
            db.rollback()
            raise MembershipNameExistsError(
                "Ya existe una membresía con ese nombre."
            )
        except Exception:
            db.rollback()
            raise

        db.refresh(membership)
        return membership

    @staticmethod
    def update_membership(
        db: Session, membership_id: int, data: MembershipUpdate
    ) -> Membresias:
        membership = MembershipService.get_membership(db, membership_id)
        changes = data.model_dump(exclude_unset=True)

        new_name = changes.get("name")
        if new_name is not None and MembershipService._name_exists(
            db, new_name, exclude_id=membership.id
        ):
            raise MembershipNameExistsError(
                "Ya existe una membresía con ese nombre."
            )

        for field, value in changes.items():
            setattr(membership, field, value)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise MembershipNameExistsError(
                "Ya existe una membresía con ese nombre."
            )
        except Exception:
            db.rollback()
            raise

        db.refresh(membership)
        return membership

    @staticmethod
    def delete_membership(db: Session, membership_id: int) -> None:
        membership = MembershipService.get_membership(db, membership_id)

        has_assignments = db.scalar(
            select(MembershipAssignment.id)
            .where(MembershipAssignment.membership_id == membership.id)
            .limit(1)
        )
        if has_assignments is not None:
            raise MembershipInUseError(
                "La membresía tiene asignaciones y no puede eliminarse. "
                "Desactívala en su lugar."
            )

        try:
            db.delete(membership)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise MembershipInUseError(
                "La membresía tiene asignaciones y no puede eliminarse. "
                "Desactívala en su lugar."
            )
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def assign_membership(
        db: Session, membership_id: int, data: AssignmentCreate
    ) -> MembershipAssignment:
        membership = MembershipService.get_membership(db, membership_id)
        if not membership.is_active:
            raise MembershipInactiveError("La membresía está inactiva.")

        user = db.get(User, data.user_id)
        if user is None:
            raise UserNotFoundError("Cliente no encontrado.")

        start = data.start_date or date.today()
        end = start + timedelta(days=membership.duration_days)

        overlapping = db.scalar(
            select(MembershipAssignment.id)
            .where(
                MembershipAssignment.user_id == data.user_id,
                MembershipAssignment.status == MembershipAssignmentStatus.ACTIVA,
                MembershipAssignment.end_date >= start,
                MembershipAssignment.start_date <= end,
            )
            .limit(1)
        )
        if overlapping is not None:
            raise ActiveAssignmentExistsError(
                "El cliente ya tiene una membresía activa en ese periodo."
            )

        assignment = MembershipAssignment(
            user_id=data.user_id,
            membership_id=membership.id,
            start_date=start,
            end_date=end,
            status=MembershipAssignmentStatus.ACTIVA,
            price_paid=(
                data.price_paid if data.price_paid is not None else membership.price
            ),
            notes=data.notes,
        )

        try:
            db.add(assignment)
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(assignment)
        return assignment
