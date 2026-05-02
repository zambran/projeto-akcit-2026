# Feature: initial-features (#001)

## Summary

CLI time tracker application written in Python that connects to SQLite to manage tasks and time spent on them. Users can start/stop/resume tasks, assign tags for categorization, and view reports filtered by date and tags.

## Components

| Module | Purpose |
|--------|---------|
| `src/tracker/cli.py` | Click CLI with 6 subcommands |
| `src/tracker/service.py` | Business logic (start, stop, resume, reports) |
| `src/tracker/repository.py` | SQLite data access layer |
| `src/tracker/models.py` | Task, Tag, TimeEntry dataclasses |
| `src/tracker/database.py` | Connection management, schema init |
| `src/tracker/formatting.py` | Report table formatting (tabulate) |

## CLI Commands

| Command | Description |
|---------|-------------|
| `tracker start "name" --tag X` | Start tracking a task |
| `tracker stop` | Stop active task |
| `tracker resume [ID]` | Resume a paused task |
| `tracker list` | Show all tasks with status |
| `tracker report --from --to --tag` | Time reports |
| `tracker tag ID --add X` | Add tags to a task |

## Key Design Decisions

- **Click** over argparse for cleaner subcommand handling
- **Raw SQL** over ORM (SQLAlchemy) for 3-table simplicity
- **Layered architecture** (CLI -> Service -> Repository) for testability
- **Single consolidated query** in list_tasks to avoid N+1

## Quality

- Tests: 72 passing
- Coverage: 97%
- Quality review: All findings fixed (N+1 queries, separation of concerns, security)
