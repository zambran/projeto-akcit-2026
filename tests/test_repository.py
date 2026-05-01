"""Tests for the repository layer."""

from tracker import repository as repo


def test_create_and_get_task(conn):
    task_id = repo.create_task(conn, "my task")
    task = repo.get_task_by_id(conn, task_id)
    assert task is not None
    assert task.name == "my task"
    assert task.id == task_id


def test_get_task_by_name(conn):
    repo.create_task(conn, "unique task")
    task = repo.get_task_by_name(conn, "unique task")
    assert task is not None
    assert task.name == "unique task"


def test_get_task_by_name_not_found(conn):
    assert repo.get_task_by_name(conn, "nonexistent") is None


def test_get_all_tasks(conn):
    repo.create_task(conn, "task 1")
    repo.create_task(conn, "task 2")
    tasks = repo.get_all_tasks(conn)
    assert len(tasks) == 2


def test_get_or_create_tag(conn):
    tag_id_1 = repo.get_or_create_tag(conn, "dev")
    tag_id_2 = repo.get_or_create_tag(conn, "dev")
    assert tag_id_1 == tag_id_2


def test_link_tag_to_task(conn):
    task_id = repo.create_task(conn, "tagged task")
    tag_id = repo.get_or_create_tag(conn, "urgent")
    repo.link_tag_to_task(conn, task_id, tag_id)
    tags = repo.get_tags_for_task(conn, task_id)
    assert len(tags) == 1
    assert tags[0].name == "urgent"


def test_link_tag_idempotent(conn):
    task_id = repo.create_task(conn, "task")
    tag_id = repo.get_or_create_tag(conn, "dev")
    repo.link_tag_to_task(conn, task_id, tag_id)
    repo.link_tag_to_task(conn, task_id, tag_id)  # duplicate
    tags = repo.get_tags_for_task(conn, task_id)
    assert len(tags) == 1


def test_create_time_entry_and_close(conn):
    task_id = repo.create_task(conn, "task")
    entry_id = repo.create_time_entry(conn, task_id)
    assert entry_id is not None

    active = repo.get_active_entry(conn)
    assert active is not None
    assert active["task_id"] == task_id

    closed_task_id = repo.close_active_entry(conn)
    assert closed_task_id == task_id

    active = repo.get_active_entry(conn)
    assert active is None


def test_close_active_entry_when_none(conn):
    result = repo.close_active_entry(conn)
    assert result is None


def test_get_entries_for_task(conn):
    task_id = repo.create_task(conn, "task")
    repo.create_time_entry(conn, task_id)
    repo.close_active_entry(conn)
    repo.create_time_entry(conn, task_id)

    entries = repo.get_entries_for_task(conn, task_id)
    assert len(entries) == 2
    assert entries[0].end_time is not None
    assert entries[1].end_time is None


def test_report_data_no_filters(conn):
    task_id = repo.create_task(conn, "task A")
    repo.create_time_entry(conn, task_id)
    repo.close_active_entry(conn)

    summaries = repo.get_report_data(conn)
    assert len(summaries) == 1
    assert summaries[0].task_name == "task A"
    assert summaries[0].total_seconds >= 0


def test_report_data_with_tag_filter(conn):
    t1 = repo.create_task(conn, "dev work")
    tag_id = repo.get_or_create_tag(conn, "dev")
    repo.link_tag_to_task(conn, t1, tag_id)
    repo.create_time_entry(conn, t1)
    repo.close_active_entry(conn)

    t2 = repo.create_task(conn, "meeting")
    repo.create_time_entry(conn, t2)
    repo.close_active_entry(conn)

    summaries = repo.get_report_data(conn, tag="dev")
    assert len(summaries) == 1
    assert summaries[0].task_name == "dev work"
