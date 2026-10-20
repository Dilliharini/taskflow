from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    status: str = Field(..., description="Database connection status: connected, disconnected, or degraded")
    latency_ms: Optional[float] = Field(None, description="Roundtrip query latency in milliseconds")
    database_url: Optional[str] = Field(None, description="Database target name")
    driver: Optional[str] = Field(None, description="SQLAlchemy dialect/driver name")
    error: Optional[str] = Field(None, description="Error message if disconnected")
    target: Optional[str] = Field(None, description="Target host:port/db")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system status: healthy, degraded, or unhealthy")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Application environment (development, production, etc.)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    database: DatabaseHealth = Field(..., description="Database connectivity status and latency")
    details: Optional[Dict[str, Any]] = None
