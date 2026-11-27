"""unir_migraciones_dietas

Revision ID: 5cbee7120bf8
Revises: 0b43095280f6, 0d73db355b8e, 9a48cf41652b
Create Date: 2026-11-26 21:33:41.807980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cbee7120bf8'
down_revision: Union[str, Sequence[str], None] = ('0b43095280f6', '0d73db355b8e', '9a48cf41652b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
