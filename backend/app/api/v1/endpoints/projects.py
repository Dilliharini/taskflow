from datetime import datetime, timedelta, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models import (
    ActivityLog, Comment, Project, ProjectMember, ProjectRole, Task, TaskPriority,
    TaskStatus, User,
)
from app.schemas.activity import ActivityDetail
from app.schemas.comment import CommentCreate, CommentDetail, CommentUpdate
from app.schemas.dashboard import DashboardRead
from app.schemas.project import (
    ProjectCreate, ProjectMemberCreate, ProjectMemberDetail, ProjectRead, ProjectUpdate,
)
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.permissions import (
    ensure_project_member, get_project_access, get_project_task, require_role,
)

router = APIRouter()


def record_activity(
    db: Session, project_id: uuid.UUID, actor_id: uuid.UUID, action: str,
    entity_type: str, entity_id: uuid.UUID | None, details: dict | None = None,
) -> None:
    db.add(ActivityLog(
        project_id=project_id, actor_id=actor_id, action=action,
        entity_type=entity_type, entity_id=entity_id, details=details,
    ))


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> DashboardRead:
    project_ids = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
    total_projects = db.scalar(select(func.count()).select_from(ProjectMember).where(ProjectMember.user_id == user.id)) or 0
    total_tasks = db.scalar(select(func.count()).select_from(Task).where(Task.project_id.in_(project_ids))) or 0
    grouped = db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.project_id.in_(project_ids))
        .group_by(Task.status)
    ).all()
    status_counts = {item.value: 0 for item in TaskStatus}
    status_counts.update({state: count for state, count in grouped})
    assigned = db.scalars(
        select(Task).where(Task.assignee_id == user.id, Task.project_id.in_(project_ids))
        .order_by(Task.due_date.asc().nullslast(), Task.updated_at.desc()).limit(10)
    ).all()
    now = datetime.now(timezone.utc)
    upcoming = db.scalars(
        select(Task).where(
            Task.project_id.in_(project_ids), Task.due_date >= now,
            Task.due_date <= now + timedelta(days=14), Task.status != TaskStatus.DONE.value,
        ).order_by(Task.due_date.asc()).limit(10)
    ).all()
    recent = db.scalars(
        select(Task).where(Task.project_id.in_(project_ids))
        .order_by(Task.updated_at.desc()).limit(10)
    ).all()
    return DashboardRead(
        total_projects=total_projects, total_tasks=total_tasks,
        tasks_by_status=status_counts, assigned_to_me=assigned,
        upcoming_due=upcoming, recently_updated=recent,
    )


