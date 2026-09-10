import io
import json
import subprocess

import pytest

import pre_commit_check as pcc

COMMIT = {"command": "git commit -m x"}


def run_main(monkeypatch, stdin_data):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        pcc.main()
    return exc_info.value.code


def test_passes_when_backlog_not_installed(monkeypatch):
    monkeypatch.setattr(pcc, "has_command", lambda name: False)
    assert run_main(monkeypatch, {"cwd": "/x", "tool_input": COMMIT}) == 0


def test_passes_when_not_backlog_project(monkeypatch):
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: False)
    assert run_main(monkeypatch, {"cwd": "/x", "tool_input": COMMIT}) == 0


def test_denies_off_task_branch(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(pcc, "has_active_task", lambda cwd: True)
    monkeypatch.setattr(pcc, "current_branch", lambda cwd: "main")
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT})
    assert code == 2
    assert "태스크 브랜치" in capsys.readouterr().err


def test_passes_on_task_branch_with_no_test_config(monkeypatch, tmp_path):
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(pcc, "has_active_task", lambda cwd: True)
    monkeypatch.setattr(pcc, "current_branch", lambda cwd: "task/TASK-3")
    assert run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT}) == 0


def test_skips_branch_check_when_no_active_task(monkeypatch, tmp_path):
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(pcc, "has_active_task", lambda cwd: False)
    monkeypatch.setattr(
        pcc, "current_branch", lambda cwd: (_ for _ in ()).throw(AssertionError("should not be called"))
    )
    assert run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT}) == 0


def test_passes_when_test_command_succeeds(monkeypatch, tmp_path):
    (tmp_path / ".claude-rails.json").write_text(json.dumps({"testCommand": "exit 0"}))
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(pcc, "has_active_task", lambda cwd: False)
    assert run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT}) == 0


def test_denies_when_test_command_fails(monkeypatch, capsys, tmp_path):
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"testCommand": "echo boom && exit 1"})
    )
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(pcc, "has_active_task", lambda cwd: True)
    monkeypatch.setattr(pcc, "current_branch", lambda cwd: "task/TASK-3")
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT})
    assert code == 2
    err = capsys.readouterr().err
    assert "테스트 실패" in err
    assert "boom" in err


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    with pytest.raises(SystemExit) as exc_info:
        pcc.main()
    assert exc_info.value.code == 0


def test_has_command_true_for_python3():
    assert pcc.has_command("python3") is True


def test_has_command_false_for_bogus():
    assert pcc.has_command("definitely-not-a-real-command-xyz") is False


def test_is_backlog_project_true(tmp_path):
    (tmp_path / "backlog").mkdir()
    (tmp_path / "backlog" / "config.yml").write_text("x: 1")
    assert pcc.is_backlog_project(str(tmp_path)) is True


def test_is_backlog_project_false(tmp_path):
    assert pcc.is_backlog_project(str(tmp_path)) is False


def test_has_active_task_real(tmp_path, monkeypatch):
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "backlog"
    script.write_text('#!/bin/bash\necho "TASK-3 - x"\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + ":" + os.environ.get("PATH", ""))
    assert pcc.has_active_task(str(tmp_path)) is True


def test_denies_dash_c_commit_off_task_branch(monkeypatch, capsys, tmp_path):
    # Regression: `git -C <path> commit ...` must still be recognized.
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(pcc, "has_active_task", lambda cwd: True)
    monkeypatch.setattr(pcc, "current_branch", lambda cwd: "main")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({
        "cwd": str(tmp_path),
        "tool_input": {"command": f"git -C {tmp_path} commit -m 'x'"},
    })))
    with pytest.raises(SystemExit) as exc_info:
        pcc.main()
    assert exc_info.value.code == 2
    assert "태스크 브랜치" in capsys.readouterr().err


def test_no_op_when_command_is_not_a_commit(monkeypatch, tmp_path):
    monkeypatch.setattr(pcc, "has_command", lambda name: True)
    monkeypatch.setattr(pcc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({
        "cwd": str(tmp_path),
        "tool_input": {"command": "git status"},
    })))
    with pytest.raises(SystemExit) as exc_info:
        pcc.main()
    assert exc_info.value.code == 0


def test_command_invokes_git_subcommand_handles_dash_c():
    assert pcc.command_invokes_git_subcommand("git -C /p commit -m x", "commit") is True


def test_command_invokes_git_subcommand_false_for_other_subcommand():
    assert pcc.command_invokes_git_subcommand("git -C /p push", "commit") is False


def test_command_invokes_git_subcommand_skips_bare_flag():
    assert pcc.command_invokes_git_subcommand("git -q commit -m x", "commit") is True


def test_command_invokes_git_subcommand_falls_back_on_unparsable_command():
    unbalanced = 'git commit -m "unterminated'
    assert pcc.command_invokes_git_subcommand(unbalanced, "commit") is True
    assert pcc.command_invokes_git_subcommand(unbalanced, "push") is False


def test_configured_test_command_reads_file(tmp_path):
    (tmp_path / ".claude-rails.json").write_text(json.dumps({"testCommand": "pytest -q"}))
    assert pcc.configured_test_command(str(tmp_path)) == "pytest -q"


def test_configured_test_command_none_without_file(tmp_path):
    assert pcc.configured_test_command(str(tmp_path)) is None


def test_current_branch_real_git(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "task/TASK-9"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "f.txt").write_text("hi")
    subprocess.run(["git", "add", "f.txt"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=T", "commit", "-q", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    assert pcc.current_branch(str(tmp_path)) == "task/TASK-9"


def test_run_shell_captures_combined_output():
    code, output = pcc.run_shell(".", "echo out; echo err >&2; exit 3")
    assert code == 3
    assert "out" in output and "err" in output
