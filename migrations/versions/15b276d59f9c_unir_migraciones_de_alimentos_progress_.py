"""unir migraciones de alimentos, progress y dietas

Revision ID: 15b276d59f9c
Revises: 5cbee7120bf8, 7cc127da6408
Create Date: 2026-11-26 21:41:27.947040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15b276d59f9c'
down_revision: Union[str, Sequence[str], None] = ('5cbee7120bf8', '7cc127da6408')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
