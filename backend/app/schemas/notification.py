import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    type: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1)


class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
