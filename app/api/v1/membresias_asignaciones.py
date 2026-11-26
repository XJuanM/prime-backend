from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.membresias import require_admin  # ajusta el import a tu nombre real de módulo
from app.infrastructure.database.session import get_db
from app.schemas.membership_assignament import (
    MembershipAssignmentCreate,
    MembershipAssignmentResponse,
)
from app.services.membership_assignament_service import (
    ActiveAssignmentExistsError,
    MembershipAssignmentService,
    MembershipUnavailableError,
    UserNotFoundError,
)

router = APIRouter(
    prefix="/asignaciones-membresia",
    tags=["Asignación de membresías"],
    dependencies=[Depends(require_admin)],
)


@router.post(
    "",
    response_model=MembershipAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_membership(
    data: MembershipAssignmentCreate,
    db: Session = Depends(get_db),
):
    """Asigna una membresía a un cliente."""
    try:
        return MembershipAssignmentService.assign_membership(db, data)
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except MembershipUnavailableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ActiveAssignmentExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))