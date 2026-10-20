import pytest
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_jwt_secret_key
from app.core.realtime import project_connections
from app.main import app
from app.models import Notification, Project, ProjectMember, Task


@pytest.fixture
def realtime_workspace(monkeypatch):
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


def make_user(client, name, email):
    response = client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "test-password-123"})
    assert response.status_code == 201
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "test-password-123"}).json()["access_token"]
    return response.json(), token, {"Authorization": f"Bearer {token}"}


def make_project(client, headers):
    response = client.post("/api/v1/projects", headers=headers, json={"name": "Realtime project"})
    assert response.status_code == 201
    return response.json()


def test_notifications_are_private_paginated_and_readable(realtime_workspace):
    client, factory = realtime_workspace
    first, _, first_headers = make_user(client, "First", "first@example.com")
    second, _, second_headers = make_user(client, "Second", "second@example.com")
    project = make_project(client, first_headers)
    added = client.post(f"/api/v1/projects/{project['id']}/members", headers=first_headers, json={"email": "second@example.com"})
    assert added.status_code == 201
    notifications = client.get("/api/v1/notifications", headers=second_headers, params={"limit": 1}).json()
    assert len(notifications) == 1
    notification_id = notifications[0]["id"]
    assert notifications[0]["user_id"] == second["id"]
    assert client.get("/api/v1/notifications/unread-count", headers=second_headers).json() == {"count": 1}
    assert client.patch(f"/api/v1/notifications/{notification_id}/read", headers=first_headers).status_code == 404
    marked = client.patch(f"/api/v1/notifications/{notification_id}/read", headers=second_headers)
    assert marked.status_code == 200 and marked.json()["is_read"] is True
    assert marked.json()["read_at"] is not None
    assert client.get("/api/v1/notifications/unread-count", headers=second_headers).json() == {"count": 0}
    client.post(f"/api/v1/projects/{project['id']}/members", headers=first_headers, json={"email": "second@example.com"})
    assert client.get("/api/v1/notifications/unread-count", headers=first_headers).json() == {"count": 0}
    with factory() as db:
        assert len(db.scalars(select(Notification).where(Notification.user_id == uuid.UUID(first["id"]))).all()) == 0


def test_assignment_status_and_comment_notifications_avoid_self_notification(realtime_workspace):
    client, factory = realtime_workspace
    owner, _, owner_headers = make_user(client, "Owner", "owner@example.com")
    teammate, _, teammate_headers = make_user(client, "Teammate", "teammate@example.com")
    project = make_project(client, owner_headers)
    client.post(f"/api/v1/projects/{project['id']}/members", headers=owner_headers, json={"email": "teammate@example.com"})
    task_resp = client.post(f"/api/v1/projects/{project['id']}/tasks", headers=owner_headers, json={"title": "Notify me", "assignee_id": teammate["id"]})
    assert task_resp.status_code == 201
    task = task_resp.json()
    user_notifs = client.get("/api/v1/notifications", headers=teammate_headers).json()
    assert {notification["type"] for notification in user_notifs} == {"task_assigned", "project_added"}
    assert client.patch(f"/api/v1/projects/{project['id']}/tasks/{task['id']}", headers=owner_headers, json={"status": "in_progress"}).status_code == 200
    comment_path = f"/api/v1/projects/{project['id']}/tasks/{task['id']}/comments"
    assert client.post(comment_path, headers=owner_headers, json={"content": "Changed status and added context"}).status_code == 201
    types = [item["type"] for item in client.get("/api/v1/notifications", headers=teammate_headers).json()]
    assert "task_status_changed" in types and "task_comment" in types
    assert client.get("/api/v1/notifications", headers=owner_headers).json() == []
    with factory() as db:
        assert db.scalar(select(ProjectMember.id).where(ProjectMember.project_id == uuid.UUID(project["id"]), ProjectMember.user_id == uuid.UUID(owner["id"]))) is not None
        assert db.scalar(select(Task.id).where(Task.id == uuid.UUID(task["id"]))) is not None


