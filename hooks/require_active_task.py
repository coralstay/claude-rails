#!/usr/bin/env python3
"""PreToolUse (matcher: Edit|Write)
Phase 1.8 + Phase 3-0: don't let Claude edit files in a backlog.md project
unless a task is In Progress and its content has actually been read this
session (`backlog task view`), so references/documentation load naturally.

Fully self-contained: no imports from any other file in this repo, so a bug
in another hook can never break this one."""

import json
import os
import shutil
import subprocess
import sys


def has_command(name):
    return shutil.which(name) is not None


def is_backlog_project(cwd):
    return (
        os.path.isdir(os.path.join(cwd, ".git"))
        and os.path.isfile(os.path.join(cwd, "backlog", "config.yml"))
    )


def has_active_task(cwd):
    result = subprocess.run(
        ["backlog", "task", "list", "--status", "In Progress", "--plain"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return "No tasks found." not in (result.stdout or "")


def deny(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    cwd = data.get("cwd", "")
    transcript = data.get("transcript_path", "") or ""

    if not has_command("backlog"):
        sys.exit(0)
    if not is_backlog_project(cwd):
        sys.exit(0)

    if not has_active_task(cwd):
        deny(
            "[claude-rails] In Progress 상태인 backlog 태스크가 없습니다. "
            '먼저 \'backlog task edit <ID> -s "In Progress"\'로 태스크를 활성화하세요.'
        )

    if transcript and os.path.isfile(transcript):
        with open(transcript, errors="ignore") as f:
            content = f.read()
        if "task view" not in content:
            deny("[claude-rails] 이 세션에서 'backlog task view <ID> --plain'으로 태스크를 먼저 읽지 않았습니다.")

    sys.exit(0)


if __name__ == "__main__":
    main()
