#!/usr/bin/env python3
"""PreToolUse (matcher: Bash)
Block catastrophic/high-risk shell commands before they run. Ported from
karanb192/claude-code-hooks' block-dangerous-commands plugin (MIT license),
scope narrowed: "force push to main" is owned exclusively by
pre_git_safety_check.py to avoid the duplicate rule that exists in the
upstream project itself (see plan's "겹침 정리" #1).

HOOK_SAFETY_LEVEL env var picks the ruleset: critical (default) | high | strict.
Unknown values fall back to critical.

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import re
import sys

CRITICAL_PATTERNS = [
    (
        r"rm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+(/|~|\$HOME)\s*($|/\s*$)",
        "rm -rf on root or home",
    ),
    (
        r"rm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s+(/|~|\$HOME)\s*($|/\s*$)",
        "rm -rf on root or home",
    ),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "fork bomb"),
    (r"\bdd\s+.*of=/dev/(disk|sda|nvme|rdisk)", "dd writing directly to a disk device"),
    (r"\bmkfs(\.\w+)?\s+/dev/", "formatting a device"),
]

RM_RF_FLAGS = r"-[a-zA-Z]*(?:r[a-zA-Z]*f[a-zA-Z]*|f[a-zA-Z]*r[a-zA-Z]*)[a-zA-Z]*\b"

HIGH_PATTERNS = CRITICAL_PATTERNS + [
    (r"\bcurl\b[^|]*\|\s*(sudo\s+)?(sh|bash|zsh)\b", "curl | sh"),
    (r"\bwget\b[^|]*\|\s*(sudo\s+)?(sh|bash|zsh)\b", "wget | sh"),
    (r"git\s+reset\s+--hard\b", "git reset --hard"),
    # rm -rf targeting a path that walks up out of the current directory via
    # ".." (rm -rf ../, rm -rf ../../foo, rm -rf ./some-dir/../../important).
    # Approximate on purpose: scoped to a single shell "segment" ([^;&|\n])
    # so it doesn't reach across an unrelated && / ; / | into another command.
    (
        rf"rm\s+{RM_RF_FLAGS}[^;&|\n]*?(?:^|[\s/])\.\.(?=/|$|\s)",
        "rm -rf escaping the current directory via ..",
    ),
    # rm -rf targeting an absolute path that isn't one of a small set of
    # common safe/temp directories. This can't know the real cwd from the
    # command string alone, so it's a practical approximation, not a proof.
    (
        rf"rm\s+{RM_RF_FLAGS}[^;&|\n]*?(?:^|\s)/(?!tmp\b|var/tmp\b|private/tmp\b|var/folders\b|dev/null\b|\s|$)\S+",
        "rm -rf on an absolute path outside common safe/temp directories",
    ),
]

STRICT_PATTERNS = HIGH_PATTERNS + [
    (r"\bsudo\s+rm\b", "sudo rm"),
    (r"\bdocker\s+(system\s+)?prune\b", "docker prune"),
]

LEVELS = {
    "critical": CRITICAL_PATTERNS,
    "high": HIGH_PATTERNS,
    "strict": STRICT_PATTERNS,
}


def get_patterns():
    level = os.environ.get("HOOK_SAFETY_LEVEL", "critical")
    return LEVELS.get(level, CRITICAL_PATTERNS)


def find_violation(command):
    for pattern, reason in get_patterns():
        if re.search(pattern, command):
            return reason
    return None


def deny(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    command = (data.get("tool_input") or {}).get("command", "")
    if not command:
        sys.exit(0)

    violation = find_violation(command)
    if violation:
        deny(
            f"[block-dangerous-commands] 위험한 명령이 차단되었습니다: {violation}\n명령: {command}"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
