"""unir migraciones del equipo

Revision ID: 7cc127da6408
Revises: 0d73db355b8e, cbcd8ad4b92f
Create Date: 2026-11-26 21:15:44.068553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cc127da6408'
down_revision: Union[str, Sequence[str], None] = ('0d73db355b8e', 'cbcd8ad4b92f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
