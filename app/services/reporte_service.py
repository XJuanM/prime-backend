from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.asignacion_membresias import MembershipAssignment
from app.models.membresias import Membresias
from app.models.reportes import Reporte, ReporteTipo
from app.models.usuarios import User
from app.schemas.reporte import ReporteCreate, ReporteUpdate
from app.services.reporte_pdf import build_report_pdf

TIPO_LABELS = {
    ReporteTipo.MEMBRESIAS: "Membresías e ingresos",
    ReporteTipo.USUARIOS: "Altas de usuarios",
}


class ReporteError(Exception):
    pass


class ReporteNotFoundError(ReporteError):
    pass


class ReporteFechasInvalidasError(ReporteError):
    pass


def _num(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


class ReporteService:

    # ------------------------------------------------------------------ CRUD
    @staticmethod
    def list_reportes(
        db: Session,
        *,
        search: str | None,
        tipo: ReporteTipo | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Reporte], int]:
        filters = []
        if search:
            filters.append(Reporte.titulo.ilike(f"%{search.strip()}%"))
        if tipo is not None:
            filters.append(Reporte.tipo == tipo)

        total = db.scalar(select(func.count(Reporte.id)).where(*filters)) or 0
        items = db.scalars(
            select(Reporte)
            .where(*filters)
            .order_by(Reporte.created_at.desc(), Reporte.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total

    @staticmethod
    def get_reporte(db: Session, reporte_id: int) -> Reporte:
        reporte = db.get(Reporte, reporte_id)
        if reporte is None:
            raise ReporteNotFoundError("Reporte no encontrado.")
        return reporte

    @staticmethod
    def create_reporte(
        db: Session, data: ReporteCreate, created_by: int
    ) -> Reporte:
        reporte = Reporte(
            titulo=data.titulo,
            tipo=data.tipo,
            fecha_inicio=data.fecha_inicio,
            fecha_fin=data.fecha_fin,
            descripcion=data.descripcion,
            created_by=created_by,
        )
        try:
            db.add(reporte)
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(reporte)
        return reporte

    @staticmethod
    def update_reporte(
        db: Session, reporte_id: int, data: ReporteUpdate
    ) -> Reporte:
        reporte = ReporteService.get_reporte(db, reporte_id)
        changes = data.model_dump(exclude_unset=True)

        # Las fechas se validan combinando lo enviado con lo guardado.
        inicio = changes.get("fecha_inicio", reporte.fecha_inicio)
        fin = changes.get("fecha_fin", reporte.fecha_fin)
        if fin < inicio:
            raise ReporteFechasInvalidasError(
                "La fecha fin no puede ser anterior a la fecha inicio."
            )

        for field, value in changes.items():
            setattr(reporte, field, value)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(reporte)
        return reporte

    @staticmethod
    def delete_reporte(db: Session, reporte_id: int) -> None:
        reporte = ReporteService.get_reporte(db, reporte_id)
        try:
            db.delete(reporte)
            db.commit()
        except Exception:
            db.rollback()
            raise

    # ------------------------------------------------------------- Contenido
    @staticmethod
    def build_content(db: Session, reporte: Reporte) -> dict:
        if reporte.tipo == ReporteTipo.MEMBRESIAS:
            return ReporteService._contenido_membresias(
                db, reporte.fecha_inicio, reporte.fecha_fin
            )
        return ReporteService._contenido_usuarios(
            db, reporte.fecha_inicio, reporte.fecha_fin
        )

    @staticmethod
    def _contenido_membresias(db: Session, inicio: date, fin: date) -> dict:
        """Asignaciones cuya fecha de inicio cae dentro del periodo."""
        in_range = (
            MembershipAssignment.start_date >= inicio,
            MembershipAssignment.start_date <= fin,
        )

        por_plan = db.execute(
            select(
                Membresias.name,
                func.count(MembershipAssignment.id),
                func.coalesce(func.sum(MembershipAssignment.price_paid), 0),
            )
            .join(
                Membresias,
                Membresias.id == MembershipAssignment.membership_id,
            )
            .where(*in_range)
            .group_by(Membresias.name)
            .order_by(func.count(MembershipAssignment.id).desc())
        ).all()

        por_estado = db.execute(
            select(
                MembershipAssignment.status,
                func.count(MembershipAssignment.id),
            )
            .where(*in_range)
            .group_by(MembershipAssignment.status)
        ).all()

        total = sum(row[1] for row in por_plan)
        ingresos = sum(_num(row[2]) for row in por_plan)

        indicadores = {
            "Total de asignaciones": total,
            "Ingresos totales": round(ingresos, 2),
        }
        for estado, cantidad in por_estado:
            indicadores[f"Asignaciones {estado.value.lower()}s"] = cantidad

        return {
            "indicadores": indicadores,
            "columnas": ["Plan", "Asignaciones", "Ingresos"],
            "filas": [
                [nombre, cantidad, round(_num(suma), 2)]
                for nombre, cantidad, suma in por_plan
            ],
        }

    @staticmethod
    def _contenido_usuarios(db: Session, inicio: date, fin: date) -> dict:
        """Usuarios creados dentro del periodo, agrupados por rol."""
        desde = datetime.combine(inicio, time.min)
        hasta = datetime.combine(fin + timedelta(days=1), time.min)

        rows = db.execute(
            select(
                User.tipo_rol,
                func.count(User.id_usuario),
                func.coalesce(
                    func.sum(case((User.is_active.is_(True), 1), else_=0)), 0
                ),
            )
            .where(User.created_at >= desde, User.created_at < hasta)
            .group_by(User.tipo_rol)
            .order_by(func.count(User.id_usuario).desc())
        ).all()

        total = sum(row[1] for row in rows)
        activos = sum(int(row[2]) for row in rows)

        return {
            "indicadores": {
                "Usuarios nuevos": total,
                "Activos": activos,
                "Inactivos": total - activos,
            },
            "columnas": ["Rol", "Usuarios nuevos", "Activos"],
            "filas": [
                [rol.value, cantidad, int(act)] for rol, cantidad, act in rows
            ],
        }

    # ------------------------------------------------------------------- PDF
    @staticmethod
    def generate_pdf(
        db: Session, reporte: Reporte, generado_por: str
    ) -> bytes:
        contenido = ReporteService.build_content(db, reporte)
        return build_report_pdf(
            titulo=reporte.titulo,
            tipo_label=TIPO_LABELS[reporte.tipo],
            fecha_inicio=reporte.fecha_inicio,
            fecha_fin=reporte.fecha_fin,
            descripcion=reporte.descripcion,
            indicadores=contenido["indicadores"],
            columnas=contenido["columnas"],
            filas=contenido["filas"],
            generado_por=generado_por,
        )