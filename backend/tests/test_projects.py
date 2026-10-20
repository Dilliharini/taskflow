import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import ActivityLog, Project, ProjectMember, Task


@pytest.fixture
def workspace(monkeypatch):
    monkeypatch.setattr("app.main.check_db_health", lambda: {"status": "connected"})
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def create_user(client, name, email):
    response = client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "test-password-123"})
    assert response.status_code == 201, response.text
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "test-password-123"}).json()["access_token"]
    return response.json(), {"Authorization": f"Bearer {token}"}


def create_project(client, headers, name="Roadmap"):
    response = client.post("/api/v1/projects", headers=headers, json={"name": name, "description": "A shared plan"})
    assert response.status_code == 201, response.text
    return response.json()


def create_task(client, headers, project_id, **overrides):
    payload = {"title": "Write tests", "description": "Cover APIs", "priority": "medium"}
    payload.update(overrides)
    response = client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_project_create_list_detail_update_and_activity(workspace):
    client, factory = workspace
    owner, headers = create_user(client, "Owner", "owner@example.com")
    project = create_project(client, headers)
    assert project["creator_name"] == "Owner"
    assert client.get("/api/v1/projects", headers=headers).json()[0]["id"] == project["id"]
    assert client.get(f"/api/v1/projects/{project['id']}", headers=headers).json()["name"] == "Roadmap"
    updated = client.patch(f"/api/v1/projects/{project['id']}", headers=headers, json={"name": "Release plan"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Release plan"
    events = client.get(f"/api/v1/projects/{project['id']}/activity", headers=headers).json()
    assert {event["action"] for event in events} >= {"created", "updated"}
    assert all(event["actor_id"] == owner["id"] for event in events)
    with factory() as db:
        assert db.scalar(select(ProjectMember).where(ProjectMember.project_id == uuid.UUID(project["id"]))).role == "owner"


def test_other_user_cannot_view_update_delete_or_read_activity(workspace):
    client, _ = workspace
    _, owner_headers = create_user(client, "Owner", "owner@example.com")
    _, outsider_headers = create_user(client, "Outsider", "outsider@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    assert client.get(f"/api/v1/projects/{project_id}", headers=outsider_headers).status_code == 404
    assert client.patch(f"/api/v1/projects/{project_id}", headers=outsider_headers, json={"name": "Stolen"}).status_code == 404
    assert client.delete(f"/api/v1/projects/{project_id}", headers=outsider_headers).status_code == 404
    assert client.get(f"/api/v1/projects/{project_id}/activity", headers=outsider_headers).status_code == 404


def test_membership_add_duplicate_list_and_last_owner_protection(workspace):
    client, _ = workspace
    owner, owner_headers = create_user(client, "Owner", "owner@example.com")
    teammate, teammate_headers = create_user(client, "Mate", "mate@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    added = client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": " MATE@example.com "})
    assert added.status_code == 201
    assert added.json()["user_id"] == teammate["id"]
    assert "password_hash" not in added.json()
    assert len(client.get(f"/api/v1/projects/{project_id}/members", headers=teammate_headers).json()) == 2
    duplicate = client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "mate@example.com"})
    assert duplicate.status_code == 409
    assert client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "missing@example.com"}).status_code == 404
    owner_member = client.delete(f"/api/v1/projects/{project_id}/members/{owner['id']}", headers=owner_headers)
    assert owner_member.status_code == 409


