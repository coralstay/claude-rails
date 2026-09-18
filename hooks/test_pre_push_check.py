import io
import json
import subprocess

import pytest

import pre_push_check as ppc

PUSH = {"command": "git push"}


def run_main(monkeypatch, stdin_data):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        ppc.main()
    return exc_info.value.code


def test_passes_when_backlog_not_installed(monkeypatch):
    monkeypatch.setattr(ppc, "has_command", lambda name: False)
    assert run_main(monkeypatch, {"cwd": "/x", "tool_input": PUSH}) == 0


def test_passes_when_not_backlog_project(monkeypatch):
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: False)
    assert run_main(monkeypatch, {"cwd": "/x", "tool_input": PUSH}) == 0


def test_passes_when_not_on_task_branch(monkeypatch):
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(ppc, "current_branch", lambda cwd: "main")
    assert run_main(monkeypatch, {"cwd": "/x", "tool_input": PUSH}) == 0


def test_passes_when_task_view_fails(monkeypatch):
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(ppc, "current_branch", lambda cwd: "task/TASK-3")
    monkeypatch.setattr(ppc, "task_view", lambda cwd, task_id: None)
    assert run_main(monkeypatch, {"cwd": "/x", "tool_input": PUSH}) == 0


def test_denies_when_not_done(monkeypatch, capsys):
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(ppc, "current_branch", lambda cwd: "task/TASK-3")
    monkeypatch.setattr(
        ppc,
        "task_view",
        lambda cwd, task_id: {"task": {"status": "In Progress", "finalSummary": ""}},
    )
    code = run_main(monkeypatch, {"cwd": "/x", "tool_input": PUSH})
    assert code == 2
    assert "Done 상태가 아닙니다" in capsys.readouterr().err


def test_denies_when_done_but_no_summary(monkeypatch, capsys):
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(ppc, "current_branch", lambda cwd: "task/TASK-3")
    monkeypatch.setattr(
        ppc,
        "task_view",
        lambda cwd, task_id: {"task": {"status": "Done", "finalSummary": "   "}},
    )
    code = run_main(monkeypatch, {"cwd": "/x", "tool_input": PUSH})
    assert code == 2
    assert "final summary가 비어있습니다" in capsys.readouterr().err


def test_passes_when_done_with_summary(monkeypatch):
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(ppc, "current_branch", lambda cwd: "task/TASK-3")
    monkeypatch.setattr(
        ppc,
        "task_view",
        lambda cwd, task_id: {"task": {"status": "Done", "finalSummary": "Shipped."}},
    )
    assert run_main(monkeypatch, {"cwd": "/x", "tool_input": PUSH}) == 0


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    with pytest.raises(SystemExit) as exc_info:
        ppc.main()
    assert exc_info.value.code == 0


def test_task_view_returns_none_on_nonzero_exit(tmp_path, monkeypatch):
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "backlog"
    script.write_text("#!/bin/bash\nexit 1\n")
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + ":" + os.environ.get("PATH", ""))
    assert ppc.task_view(str(tmp_path), "TASK-3") is None


def test_has_command_true_for_python3():
    assert ppc.has_command("python3") is True


def test_has_command_false_for_bogus():
    assert ppc.has_command("definitely-not-a-real-command-xyz") is False


def test_is_backlog_project_true(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "backlog").mkdir()
    (tmp_path / "backlog" / "config.yml").write_text("x: 1")
    assert ppc.is_backlog_project(str(tmp_path)) is True


def test_is_backlog_project_false_without_git(tmp_path):
    (tmp_path / "backlog").mkdir()
    (tmp_path / "backlog" / "config.yml").write_text("x: 1")
    assert ppc.is_backlog_project(str(tmp_path)) is False


def test_is_backlog_project_false(tmp_path):
    assert ppc.is_backlog_project(str(tmp_path)) is False


def test_denies_bare_git_dash_c_push_when_not_done(monkeypatch, capsys):
    # Regression: `git -C <path> push ...` previously slipped past because
    # settings.json's `if` filter only recognized `git push` as the literal
    # prefix. The hook must catch this itself now.
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: True)
    monkeypatch.setattr(ppc, "current_branch", lambda cwd: "task/TASK-3")
    monkeypatch.setattr(
        ppc,
        "task_view",
        lambda cwd, task_id: {"task": {"status": "In Progress", "finalSummary": ""}},
    )
    stdin_data = {
        "cwd": "/x",
        "tool_input": {
            "command": "git -C /home/user/project push -u origin task/TASK-3"
        },
    }
    code = run_main(monkeypatch, stdin_data)
    assert code == 2
    assert "Done 상태가 아닙니다" in capsys.readouterr().err


def test_no_op_when_command_is_not_a_push(monkeypatch):
    monkeypatch.setattr(ppc, "has_command", lambda name: True)
    monkeypatch.setattr(ppc, "is_backlog_project", lambda cwd: True)
    stdin_data = {"cwd": "/x", "tool_input": {"command": "git status"}}
    assert run_main(monkeypatch, stdin_data) == 0


def test_command_invokes_git_subcommand_handles_dash_c():
    cmd = "git -C /some/path push -u origin task/TASK-3"
    assert ppc.command_invokes_git_subcommand(cmd, "push") is True


def test_command_invokes_git_subcommand_false_for_other_subcommand():
    cmd = "git -C /some/path status"
    assert ppc.command_invokes_git_subcommand(cmd, "push") is False


def test_command_invokes_git_subcommand_plain():
    assert ppc.command_invokes_git_subcommand("git push", "push") is True


def test_command_invokes_git_subcommand_in_compound_command():
    assert ppc.command_invokes_git_subcommand("npm test && git push", "push") is True


def test_command_invokes_git_subcommand_skips_bare_flag():
    assert ppc.command_invokes_git_subcommand("git -q push", "push") is True


def test_command_invokes_git_subcommand_falls_back_on_unparsable_command():
    unbalanced = 'git commit -m "unterminated'
    assert ppc.command_invokes_git_subcommand(unbalanced, "commit") is True
    assert ppc.command_invokes_git_subcommand(unbalanced, "push") is False


def test_current_branch_real_git(tmp_path):
    subprocess.run(
        ["git", "init", "-q", "-b", "task/TASK-9"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "f.txt").write_text("hi")
    subprocess.run(
        ["git", "add", "f.txt"], cwd=tmp_path, check=True, capture_output=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=T",
            "commit",
            "-q",
            "-m",
            "init",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    assert ppc.current_branch(str(tmp_path)) == "task/TASK-9"


def test_task_view_returns_none_on_malformed_json(tmp_path, monkeypatch):
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "backlog"
    script.write_text("#!/bin/bash\necho 'not json'\n")
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + ":" + os.environ.get("PATH", ""))
    assert ppc.task_view(str(tmp_path), "TASK-3") is None
