#!/usr/bin/env python3
"""PermissionRequest
Auto-approves permission prompts that carry no real risk, so read-only
exploration doesn't interrupt the agent every few seconds. Ported from
disler/claude-code-hooks-mastery's permission-request demo hook
(Python/uv-script reference implementation).

Scope, deliberately conservative:
- Read, Glob, Grep are always auto-allowed (no side effects).
- Bash is auto-allowed only for a fixed allowlist of read-only commands
  (ls, cat, pwd, echo, git status/log/diff/show, etc.) with no shell
  metacharacters (pipes/redirects/subshells/chaining) present - those are
  left to the normal permission flow since they can hide side effects.
Everything else (Edit, Write, other Bash, MCP tools, ...) is left alone -
this hook only ever adds "allow" outcomes, never "deny".

Fully self-contained: no imports from any other file in this repo."""

import json
import re
import sys

AUTO_ALLOW_TOOLS = {"Read", "Glob", "Grep"}

SAFE_BASH_COMMANDS = {
    "ls", "pwd", "cat", "echo", "whoami", "date", "which", "head", "tail",
    "wc", "find",
}

SAFE_GIT_SUBCOMMANDS = {"status", "log", "diff", "show", "branch", "remote"}

SHELL_METACHARACTER_RE = re.compile(r"[|;&$`(){}<>]|\n")


def is_safe_bash_command(command):
    if SHELL_METACHARACTER_RE.search(command):
        return False

    parts = command.strip().split()
    if not parts:
        return False

    program = parts[0]
    if program == "git":
        return len(parts) > 1 and parts[1] in SAFE_GIT_SUBCOMMANDS
    return program in SAFE_BASH_COMMANDS


def should_auto_allow(tool_name, tool_input):
    if tool_name in AUTO_ALLOW_TOOLS:
        return True
    if tool_name == "Bash":
        return is_safe_bash_command((tool_input or {}).get("command", ""))
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if should_auto_allow(tool_name, tool_input):
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PermissionRequest",
                        "permissionDecision": "allow",
                        "permissionDecisionReason": "permission_auto_allow: read-only tool/command",
                    }
                }
            )
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
