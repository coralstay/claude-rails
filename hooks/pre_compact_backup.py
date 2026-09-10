#!/usr/bin/env python3
"""PreCompact
Backs up the full transcript right before context compaction discards it,
so nothing said earlier in the session is unrecoverably lost. Ported from
disler/claude-code-hooks-mastery's pre_compact hook (Python/uv-script
reference implementation).

Output: ~/.claude/hooks-logs/transcript_backups/<session_id>-<timestamp>.jsonl,
a byte-for-byte copy of the transcript file named by `transcript_path`.

Fully self-contained: no imports from any other file in this repo."""

import json
import os
import shutil
import sys
from datetime import datetime, timezone

BACKUP_DIR = os.path.expanduser("~/.claude/hooks-logs/transcript_backups")


def backup_path(session_id):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return os.path.join(BACKUP_DIR, f"{session_id}-{timestamp}.jsonl")


def backup_transcript(transcript_path, session_id):
    if not transcript_path or not os.path.isfile(transcript_path):
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)
    dest = backup_path(session_id)
    shutil.copyfile(transcript_path, dest)
    return dest


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    backup_transcript(data.get("transcript_path"), data.get("session_id", "unknown"))
    sys.exit(0)


if __name__ == "__main__":
    main()
