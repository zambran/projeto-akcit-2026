"""Tests for the service layer."""

import pytest

from tracker import service, repository as repo


def test_start_task_creates_entry(conn):
    name, paused = service.start_task(conn, "my task")
    assert name == "my task"
    assert paused is None
    active = repo.get_active_entry(conn)
    assert active is not None
    assert active["task_name"] == "my task"


def test_start_task_auto_pauses_active(conn):
    service.start_task(conn, "task A")
    name, paused = service.start_task(conn, "task B")
    assert name == "task B"
    assert paused == "task A"
    active = repo.get_active_entry(conn)
    assert active["task_name"] == "task B"


def test_start_task_with_tags(conn):
    service.start_task(conn, "tagged", tags=["dev", "urgent"])
    task = repo.get_task_by_name(conn, "tagged")
    tag_names = [t.name for t in task.tags]
    assert "dev" in tag_names
    assert "urgent" in tag_names


def test_start_task_reuses_existing(conn):
    service.start_task(conn, "repeat")
    service.stop_task(conn)
    service.start_task(conn, "repeat")
    tasks = repo.get_all_tasks(conn)
    matching = [t for t in tasks if t.name == "repeat"]
    assert len(matching) == 1
    assert len(matching[0].entries) == 2


def test_start_task_empty_name_raises(conn):
    with pytest.raises(ValueError, match="empty"):
        service.start_task(conn, "")


def test_start_task_whitespace_name_raises(conn):
    with pytest.raises(ValueError, match="empty"):
        service.start_task(conn, "   ")


def test_stop_task(conn):
    service.start_task(conn, "task")
    stopped = service.stop_task(conn)
    assert stopped == "task"
    assert repo.get_active_entry(conn) is None


def test_stop_task_when_none_active(conn):
    stopped = service.stop_task(conn)
    assert stopped is None


def test_resume_task(conn):
    service.start_task(conn, "task A")
    service.stop_task(conn)
    task = repo.get_task_by_name(conn, "task A")

    resumed, paused = service.resume_task(conn, task.id)
    assert resumed == "task A"
    assert paused is None
    active = repo.get_active_entry(conn)
    assert active["task_name"] == "task A"


def test_resume_task_auto_pauses_active(conn):
    service.start_task(conn, "task A")
    service.start_task(conn, "task B")
    service.stop_task(conn)
    task_a = repo.get_task_by_name(conn, "task A")

    resumed, paused = service.resume_task(conn, task_a.id)
    assert resumed == "task A"
    assert paused is None  # task B was already stopped


def test_resume_task_pauses_current(conn):
    service.start_task(conn, "task A")
    service.stop_task(conn)
    service.start_task(conn, "task B")
    task_a = repo.get_task_by_name(conn, "task A")

    resumed, paused = service.resume_task(conn, task_a.id)
    assert resumed == "task A"
    assert paused == "task B"


def test_resume_nonexistent_task(conn):
    with pytest.raises(ValueError, match="not found"):
        service.resume_task(conn, 9999)


def test_get_paused_tasks(conn):
    service.start_task(conn, "task A")
    service.start_task(conn, "task B")  # pauses A
    paused = service.get_paused_tasks(conn)
    assert len(paused) == 1
    assert paused[0].name == "task A"


def test_list_tasks(conn):
    service.start_task(conn, "task A")
    service.start_task(conn, "task B")
    tasks = service.list_tasks(conn)
    assert len(tasks) == 2


def test_add_tag(conn):
    service.start_task(conn, "task")
    task = repo.get_task_by_name(conn, "task")
    name = service.add_tag(conn, task.id, "new-tag")
    assert name == "task"
    updated = repo.get_task_by_id(conn, task.id)
    assert any(t.name == "new-tag" for t in updated.tags)


def test_add_tag_nonexistent_task(conn):
    with pytest.raises(ValueError, match="not found"):
        service.add_tag(conn, 9999, "tag")


def test_get_daily_report(conn):
    service.start_task(conn, "today task")
    service.stop_task(conn)
    summaries = service.get_daily_report(conn)
    assert len(summaries) == 1
    assert summaries[0].task_name == "today task"


def test_get_filtered_report_defaults_to_daily(conn):
    service.start_task(conn, "task")
    service.stop_task(conn)
    summaries = service.get_filtered_report(conn)
    assert len(summaries) >= 1


def test_get_filtered_report_by_tag(conn):
    service.start_task(conn, "dev work", tags=["dev"])
    service.stop_task(conn)
    service.start_task(conn, "meeting", tags=["meeting"])
    service.stop_task(conn)

    summaries = service.get_filtered_report(conn, tag="dev")
    assert len(summaries) == 1
    assert summaries[0].task_name == "dev work"
