import io
import json

import pytest

import pre_git_safety_check as gsc


def run_main(monkeypatch, command):
    stdin_data = {"tool_name": "Bash", "tool_input": {"command": command}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        gsc.main()
    return exc_info.value.code


def test_blocks_push_to_main(monkeypatch, capsys):
    code = run_main(monkeypatch, "git push origin main")
    assert code == 2
    assert "main" in capsys.readouterr().err


def test_blocks_push_to_master(monkeypatch):
    assert run_main(monkeypatch, "git push origin master") == 2


def test_blocks_push_with_refspec_to_main(monkeypatch):
    assert run_main(monkeypatch, "git push origin HEAD:main") == 2


def test_allows_push_to_task_branch(monkeypatch):
    assert run_main(monkeypatch, "git push -u origin task/TASK-3") == 0


def test_allows_bare_push(monkeypatch):
    # Documented limitation: bare `git push` (implicit current branch) isn't
    # checked, since determining the current branch would require shelling
    # out to git from within the hook.
    assert run_main(monkeypatch, "git push") == 0


def test_allows_dash_c_push_to_task_branch(monkeypatch):
    assert run_main(monkeypatch, "git -C /some/path push origin task/TASK-9") == 0


def test_blocks_dash_c_push_to_main(monkeypatch):
    assert run_main(monkeypatch, "git -C /some/path push origin main") == 2


def test_blocks_branch_delete_main(monkeypatch, capsys):
    code = run_main(monkeypatch, "git branch -D main")
    assert code == 2
    assert "main" in capsys.readouterr().err


def test_blocks_branch_delete_master_long_flag(monkeypatch):
    assert run_main(monkeypatch, "git branch --delete master") == 2


def test_allows_branch_delete_task_branch(monkeypatch):
    assert run_main(monkeypatch, "git branch -d task/TASK-3") == 0


def test_allows_branch_list(monkeypatch):
    assert run_main(monkeypatch, "git branch -a") == 0


def test_blocks_gh_pr_merge(monkeypatch, capsys):
    code = run_main(monkeypatch, "gh pr merge 5 --squash")
    assert code == 2
    assert "gh pr merge" in capsys.readouterr().err


def test_blocks_gh_pr_close(monkeypatch):
    assert run_main(monkeypatch, "gh pr close 5") == 2


def test_blocks_gh_issue_close(monkeypatch):
    assert run_main(monkeypatch, "gh issue close 12") == 2


def test_blocks_gh_release_delete(monkeypatch):
    assert run_main(monkeypatch, "gh release delete v1.0.0") == 2


def test_blocks_gh_repo_delete(monkeypatch):
    assert run_main(monkeypatch, "gh repo delete owner/repo") == 2


def test_allows_gh_pr_create(monkeypatch):
    assert run_main(monkeypatch, "gh pr create --title x --body y") == 0


def test_allows_gh_pr_view(monkeypatch):
    assert run_main(monkeypatch, "gh pr view 5") == 0


def test_allows_unrelated_command(monkeypatch):
    assert run_main(monkeypatch, "git status") == 0


def test_no_op_when_command_missing(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {}})))
    with pytest.raises(SystemExit) as exc_info:
        gsc.main()
    assert exc_info.value.code == 0


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    with pytest.raises(SystemExit) as exc_info:
        gsc.main()
    assert exc_info.value.code == 0


def test_git_args_after_subcommand_returns_none_when_absent():
    assert gsc.git_args_after_subcommand("git status", "push") is None


def test_git_args_after_subcommand_falls_back_on_unparsable():
    assert gsc.git_args_after_subcommand('git push "unterminated', "push") is None
