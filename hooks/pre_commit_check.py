#!/usr/bin/env python3
"""PreToolUse (matcher: Bash, if: Bash(git *))
Phase 3-1 + 3-4: commits must happen on a task/<ID> branch, and (if the
project opted in via .claude-rails.json) tests must pass first.

The settings.json `if` filter only narrows to "any git command" - this
script does its own subcommand detection so `git -C <path> commit` (flags
before the subcommand) is still recognized as a commit, not just
`git commit`.

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import shlex
import shutil
import subprocess
import sys

FLAGS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def has_command(name):
    return shutil.which(name) is not None


def command_invokes_git_subcommand(command, subcommand):
    """True if `command` runs `git <subcommand>` anywhere, regardless of
    global flags (like `-C <path>`) placed before the subcommand."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return subcommand in command

    i = 0
    while i < len(tokens):
        if tokens[i] != "git":
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


def is_backlog_project(cwd):
    return os.path.isfile(os.path.join(cwd, "backlog", "config.yml"))


def has_active_task(cwd):
    result = subprocess.run(
        ["backlog", "task", "list", "--status", "In Progress", "--plain"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return "No tasks found." not in (result.stdout or "")


def current_branch(cwd):
    result = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def configured_test_command(cwd):
    config_path = os.path.join(cwd, ".claude-rails.json")
    if not os.path.isfile(config_path):
        return None
    with open(config_path) as f:
        config = json.load(f)
    return config.get("testCommand") or None


def run_shell(cwd, command):
    result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output


def deny(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    cwd = data.get("cwd", "")
    command = (data.get("tool_input") or {}).get("command", "")

    if not command_invokes_git_subcommand(command, "commit"):
        sys.exit(0)
    if not has_command("backlog"):
        sys.exit(0)
    if not is_backlog_project(cwd):
        sys.exit(0)

    if has_active_task(cwd):
        branch = current_branch(cwd)
        if not branch.startswith("task/"):
            deny(f"[claude-rails] 커밋하기 전에 태스크 브랜치(task/TASK-ID)로 전환하세요. 현재 브랜치: {branch}")

    test_command = configured_test_command(cwd)
    if test_command:
        exit_code, output = run_shell(cwd, test_command)
        if exit_code != 0:
            deny(
                f"[claude-rails] 커밋 전 테스트 실패 ('{test_command}', exit {exit_code}):\n"
                + output[-800:]
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
