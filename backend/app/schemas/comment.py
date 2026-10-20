import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentRead(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
