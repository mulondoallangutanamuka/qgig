"""add_expiry_date_to_jobs

Revision ID: 14a8ca2ff8af
Revises: 9f4d64756c60
Create Date: 2025-12-30 16:33:05.958732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14a8ca2ff8af'
down_revision: Union[str, Sequence[str], None] = '9f4d64756c60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('jobs', sa.Column('expiry_date', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_jobs_expiry_date'), 'jobs', ['expiry_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_jobs_expiry_date'), table_name='jobs')
    op.drop_column('jobs', 'expiry_date')
