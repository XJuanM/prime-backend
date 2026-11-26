from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asignacion_membresias import (
    MembershipAssignment,
    MembershipAssignmentStatus,
)
from app.models.membresias import Membresias
from app.models.usuarios import User
from app.schemas.membership_assignment import MembershipAssignmentCreate


class AssignmentError(Exception):
    pass


class UserNotFoundError(AssignmentError):
    pass


class MembershipUnavailableError(AssignmentError):
    pass


class ActiveAssignmentExistsError(AssignmentError):
    pass


class MembershipAssignmentService:

    @staticmethod
    def assign_membership(
        db: Session, data: MembershipAssignmentCreate
    ) -> MembershipAssignment:
        user = db.get(User, data.user_id)
        if user is None:
            raise UserNotFoundError("Cliente no encontrado.")

        membership = db.get(Membresias, data.membership_id)
        if membership is None or not membership.is_active:
            raise MembershipUnavailableError(
                "La membresía no existe o está inactiva."
            )

        start = data.start_date or date.today()
        # Si dura 30 días y empieza el día 1, termina el día 31.
        end = start + timedelta(days=membership.duration_days)

        # Evita solapar con una asignación activa vigente.
        overlapping = db.scalar(
            select(MembershipAssignment.id)
            .where(
                MembershipAssignment.user_id == user.id_usuario,
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
            user_id=user.id_usuario,
            membership_id=membership.id,
            start_date=start,
            end_date=end,
            status=MembershipAssignmentStatus.ACTIVA,
            price_paid=(
                data.price_paid
                if data.price_paid is not None
                else membership.price
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