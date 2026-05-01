"""Report formatting utilities using tabulate."""

from tabulate import tabulate

from tracker.models import TaskSummary


def format_duration(total_seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    total = int(total_seconds)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_report(summaries: list[TaskSummary]) -> str:
    """Format task summaries as a terminal table."""
    if not summaries:
        return "No tasks found for the given filters."

    rows = []
    for s in summaries:
        rows.append([
            s.task_name,
            ", ".join(s.tags) if s.tags else "-",
            format_duration(s.total_seconds),
            f"{s.percentage:.1f}%",
        ])

    grand_total = sum(s.total_seconds for s in summaries)
    rows.append(["TOTAL", "", format_duration(grand_total), "100.0%"])

    return tabulate(
        rows,
        headers=["Task", "Tags", "Time", "%"],
        tablefmt="simple",
    )


def format_task_list(tasks) -> str:
    """Format task list with status and time info."""
    if not tasks:
        return "No tasks found."

    rows = []
    for t in tasks:
        status = "active" if t.is_active else "paused"
        tags = ", ".join(tag.name for tag in t.tags) if t.tags else "-"
        time_str = format_duration(t.total_seconds)
        rows.append([t.id, t.name, status, tags, time_str])

    return tabulate(
        rows,
        headers=["ID", "Task", "Status", "Tags", "Time"],
        tablefmt="simple",
    )
