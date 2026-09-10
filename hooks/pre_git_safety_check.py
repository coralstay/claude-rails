#!/usr/bin/env python3
"""PreToolUse (matcher: Bash, if: Bash(git *))
Branch-aware git guardrails + destructive gh CLI protection. Ported from
karanb192/claude-code-hooks' git-safety plugin (MIT license). Owns every
git-specific destructive rule exclusively (including "force push to main",
which duplicated block_dangerous_commands upstream - see plan's "겹침 정리" #1).

Covers: direct push to main/master, deleting a protected branch, and
destructive `gh` operations (pr merge/close, issue close, release/repo delete).

Does its own subcommand/arg detection so `git -C <path> push` (flags before
the subcommand) is still recognized - same technique as pre_push_check.py,
duplicated here on purpose (each hook stays fully self-contained).

Fully self-contained: no imports from any other file in this repo."""

import json
import shlex
import sys

PROTECTED_BRANCHES = {"main", "master"}
FLAGS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def git_args_after_subcommand(command, subcommand):
    """Return the tokens that come after the given git subcommand, or None
    if that subcommand isn't invoked."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None

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
                return tokens[j + 1 :]
            break
        i = j
    return None


def deny(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def check_push(command):
    args = git_args_after_subcommand(command, "push")
    if args is None:
        return
    non_flags = [a for a in args if not a.startswith("-")]
    # `git push origin main` / `git push origin main:main` targets a branch
    # explicitly; a bare `git push` (no refspec) pushes the current branch,
    # which this hook can't determine without running git - only the
    # explicit-refspec form is checked here.
    for arg in non_flags[1:]:
        target = arg.split(":")[-1]
        if target in PROTECTED_BRANCHES:
            deny(f"[git-safety] '{target}' 브랜치로 직접 push하는 것은 금지됩니다: {command}")


def check_branch_delete(command):
    args = git_args_after_subcommand(command, "branch")
    if args is None:
        return
    if not any(a in ("-d", "-D", "--delete") for a in args):
        return
    for arg in args:
        if arg in PROTECTED_BRANCHES:
            deny(f"[git-safety] 보호된 브랜치 '{arg}' 삭제는 금지됩니다: {command}")


def check_gh_destructive(command):
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    if "gh" not in tokens:
        return

    gh_idx = tokens.index("gh")
    rest = tokens[gh_idx + 1 :]

    destructive_patterns = [
        ("pr", "merge"),
        ("pr", "close"),
        ("issue", "close"),
        ("release", "delete"),
        ("repo", "delete"),
    ]
    for noun, verb in destructive_patterns:
        if noun in rest and verb in rest:
            deny(f"[git-safety] 'gh {noun} {verb}' 계열 명령은 금지됩니다: {command}")


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    command = (data.get("tool_input") or {}).get("command", "")
    if not command:
        sys.exit(0)

    check_push(command)
    check_branch_delete(command)
    check_gh_destructive(command)

    sys.exit(0)


if __name__ == "__main__":
    main()
