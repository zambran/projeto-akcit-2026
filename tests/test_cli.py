"""Integration tests for CLI commands using Click CliRunner."""

import os
import tempfile
from unittest.mock import patch

from click.testing import CliRunner

from tracker.cli import cli
from tracker.database import get_connection


class TestCLI:
    """CLI integration tests with file-based temp database."""

    def setup_method(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_path = self._tmp.name
        self._tmp.close()
        self.runner = CliRunner()
        self._patcher = patch(
            "tracker.cli.get_connection",
            side_effect=lambda: get_connection(self._db_path),
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()
        os.unlink(self._db_path)

    def test_start_task(self):
        result = self.runner.invoke(cli, ["start", "code review"])
        assert result.exit_code == 0
        assert "Started: code review" in result.output

    def test_start_task_with_tags(self):
        result = self.runner.invoke(cli, ["start", "task", "--tag", "dev", "--tag", "urgent"])
        assert result.exit_code == 0
        assert "Started: task [dev, urgent]" in result.output

    def test_start_auto_pauses(self):
        self.runner.invoke(cli, ["start", "task A"])
        result = self.runner.invoke(cli, ["start", "task B"])
        assert result.exit_code == 0
        assert "Paused: task A" in result.output
        assert "Started: task B" in result.output

    def test_stop_task(self):
        self.runner.invoke(cli, ["start", "task"])
        result = self.runner.invoke(cli, ["stop"])
        assert result.exit_code == 0
        assert "Stopped: task" in result.output

    def test_stop_no_active(self):
        result = self.runner.invoke(cli, ["stop"])
        assert result.exit_code == 0
        assert "No active task" in result.output

    def test_resume_with_id(self):
        self.runner.invoke(cli, ["start", "task A"])
        self.runner.invoke(cli, ["stop"])
        result = self.runner.invoke(cli, ["resume", "1"])
        assert result.exit_code == 0
        assert "Resumed: task A" in result.output

    def test_resume_no_paused(self):
        result = self.runner.invoke(cli, ["resume"], input="\n")
        assert "No paused tasks" in result.output

    def test_list_tasks(self):
        self.runner.invoke(cli, ["start", "task A", "--tag", "dev"])
        self.runner.invoke(cli, ["start", "task B"])
        result = self.runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "task A" in result.output
        assert "task B" in result.output
        assert "active" in result.output
        assert "paused" in result.output

    def test_report_default_today(self):
        self.runner.invoke(cli, ["start", "task"])
        self.runner.invoke(cli, ["stop"])
        result = self.runner.invoke(cli, ["report"])
        assert result.exit_code == 0
        assert "task" in result.output
        assert "TOTAL" in result.output

    def test_report_empty(self):
        result = self.runner.invoke(cli, ["report"])
        assert result.exit_code == 0
        assert "No tasks found" in result.output

    def test_report_with_tag_filter(self):
        self.runner.invoke(cli, ["start", "dev work", "--tag", "dev"])
        self.runner.invoke(cli, ["stop"])
        self.runner.invoke(cli, ["start", "meeting", "--tag", "meeting"])
        self.runner.invoke(cli, ["stop"])
        result = self.runner.invoke(cli, ["report", "--tag", "dev"])
        assert result.exit_code == 0
        assert "dev work" in result.output
        assert "meeting" not in result.output.split("TOTAL")[0]

    def test_tag_command(self):
        self.runner.invoke(cli, ["start", "task"])
        self.runner.invoke(cli, ["stop"])
        result = self.runner.invoke(cli, ["tag", "1", "--add", "new-tag"])
        assert result.exit_code == 0
        assert "new-tag" in result.output
        assert "task" in result.output

    def test_start_empty_name(self):
        result = self.runner.invoke(cli, ["start", ""])
        assert result.exit_code != 0

    def test_full_lifecycle(self):
        """E2E-1: Full task lifecycle."""
        r = self.runner.invoke(cli, ["start", "code review", "--tag", "dev"])
        assert r.exit_code == 0

        r = self.runner.invoke(cli, ["start", "standup", "--tag", "meeting"])
        assert "Paused: code review" in r.output

        r = self.runner.invoke(cli, ["resume", "1"])
        assert "Resumed: code review" in r.output

        r = self.runner.invoke(cli, ["stop"])
        assert "Stopped: code review" in r.output

        r = self.runner.invoke(cli, ["report"])
        assert "code review" in r.output
        assert "standup" in r.output
        assert "TOTAL" in r.output
