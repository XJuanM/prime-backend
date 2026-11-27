"""crear tabla reportes

Revision ID: b7d41e9c2a10
Revises: 9a48cf41652b
Create Date: 2026-11-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b7d41e9c2a10'
down_revision: Union[str, Sequence[str], None] = '341c068e2287'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        
        "reportes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("titulo", sa.String(length=150), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "membresias",
                "usuarios",
                name="ck_reportes_tipo",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "fecha_fin >= fecha_inicio", name="ck_reportes_fechas_validas"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["usuarios.id_usuario"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reportes_tipo_created_at", "reportes", ["tipo", "created_at"]
    )

def downgrade() -> None:
    op.drop_index("ix_reportes_tipo_created_at", table_name="reportes")
    op.drop_table("reportes")