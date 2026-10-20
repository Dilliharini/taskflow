from typing import Dict, List
from pydantic import BaseModel
from app.schemas.task import TaskRead


class DashboardRead(BaseModel):
    total_projects: int
    total_tasks: int
    tasks_by_status: Dict[str, int]
    assigned_to_me: List[TaskRead]
    upcoming_due: List[TaskRead]
    recently_updated: List[TaskRead]