
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.bug import BugPriority, BugStatus


class BugCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    priority: BugPriority = BugPriority.MEDIUM


class BugUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=5)
    priority: BugPriority | None = None
    status: BugStatus | None = None


class BugRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: BugPriority
    status: BugStatus
    reporter_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
class BugAssign(BaseModel):
    assignee_id: int | None = Field(default=None, gt=0)
