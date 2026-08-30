#!/bin/bash
# Stop
# Phase 3-4b: don't let Claude end its turn with uncommitted changes while a
# task is In Progress - forces the small-commit loop to actually finish.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_lib.sh"

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd')

command -v backlog >/dev/null 2>&1 || exit 0
is_backlog_project "$cwd" || exit 0
no_active_task "$cwd" && exit 0

dirty=$(git -C "$cwd" status --porcelain 2>/dev/null)
if [ -n "$dirty" ]; then
  deny "[claude-rails] 커밋하지 않은 변경사항이 있습니다. 작은 단위로 커밋을 마무리한 뒤 턴을 종료하세요."
fi

exit 0
