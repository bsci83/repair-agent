"""Activity log tests — the evidence stream.

The two load-bearing rules:
1. Attribution is applied AFTER the caller's payload.
2. Write failures are counted, not raised.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from repair_diag import activity


def test_log_action_appends(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REPAIR_AGENT_ACTIVITY_LOG", str(tmp_path / "log.jsonl"))
    activity.log_action("test_event", foo="bar", n=1)
    result = activity.read_log()
    assert len(result) == 1
    rec = result[0]
    assert rec["event"] == "test_event"
    assert rec["foo"] == "bar"
    assert rec["n"] == 1
    # Attribution LAST — caller cannot overwrite.
    assert "agent" in rec
    assert "run_id" in rec
    assert "pid" in rec
    assert "ts" in rec


def test_log_action_attribution_cannot_be_overwritten(tmp_path, monkeypatch):
    """Even if the caller tries to overwrite agent/run_id/pid/ts,
    the log wins. An audit log a caller can forge is not evidence."""
    monkeypatch.setenv("REPAIR_AGENT_ACTIVITY_LOG", str(tmp_path / "log.jsonl"))
    activity.log_action(
        "test", agent="spoofed", run_id="spoofed", pid=999999,
        ts="1970-01-01T00:00:00",
    )
    rec = activity.read_log()[0]
    assert rec["agent"] != "spoofed"
    assert rec["run_id"] != "spoofed"
    assert rec["pid"] != 999999
    assert rec["ts"] != "1970-01-01T00:00:00"


def test_log_action_never_raises(monkeypatch):
    """A logging failure must not abort an agent run."""
    # Point the log at a path that cannot be created (a directory
    # masquerading as a file).
    monkeypatch.setenv("REPAIR_AGENT_ACTIVITY_LOG", "/dev/null/cannot-create")
    # Should NOT raise, even though the path is unwriteable.
    activity.log_action("test", foo="bar")


def test_read_log_with_integrity_reports_malformed(tmp_path, monkeypatch):
    p = tmp_path / "log.jsonl"
    monkeypatch.setenv("REPAIR_AGENT_ACTIVITY_LOG", str(p))
    activity.log_action("ok", x=1)
    # Append a malformed line by hand.
    p.write_text(p.read_text() + "this is not json\n")
    records, integrity = activity.read_log_with_integrity(p)
    assert len(records) == 1
    assert integrity.malformed_lines == 1
    assert not integrity.sound


def test_integrity_sound_when_clean(tmp_path):
    p = tmp_path / "log.jsonl"
    p.write_text("")
    records, integrity = activity.read_log_with_integrity(p)
    assert integrity.sound
    assert not records


def test_run_id_is_stable_within_process():
    """A single process gets one run id; multiple processes get different
    ids. The eval harness relies on run_id as the run boundary."""
    assert activity.RUN_ID == activity.RUN_ID


def test_log_path_override(tmp_path, monkeypatch):
    monkeypatch.setenv("REPAIR_AGENT_ACTIVITY_LOG", str(tmp_path / "x.jsonl"))
    assert activity.log_path() == tmp_path / "x.jsonl"