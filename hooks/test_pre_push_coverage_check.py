import io
import json

import pytest

import pre_push_coverage_check as ppc

PUSH_INPUT = {"command": "git push"}


def run_main(monkeypatch, stdin_data):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        ppc.main()
    return exc_info.value.code


def test_no_op_when_command_is_not_a_push(tmp_path, monkeypatch, capsys):
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "exit 1"})
    )
    code = run_main(
        monkeypatch, {"cwd": str(tmp_path), "tool_input": {"command": "git status"}}
    )
    assert code == 0
    assert capsys.readouterr().out == ""
    assert not (tmp_path / ".claude-rails" / "coverage-log.jsonl").exists()


def test_no_op_when_no_config_file(tmp_path, monkeypatch, capsys):
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": PUSH_INPUT})
    assert code == 0
    assert capsys.readouterr().out == ""
    assert not (tmp_path / ".claude-rails" / "coverage-log.jsonl").exists()


def test_no_op_when_coverage_command_key_missing(tmp_path, monkeypatch, capsys):
    (tmp_path / ".claude-rails.json").write_text(json.dumps({}))
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": PUSH_INPUT})
    assert code == 0
    assert capsys.readouterr().out == ""
    assert not (tmp_path / ".claude-rails" / "coverage-log.jsonl").exists()


def test_allows_and_reports_when_command_succeeds(tmp_path, monkeypatch, capsys):
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "echo 'TOTAL 100%' && exit 0"})
    )
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": PUSH_INPUT})
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "TOTAL 100%" in hso["systemMessage"]

    log_file = tmp_path / ".claude-rails" / "coverage-log.jsonl"
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["passed"] is True
    assert record["exit_code"] == 0
    assert "TOTAL 100%" in record["output"]
    assert "timestamp" in record


def test_denies_and_reports_when_command_fails(tmp_path, monkeypatch, capsys):
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "echo 'TOTAL 42%' && exit 1"})
    )
    code = run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": PUSH_INPUT})
    assert code == 0  # blocking happens via JSON permissionDecision, not exit code
    payload = json.loads(capsys.readouterr().out)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "미달" in hso["permissionDecisionReason"]
    assert "TOTAL 42%" in hso["systemMessage"]

    log_file = tmp_path / ".claude-rails" / "coverage-log.jsonl"
    record = json.loads(log_file.read_text().splitlines()[0])
    assert record["passed"] is False
    assert record["exit_code"] == 1


def test_fires_on_dash_c_push(tmp_path, monkeypatch, capsys):
    # Regression: `git -C <path> push ...` must still be recognized, not
    # just a literal `git push` prefix.
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "echo ran && exit 0"})
    )
    code = run_main(
        monkeypatch,
        {
            "cwd": str(tmp_path),
            "tool_input": {"command": f"git -C {tmp_path} push -u origin x"},
        },
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "allow"


def _init_git_repo(cwd, branch):
    import subprocess

    subprocess.run(
        ["git", "init", "-q", "-b", branch], cwd=cwd, check=True, capture_output=True
    )
    (cwd / "f.txt").write_text("hi")
    subprocess.run(["git", "add", "f.txt"], cwd=cwd, check=True, capture_output=True)
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
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def test_log_includes_session_project_branch_task_id(tmp_path, monkeypatch):
    _init_git_repo(tmp_path, "task/TASK-42")
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "exit 0"})
    )
    run_main(
        monkeypatch,
        {"cwd": str(tmp_path), "session_id": "sess-abc123", "tool_input": PUSH_INPUT},
    )

    log_file = tmp_path / ".claude-rails" / "coverage-log.jsonl"
    record = json.loads(log_file.read_text().splitlines()[0])
    assert record["session_id"] == "sess-abc123"
    assert record["project"] == tmp_path.name
    assert record["branch"] == "task/TASK-42"
    assert record["task_id"] == "TASK-42"


def test_log_task_id_is_none_off_task_branch(tmp_path, monkeypatch):
    _init_git_repo(tmp_path, "main")
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "exit 0"})
    )
    run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": PUSH_INPUT})

    log_file = tmp_path / ".claude-rails" / "coverage-log.jsonl"
    record = json.loads(log_file.read_text().splitlines()[0])
    assert record["branch"] == "main"
    assert record["task_id"] is None


def test_task_id_from_branch():
    assert ppc.task_id_from_branch("task/TASK-7") == "TASK-7"
    assert ppc.task_id_from_branch("main") is None
    assert ppc.task_id_from_branch("") is None


def test_log_appends_across_multiple_push_attempts(tmp_path, monkeypatch):
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "exit 1"})
    )
    run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": PUSH_INPUT})
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "exit 0"})
    )
    run_main(monkeypatch, {"cwd": str(tmp_path), "tool_input": PUSH_INPUT})

    log_file = tmp_path / ".claude-rails" / "coverage-log.jsonl"
    lines = log_file.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["passed"] is False
    assert json.loads(lines[1])["passed"] is True


def test_append_log_creates_directory(tmp_path):
    ppc.append_log(str(tmp_path), {"a": 1})
    log_file = tmp_path / ".claude-rails" / "coverage-log.jsonl"
    assert json.loads(log_file.read_text().strip()) == {"a": 1}


def test_log_path(tmp_path):
    assert ppc.log_path(str(tmp_path)) == str(
        tmp_path / ".claude-rails" / "coverage-log.jsonl"
    )


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    with pytest.raises(SystemExit) as exc_info:
        ppc.main()
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == ""


def test_configured_coverage_command_reads_file(tmp_path):
    (tmp_path / ".claude-rails.json").write_text(
        json.dumps({"coverageCommand": "pytest --cov"})
    )
    assert ppc.configured_coverage_command(str(tmp_path)) == "pytest --cov"


def test_configured_coverage_command_none_without_file(tmp_path):
    assert ppc.configured_coverage_command(str(tmp_path)) is None


def test_run_shell_captures_combined_output():
    code, output = ppc.run_shell(".", "echo out; echo err >&2; exit 5")
    assert code == 5
    assert "out" in output and "err" in output


def test_command_invokes_git_subcommand_handles_dash_c():
    assert ppc.command_invokes_git_subcommand("git -C /p push", "push") is True


def test_command_invokes_git_subcommand_false_for_other_subcommand():
    assert ppc.command_invokes_git_subcommand("git -C /p status", "push") is False


def test_command_invokes_git_subcommand_skips_bare_flag():
    assert ppc.command_invokes_git_subcommand("git -q push", "push") is True


def test_command_invokes_git_subcommand_falls_back_on_unparsable_command():
    unbalanced = 'git push "unterminated'
    assert ppc.command_invokes_git_subcommand(unbalanced, "push") is True


def test_command_invokes_git_subcommand_detects_absolute_path_bypass():
    assert ppc.command_invokes_git_subcommand("/usr/bin/git push", "push") is True


def test_command_invokes_git_subcommand_detects_relative_path_bypass():
    assert ppc.command_invokes_git_subcommand("./git push", "push") is True


def test_command_invokes_git_subcommand_ignores_git_outside_verb_position():
    assert ppc.command_invokes_git_subcommand("echo /usr/bin/git", "push") is False
