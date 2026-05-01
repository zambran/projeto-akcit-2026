"""CLI commands using Click."""

import click

from tracker.database import get_connection
from tracker.formatting import format_duration, format_report, format_task_list
from tracker import service


@click.group()
def cli():
    """Task time tracker - track where your time goes."""
    pass


@cli.command()
@click.argument("name")
@click.option("--tag", "-t", multiple=True, help="Tags to assign to the task.")
def start(name: str, tag: tuple[str, ...]):
    """Start tracking a task. Auto-pauses any active task."""
    conn = get_connection()
    try:
        started, paused = service.start_task(conn, name, list(tag) if tag else None)
        if paused:
            click.echo(f"Paused: {paused}")
        tags_str = f" [{', '.join(tag)}]" if tag else ""
        click.echo(f"Started: {started}{tags_str}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()


@cli.command()
def stop():
    """Stop/pause the currently active task."""
    conn = get_connection()
    try:
        stopped = service.stop_task(conn)
        if stopped:
            click.echo(f"Stopped: {stopped}")
        else:
            click.echo("No active task to stop.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()


@cli.command()
@click.argument("task_id", required=False, type=int)
def resume(task_id: int | None):
    """Resume a paused task. Without ID, shows a list to pick from."""
    conn = get_connection()
    try:
        if task_id is None:
            paused_tasks = service.get_paused_tasks(conn)
            if not paused_tasks:
                click.echo("No paused tasks to resume.")
                return
            click.echo("Paused tasks:")
            for t in paused_tasks:
                tags = ", ".join(tg.name for tg in t.tags)
                tags_str = f" [{tags}]" if tags else ""
                time_str = format_duration(t.total_seconds)
                click.echo(f"  {t.id}: {t.name}{tags_str} ({time_str})")
            task_id = click.prompt("Enter task ID to resume", type=int)

        resumed, paused = service.resume_task(conn, task_id)
        if paused:
            click.echo(f"Paused: {paused}")
        click.echo(f"Resumed: {resumed}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()


@cli.command("list")
def list_tasks():
    """Show all tasks with status, tags, and accumulated time."""
    conn = get_connection()
    try:
        tasks = service.list_tasks(conn)
        click.echo(format_task_list(tasks))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()


@cli.command()
@click.option("--from", "date_from", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--to", "date_to", default=None, help="End date (YYYY-MM-DD).")
@click.option("--tag", "-t", default=None, help="Filter by tag name.")
def report(date_from: str | None, date_to: str | None, tag: str | None):
    """Show time report. Default: today's summary."""
    conn = get_connection()
    try:
        summaries = service.get_filtered_report(conn, date_from, date_to, tag)
        click.echo(format_report(summaries))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()


@cli.command()
@click.argument("task_id", type=int)
@click.option("--add", "tag_name", required=True, help="Tag name to add.")
def tag(task_id: int, tag_name: str):
    """Add a tag to an existing task."""
    conn = get_connection()
    try:
        task_name = service.add_tag(conn, task_id, tag_name)
        click.echo(f"Tag '{tag_name}' added to '{task_name}'.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()
