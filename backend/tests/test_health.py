from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test that root endpoint returns operational metadata and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "TaskFlow API"
    assert data["status"] == "operational"
    assert "docs" in data
    assert "health" in data


def test_ping_endpoint(client: TestClient):
    """Test rapid ping/pong liveness endpoint."""
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}


def test_health_endpoint_schema(client: TestClient):
    """Test that health check adheres to HealthResponse schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "TaskFlow API"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "database" in data
    assert data["database"]["status"] in ["connected", "disconnected", "unexpected_result"]
    assert data["status"] in ["healthy", "degraded"]


def test_top_level_health_alias(client: TestClient):
    """Test that /health functions as a top-level alias."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "TaskFlow API"
    assert "database" in data


def test_health_connected_db(client: TestClient, monkeypatch):
    """Test health endpoint when database connectivity is active."""
    fake_db_result = {
        "status": "connected",
        "latency_ms": 1.45,
        "database_url": "taskflow",
        "driver": "postgresql",
    }
    monkeypatch.setattr("app.api.v1.endpoints.health.check_db_health", lambda: fake_db_result)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"
    assert data["database"]["latency_ms"] == 1.45


def test_health_degraded_db_non_strict(client: TestClient, monkeypatch):
    """Test health endpoint when database connectivity fails (non-strict mode)."""
    fake_db_result = {
        "status": "disconnected",
        "latency_ms": 15.2,
        "error": "Connection refused",
        "target": "localhost:5432/taskflow",
    }
    monkeypatch.setattr("app.api.v1.endpoints.health.check_db_health", lambda: fake_db_result)

    response = client.get("/api/v1/health")
    # In non-strict mode, returns 200 so UI and monitors can read the diagnostic payload
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"]["status"] == "disconnected"
    assert "Connection refused" in data["database"]["error"]


def test_health_degraded_db_strict(client: TestClient, monkeypatch):
    """Test health endpoint when database connectivity fails with strict=True."""
    fake_db_result = {
        "status": "disconnected",
        "latency_ms": 15.2,
        "error": "Connection refused",
        "target": "localhost:5432/taskflow",
    }
    monkeypatch.setattr("app.api.v1.endpoints.health.check_db_health", lambda: fake_db_result)

    response = client.get("/api/v1/health?strict=true")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"]["status"] == "disconnected"


def test_cors_headers(client: TestClient):
    """Test that CORS headers are properly returned for allowed origins."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
