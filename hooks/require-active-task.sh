#!/bin/bash
# PreToolUse (matcher: Edit|Write)
# Phase 1.8 + Phase 3-0: don't let Claude edit files in a backlog.md project
# unless a task is In Progress and its content has actually been read this
# session (`backlog task view`), so references/documentation load naturally.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_lib.sh"

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd')
transcript=$(echo "$input" | jq -r '.transcript_path // empty')

command -v backlog >/dev/null 2>&1 || exit 0
is_backlog_project "$cwd" || exit 0

if no_active_task "$cwd"; then
  deny "[claude-rails] In Progress 상태인 backlog 태스크가 없습니다. 먼저 'backlog task edit <ID> -s \"In Progress\"'로 태스크를 활성화하세요."
fi

if [ -n "$transcript" ] && [ -f "$transcript" ] && ! grep -q "task view" "$transcript" 2>/dev/null; then
  deny "[claude-rails] 이 세션에서 'backlog task view <ID> --plain'으로 태스크를 먼저 읽지 않았습니다."
fi

exit 0