@router.get("/tasks/search", response_model=list[TaskRead])
def search_tasks(
    q: str | None = Query(default=None, max_length=200),
    project_id: uuid.UUID | None = None,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = None,
    assignee_id: uuid.UUID | None = None,
    due_from: datetime | None = None,
    due_to: datetime | None = None,
    sort: str = Query(default="updated_at", pattern="^(updated_at|created_at|due_date|title|priority)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> list[Task]:
    accessible_projects = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
    stmt = select(Task).where(Task.project_id.in_(accessible_projects))
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    if q and q.strip():
        needle = f"%{q.strip()}%"
        stmt = stmt.where(Task.title.ilike(needle) | Task.description.ilike(needle))
    if status_filter:
        stmt = stmt.where(Task.status == status_filter.value)
    if priority:
        stmt = stmt.where(Task.priority == priority.value)
    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if due_from:
        stmt = stmt.where(Task.due_date >= due_from)
    if due_to:
        stmt = stmt.where(Task.due_date <= due_to)
    sort_column = getattr(Task, sort)
    stmt = stmt.order_by(sort_column.asc() if order == "asc" else sort_column.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.execute(select(Project, User.name).select_from(Project)
                      .join(ProjectMember, ProjectMember.project_id == Project.id)
                      .join(User, User.id == Project.owner_id)
                      .where(ProjectMember.user_id == user.id).order_by(Project.updated_at.desc())).all()
    return [{**ProjectRead.model_validate(project).model_dump(), "creator_name": name} for project, name in rows]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    project = Project(name=payload.name, description=payload.description, owner_id=user.id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role=ProjectRole.OWNER.value))
    record_activity(db, project.id, user.id, "created", "project", project.id, {"name": project.name})
    db.commit()
    db.refresh(project)
    return {**ProjectRead.model_validate(project).model_dump(), "creator_name": user.name}


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    project, _ = get_project_access(db, project_id, user)
    return {**ProjectRead.model_validate(project).model_dump(), "creator_name": project.owner.name}


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: uuid.UUID, payload: ProjectUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    project, role = get_project_access(db, project_id, user)
    require_role(role, ProjectRole.OWNER, ProjectRole.ADMIN)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(project, field, value)
    record_activity(db, project.id, user.id, "updated", "project", project.id, {"fields": list(changes)})
    db.commit()
    db.refresh(project)
    return {**ProjectRead.model_validate(project).model_dump(), "creator_name": project.owner.name}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Response:
    project, role = get_project_access(db, project_id, user)
    require_role(role, ProjectRole.OWNER)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/members", response_model=list[ProjectMemberDetail])
def list_members(project_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    get_project_access(db, project_id, user)
    rows = db.execute(
        select(ProjectMember, User.name, User.email)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.joined_at.asc())
    ).all()
    return [{"id": m.id, "user_id": m.user_id, "name": name, "email": email, "role": m.role, "joined_at": m.joined_at} for m, name, email in rows]


@router.post("/{project_id}/members", response_model=ProjectMemberDetail, status_code=status.HTTP_201_CREATED)
def add_member(project_id: uuid.UUID, payload: ProjectMemberCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    _, role = get_project_access(db, project_id, user)
    require_role(role, ProjectRole.OWNER, ProjectRole.ADMIN)
    if payload.role == ProjectRole.OWNER or (payload.role == ProjectRole.ADMIN and role != ProjectRole.OWNER.value):
        raise HTTPException(status_code=403, detail="Only an owner can grant the admin role.")
    target = db.scalar(select(User).where(User.email == str(payload.email).casefold(), User.is_active.is_(True)))
    if target is None:
        raise HTTPException(status_code=404, detail="No active user exists with that email.")
    member = ProjectMember(project_id=project_id, user_id=target.id, role=payload.role.value)
    db.add(member)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That user is already a project member.") from None
    record_activity(db, project_id, user.id, "member_added", "project_member", member.id, {"email": target.email, "role": member.role})
    db.commit()
    db.refresh(member)
    return {"id": member.id, "user_id": target.id, "name": target.name, "email": target.email, "role": member.role, "joined_at": member.joined_at}


@router.delete("/{project_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(project_id: uuid.UUID, member_user_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Response:
    _, role = get_project_access(db, project_id, user)
    require_role(role, ProjectRole.OWNER, ProjectRole.ADMIN)
    member = db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == member_user_id))
    if member is None:
        raise HTTPException(status_code=404, detail="Project member not found.")
    if member.role == ProjectRole.OWNER.value:
        raise HTTPException(status_code=409, detail="Project owners cannot be removed. Transfer ownership first.")
    if role != ProjectRole.OWNER.value and member.role != ProjectRole.MEMBER.value:
        raise HTTPException(status_code=403, detail="Admins cannot remove another admin.")
    details = {"user_id": str(member.user_id), "role": member.role}
    record_activity(db, project_id, user.id, "member_removed", "project_member", member.id, details)
    db.delete(member)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/tasks", response_model=list[TaskRead])
def list_tasks(
    project_id: uuid.UUID,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = None,
    assignee_id: uuid.UUID | None = None,
    due_from: datetime | None = None,
    due_to: datetime | None = None,
    q: str | None = Query(default=None, max_length=200),
    sort: str = Query(default="position", pattern="^(position|updated_at|created_at|due_date|title|priority)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=100, ge=1, le=200), offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> list[Task]:
    get_project_access(db, project_id, user)
    stmt = select(Task).where(Task.project_id == project_id)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter.value)
    if priority:
        stmt = stmt.where(Task.priority == priority.value)
    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if due_from:
        stmt = stmt.where(Task.due_date >= due_from)
    if due_to:
        stmt = stmt.where(Task.due_date <= due_to)
    if q and q.strip():
        needle = f"%{q.strip()}%"
        stmt = stmt.where(Task.title.ilike(needle) | Task.description.ilike(needle))
    sort_column = getattr(Task, sort)
    stmt = stmt.order_by(sort_column.asc() if order == "asc" else sort_column.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.post("/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(project_id: uuid.UUID, payload: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Task:
    get_project_access(db, project_id, user)
    ensure_project_member(db, project_id, payload.assignee_id)
    task = Task(project_id=project_id, created_by_id=user.id, **payload.model_dump())
    db.add(task)
    db.flush()
    record_activity(db, project_id, user.id, "created", "task", task.id, {"title": task.title})
    db.commit()
    db.refresh(task)
    return task


@router.get("/{project_id}/tasks/{task_id}", response_model=TaskRead)
def get_task(project_id: uuid.UUID, task_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Task:
    get_project_access(db, project_id, user)
    return get_project_task(db, project_id, task_id)


@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskRead)
def update_task(project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Task:
    get_project_access(db, project_id, user)
    task = get_project_task(db, project_id, task_id)
    changes = payload.model_dump(exclude_unset=True)
    if "assignee_id" in changes:
        ensure_project_member(db, project_id, changes["assignee_id"])
    old_values = {key: getattr(task, key) for key in changes}
    for field, value in changes.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(task, field, value)
    if changes:
        record_activity(db, project_id, user.id, "updated", "task", task.id, {
            "fields": list(changes),
            "changes": {key: {"from": str(old_values[key]), "to": str(getattr(task, key))} for key in changes if key in {"status", "priority", "assignee_id"}},
        })
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(project_id: uuid.UUID, task_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Response:
    _, role = get_project_access(db, project_id, user)
    require_role(role, ProjectRole.OWNER, ProjectRole.ADMIN)
    task = get_project_task(db, project_id, task_id)
    record_activity(db, project_id, user.id, "deleted", "task", task.id, {"title": task.title})
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/tasks/{task_id}/comments", response_model=list[CommentDetail])
def list_comments(project_id: uuid.UUID, task_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    get_project_access(db, project_id, user)
    get_project_task(db, project_id, task_id)
    rows = db.execute(select(Comment, User.name).join(User, User.id == Comment.author_id)
                      .where(Comment.task_id == task_id).order_by(Comment.created_at.asc())).all()
    return [{"id": c.id, "task_id": c.task_id, "author_id": c.author_id, "author_name": name,
             "content": c.content, "created_at": c.created_at, "updated_at": c.updated_at} for c, name in rows]


@router.post("/{project_id}/tasks/{task_id}/comments", response_model=CommentDetail, status_code=status.HTTP_201_CREATED)
def create_comment(project_id: uuid.UUID, task_id: uuid.UUID, payload: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    get_project_access(db, project_id, user)
    get_project_task(db, project_id, task_id)
    comment = Comment(task_id=task_id, author_id=user.id, content=payload.content)
    db.add(comment)
    db.flush()
    record_activity(db, project_id, user.id, "commented", "comment", comment.id, {"task_id": str(task_id)})
    db.commit()
    db.refresh(comment)
    return {"id": comment.id, "task_id": comment.task_id, "author_id": user.id,
            "author_name": user.name, "content": comment.content,
            "created_at": comment.created_at, "updated_at": comment.updated_at}


@router.patch("/{project_id}/tasks/{task_id}/comments/{comment_id}", response_model=CommentDetail)
def update_comment(project_id: uuid.UUID, task_id: uuid.UUID, comment_id: uuid.UUID, payload: CommentUpdate,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    _, role = get_project_access(db, project_id, user)
    get_project_task(db, project_id, task_id)
    comment = db.scalar(select(Comment).where(Comment.id == comment_id, Comment.task_id == task_id))
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != user.id and role not in (ProjectRole.OWNER.value, ProjectRole.ADMIN.value):
        raise HTTPException(status_code=403, detail="Only the author or a project admin can edit this comment.")
    comment.content = payload.content
    record_activity(db, project_id, user.id, "comment_updated", "comment", comment.id, {"task_id": str(task_id)})
    db.commit()
    db.refresh(comment)
    return {"id": comment.id, "task_id": task_id, "author_id": comment.author_id,
            "author_name": db.get(User, comment.author_id).name, "content": comment.content,
            "created_at": comment.created_at, "updated_at": comment.updated_at}


@router.delete("/{project_id}/tasks/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(project_id: uuid.UUID, task_id: uuid.UUID, comment_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Response:
    _, role = get_project_access(db, project_id, user)
    get_project_task(db, project_id, task_id)
    comment = db.scalar(select(Comment).where(Comment.id == comment_id, Comment.task_id == task_id))
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != user.id and role not in (ProjectRole.OWNER.value, ProjectRole.ADMIN.value):
        raise HTTPException(status_code=403, detail="Only the author or a project admin can delete this comment.")
    record_activity(db, project_id, user.id, "comment_deleted", "comment", comment.id, {"task_id": str(task_id)})
    db.delete(comment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/activity", response_model=list[ActivityDetail])
def list_activity(project_id: uuid.UUID, limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0),
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    get_project_access(db, project_id, user)
    rows = db.execute(select(ActivityLog, User.name).outerjoin(User, User.id == ActivityLog.actor_id)
                      .where(ActivityLog.project_id == project_id)
                      .order_by(ActivityLog.created_at.desc()).limit(limit).offset(offset)).all()
    return [{**ActivityDetail.model_validate(item).model_dump(), "actor_name": name} for item, name in rows]