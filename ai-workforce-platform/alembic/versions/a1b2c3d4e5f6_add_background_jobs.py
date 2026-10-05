"""add background_jobs table

Revision ID: a1b2c3d4e5f6
Revises: 5ef451de3c5c
Create Date: 2026-07-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5ef451de3c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- background_jobs ---
    op.create_table(
        'background_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('goal_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='queued', nullable=False),
        sa.Column('payload', JSON, nullable=True),
        sa.Column('result', JSON, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('worker_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_background_jobs_status', 'background_jobs', ['status'])
    op.create_index('ix_background_jobs_goal_id', 'background_jobs', ['goal_id'])
    op.create_index('ix_background_jobs_created_at', 'background_jobs', ['created_at'])
    op.create_index('ix_background_jobs_job_type', 'background_jobs', ['job_type'])


def downgrade() -> None:
    op.drop_index('ix_background_jobs_job_type', table_name='background_jobs')
    op.drop_index('ix_background_jobs_created_at', table_name='background_jobs')
    op.drop_index('ix_background_jobs_goal_id', table_name='background_jobs')
    op.drop_index('ix_background_jobs_status', table_name='background_jobs')
    op.drop_table('background_jobs')
