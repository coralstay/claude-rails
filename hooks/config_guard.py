#!/usr/bin/env python3
"""PreToolUse (matcher: Bash|Edit|Write)
"Who guards the guards": block the agent from tampering with its own
guardrail configuration (~/.claude/settings.json, ~/.claude/hooks/,
.claude/settings*.json, .mcp.json, plugin manifests). Ported from
karanb192/claude-code-hooks' config-guard plugin (MIT license).

Motivated by two real incidents documented upstream: the Aug 2026 CHAINDROP
npm worm hid its payload in .claude/settings.json, and CVE-2026-25725 let a
sandbox escape by injecting hooks into a settings.json that didn't exist yet
- so *creating* a protected file counts as mutation here, not just editing
an existing one. Reads always pass.

CONFIG_GUARD_ALLOW=true bypasses this for one call (deliberate config edits).

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import re
import sys

PROTECTED_PATH_PATTERNS = [
    r"(^|/)\.claude/settings(\.local)?\.json$",
    r"(^|/)\.claude/hooks/",
    r"(^|/)\.mcp\.json$",
    r"(^|/)\.claude-plugin/plugin\.json$",
    r"(^|/)\.claude/settings\.json$",
]

PROTECTED_RE = re.compile("|".join(f"(?:{p})" for p in PROTECTED_PATH_PATTERNS))

MUTATING_VERBS = {"rm", "mv", "cp", "truncate", "tee", "dd"}

REDIRECT_TARGET_RE = re.compile(r">" + r">?\s*(\S+)")
SUBCOMMAND_SPLIT_RE = re.compile(r"&&|\|\||;|\|")


def is_protected_path(path):
    if not path:
        return False
    expanded = os.path.expanduser(path).replace("\\", "/")
    return bool(PROTECTED_RE.search(expanded))


def bash_targets_protected_config(command):
    """Checks each `;`/`&&`/`|`-separated subcommand on its own: a redirect
    target or a mutating verb's own arguments must point at a protected
    path - a protected-looking token elsewhere in the command (e.g. a `cd`
    target earlier in the pipeline) does not count."""
    if not command:
        return False

    for sub in SUBCOMMAND_SPLIT_RE.split(command):
        sub = sub.strip()
        if not sub:
            continue

        for target in REDIRECT_TARGET_RE.findall(sub):
            if is_protected_path(target):
                return True

        tokens = re.split(r"\s+", sub)
        verb = tokens[0] if tokens else ""
        if verb == "sed" and "-i" not in tokens:
            continue
        if verb not in MUTATING_VERBS and verb != "sed":
            continue
        if any(is_protected_path(token) for token in tokens[1:]):
            return True

    return False


def deny(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def main():
    if os.environ.get("CONFIG_GUARD_ALLOW") == "true":
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input") or {}

    if tool_name in ("Edit", "Write"):
        path = tool_input.get("file_path", "")
        if is_protected_path(path):
            deny(f"[config-guard] 자기 자신의 훅/설정 파일 수정은 금지됩니다: {path}")

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if bash_targets_protected_config(command):
            deny(f"[config-guard] 훅/설정 파일을 변경하는 명령으로 보여 차단되었습니다: {command}")

    sys.exit(0)


if __name__ == "__main__":
    main()