def test_member_cannot_manage_project_or_members(workspace):
    client, _ = workspace
    _, owner_headers = create_user(client, "Owner", "owner@example.com")
    _, member_headers = create_user(client, "Member", "member@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    assert client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "member@example.com"}).status_code == 201
    assert client.patch(f"/api/v1/projects/{project_id}", headers=member_headers, json={"name": "No"}).status_code == 403
    assert client.post(f"/api/v1/projects/{project_id}/members", headers=member_headers, json={"email": "owner@example.com"}).status_code == 403


def test_admin_cannot_grant_admin_role(workspace):
    client, _ = workspace
    _, owner_headers = create_user(client, "Owner", "owner@example.com")
    _, admin_headers = create_user(client, "Admin", "admin@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    assert client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "admin@example.com", "role": "admin"}).status_code == 201
    denied = client.post(f"/api/v1/projects/{project_id}/members", headers=admin_headers, json={"email": "owner@example.com", "role": "admin"})
    assert denied.status_code == 403


def test_task_create_update_assign_filter_and_activity(workspace):
    client, factory = workspace
    _, owner_headers = create_user(client, "Owner", "owner@example.com")
    teammate, teammate_headers = create_user(client, "Mate", "mate@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "mate@example.com"})
    task = create_task(client, owner_headers, project_id, assignee_id=teammate["id"], status="in_progress", priority="high")
    assert task["created_by_id"]
    assert client.get(f"/api/v1/projects/{project_id}/tasks?status=in_progress&priority=high&q=tests", headers=teammate_headers).json()[0]["id"] == task["id"]
    updated = client.patch(f"/api/v1/projects/{project_id}/tasks/{task['id']}", headers=teammate_headers, json={"status": "done", "priority": "urgent"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    assert updated.json()["priority"] == "urgent"
    assert client.get(f"/api/v1/projects/{project_id}/tasks?status=todo", headers=owner_headers).json() == []
    with factory() as db:
        actions = set(db.scalars(select(ActivityLog.action).where(ActivityLog.project_id == uuid.UUID(project_id))).all())
    assert "created" in actions and "updated" in actions


def test_task_rejects_non_member_assignment_and_bad_enums(workspace):
    client, _ = workspace
    _, headers = create_user(client, "Owner", "owner@example.com")
    outsider, _ = create_user(client, "Outside", "outside@example.com")
    project = create_project(client, headers)
    path = f"/api/v1/projects/{project['id']}/tasks"
    assert client.post(path, headers=headers, json={"title": "Bad assignee", "assignee_id": outsider["id"]}).status_code == 422
    assert client.post(path, headers=headers, json={"title": "Bad status", "status": "blocked"}).status_code == 422


def test_member_can_create_tasks_but_cannot_delete_them(workspace):
    client, _ = workspace
    _, owner_headers = create_user(client, "Owner", "owner@example.com")
    _, member_headers = create_user(client, "Member", "member@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "member@example.com"})
    task = create_task(client, member_headers, project_id)
    assert client.delete(f"/api/v1/projects/{project_id}/tasks/{task['id']}", headers=member_headers).status_code == 403


def test_comment_crud_and_authorization(workspace):
    client, _ = workspace
    _, owner_headers = create_user(client, "Owner", "owner@example.com")
    _, member_headers = create_user(client, "Member", "member@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "member@example.com"})
    task = create_task(client, owner_headers, project_id)
    comments_path = f"/api/v1/projects/{project_id}/tasks/{task['id']}/comments"
    comment = client.post(comments_path, headers=member_headers, json={"content": "Looks good"})
    assert comment.status_code == 201
    assert comment.json()["author_name"] == "Member"
    assert client.patch(f"{comments_path}/{comment.json()['id']}", headers=owner_headers, json={"content": "Edited by admin"}).status_code == 200
    assert client.get(comments_path, headers=owner_headers).json()[0]["content"] == "Edited by admin"
    outsider, outsider_headers = create_user(client, "Outside", "outside@example.com")
    assert client.get(comments_path, headers=outsider_headers).status_code == 404
    assert outsider["id"]
    assert client.delete(f"{comments_path}/{comment.json()['id']}", headers=owner_headers).status_code == 204


def test_dashboard_counts_are_scoped_and_auth_is_required(workspace):
    client, _ = workspace
    _, first_headers = create_user(client, "First", "first@example.com")
    _, second_headers = create_user(client, "Second", "second@example.com")
    first_project = create_project(client, first_headers, "First project")
    create_task(client, first_headers, first_project["id"], status="done")
    create_project(client, second_headers, "Private project")
    first_dashboard = client.get("/api/v1/projects/dashboard", headers=first_headers)
    assert first_dashboard.status_code == 200
    assert first_dashboard.json()["total_projects"] == 1
    assert first_dashboard.json()["total_tasks"] == 1
    assert first_dashboard.json()["tasks_by_status"]["done"] == 1
    assert client.get("/api/v1/projects/dashboard").status_code == 401


def test_failed_operation_does_not_record_activity_and_project_delete_is_owner_only(workspace):
    client, factory = workspace
    _, owner_headers = create_user(client, "Owner", "owner@example.com")
    _, member_headers = create_user(client, "Member", "member@example.com")
    project = create_project(client, owner_headers)
    project_id = project["id"]
    client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "member@example.com"})
    before = client.get(f"/api/v1/projects/{project_id}/activity", headers=owner_headers).json()
    assert client.patch(f"/api/v1/projects/{project_id}", headers=member_headers, json={"name": "Forbidden"}).status_code == 403
    after = client.get(f"/api/v1/projects/{project_id}/activity", headers=owner_headers).json()
    assert len(after) == len(before)
    assert client.delete(f"/api/v1/projects/{project_id}", headers=member_headers).status_code == 403
    with factory() as db:
        assert db.scalar(select(Project).where(Project.id == uuid.UUID(project_id))) is not None
        assert db.scalar(select(Task.id).where(Task.project_id == uuid.UUID(project_id))) is None