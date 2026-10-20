"""initial_schema

Revision ID: 1333f3d04ff1
Revises: 
Create Date: 2026-10-20 15:25:03.567134

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1333f3d04ff1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Projects Table
    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_projects'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_projects_owner_id_users', ondelete='RESTRICT'),
    )
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])

    # 3. Project Members Table
    op.create_table(
        'project_members',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('project_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), server_default=sa.text("'member'"), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_project_members'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_project_members_project_id_projects', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_project_members_user_id_users', ondelete='CASCADE'),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_members_project_user'),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member')", name='ck_project_members_role'),
    )
    op.create_index('ix_project_members_project_id', 'project_members', ['project_id'])
    op.create_index('ix_project_members_user_id', 'project_members', ['user_id'])

    # 4. Tasks Table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('project_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assignee_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('created_by_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'todo'"), nullable=False),
        sa.Column('priority', sa.String(length=50), server_default=sa.text("'medium'"), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('position', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_tasks'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_tasks_project_id_projects', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], name='fk_tasks_assignee_id_users', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name='fk_tasks_created_by_id_users', ondelete='RESTRICT'),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'done')", name='ck_tasks_status'),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='ck_tasks_priority'),
    )
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('ix_tasks_assignee_id', 'tasks', ['assignee_id'])
    op.create_index('ix_tasks_created_by_id', 'tasks', ['created_by_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_priority', 'tasks', ['priority'])

    # 5. Comments Table
    op.create_table(
        'comments',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('task_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('author_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_comments'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_comments_task_id_tasks', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], name='fk_comments_author_id_users', ondelete='CASCADE'),
    )
    op.create_index('ix_comments_task_id', 'comments', ['task_id'])
    op.create_index('ix_comments_author_id', 'comments', ['author_id'])

    # 6. Notifications Table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_notifications'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notifications_user_id_users', ondelete='CASCADE'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    # 7. Activity Logs Table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('project_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('actor_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            'details',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=True,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_activity_logs'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_activity_logs_project_id_projects', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name='fk_activity_logs_actor_id_users', ondelete='SET NULL'),
    )
    op.create_index('ix_activity_logs_project_id', 'activity_logs', ['project_id'])
    op.create_index('ix_activity_logs_actor_id', 'activity_logs', ['actor_id'])
    op.create_index('ix_activity_logs_entity_id', 'activity_logs', ['entity_id'])
    op.create_index('ix_activity_logs_created_at', 'activity_logs', ['created_at'])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table('activity_logs')
    op.drop_table('notifications')
    op.drop_table('comments')
    op.drop_table('tasks')
    op.drop_table('project_members')
    op.drop_table('projects')
    op.drop_table('users')
