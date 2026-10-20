from datetime import datetime, timedelta, timezone
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_jwt_secret_key, hash_password, verify_password
from app.main import app
from app.models import User


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setattr("app.main.check_db_health", lambda: {"status": "connected"})
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def register(client: TestClient, email: str = "person@example.com"):
    return client.post(
        "/api/v1/auth/register",
        json={"name": "TaskFlow User", "email": email, "password": "correct-horse-42"},
    )


def login(client: TestClient, email: str = "person@example.com", password: str = "correct-horse-42"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_password_hashing_and_verification():
    hashed = hash_password("correct-horse-42")
    assert hashed.startswith("$argon2id$")
    assert hashed != "correct-horse-42"
    assert verify_password("correct-horse-42", hashed)
    assert not verify_password("incorrect-password", hashed)


def test_successful_registration_normalizes_email_and_never_returns_hash(auth_client):
    response = register(auth_client, "  Person@Example.COM  ")
    assert response.status_code == 201
    user = response.json()
    assert user["email"] == "person@example.com"
    assert "password_hash" not in user
    assert "password" not in user
    assert login(auth_client).status_code == 200


def test_duplicate_email_registration_is_conflict(auth_client):
    assert register(auth_client).status_code == 201
    response = register(auth_client, "PERSON@example.com")
    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "email": "person@example.com", "password": "correct-horse-42"},
        {"name": "Name", "email": "not-an-email", "password": "correct-horse-42"},
        {"name": "Name", "email": "person@example.com", "password": "short"},
        {"name": "Name", "email": "person@example.com", "password": "x" * 129},
    ],
)
def test_invalid_registration_input_returns_validation_error(auth_client, payload):
    assert auth_client.post("/api/v1/auth/register", json=payload).status_code == 422


def test_successful_login_returns_token_and_safe_profile(auth_client):
    assert register(auth_client).status_code == 201
    response = login(auth_client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert body["access_token"]
    assert "password_hash" not in body
    assert "password" not in body


@pytest.mark.parametrize(
    "email,password",
    [("person@example.com", "wrong-password"), ("unknown@example.com", "correct-horse-42")],
)
def test_invalid_login_credentials_are_generic(auth_client, email, password):
    register(auth_client)
    response = login(auth_client, email, password)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_current_user_and_logout_require_valid_token(auth_client):
    register(auth_client)
    token = login(auth_client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = auth_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "person@example.com"
    assert "password_hash" not in response.json()
    assert auth_client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert "remains valid until it expires" in auth_client.post("/api/v1/auth/logout", headers=headers).json()["message"]


def test_current_user_rejects_missing_invalid_and_expired_tokens(auth_client):
    assert auth_client.get("/api/v1/auth/me").status_code == 401
    assert auth_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    claims = {
        "sub": str(uuid.uuid4()),
        "jti": "expired-test",
        "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
        "type": "access",
    }
    expired = jwt.encode(claims, get_jwt_secret_key(), algorithm=settings.JWT_ALGORITHM)
    response = auth_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_inactive_user_cannot_login_or_use_existing_token(auth_client):
    register(auth_client)
    token = login(auth_client).json()["access_token"]
    db_dependency = app.dependency_overrides[get_db]
    session_generator = db_dependency()
    session = next(session_generator)
    try:
        user = session.scalar(select(User).where(User.email == "person@example.com"))
        user.is_active = False
        session.commit()
    finally:
        session_generator.close()
    assert login(auth_client).status_code == 401
    response = auth_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401