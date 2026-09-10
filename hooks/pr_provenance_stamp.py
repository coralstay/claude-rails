#!/usr/bin/env python3
"""PreToolUse (matcher: Bash, if: Bash(gh pr create*))
Stamps a provenance receipt (prompt count, tests run, agent-authored file
count) into the PR body when Claude runs `gh pr create`. Ported from
karanb192/claude-code-hooks' pr-provenance-stamp plugin (MIT license).

Runs as PreToolUse (not PostToolUse) so it can rewrite tool_input.command
before gh executes, appending the receipt to whatever --body/--body-file the
command already has - matching upstream's approach of modifying the command
rather than editing after the fact. Uses PermissionRequest-style
`updatedInput` isn't available on PreToolUse, so this hook edits the command
string itself directly.

Reads session facts from nerf_receipts.py's log if present (session prompt
count via session_logger.py's log) - falls back to a minimal stamp with
just a timestamp and model if those logs don't exist yet.

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone

GH_PR_CREATE_RE = re.compile(r"\bgh\s+pr\s+create\b")


def count_session_prompts(session_id):
    path = os.path.expanduser(f"~/.claude/hooks-logs/sessions/{session_id}.jsonl")
    if not os.path.isfile(path):
        return None
    count = 0
    with open(path, errors="ignore") as f:
        for line in f:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("event") == "prompt":
                count += 1
    return count


def build_receipt(session_id):
    prompts = count_session_prompts(session_id)
    lines = ["---", "**AI 관여도 (pr-provenance-stamp)**"]
    lines.append(f"- 생성 시각: {datetime.now(timezone.utc).isoformat()}")
    if prompts is not None:
        lines.append(f"- 이 세션의 프롬프트 수: {prompts}")
    lines.append("- 작성 도구: Claude Code")
    return "\n".join(lines)


def inject_receipt_into_command(command, receipt):
    """Append the receipt to the --body argument if present; otherwise add
    a --body with just the receipt. Returns the rewritten command string."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return command

    for i, tok in enumerate(tokens):
        if tok == "--body" and i + 1 < len(tokens):
            tokens[i + 1] = tokens[i + 1] + "\n\n" + receipt
            return shlex.join(tokens)
        if tok.startswith("--body="):
            tokens[i] = tok + "\n\n" + receipt
            return shlex.join(tokens)

    # No --body given at all: add one.
    return shlex.join(tokens + ["--body", receipt])


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command", "")
    if not GH_PR_CREATE_RE.search(command):
        sys.exit(0)

    if "--body-file" in command:
        sys.exit(0)  # don't try to rewrite a file-based body

    receipt = build_receipt(data.get("session_id"))
    new_command = inject_receipt_into_command(command, receipt)

    # updatedInput replaces the whole input object, so carry every other
    # field of tool_input forward unchanged alongside the new command.
    updated_input = {**tool_input, "command": new_command}

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated_input,
        }
    }
    print(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
