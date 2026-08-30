#!/bin/bash
# PreToolUse (matcher: Bash, if: Bash(git push *))
# Phase 4.3: only push a task/<ID> branch once that task is Done and carries
# a final summary.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_lib.sh"

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd')

is_backlog_project "$cwd" || exit 0

branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)
[[ "$branch" == task/* ]] || exit 0
task_id="${branch#task/}"

view_json=$(cd "$cwd" && backlog task view "$task_id" --json 2>/dev/null)
[ -z "$view_json" ] && exit 0

status=$(echo "$view_json" | jq -r '.task.status // empty')
summary=$(echo "$view_json" | jq -r '.task.finalSummary // empty')

if [ "$status" != "Done" ]; then
  deny "[claude-rails] $task_id 가 아직 Done 상태가 아닙니다 (현재: $status). 완료 처리 후 push하세요."
fi
if [ -z "$(echo "$summary" | tr -d '[:space:]')" ]; then
  deny "[claude-rails] $task_id 의 final summary가 비어있습니다. 'backlog task edit $task_id --final-summary \"...\"' 로 작성 후 push하세요."
fi

exit 0
