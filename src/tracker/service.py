"""Business logic for the task tracker."""

import sqlite3
from datetime import date

from tracker import repository as repo
from tracker.models import Task, TaskSummary


def start_task(
    conn: sqlite3.Connection, name: str, tags: list[str] | None = None
) -> tuple[str, str | None]:
    """Start tracking a task. Returns (started_task_name, paused_task_name or None)."""
    if not name or not name.strip():
        raise ValueError("Task name cannot be empty.")

    name = name.strip()
    paused_name = None

    # Auto-pause active task (BR-1)
    active = repo.get_active_entry(conn)
    if active:
        repo.close_active_entry(conn)
        paused_name = active["task_name"]

    # Get or create task
    task = repo.get_task_by_name(conn, name)
    if task:
        task_id = task.id
    else:
        task_id = repo.create_task(conn, name)

    # Create new time entry
    repo.create_time_entry(conn, task_id)

    # Assign tags
    if tags:
        for tag_name in tags:
            tag_id = repo.get_or_create_tag(conn, tag_name)
            repo.link_tag_to_task(conn, task_id, tag_id)

    return name, paused_name


def stop_task(conn: sqlite3.Connection) -> str | None:
    """Stop the current active task. Returns stopped task name or None."""
    active = repo.get_active_entry(conn)
    if active is None:
        return None
    repo.close_active_entry(conn)
    return active["task_name"]


def resume_task(conn: sqlite3.Connection, task_id: int) -> tuple[str, str | None]:
    """Resume a paused task. Returns (resumed_task_name, paused_task_name or None)."""
    task = repo.get_task_by_id(conn, task_id)
    if task is None:
        raise ValueError(f"Task with id {task_id} not found.")

    paused_name = None

    # Auto-pause active task (BR-1)
    active = repo.get_active_entry(conn)
    if active:
        repo.close_active_entry(conn)
        paused_name = active["task_name"]

    # Create new time entry for resumed task (BR-3)
    repo.create_time_entry(conn, task_id)

    return task.name, paused_name


def get_paused_tasks(conn: sqlite3.Connection) -> list[Task]:
    """Get all tasks that have entries but are not currently active."""
    all_tasks = repo.get_all_tasks(conn)
    active = repo.get_active_entry(conn)
    active_task_id = active["task_id"] if active else None
    return [t for t in all_tasks if t.id != active_task_id and t.entries]


def list_tasks(conn: sqlite3.Connection) -> list[Task]:
    """Get all tasks."""
    return repo.get_all_tasks(conn)


def add_tag(conn: sqlite3.Connection, task_id: int, tag_name: str) -> str:
    """Add a tag to an existing task. Returns task name."""
    task = repo.get_task_by_id(conn, task_id)
    if task is None:
        raise ValueError(f"Task with id {task_id} not found.")
    tag_id = repo.get_or_create_tag(conn, tag_name)
    repo.link_tag_to_task(conn, task_id, tag_id)
    return task.name


# --- Reports ---

def get_daily_report(conn: sqlite3.Connection) -> list[TaskSummary]:
    """Get today's task summary report."""
    today = date.today().isoformat()
    return repo.get_report_data(conn, date_from=today, date_to=today)


def get_filtered_report(
    conn: sqlite3.Connection,
    date_from: str | None = None,
    date_to: str | None = None,
    tag: str | None = None,
) -> list[TaskSummary]:
    """Get filtered task summary report."""
    if not date_from and not date_to and not tag:
        return get_daily_report(conn)
    return repo.get_report_data(conn, date_from=date_from, date_to=date_to, tag=tag)