def test_mark_all_read_and_missing_notification(realtime_workspace):
    client, _ = realtime_workspace
    _, _, headers = make_user(client, "Owner", "owner@example.com")
    project = make_project(client, headers)
    _, _, other_headers = make_user(client, "Member", "member@example.com")
    client.post(f"/api/v1/projects/{project['id']}/members", headers=headers, json={"email": "member@example.com"})
    assert client.patch("/api/v1/notifications/read-all", headers=other_headers).json() == {"count": 0}
    assert client.get("/api/v1/notifications/unread-count", headers=other_headers).json() == {"count": 0}
    assert client.patch("/api/v1/notifications/00000000-0000-0000-0000-000000000000/read", headers=other_headers).status_code == 404


def test_websocket_requires_auth_and_project_membership(realtime_workspace):
    client, _ = realtime_workspace
    _, owner_token, owner_headers = make_user(client, "Owner", "owner@example.com")
    _, outsider_token, _ = make_user(client, "Outsider", "outsider@example.com")
    project = make_project(client, owner_headers)
    url = f"/api/v1/ws/projects/{project['id']}"
    with pytest.raises(WebSocketDisconnect) as missing:
        with client.websocket_connect(url) as websocket:
            websocket.send_json({"type": "not-auth"})
            websocket.receive_text()
    assert missing.value.code == 4401
    with pytest.raises(WebSocketDisconnect) as denied:
        with client.websocket_connect(url) as websocket:
            websocket.send_json({"type": "auth", "access_token": outsider_token})
            websocket.receive_text()
    assert denied.value.code == 4403
    with client.websocket_connect(url) as websocket:
        websocket.send_json({"type": "auth", "access_token": owner_token})
        websocket.send_text("keepalive")
        assert project_connections.connection_count(project["id"]) == 1
    assert project_connections.connection_count(project["id"]) == 0


def test_websocket_delivers_project_and_user_notifications(realtime_workspace):
    client, _ = realtime_workspace
    _, owner_token, owner_headers = make_user(client, "Owner", "owner@example.com")
    teammate, teammate_token, _ = make_user(client, "Teammate", "teammate@example.com")
    project = make_project(client, owner_headers)
    project_id = project["id"]
    client.post(f"/api/v1/projects/{project_id}/members", headers=owner_headers, json={"email": "teammate@example.com"})
    with client.websocket_connect(f"/api/v1/ws/projects/{project_id}") as socket:
        socket.send_json({"type": "auth", "access_token": teammate_token})
        socket.send_text("keepalive")
        client.post(f"/api/v1/projects/{project_id}/tasks", headers=owner_headers, json={"title": "Live task", "assignee_id": teammate["id"]})
        events = [socket.receive_json(), socket.receive_json(), socket.receive_json()]
    event_types = {event["type"] for event in events}
    assert {"task_created", "activity_created", "notification_created"}.issubset(event_types)
    assert all(event["project_id"] == project_id for event in events)


def test_websocket_rejects_invalid_token(realtime_workspace):
    client, _ = realtime_workspace
    _, _, owner_headers = make_user(client, "Owner", "owner@example.com")
    project = make_project(client, owner_headers)
    with pytest.raises(WebSocketDisconnect) as rejected:
        with client.websocket_connect(f"/api/v1/ws/projects/{project['id']}") as socket:
            socket.send_json({"type": "auth", "access_token": "not-a-jwt"})
            socket.send_text("invalid")
            socket.receive_text()
    assert rejected.value.code == 4401


def test_websocket_rejects_expired_token(realtime_workspace):
    client, _ = realtime_workspace
    _, _, headers = make_user(client, "Owner", "owner@example.com")
    project = make_project(client, headers)
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode({
        "sub": "1d95228e-95f1-4a2b-8814-b4cd8a22eb1b",
        "jti": "expired-websocket-test",
        "iat": int((now - timedelta(hours=2)).timestamp()),
        "exp": int((now - timedelta(hours=1)).timestamp()),
        "type": "access",
    }, get_jwt_secret_key(), algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(WebSocketDisconnect) as rejected:
        with client.websocket_connect(f"/api/v1/ws/projects/{project['id']}") as socket:
            socket.send_json({"type": "auth", "access_token": expired_token})
            socket.send_text("expired")
            socket.receive_text()
    assert rejected.value.code == 4401