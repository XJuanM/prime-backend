from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.enums.muscle_group import MuscleGroup
from app.models.progreso import ProgressRecord
from app.schemas.progress import (
    MonthlyProgressResponse,
    ProgressCreate,
    ProgressUpdate,
    WeekVariation,
)

WEEKS_PER_MONTH = 4
MAX_SESSIONS_PER_WEEK = 3


class ProgressServiceError(Exception):
    pass


class ProgressNotFoundError(ProgressServiceError):
    pass


class ProgressAlreadyExistsError(ProgressServiceError):
    pass


class ProgressWeekFullError(ProgressAlreadyExistsError):
    """Ya hay 3 sesiones de ese músculo en esa semana (el router responde 409)."""


class ProgressIncompleteMonthError(ProgressServiceError):
    pass


class ProgressService:
    # ---------- Registro ----------
    @staticmethod
    def create_record(
        db: Session, user_id: int, data: ProgressCreate
    ) -> ProgressRecord:
        used = set(
            db.scalars(
                select(ProgressRecord.session_number).where(
                    ProgressRecord.id_usuario == user_id,
                    ProgressRecord.muscle_group == data.muscle_group,
                    ProgressRecord.year == data.year,
                    ProgressRecord.month == data.month,
                    ProgressRecord.week_of_month == data.week_of_month,
                )
            )
        )

        free = [n for n in range(1, MAX_SESSIONS_PER_WEEK + 1) if n not in used]
        if not free:
            raise ProgressWeekFullError(
                f"Ya registraste las {MAX_SESSIONS_PER_WEEK} sesiones máximas "
                "de este músculo en esa semana."
            )

        record = ProgressRecord(
            id_usuario=user_id, session_number=free[0], **data.model_dump()
        )
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ProgressAlreadyExistsError(
                "No se pudo registrar la sesión (posible registro simultáneo). "
                "Intenta de nuevo."
            )
        db.refresh(record)
        return record

    @staticmethod
    def update_record(
        db: Session, user_id: int, progress_id: int, data: ProgressUpdate
    ) -> ProgressRecord:
        record = ProgressService.get_record(db, user_id, progress_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(record, field, value)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_record(db: Session, user_id: int, progress_id: int) -> None:
        record = ProgressService.get_record(db, user_id, progress_id)
        db.delete(record)
        db.commit()

    # ---------- Consulta ----------
    @staticmethod
    def get_record(db: Session, user_id: int, progress_id: int) -> ProgressRecord:
        record = db.scalar(
            select(ProgressRecord).where(
                ProgressRecord.id_progreso == progress_id,
                ProgressRecord.id_usuario == user_id,
            )
        )
        if not record:
            raise ProgressNotFoundError("Registro de progreso no encontrado.")
        return record

    @staticmethod
    def list_records(
        db: Session,
        user_id: int,
        muscle_group: MuscleGroup | None = None,
        year: int | None = None,
        month: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProgressRecord]:
        stmt = select(ProgressRecord).where(ProgressRecord.id_usuario == user_id)
        if muscle_group:
            stmt = stmt.where(ProgressRecord.muscle_group == muscle_group)
        if year:
            stmt = stmt.where(ProgressRecord.year == year)
        if month:
            stmt = stmt.where(ProgressRecord.month == month)

        stmt = (
            stmt.order_by(
                ProgressRecord.year.desc(),
                ProgressRecord.month.desc(),
                ProgressRecord.week_of_month.asc(),
                ProgressRecord.session_number.asc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt))

    # ---------- Métricas ----------
    @staticmethod
    def monthly_progress(
        db: Session,
        user_id: int,
        muscle_group: MuscleGroup,
        year: int,
        month: int,
    ) -> MonthlyProgressResponse:
        records = list(
            db.scalars(
                select(ProgressRecord).where(
                    ProgressRecord.id_usuario == user_id,
                    ProgressRecord.muscle_group == muscle_group,
                    ProgressRecord.year == year,
                    ProgressRecord.month == month,
                )
            )
        )

        by_week: dict[int, list[ProgressRecord]] = defaultdict(list)
        for r in records:
            by_week[r.week_of_month].append(r)

        missing = [w for w in range(1, WEEKS_PER_MONTH + 1) if w not in by_week]
        if missing:
            raise ProgressIncompleteMonthError(
                "Se requiere al menos una sesión en cada una de las 4 semanas "
                f"del mes. Faltan las semanas: {', '.join(map(str, missing))}."
            )

        weeks: list[WeekVariation] = []
        changes: list[float] = []
        previous: float | None = None
        averages: list[float] = []

        for week in range(1, WEEKS_PER_MONTH + 1):
            sessions = by_week[week]
            avg = sum(s.volume for s in sessions) / len(sessions)
            averages.append(avg)

            change = None
            if previous is not None:
                change = round((avg - previous) / previous * 100, 2)
                changes.append(change)

            weeks.append(
                WeekVariation(
                    week_of_month=week,
                    sessions=len(sessions),
                    avg_session_volume=round(avg, 2),
                    change_vs_previous_pct=change,
                )
            )
            previous = avg

        initial, final = averages[0], averages[-1]

        return MonthlyProgressResponse(
            user_id=user_id,
            muscle_group=muscle_group,
            year=year,
            month=month,
            initial_volume=round(initial, 2),
            final_volume=round(final, 2),
            progress_pct=round((final - initial) / initial * 100, 2),
            average_weekly_change_pct=round(sum(changes) / len(changes), 2),
            weeks=weeks,
        )
