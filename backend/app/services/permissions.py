import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Project, ProjectMember, ProjectRole, Task, User


def get_project_access(db: Session, project_id: uuid.UUID, user: User) -> tuple[Project, str]:
    row = db.execute(
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.id == project_id, ProjectMember.user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return row[0], row[1]


def require_role(role: str, *allowed: ProjectRole) -> None:
    if role not in {item.value for item in allowed}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action.")


def get_project_task(db: Session, project_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.project_id == project_id))
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def ensure_project_member(db: Session, project_id: uuid.UUID, user_id: uuid.UUID | None) -> None:
    if user_id is None:
        return
    if db.scalar(
        select(ProjectMember.id).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    ) is None:
        raise HTTPException(status_code=422, detail="Assignee must be a member of this project.")