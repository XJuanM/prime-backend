import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.domain.enums.user_role import Roles
from app.infrastructure.database.session import get_db
from app.models.reportes import ReporteTipo
from app.models.usuarios import User
from app.schemas.reporte import (
    ReporteContenido,
    ReporteCreate,
    ReporteDetalleResponse,
    ReporteListResponse,
    ReporteResponse,
    ReporteUpdate,
)
from app.services.reporte_service import (
    ReporteFechasInvalidasError,
    ReporteNotFoundError,
    ReporteService,
)

# Roles con acceso al módulo de reportes. Agrega Roles.ENTRENADOR si los
# entrenadores también deben consultarlos.
ROLES_PERMITIDOS = {Roles.SUPER_ADMIN, Roles.ADMINISTRADOR}


def require_reportes_access(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ROLES_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para gestionar reportes.",
        )
    return current_user


router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    dependencies=[Depends(require_reportes_access)],
)


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "reporte"


@router.get("", response_model=ReporteListResponse)
def list_reportes(
    search: str | None = Query(default=None, max_length=100),
    tipo: ReporteTipo | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """RF-041: lista los reportes guardados con filtros y paginación."""
    items, total = ReporteService.list_reportes(
        db, search=search, tipo=tipo, page=page, page_size=page_size
    )
    return ReporteListResponse(
        items=[ReporteResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=ReporteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reporte(
    data: ReporteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reportes_access),
):
    """RF-038: crea (guarda) un reporte con su tipo y periodo."""
    return ReporteService.create_reporte(db, data, created_by=current_user.id)


@router.get("/{reporte_id}", response_model=ReporteDetalleResponse)
def get_reporte(
    reporte_id: int,
    db: Session = Depends(get_db),
):
    """RF-041: consulta un reporte con sus datos calculados al momento."""
    try:
        reporte = ReporteService.get_reporte(db, reporte_id)
    except ReporteNotFoundError as exc:
        raise _not_found(exc)

    contenido = ReporteService.build_content(db, reporte)
    base = ReporteResponse.model_validate(reporte)
    return ReporteDetalleResponse(
        **base.model_dump(),
        contenido=ReporteContenido(**contenido),
    )


@router.patch("/{reporte_id}", response_model=ReporteResponse)
def update_reporte(
    reporte_id: int,
    data: ReporteUpdate,
    db: Session = Depends(get_db),
):
    """RF-039: actualiza parcialmente un reporte (solo los campos enviados)."""
    try:
        return ReporteService.update_reporte(db, reporte_id, data)
    except ReporteNotFoundError as exc:
        raise _not_found(exc)
    except ReporteFechasInvalidasError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.delete("/{reporte_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reporte(
    reporte_id: int,
    db: Session = Depends(get_db),
):
    """RF-040: elimina un reporte."""
    try:
        ReporteService.delete_reporte(db, reporte_id)
    except ReporteNotFoundError as exc:
        raise _not_found(exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{reporte_id}/descargar",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Archivo PDF del reporte.",
        }
    },
)
def download_reporte(
    reporte_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reportes_access),
):
    """RF-041: descarga el reporte en PDF."""
    try:
        reporte = ReporteService.get_reporte(db, reporte_id)
    except ReporteNotFoundError as exc:
        raise _not_found(exc)

    generado_por = (
        " ".join(filter(None, [current_user.first_name, current_user.last_name]))
        or current_user.email
        or f"usuario {current_user.id}"
    )
    pdf = ReporteService.generate_pdf(db, reporte, generado_por)

    filename = f"reporte-{reporte.id}-{_slug(reporte.titulo)}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )