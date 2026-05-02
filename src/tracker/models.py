"""Data models for the task tracker."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Tag:
    id: int
    name: str


@dataclass
class TimeEntry:
    id: int
    task_id: int
    start_time: datetime
    end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


@dataclass
class Task:
    id: int
    name: str
    created_at: datetime
    tags: list[Tag] = field(default_factory=list)
    entries: list[TimeEntry] = field(default_factory=list)

    @property
    def total_seconds(self) -> float:
        return sum(e.duration_seconds for e in self.entries)

    @property
    def is_active(self) -> bool:
        return any(e.end_time is None for e in self.entries)


@dataclass
class TaskSummary:
    task_id: int
    task_name: str
    tags: list[str]
    total_seconds: float
    percentage: float = 0.0
