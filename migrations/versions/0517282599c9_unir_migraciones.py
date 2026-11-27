"""unir migraciones

Revision ID: 0517282599c9
Revises: 9a48cf41652b, a0c96725f30f
Create Date: 2026-11-26 19:10:07.606140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0517282599c9'
down_revision: Union[str, Sequence[str], None] = ('9a48cf41652b', 'a0c96725f30f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
