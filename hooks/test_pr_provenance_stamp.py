import io
import json

import pytest

import pr_provenance_stamp as pps


def run_main(monkeypatch, command, session_id="s1", extra_input=None):
    tool_input = {"command": command, **(extra_input or {})}
    stdin_data = {"tool_name": "Bash", "tool_input": tool_input, "session_id": session_id}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        pps.main()
    return exc_info.value.code


def test_non_pr_create_command_is_no_op(monkeypatch, capsys):
    code = run_main(monkeypatch, "gh pr view 5")
    assert code == 0
    assert capsys.readouterr().out == ""


def test_appends_receipt_to_existing_body_flag(monkeypatch, capsys):
    code = run_main(monkeypatch, 'gh pr create --title x --body "original body"')
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    new_command = hso["updatedInput"]["command"]
    assert "original body" in new_command
    assert "AI 관여도" in new_command


def test_adds_body_flag_when_none_given(monkeypatch, capsys):
    code = run_main(monkeypatch, "gh pr create --title x")
    payload = json.loads(capsys.readouterr().out)
    new_command = payload["hookSpecificOutput"]["updatedInput"]["command"]
    assert "--body" in new_command
    assert "AI 관여도" in new_command


def test_preserves_other_tool_input_fields(monkeypatch, capsys):
    code = run_main(monkeypatch, "gh pr create --title x", extra_input={"description": "keep me", "timeout": 30})
    payload = json.loads(capsys.readouterr().out)
    updated = payload["hookSpecificOutput"]["updatedInput"]
    assert updated["description"] == "keep me"
    assert updated["timeout"] == 30


def test_skips_body_file_form(monkeypatch, capsys):
    code = run_main(monkeypatch, "gh pr create --title x --body-file /tmp/body.md")
    assert code == 0
    assert capsys.readouterr().out == ""


def test_includes_prompt_count_when_session_log_exists(monkeypatch, capsys, tmp_path):
    import os

    log_dir = tmp_path / "sessions"
    log_dir.mkdir()
    (log_dir / "s2.jsonl").write_text(
        json.dumps({"event": "prompt", "prompt": "a"}) + "\n" + json.dumps({"event": "prompt", "prompt": "b"}) + "\n"
    )
    real_expanduser = os.path.expanduser
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda p: p.replace("~/.claude/hooks-logs", str(tmp_path)) if "hooks-logs" in p else real_expanduser(p),
    )
    code = run_main(monkeypatch, "gh pr create --title x", session_id="s2")
    payload = json.loads(capsys.readouterr().out)
    new_command = payload["hookSpecificOutput"]["updatedInput"]["command"]
    assert "프롬프트 수: 2" in new_command


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    with pytest.raises(SystemExit) as exc_info:
        pps.main()
    assert exc_info.value.code == 0


def test_count_session_prompts_none_when_log_missing():
    assert pps.count_session_prompts("no-such-session") is None


def test_inject_receipt_into_command_no_body_flag():
    result = pps.inject_receipt_into_command("gh pr create --title x", "RECEIPT")
    assert "--body" in result
    assert "RECEIPT" in result


def test_inject_receipt_into_command_equals_form():
    result = pps.inject_receipt_into_command("gh pr create --body=short", "RECEIPT")
    assert "RECEIPT" in result
    assert "short" in result
