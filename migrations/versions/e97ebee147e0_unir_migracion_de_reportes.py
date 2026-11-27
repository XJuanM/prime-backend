"""unir migracion de reportes

Revision ID: e97ebee147e0
Revises: 15b276d59f9c, b7d41e9c2a10
Create Date: 2026-11-27 06:49:18.277578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e97ebee147e0'
down_revision: Union[str, Sequence[str], None] = ('15b276d59f9c', 'b7d41e9c2a10')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
