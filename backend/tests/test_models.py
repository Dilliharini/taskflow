import uuid
import pytest
from sqlalchemy import inspect
from app.models import (
    Base,
    User,
    Project,
    ProjectMember,
    Task,
    Comment,
    Notification,
    ActivityLog,
    ProjectRole,
    TaskStatus,
    TaskPriority,
)
from app.schemas.user import UserRead, UserCreate, UserInDB


def test_model_imports_and_table_registration():
    """Verify all models are successfully imported and registered in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "users",
        "projects",
        "project_members",
        "tasks",
        "comments",
        "notifications",
        "activity_logs",
    }
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"


def test_required_columns_and_primary_keys():
    """Verify primary keys and required (non-null) columns across all entities."""
    # 1. Users table
    users_table = Base.metadata.tables["users"]
    assert "id" in users_table.primary_key.columns
    assert users_table.c.name.nullable is False
    assert users_table.c.email.nullable is False
    assert users_table.c.password_hash.nullable is False
    assert users_table.c.is_active.nullable is False
    assert users_table.c.created_at.nullable is False
    assert users_table.c.updated_at.nullable is False

    # 2. Projects table
    projects_table = Base.metadata.tables["projects"]
    assert "id" in projects_table.primary_key.columns
    assert projects_table.c.name.nullable is False
    assert projects_table.c.description.nullable is True
    assert projects_table.c.owner_id.nullable is False

    # 3. Project Members table
    pm_table = Base.metadata.tables["project_members"]
    assert "id" in pm_table.primary_key.columns
    assert pm_table.c.project_id.nullable is False
    assert pm_table.c.user_id.nullable is False
    assert pm_table.c.role.nullable is False

    # 4. Tasks table
    tasks_table = Base.metadata.tables["tasks"]
    assert "id" in tasks_table.primary_key.columns
    assert tasks_table.c.project_id.nullable is False
    assert tasks_table.c.title.nullable is False
    assert tasks_table.c.description.nullable is True
    assert tasks_table.c.assignee_id.nullable is True
    assert tasks_table.c.created_by_id.nullable is False
    assert tasks_table.c.status.nullable is False
    assert tasks_table.c.priority.nullable is False
    assert tasks_table.c.position.nullable is False

    # 5. Comments table
    comments_table = Base.metadata.tables["comments"]
    assert "id" in comments_table.primary_key.columns
    assert comments_table.c.task_id.nullable is False
    assert comments_table.c.author_id.nullable is False
    assert comments_table.c.content.nullable is False

    # 6. Notifications table
    notifications_table = Base.metadata.tables["notifications"]
    assert "id" in notifications_table.primary_key.columns
    assert notifications_table.c.user_id.nullable is False
    assert notifications_table.c.type.nullable is False
    assert notifications_table.c.message.nullable is False
    assert notifications_table.c.is_read.nullable is False
    assert notifications_table.c.read_at.nullable is True

    # 7. Activity Logs table
    activity_table = Base.metadata.tables["activity_logs"]
    assert "id" in activity_table.primary_key.columns
    assert activity_table.c.project_id.nullable is False
    assert activity_table.c.actor_id.nullable is True
    assert activity_table.c.action.nullable is False
    assert activity_table.c.entity_type.nullable is False
    assert activity_table.c.details.nullable is True


def test_foreign_key_definitions():
    """Verify that foreign keys and delete behaviors match design requirements."""
    # Projects -> Users
    projects_table = Base.metadata.tables["projects"]
    owner_fk = next(fk for fk in projects_table.foreign_keys if fk.parent.name == "owner_id")
    assert owner_fk.target_fullname == "users.id"
    assert owner_fk.ondelete == "RESTRICT"

    # Project Members -> Projects, Users
    pm_table = Base.metadata.tables["project_members"]
    pm_project_fk = next(fk for fk in pm_table.foreign_keys if fk.parent.name == "project_id")
    assert pm_project_fk.target_fullname == "projects.id"
    assert pm_project_fk.ondelete == "CASCADE"
    pm_user_fk = next(fk for fk in pm_table.foreign_keys if fk.parent.name == "user_id")
    assert pm_user_fk.target_fullname == "users.id"
    assert pm_user_fk.ondelete == "CASCADE"

    # Tasks -> Projects, Users
    tasks_table = Base.metadata.tables["tasks"]
    task_proj_fk = next(fk for fk in tasks_table.foreign_keys if fk.parent.name == "project_id")
    assert task_proj_fk.target_fullname == "projects.id"
    assert task_proj_fk.ondelete == "CASCADE"
    task_assignee_fk = next(fk for fk in tasks_table.foreign_keys if fk.parent.name == "assignee_id")
    assert task_assignee_fk.target_fullname == "users.id"
    assert task_assignee_fk.ondelete == "SET NULL"
    task_creator_fk = next(fk for fk in tasks_table.foreign_keys if fk.parent.name == "created_by_id")
    assert task_creator_fk.target_fullname == "users.id"
    assert task_creator_fk.ondelete == "RESTRICT"

    # Comments -> Tasks, Users
    comments_table = Base.metadata.tables["comments"]
    c_task_fk = next(fk for fk in comments_table.foreign_keys if fk.parent.name == "task_id")
    assert c_task_fk.target_fullname == "tasks.id"
    assert c_task_fk.ondelete == "CASCADE"
    c_author_fk = next(fk for fk in comments_table.foreign_keys if fk.parent.name == "author_id")
    assert c_author_fk.target_fullname == "users.id"
    assert c_author_fk.ondelete == "CASCADE"

    # Notifications -> Users
    notif_table = Base.metadata.tables["notifications"]
    notif_user_fk = next(fk for fk in notif_table.foreign_keys if fk.parent.name == "user_id")
    assert notif_user_fk.target_fullname == "users.id"
    assert notif_user_fk.ondelete == "CASCADE"

    # Activity Logs -> Projects, Users
    act_table = Base.metadata.tables["activity_logs"]
    act_proj_fk = next(fk for fk in act_table.foreign_keys if fk.parent.name == "project_id")
    assert act_proj_fk.target_fullname == "projects.id"
    assert act_proj_fk.ondelete == "CASCADE"
    act_actor_fk = next(fk for fk in act_table.foreign_keys if fk.parent.name == "actor_id")
    assert act_actor_fk.target_fullname == "users.id"
    assert act_actor_fk.ondelete == "SET NULL"


def test_unique_user_email_constraint():
    """Verify that email on users table has unique constraint or index."""
    users_table = Base.metadata.tables["users"]
    email_col = users_table.c.email
    assert email_col.unique is True or any(
        "email" in [c.name for c in idx.columns] and idx.unique for idx in users_table.indexes
    )


def test_duplicate_project_membership_constraint():
    """Verify that a compound unique constraint exists on (project_id, user_id)."""
    pm_table = Base.metadata.tables["project_members"]
    unique_constraints = [
        c for c in pm_table.constraints
        if hasattr(c, "columns") and {col.name for col in c.columns} == {"project_id", "user_id"}
    ]
    assert len(unique_constraints) > 0, "Missing unique constraint on project_members(project_id, user_id)"


def test_task_defaults_and_nullable_fields():
    """Verify default values and check constraints on Task entity."""
    tasks_table = Base.metadata.tables["tasks"]
    assert tasks_table.c.description.nullable is True
    assert tasks_table.c.due_date.nullable is True
    assert tasks_table.c.assignee_id.nullable is True

    # Check constraints on status and priority
    check_constraints = [c.sqltext.text for c in tasks_table.constraints if hasattr(c, "sqltext")]
    assert any("status IN" in sql for sql in check_constraints), "Missing check constraint for task status"
    assert any("priority IN" in sql for sql in check_constraints), "Missing check constraint for task priority"


def test_model_relationships():
    """Verify that ORM relationships are properly wired without circular mapping errors."""
    mapper_user = inspect(User)
    assert "owned_projects" in mapper_user.relationships
    assert "memberships" in mapper_user.relationships
    assert "assigned_tasks" in mapper_user.relationships
    assert "created_tasks" in mapper_user.relationships
    assert "comments" in mapper_user.relationships
    assert "notifications" in mapper_user.relationships
    assert "activities" in mapper_user.relationships

    mapper_project = inspect(Project)
    assert "owner" in mapper_project.relationships
    assert "members" in mapper_project.relationships
    assert "tasks" in mapper_project.relationships
    assert "activity_logs" in mapper_project.relationships

    mapper_task = inspect(Task)
    assert "project" in mapper_task.relationships
    assert "assignee" in mapper_task.relationships
    assert "creator" in mapper_task.relationships
    assert "comments" in mapper_task.relationships

    mapper_comment = inspect(Comment)
    assert "task" in mapper_comment.relationships
    assert "author" in mapper_comment.relationships

    mapper_notification = inspect(Notification)
    assert "user" in mapper_notification.relationships

    mapper_activity = inspect(ActivityLog)
    assert "project" in mapper_activity.relationships
    assert "actor" in mapper_activity.relationships


def test_pydantic_schemas_security():
    """Verify that public User schemas never expose password_hash."""
    user_read_fields = UserRead.model_fields.keys()
    assert "password_hash" not in user_read_fields, "Security violation: password_hash found in UserRead schema"
    assert "password" not in user_read_fields, "Security violation: password found in UserRead schema"

    # UserInDB is the internal-only schema that includes password_hash
    assert "password_hash" in UserInDB.model_fields.keys()
