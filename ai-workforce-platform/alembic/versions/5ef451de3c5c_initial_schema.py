"""initial schema

Revision ID: 5ef451de3c5c
Revises: 
Create Date: 2026-07-30 23:57:02.678585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = '5ef451de3c5c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- companies ---
    op.create_table(
        'companies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('plan', sa.String(50), server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- departments ---
    op.create_table(
        'departments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- teams ---
    op.create_table(
        'teams',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('department_id', UUID(as_uuid=True), sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- agents ---
    op.create_table(
        'agents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('template_id', UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='idle'),
        sa.Column('system_prompt', sa.String(10000), nullable=True),
        sa.Column('model', sa.String(100), server_default='gpt-4o-mini'),
        sa.Column('config', JSON, nullable=True),
        sa.Column('performance_score', sa.Float, server_default='0.0'),
        sa.Column('total_tasks', sa.Integer, server_default='0'),
        sa.Column('successful_tasks', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- agent_capabilities ---
    op.create_table(
        'agent_capabilities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('capability_name', sa.String(100), nullable=False),
        sa.Column('proficiency', sa.String(50), server_default='competent'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- agent_sessions ---
    op.create_table(
        'agent_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('task_id', UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tokens_used', sa.Integer, server_default='0'),
        sa.Column('cost_usd', sa.Float, server_default='0.0'),
        sa.Column('status', sa.String(50), server_default='active'),
    )

    # --- projects ---
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('goal_text', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), server_default='planning'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- tasks ---
    op.create_table(
        'tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('priority', sa.Integer, server_default='3'),
        sa.Column('assigned_agent_id', UUID(as_uuid=True), nullable=True),
        sa.Column('wave_number', sa.Integer, server_default='0'),
        sa.Column('output', JSON, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # --- task_dependencies ---
    op.create_table(
        'task_dependencies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('depends_on_id', UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- task_checkpoints ---
    op.create_table(
        'task_checkpoints',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('state', JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- episodic_memory ---
    op.create_table(
        'episodic_memory',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', JSON, nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- semantic_memory ---
    op.create_table(
        'semantic_memory',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_type', sa.String(100), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', JSON, nullable=True),
        sa.Column('confidence', sa.Float, server_default='0.5'),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- tools ---
    op.create_table(
        'tools',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tool_type', sa.String(100), nullable=False),
        sa.Column('capabilities', JSON, server_default='{}'),
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('config', JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- agent_tools ---
    op.create_table(
        'agent_tools',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('tool_id', UUID(as_uuid=True), sa.ForeignKey('tools.id'), nullable=False),
        sa.Column('permissions', JSON, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- users ---
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('role', sa.String(50), server_default='member'),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('agent_tools')
    op.drop_table('tools')
    op.drop_table('semantic_memory')
    op.drop_table('episodic_memory')
    op.drop_table('task_checkpoints')
    op.drop_table('task_dependencies')
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('agent_sessions')
    op.drop_table('agent_capabilities')
    op.drop_table('agents')
    op.drop_table('teams')
    op.drop_table('departments')
    op.drop_table('companies')
