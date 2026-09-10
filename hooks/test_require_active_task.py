import io
import json

import pytest

import require_active_task as rat


def run_main(monkeypatch, stdin_data):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        rat.main()
    return exc_info.value.code


def test_passes_when_backlog_not_installed(monkeypatch):
    monkeypatch.setattr(rat, "has_command", lambda name: False)
    assert run_main(monkeypatch, {"cwd": "/x"}) == 0


def test_passes_when_not_a_backlog_project(monkeypatch):
    monkeypatch.setattr(rat, "has_command", lambda name: True)
    monkeypatch.setattr(rat, "is_backlog_project", lambda cwd: False)
    assert run_main(monkeypatch, {"cwd": "/x"}) == 0


def test_denies_when_no_active_task(monkeypatch, capsys):
    monkeypatch.setattr(rat, "has_command", lambda name: True)
    monkeypatch.setattr(rat, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(rat, "has_active_task", lambda cwd: False)
    code = run_main(monkeypatch, {"cwd": "/x"})
    assert code == 2
    assert "In Progress" in capsys.readouterr().err


def test_denies_when_transcript_missing_task_view(monkeypatch, capsys, tmp_path):
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("some unrelated log line\n")
    monkeypatch.setattr(rat, "has_command", lambda name: True)
    monkeypatch.setattr(rat, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(rat, "has_active_task", lambda cwd: True)
    code = run_main(monkeypatch, {"cwd": "/x", "transcript_path": str(transcript)})
    assert code == 2
    assert "task view" in capsys.readouterr().err


def test_passes_when_transcript_has_task_view(monkeypatch, tmp_path):
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("ran: backlog task view TASK-3 --plain\n")
    monkeypatch.setattr(rat, "has_command", lambda name: True)
    monkeypatch.setattr(rat, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(rat, "has_active_task", lambda cwd: True)
    assert run_main(monkeypatch, {"cwd": "/x", "transcript_path": str(transcript)}) == 0


def test_passes_when_no_transcript_given(monkeypatch):
    monkeypatch.setattr(rat, "has_command", lambda name: True)
    monkeypatch.setattr(rat, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(rat, "has_active_task", lambda cwd: True)
    assert run_main(monkeypatch, {"cwd": "/x"}) == 0


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    with pytest.raises(SystemExit) as exc_info:
        rat.main()
    assert exc_info.value.code == 0


def test_has_command_true_for_python3():
    assert rat.has_command("python3") is True


def test_has_command_false_for_bogus():
    assert rat.has_command("definitely-not-a-real-command-xyz") is False


def test_is_backlog_project_true(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "backlog").mkdir()
    (tmp_path / "backlog" / "config.yml").write_text("x: 1")
    assert rat.is_backlog_project(str(tmp_path)) is True


def test_is_backlog_project_false_without_git(tmp_path):
    (tmp_path / "backlog").mkdir()
    (tmp_path / "backlog" / "config.yml").write_text("x: 1")
    assert rat.is_backlog_project(str(tmp_path)) is False


def test_is_backlog_project_false(tmp_path):
    assert rat.is_backlog_project(str(tmp_path)) is False


def _fake_backlog_script(tmp_path, body):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "backlog"
    script.write_text(f"#!/bin/bash\n{body}\n")
    script.chmod(0o755)
    return str(bin_dir)


def test_has_active_task_true_when_tasks_exist(tmp_path, monkeypatch):
    import os

    bin_dir = _fake_backlog_script(tmp_path, 'echo "TASK-3 - something"')
    monkeypatch.setenv("PATH", bin_dir + ":" + os.environ.get("PATH", ""))
    assert rat.has_active_task(str(tmp_path)) is True


def test_has_active_task_false_when_no_tasks(tmp_path, monkeypatch):
    import os

    bin_dir = _fake_backlog_script(tmp_path, 'echo "No tasks found."')
    monkeypatch.setenv("PATH", bin_dir + ":" + os.environ.get("PATH", ""))
    assert rat.has_active_task(str(tmp_path)) is False
