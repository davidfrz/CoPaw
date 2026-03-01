# -*- coding: utf-8 -*-
"""Unit tests for the AuditLogger."""
# pylint: disable=redefined-outer-name

import json
from pathlib import Path

import pytest

from copaw.app.audit.models import AuditAction, AuditEntry
from copaw.app.audit.logger import AuditLogger


@pytest.fixture
def audit_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture
def audit(audit_path: Path) -> AuditLogger:
    return AuditLogger(path=audit_path)


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


class TestWrite:
    def test_log_creates_file(self, audit: AuditLogger, audit_path: Path):
        audit.log(action="tool_call", target="read_file", actor="agent")
        assert audit_path.exists()

    def test_log_returns_entry(self, audit: AuditLogger):
        entry = audit.log(
            action="tool_call",
            target="execute_shell_command",
            summary="Ran: ls",
            actor="agent",
        )
        assert isinstance(entry, AuditEntry)
        assert entry.action == "tool_call"
        assert entry.target == "execute_shell_command"
        assert entry.summary == "Ran: ls"
        assert entry.result == "success"

    def test_log_appends_jsonl(self, audit: AuditLogger, audit_path: Path):
        audit.log(action="tool_call", target="a")
        audit.log(action="config_change", target="b")

        lines = audit_path.read_text().strip().splitlines()
        assert len(lines) == 2

        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first["target"] == "a"
        assert second["target"] == "b"

    def test_log_with_detail(self, audit: AuditLogger, audit_path: Path):
        audit.log(
            action="skill_change",
            target="my_skill",
            detail={"old": "v1", "new": "v2"},
        )
        line = json.loads(audit_path.read_text().strip())
        assert line["detail"]["old"] == "v1"


# ---------------------------------------------------------------------------
# Reading / querying
# ---------------------------------------------------------------------------


class TestQuery:
    def test_query_empty(self, audit: AuditLogger):
        assert audit.query() == []

    def test_query_all(self, audit: AuditLogger):
        audit.log(action="tool_call", target="a")
        audit.log(action="config_change", target="b")
        entries = audit.query()
        assert len(entries) == 2

    def test_query_filter_by_action(self, audit: AuditLogger):
        audit.log(action="tool_call", target="a")
        audit.log(action="config_change", target="b")
        audit.log(action="tool_call", target="c")
        entries = audit.query(action="tool_call")
        assert len(entries) == 2
        assert all(e.action == "tool_call" for e in entries)

    def test_query_filter_by_actor(self, audit: AuditLogger):
        audit.log(action="tool_call", target="a", actor="agent")
        audit.log(action="tool_call", target="b", actor="user")
        entries = audit.query(actor="agent")
        assert len(entries) == 1
        assert entries[0].actor == "agent"

    def test_query_newest_first(self, audit: AuditLogger):
        import time

        audit.log(action="tool_call", target="first")
        time.sleep(0.01)
        audit.log(action="tool_call", target="second")
        entries = audit.query()
        assert entries[0].target == "second"
        assert entries[1].target == "first"

    def test_query_pagination(self, audit: AuditLogger):
        for i in range(10):
            audit.log(action="tool_call", target=str(i))

        page1 = audit.query(limit=3, offset=0)
        page2 = audit.query(limit=3, offset=3)
        assert len(page1) == 3
        assert len(page2) == 3
        # No overlap
        ids1 = {e.id for e in page1}
        ids2 = {e.id for e in page2}
        assert ids1.isdisjoint(ids2)

    def test_count(self, audit: AuditLogger):
        audit.log(action="tool_call", target="a")
        audit.log(action="config_change", target="b")
        audit.log(action="tool_call", target="c")
        assert audit.count() == 3
        assert audit.count(action="tool_call") == 2
        assert audit.count(action="config_change") == 1


# ---------------------------------------------------------------------------
# Rotation
# ---------------------------------------------------------------------------


class TestRotation:
    def test_rotation_on_size(self, audit_path: Path):
        # Use a very small max_bytes to trigger rotation
        audit = AuditLogger(path=audit_path, max_bytes=100)

        # Write enough to exceed 100 bytes
        for i in range(10):
            audit.log(action="tool_call", target=f"target_{i}")

        rotated = audit_path.with_suffix(".jsonl.1")
        assert rotated.exists()
        # Current file should exist and be smaller
        assert audit_path.exists()


# ---------------------------------------------------------------------------
# Malformed lines
# ---------------------------------------------------------------------------


class TestMalformed:
    def test_skips_bad_lines(self, audit: AuditLogger, audit_path: Path):
        # Write a valid entry then a bad line
        audit.log(action="tool_call", target="good")
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write("this is not json\n")
            f.write('{"bad": true}\n')

        entries = audit.query()
        assert len(entries) == 1
        assert entries[0].target == "good"


# ---------------------------------------------------------------------------
# AuditAction enum
# ---------------------------------------------------------------------------


class TestAuditAction:
    def test_all_actions(self):
        expected = {
            "tool_call",
            "approval_decision",
            "config_change",
            "skill_change",
            "mcp_change",
            "cron_change",
        }
        assert {a.value for a in AuditAction} == expected
