import io
import json

import pytest

import dead_rules_audit as dra


@pytest.fixture(autouse=True)
def isolate_log(tmp_path, monkeypatch):
    path = str(tmp_path / "dead-rules-audit.jsonl")
    monkeypatch.setattr(dra, "LOG_PATH", path)
    yield path


def run_main(monkeypatch, event):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    with pytest.raises(SystemExit) as exc_info:
        dra.main()
    return exc_info.value.code


def read_records(path):
    return [json.loads(line) for line in open(path).read().splitlines()]


def test_session_start_counts_rules_in_claude_md(monkeypatch, isolate_log, tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "# Rules\n- Always write tests\n- Never commit secrets\nSome prose line.\n"
    )
    code = run_main(monkeypatch, {"hook_event_name": "SessionStart", "session_id": "s1", "cwd": str(tmp_path)})
    assert code == 0
    record = read_records(isolate_log)[0]
    assert record["rule_count"] == 2


def test_session_start_no_claude_md(monkeypatch, isolate_log, tmp_path):
    run_main(monkeypatch, {"hook_event_name": "SessionStart", "session_id": "s2", "cwd": str(tmp_path)})
    record = read_records(isolate_log)[0]
    assert record["rule_count"] == 0


def test_post_tool_use_logs_edit(monkeypatch, isolate_log):
    run_main(
        monkeypatch,
        {"hook_event_name": "PostToolUse", "session_id": "s3", "tool_input": {"file_path": "/x/main.py"}},
    )
    record = read_records(isolate_log)[0]
    assert record["event"] == "edit"
    assert record["file_path"] == "/x/main.py"


def test_session_end_produces_scorecard(monkeypatch, isolate_log, tmp_path):
    (tmp_path / "CLAUDE.md").write_text("- Always write tests\n")
    run_main(monkeypatch, {"hook_event_name": "SessionStart", "session_id": "s4", "cwd": str(tmp_path)})
    run_main(monkeypatch, {"hook_event_name": "PostToolUse", "session_id": "s4", "tool_input": {"file_path": "/x/a.py"}})
    run_main(monkeypatch, {"hook_event_name": "PostToolUse", "session_id": "s4", "tool_input": {"file_path": "/x/b.py"}})
    run_main(monkeypatch, {"hook_event_name": "SessionEnd", "session_id": "s4"})

    records = read_records(isolate_log)
    scorecard = [r for r in records if r["event"] == "scorecard"][0]
    assert scorecard["rule_count"] == 1
    assert scorecard["edit_count"] == 2


def test_session_end_ignores_other_sessions(monkeypatch, isolate_log, tmp_path):
    run_main(monkeypatch, {"hook_event_name": "PostToolUse", "session_id": "other", "tool_input": {"file_path": "/x"}})
    run_main(monkeypatch, {"hook_event_name": "SessionEnd", "session_id": "s5"})
    scorecard = [r for r in read_records(isolate_log) if r["event"] == "scorecard"][0]
    assert scorecard["edit_count"] == 0


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    with pytest.raises(SystemExit) as exc_info:
        dra.main()
    assert exc_info.value.code == 0


def test_extract_rules_variants():
    content = "Do this thing\nDon't do that\nrandom prose\n- Always test\n* Use ruff\nNever skip\n"
    rules = dra.extract_rules(content)
    assert len(rules) == 5
    assert "random prose" not in rules


def test_find_claude_md_present_and_absent(tmp_path):
    assert dra.find_claude_md(str(tmp_path)) is None
    (tmp_path / "CLAUDE.md").write_text("x")
    assert dra.find_claude_md(str(tmp_path)) == str(tmp_path / "CLAUDE.md")
