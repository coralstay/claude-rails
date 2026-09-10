#!/usr/bin/env python3
"""PreToolUse (matcher: Bash, if: Bash(git *))
Enforce fast-forward-only merges so history stays linear and rebase-friendly
(no merge commits, no squash). `merge.ff=only` in git config already makes
a non-fast-forward `git merge` fail, but this hook catches it earlier with a
clearer message and also blocks explicit opt-outs like `--no-ff`.

The settings.json `if` filter only narrows to "any git command" - this
script does its own subcommand detection so `git -C <path> merge` (flags
before the subcommand) is still recognized as a merge, not just
`git merge`.

Fully self-contained: no imports from any other file in this repo."""

import json
import shlex
import sys

DISALLOWED_FLAGS = ("--no-ff", "--squash", "-s ", "--strategy")
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


def deny(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    command = (data.get("tool_input") or {}).get("command", "")

    if not command_invokes_git_subcommand(command, "merge"):
        sys.exit(0)

    for flag in DISALLOWED_FLAGS:
        if flag in command:
            deny(
                f"[claude-rails] '{flag.strip()}' 옵션은 이 프로젝트에서 금지됩니다 "
                "(fast-forward 전용 정책). 먼저 로컬에서 rebase한 뒤 "
                "'git merge --ff-only <branch>'로 병합하세요."
            )

    if "--ff-only" not in command:
        deny(
            "[claude-rails] 'git merge'는 반드시 '--ff-only'와 함께 써야 합니다 "
            "(fast-forward 전용 정책). 먼저 로컬에서 rebase한 뒤 "
            "'git merge --ff-only <branch>'로 병합하세요."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
