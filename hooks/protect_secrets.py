#!/usr/bin/env python3
"""PreToolUse (matcher: Read|Edit|Write|Bash)
Prevent reading, modifying, or exfiltrating secret files (.env, SSH keys,
cloud credentials, keystores). Ported from karanb192/claude-code-hooks'
protect-secrets plugin (MIT license).

Covers the Bash-level bypass (grep/cat/cp on a protected file, not just the
Read/Edit/Write tools directly) since that's the documented real-world gap
this plugin fixed upstream.

HOOK_SAFETY_LEVEL: critical|high|strict (default: high).

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import re
import sys

PROTECTED_PATTERNS = [
    r"(^|/)\.env(\.[a-zA-Z0-9_.-]+)?$",
    r"(^|/)\.aws/credentials$",
    r"(^|/)\.ssh/id_[a-zA-Z0-9]+$",
    r"\.pem$",
    r"(^|/)\.npmrc$",
    r"(^|/)\.netrc$",
    r"\.pfx$",
    r"\.keystore$",
    r"(^|/)secrets?\.ya?ml$",
]

PROTECTED_RE = re.compile("|".join(f"(?:{p})" for p in PROTECTED_PATTERNS))


def is_protected_path(path):
    if not path:
        return False
    normalized = path.replace("\\", "/")
    return bool(PROTECTED_RE.search(normalized))


def bash_targets_protected_file(command):
    """Best-effort: does any whitespace-delimited token in this shell command
    look like a protected file path (covers `grep -r . .env`, `cat .env`,
    `cp .env /tmp`, etc.). Token-based rather than a single substring search
    so the `$`-anchored patterns in PROTECTED_PATTERNS still work correctly
    against a multi-argument command line."""
    if not command:
        return False
    tokens = re.split(r"\s+", command)
    return any(is_protected_path(tok) for tok in tokens)


def deny(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input") or {}

    if tool_name in ("Read", "Edit", "Write"):
        path = tool_input.get("file_path", "")
        if is_protected_path(path):
            deny(f"[protect-secrets] 보호된 파일입니다, 접근이 차단되었습니다: {path}")

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if bash_targets_protected_file(command):
            deny(f"[protect-secrets] 보호된 파일을 건드리는 명령으로 보여 차단되었습니다: {command}")

    sys.exit(0)


if __name__ == "__main__":
    main()
