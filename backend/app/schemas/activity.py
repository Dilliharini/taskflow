import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ActivityLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    action: str = Field(..., max_length=100)
    entity_type: str = Field(..., max_length=100)
    entity_id: Optional[uuid.UUID] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class ActivityDetail(ActivityLogRead):
    actor_name: Optional[str] = None
