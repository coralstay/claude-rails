#!/bin/bash
# PreToolUse (matcher: Bash, if: Bash(git commit *))
# Phase 3-1 + 3-4: commits must happen on a task/<ID> branch, and (if the
# project opted in via .claude-rails.json) tests must pass first.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_lib.sh"

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd')

is_backlog_project "$cwd" || exit 0

if ! no_active_task "$cwd"; then
  branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [[ "$branch" != task/* ]]; then
    deny "[claude-rails] 커밋하기 전에 태스크 브랜치(task/TASK-ID)로 전환하세요. 현재 브랜치: $branch"
  fi
fi

config_file="$cwd/.claude-rails.json"
if [ -f "$config_file" ]; then
  test_cmd=$(jq -r '.testCommand // empty' "$config_file")
  if [ -n "$test_cmd" ]; then
    test_output=$(cd "$cwd" && eval "$test_cmd" 2>&1)
    test_exit=$?
    if [ "$test_exit" -ne 0 ]; then
      deny "[claude-rails] 커밋 전 테스트 실패 ('$test_cmd', exit $test_exit):
${test_output: -800}"
    fi
  fi
fi

exit 0
