#!/usr/bin/env python3
"""PreToolUse (matcher: Bash, if: Bash(git *))
Optional coverage gate: if the project's .claude-rails.json configures a
`coverageCommand` (e.g. "python3 -m pytest --cov=. --cov-fail-under=100"),
run it before every push and show the real, measured report - every time,
pass or fail. Blocks the push only when the command itself fails (e.g.
coverage.py's own --cov-fail-under exits non-zero below the threshold).
Never fabricates a percentage; a project with no coverageCommand configured
gets no message at all. Every attempt (pass or fail) is also appended to
<cwd>/.claude-rails/coverage-log.jsonl so there's a permanent record beyond
the transcript, which scrolls away.

The settings.json `if` filter only narrows to "any git command" - this
script does its own subcommand detection so `git -C <path> push` (flags
before the subcommand) is still recognized as a push, not just `git push`.

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone

FLAGS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def command_invokes_git_subcommand(command, subcommand):
    """True if `command` runs `git <subcommand>` anywhere, regardless of
    global flags (like `-C <path>`) placed before the subcommand."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return subcommand in command

    i = 0
    while i < len(tokens):
        if os.path.basename(tokens[i]) != "git":
            i += 1
            continue
        j = i + 1
        while j < len(tokens):
            tok = tokens[j]
            if tok in FLAGS_WITH_ARG:
                j += 2
                continue
            if tok.startswith("-"):
                j += 1
                continue
            if tok == subcommand:
                return True
            break
        i = j
    return False


def configured_coverage_command(cwd):
    config_path = os.path.join(cwd, ".claude-rails.json")
    if not os.path.isfile(config_path):
        return None
    with open(config_path) as f:
        config = json.load(f)
    return config.get("coverageCommand") or None


def current_branch(cwd):
    result = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def task_id_from_branch(branch):
    """Extract "TASK-7" from "task/TASK-7", or None for branches that don't
    follow that convention (main, feature branches from other workflows,
    etc.)."""
    prefix = "task/"
    if branch.startswith(prefix):
        return branch[len(prefix) :]
    return None


def run_shell(cwd, command):
    result = subprocess.run(
        command, cwd=cwd, shell=True, capture_output=True, text=True
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output


def log_path(cwd):
    return os.path.join(cwd, ".claude-rails", "coverage-log.jsonl")


def append_log(cwd, record):
    path = log_path(cwd)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    cwd = data.get("cwd", "")
    bash_command = (data.get("tool_input") or {}).get("command", "")

    if not command_invokes_git_subcommand(bash_command, "push"):
        sys.exit(0)

    command = configured_coverage_command(cwd)
    if not command:
        sys.exit(0)

    exit_code, output = run_shell(cwd, command)
    passed = exit_code == 0

    branch = current_branch(cwd)

    append_log(
        cwd,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": data.get("session_id"),
            "project": os.path.basename(os.path.normpath(cwd)) if cwd else None,
            "branch": branch or None,
            "task_id": task_id_from_branch(branch),
            "command": command,
            "exit_code": exit_code,
            "passed": passed,
            "output": output[-4000:],
        },
    )

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow" if passed else "deny",
            "permissionDecisionReason": (
                "커버리지 기준 통과"
                if passed
                else f"커버리지 기준 미달 (exit {exit_code})"
            ),
            "systemMessage": (
                f"[claude-rails] 커버리지 리포트 ('{command}', exit {exit_code}):\n"
                + output[-4000:]
            ),
        }
    }
    print(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
