import io
import json
import textwrap

import pytest

import dedup_drift_guard as ddg

COMMIT = {"command": "git commit -m x"}


def run_main(monkeypatch, stdin_data):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        ddg.main()
    return exc_info.value.code


def write_hook(hooks_dir, filename, body):
    (hooks_dir / filename).write_text(textwrap.dedent(body))


IDENTICAL_BODY = """
    def is_backlog_project(cwd):
        import os
        return os.path.isdir(os.path.join(cwd, ".git"))
    """

DIFFERENT_BODY = """
    def is_backlog_project(cwd):
        import os
        return os.path.isfile(os.path.join(cwd, ".git"))
    """

NO_FUNCTION_BODY = """
    def something_else(cwd):
        return True
    """


def make_fake_registry_dir(tmp_path, monkeypatch, bodies):
    """bodies: dict of filename -> source text. Creates tmp_path/hooks/
    with one file per entry in ddg.REGISTRY['is_backlog_project'], using
    `bodies` to override specific files (defaulting to IDENTICAL_BODY),
    and points the guard's REGISTRY files at that fake directory via cwd.
    """
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    for filename in ddg.REGISTRY["is_backlog_project"]:
        write_hook(hooks_dir, filename, bodies.get(filename, IDENTICAL_BODY))
    return hooks_dir


def test_no_op_when_command_is_not_a_commit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            json.dumps({"cwd": str(tmp_path), "tool_input": {"command": "git status"}})
        ),
    )
    with pytest.raises(SystemExit) as exc_info:
        ddg.main()
    assert exc_info.value.code == 0


def test_passes_when_hooks_dir_missing_registry_files(monkeypatch, tmp_path):
    # self-guard: not the claude-rails repo (no hooks/ at all)
    assert run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT}) == 0


def test_allows_commit_when_all_copies_identical(monkeypatch, tmp_path):
    make_fake_registry_dir(tmp_path, monkeypatch, {})
    assert run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT}) == 0


def test_blocks_commit_when_one_copy_differs(monkeypatch, capsys, tmp_path):
    make_fake_registry_dir(tmp_path, monkeypatch, {"session_start.py": DIFFERENT_BODY})
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT})
    assert code == 2
    err = capsys.readouterr().err
    assert "is_backlog_project" in err
    assert "session_start.py" in err


def test_blocks_commit_when_function_missing_in_one_copy(monkeypatch, capsys, tmp_path):
    make_fake_registry_dir(
        tmp_path, monkeypatch, {"pre_push_check.py": NO_FUNCTION_BODY}
    )
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": COMMIT})
    assert code == 2
    err = capsys.readouterr().err
    assert "is_backlog_project" in err
    assert "pre_push_check.py" in err
    assert "찾을 수 없습니다" in err


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    with pytest.raises(SystemExit) as exc_info:
        ddg.main()
    assert exc_info.value.code == 0


def test_command_invokes_git_subcommand_handles_dash_c():
    assert ddg.command_invokes_git_subcommand("git -C /p commit -m x", "commit") is True


def test_command_invokes_git_subcommand_false_for_other_subcommand():
    assert ddg.command_invokes_git_subcommand("git -C /p push", "commit") is False


def test_registry_files_present_true_against_real_repo():
    import os

    real_hooks_dir = os.path.dirname(os.path.abspath(ddg.__file__))
    assert ddg.registry_files_present(real_hooks_dir) is True


def test_registry_files_present_false_for_unrelated_dir(tmp_path):
    assert ddg.registry_files_present(str(tmp_path)) is False


def test_function_ast_dump_none_for_missing_file(tmp_path):
    assert (
        ddg.function_ast_dump(str(tmp_path / "nope.py"), "is_backlog_project") is None
    )


def test_function_ast_dump_none_for_unparsable_file(tmp_path):
    path = tmp_path / "bad.py"
    path.write_text("def broken(:\n")
    assert ddg.function_ast_dump(str(path), "is_backlog_project") is None


def test_find_drift_empty_when_real_repo_hooks_in_sync():
    import os

    real_hooks_dir = os.path.dirname(os.path.abspath(ddg.__file__))
    assert ddg.find_drift(real_hooks_dir) == []
