import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Comment cannot be blank")
        return value


class CommentCreate(CommentBase):
    pass


class CommentRead(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CommentUpdate(CommentBase):
    pass


class CommentDetail(CommentRead):
    author_name: str
