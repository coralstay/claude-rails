import io
import json

import pytest

import pre_merge_check as pmc


def run_main(monkeypatch, command):
    stdin_data = {"tool_name": "Bash", "tool_input": {"command": command}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        pmc.main()
    return exc_info.value.code


def test_passes_non_merge_commands(monkeypatch):
    assert run_main(monkeypatch, "git status") == 0
    assert run_main(monkeypatch, "git push origin main") == 0


def test_allows_merge_with_ff_only(monkeypatch):
    assert run_main(monkeypatch, "git merge --ff-only task/TASK-3") == 0


def test_denies_plain_merge_without_ff_only(monkeypatch, capsys):
    code = run_main(monkeypatch, "git merge task/TASK-3")
    assert code == 2
    assert "--ff-only" in capsys.readouterr().err


def test_denies_no_ff(monkeypatch, capsys):
    code = run_main(monkeypatch, "git merge --no-ff task/TASK-3")
    assert code == 2
    assert "--no-ff" in capsys.readouterr().err


def test_denies_squash(monkeypatch, capsys):
    code = run_main(monkeypatch, "git merge --squash task/TASK-3")
    assert code == 2
    assert "--squash" in capsys.readouterr().err


def test_denies_explicit_strategy(monkeypatch, capsys):
    code = run_main(monkeypatch, "git merge --strategy=recursive task/TASK-3")
    assert code == 2
    assert "--strategy" in capsys.readouterr().err


def test_denies_dash_c_merge_without_ff_only(monkeypatch, capsys):
    code = run_main(monkeypatch, "git -C /some/path merge task/TASK-3")
    assert code == 2
    assert "--ff-only" in capsys.readouterr().err


def test_allows_dash_c_merge_with_ff_only(monkeypatch):
    assert run_main(monkeypatch, "git -C /some/path merge --ff-only task/TASK-3") == 0


def test_command_invokes_git_subcommand_handles_dash_c():
    assert pmc.command_invokes_git_subcommand("git -C /p merge x", "merge") is True


def test_command_invokes_git_subcommand_false_for_other_subcommand():
    assert pmc.command_invokes_git_subcommand("git -C /p status", "merge") is False


def test_command_invokes_git_subcommand_skips_bare_flag():
    assert pmc.command_invokes_git_subcommand("git -q merge --ff-only x", "merge") is True


def test_command_invokes_git_subcommand_falls_back_on_unparsable_command():
    unbalanced = 'git merge "unterminated'
    assert pmc.command_invokes_git_subcommand(unbalanced, "merge") is True


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    with pytest.raises(SystemExit) as exc_info:
        pmc.main()
    assert exc_info.value.code == 0


def test_main_exits_cleanly_when_command_missing(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_name": "Bash"})))
    with pytest.raises(SystemExit) as exc_info:
        pmc.main()
    assert exc_info.value.code == 0
