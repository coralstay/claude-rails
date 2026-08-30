#!/bin/bash
# Shared helpers for claude-rails hook scripts.

# Block the current action. Exit code 2 is the one blocking mechanism that
# works uniformly across PreToolUse, Stop, and the other blockable events.
deny() {
  echo "$1" >&2
  exit 2
}

is_backlog_project() {
  [ -f "$1/backlog/config.yml" ]
}

# True (exit 0) when there is no "In Progress" backlog task in $1.
no_active_task() {
  local cwd="$1"
  local list
  list=$(cd "$cwd" && backlog task list --status "In Progress" --plain 2>/dev/null)
  echo "$list" | grep -q "No tasks found."
}
