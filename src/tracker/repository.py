"""Data access layer for the task tracker."""

import sqlite3
from datetime import datetime

from tracker.models import Tag, Task, TaskSummary, TimeEntry

_DT_FMT = "%Y-%m-%d %H:%M:%S"


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.strptime(value, _DT_FMT)


# --- Tasks ---

def create_task(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.execute("INSERT INTO tasks (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def get_task_by_name(conn: sqlite3.Connection, name: str) -> Task | None:
    row = conn.execute("SELECT * FROM tasks WHERE name = ?", (name,)).fetchone()
    if row is None:
        return None
    return _row_to_task(conn, row)


def get_task_by_id(conn: sqlite3.Connection, task_id: int) -> Task | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    return _row_to_task(conn, row)


def get_all_tasks(conn: sqlite3.Connection) -> list[Task]:
    """Get all tasks with tags and entries in batch (no N+1)."""
    task_rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    if not task_rows:
        return []

    task_ids = [r["id"] for r in task_rows]
    placeholders = ",".join("?" * len(task_ids))

    # Batch-load all tags
    tag_rows = conn.execute(
        f"SELECT tt.task_id, t.id, t.name FROM tags t "
        f"JOIN task_tags tt ON t.id = tt.tag_id "
        f"WHERE tt.task_id IN ({placeholders})",
        task_ids,
    ).fetchall()
    tags_by_task: dict[int, list[Tag]] = {}
    for r in tag_rows:
        tags_by_task.setdefault(r["task_id"], []).append(Tag(id=r["id"], name=r["name"]))

    # Batch-load all time entries
    entry_rows = conn.execute(
        f"SELECT * FROM time_entries WHERE task_id IN ({placeholders}) ORDER BY start_time",
        task_ids,
    ).fetchall()
    entries_by_task: dict[int, list[TimeEntry]] = {}
    for r in entry_rows:
        entries_by_task.setdefault(r["task_id"], []).append(
            TimeEntry(
                id=r["id"],
                task_id=r["task_id"],
                start_time=_parse_dt(r["start_time"]),
                end_time=_parse_dt(r["end_time"]),
            )
        )

    return [
        Task(
            id=r["id"],
            name=r["name"],
            created_at=_parse_dt(r["created_at"]),
            tags=tags_by_task.get(r["id"], []),
            entries=entries_by_task.get(r["id"], []),
        )
        for r in task_rows
    ]


def _row_to_task(conn: sqlite3.Connection, row: sqlite3.Row) -> Task:
    task_id = row["id"]
    tags = get_tags_for_task(conn, task_id)
    entries = get_entries_for_task(conn, task_id)
    return Task(
        id=task_id,
        name=row["name"],
        created_at=_parse_dt(row["created_at"]),
        tags=tags,
        entries=entries,
    )


# --- Tags ---

def get_or_create_tag(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def link_tag_to_task(conn: sqlite3.Connection, task_id: int, tag_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
        (task_id, tag_id),
    )
    conn.commit()


def get_tags_for_task(conn: sqlite3.Connection, task_id: int) -> list[Tag]:
    rows = conn.execute(
        "SELECT t.id, t.name FROM tags t "
        "JOIN task_tags tt ON t.id = tt.tag_id "
        "WHERE tt.task_id = ?",
        (task_id,),
    ).fetchall()
    return [Tag(id=r["id"], name=r["name"]) for r in rows]


# --- Time Entries ---

def create_time_entry(conn: sqlite3.Connection, task_id: int) -> int:
    cur = conn.execute("INSERT INTO time_entries (task_id) VALUES (?)", (task_id,))
    conn.commit()
    return cur.lastrowid


def close_active_entry(conn: sqlite3.Connection) -> int | None:
    """Close any active time entry. Returns the task_id that was active, or None."""
    row = conn.execute(
        "SELECT id, task_id FROM time_entries WHERE end_time IS NULL"
    ).fetchone()
    if row is None:
        return None
    conn.execute(
        "UPDATE time_entries SET end_time = datetime('now', 'localtime') WHERE id = ?",
        (row["id"],),
    )
    conn.commit()
    return row["task_id"]


def get_active_entry(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        "SELECT te.id, te.task_id, te.start_time, t.name as task_name "
        "FROM time_entries te JOIN tasks t ON te.task_id = t.id "
        "WHERE te.end_time IS NULL"
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def get_entries_for_task(conn: sqlite3.Connection, task_id: int) -> list[TimeEntry]:
    rows = conn.execute(
        "SELECT * FROM time_entries WHERE task_id = ? ORDER BY start_time",
        (task_id,),
    ).fetchall()
    return [
        TimeEntry(
            id=r["id"],
            task_id=r["task_id"],
            start_time=_parse_dt(r["start_time"]),
            end_time=_parse_dt(r["end_time"]),
        )
        for r in rows
    ]


# --- Reports ---

def _build_report_query(
    date_from: str | None, date_to: str | None, tag: str | None
) -> tuple[str, list]:
    """Build the aggregation query with optional filters."""
    query = """
        SELECT
            t.id as task_id,
            t.name as task_name,
            SUM(
                CAST(
                    (julianday(COALESCE(te.end_time, datetime('now', 'localtime')))
                     - julianday(te.start_time)) * 86400 AS REAL
                )
            ) as total_seconds
        FROM tasks t
        JOIN time_entries te ON t.id = te.task_id
    """
    params: list = []
    conditions = []

    if tag:
        query += " JOIN task_tags tt ON t.id = tt.task_id JOIN tags tg ON tt.tag_id = tg.id "
        conditions.append("tg.name = ?")
        params.append(tag)

    if date_from:
        conditions.append("date(te.start_time) >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("date(te.start_time) <= ?")
        params.append(date_to)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY t.id, t.name ORDER BY total_seconds DESC"
    return query, params


def _batch_load_tags(conn: sqlite3.Connection, task_ids: list[int]) -> dict[int, list[str]]:
    """Load tags for multiple tasks in a single query."""
    if not task_ids:
        return {}
    placeholders = ",".join("?" * len(task_ids))
    rows = conn.execute(
        f"SELECT tt.task_id, tg.name FROM tags tg "
        f"JOIN task_tags tt ON tg.id = tt.tag_id "
        f"WHERE tt.task_id IN ({placeholders})",
        task_ids,
    ).fetchall()
    tags_by_task: dict[int, list[str]] = {}
    for r in rows:
        tags_by_task.setdefault(r["task_id"], []).append(r["name"])
    return tags_by_task


def get_report_data(
    conn: sqlite3.Connection,
    date_from: str | None = None,
    date_to: str | None = None,
    tag: str | None = None,
) -> list[TaskSummary]:
    """Get aggregated report data with optional filters."""
    query, params = _build_report_query(date_from, date_to, tag)
    rows = conn.execute(query, params).fetchall()

    if not rows:
        return []

    task_ids = [r["task_id"] for r in rows]
    tags_by_task = _batch_load_tags(conn, task_ids)
    grand_total = sum(r["total_seconds"] for r in rows)

    return [
        TaskSummary(
            task_id=r["task_id"],
            task_name=r["task_name"],
            tags=tags_by_task.get(r["task_id"], []),
            total_seconds=r["total_seconds"],
            percentage=(r["total_seconds"] / grand_total * 100) if grand_total > 0 else 0,
        )
        for r in rows
    ]
