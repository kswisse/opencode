"""add request_id to background_jobs

Revision ID: obs001
Revises: 
Create Date: 2026-07-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'obs001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('background_jobs', sa.Column('request_id', sa.String(255), nullable=True))
    op.create_index('ix_background_jobs_request_id', 'background_jobs', ['request_id'])


def downgrade() -> None:
    op.drop_index('ix_background_jobs_request_id', table_name='background_jobs')
    op.drop_column('background_jobs', 'request_id')
