import io
import json
import os
import subprocess

import pytest

import block_stop_if_dirty as bsd


def run_main(monkeypatch, stdin_data):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        bsd.main()
    return exc_info.value.code


def test_passes_when_backlog_not_installed(monkeypatch):
    monkeypatch.setattr(bsd, "has_command", lambda name: False)
    assert run_main(monkeypatch, {"cwd": "/x"}) == 0


def test_passes_when_not_backlog_project(monkeypatch):
    monkeypatch.setattr(bsd, "has_command", lambda name: True)
    monkeypatch.setattr(bsd, "is_backlog_project", lambda cwd: False)
    assert run_main(monkeypatch, {"cwd": "/x"}) == 0


def test_passes_when_no_active_task(monkeypatch):
    monkeypatch.setattr(bsd, "has_command", lambda name: True)
    monkeypatch.setattr(bsd, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(bsd, "has_active_task", lambda cwd: False)
    assert run_main(monkeypatch, {"cwd": "/x"}) == 0


def test_denies_when_dirty(monkeypatch, capsys):
    monkeypatch.setattr(bsd, "has_command", lambda name: True)
    monkeypatch.setattr(bsd, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(bsd, "has_active_task", lambda cwd: True)
    monkeypatch.setattr(bsd, "is_dirty", lambda cwd: True)
    code = run_main(monkeypatch, {"cwd": "/x"})
    assert code == 2
    assert "커밋하지" in capsys.readouterr().err


def test_passes_when_clean(monkeypatch):
    monkeypatch.setattr(bsd, "has_command", lambda name: True)
    monkeypatch.setattr(bsd, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(bsd, "has_active_task", lambda cwd: True)
    monkeypatch.setattr(bsd, "is_dirty", lambda cwd: False)
    assert run_main(monkeypatch, {"cwd": "/x"}) == 0


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    with pytest.raises(SystemExit) as exc_info:
        bsd.main()
    assert exc_info.value.code == 0


def test_has_command_true_for_python3():
    assert bsd.has_command("python3") is True


def test_has_command_false_for_bogus():
    assert bsd.has_command("definitely-not-a-real-command-xyz") is False


def test_is_backlog_project_true(tmp_path):
    (tmp_path / "backlog").mkdir()
    (tmp_path / "backlog" / "config.yml").write_text("x: 1")
    assert bsd.is_backlog_project(str(tmp_path)) is True


def test_is_backlog_project_false(tmp_path):
    assert bsd.is_backlog_project(str(tmp_path)) is False


def test_has_active_task_real(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "backlog"
    script.write_text('#!/bin/bash\necho "No tasks found."\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + ":" + os.environ.get("PATH", ""))
    assert bsd.has_active_task(str(tmp_path)) is False


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_is_dirty_real_git_clean(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "f.txt").write_text("hi")
    _git(tmp_path, "add", "f.txt")
    _git(tmp_path, "commit", "-q", "-m", "init")
    assert bsd.is_dirty(str(tmp_path)) is False


def test_is_dirty_real_git_dirty(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "f.txt").write_text("hi")
    _git(tmp_path, "add", "f.txt")
    _git(tmp_path, "commit", "-q", "-m", "init")
    (tmp_path / "f.txt").write_text("changed")
    assert bsd.is_dirty(str(tmp_path)) is True
