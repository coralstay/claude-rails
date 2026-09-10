#!/usr/bin/env python3
"""PostToolUse (matcher: Write|Edit)
Auto-formats the edited file, then runs lint/type checks and feeds back
whatever formatting couldn't fix. Merges two upstream plugins into one pass
so ruff/tsc aren't invoked twice per edit (see plan's "겹침 정리" #3):
karanb192/claude-code-hooks' format-code (auto-fix) +
disler/claude-code-hooks-mastery's ruff_validator/ty_validator
(report-only), both MIT/open-source.

Order per file: 1) format (ruff format / prettier --write), 2) lint/type
check what remains (ruff check / tsc --noEmit) and report via systemMessage
- never blocks (this is feedback, not enforcement; block_dangerous_commands
and friends own actual blocking).

Silently does nothing if the relevant tool isn't on PATH.

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import shutil
import subprocess
import sys

PY_EXTENSIONS = {".py"}
PRETTIER_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".yaml", ".yml", ".html", ".css"}


def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def format_and_check_python(path):
    messages = []
    if shutil.which("ruff"):
        run(["ruff", "format", path])
        code, output = run(["ruff", "check", path])
        if code != 0:
            messages.append(f"ruff check:\n{output.strip()}")
    return messages


def format_and_check_js(path, ext):
    messages = []
    if shutil.which("prettier") or shutil.which("npx"):
        cmd = ["prettier", "--write", path] if shutil.which("prettier") else ["npx", "--yes", "prettier", "--write", path]
        run(cmd)
    if ext in (".ts", ".tsx") and shutil.which("tsc"):
        code, output = run(["tsc", "--noEmit", path])
        if code != 0:
            messages.append(f"tsc --noEmit:\n{output.strip()}")
    return messages


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("tool_name") not in ("Write", "Edit"):
        sys.exit(0)

    path = (data.get("tool_input") or {}).get("file_path", "")
    if not path or not os.path.isfile(path):
        sys.exit(0)

    _, ext = os.path.splitext(path)
    messages = []

    if ext in PY_EXTENSIONS:
        messages = format_and_check_python(path)
    elif ext in PRETTIER_EXTENSIONS:
        messages = format_and_check_js(path, ext)

    if messages:
        print(f"[format-code] {path}\n" + "\n\n".join(messages), file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
