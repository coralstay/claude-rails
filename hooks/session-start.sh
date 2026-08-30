#!/bin/bash
# SessionStart: if cwd is a backlog.md project, brief Claude with the official
# workflow guide and surface any integrity issues. Cannot block (SessionStart
# doesn't support it) - this is context injection only.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/_lib.sh"

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd')

command -v backlog >/dev/null 2>&1 || exit 0
is_backlog_project "$cwd" || exit 0

overview=$(cd "$cwd" && backlog instructions overview 2>/dev/null)
doctor_out=$(cd "$cwd" && backlog doctor 2>/dev/null)

jq -n --arg ctx "$overview" --arg doctor "$doctor_out" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx,
    systemMessage: ("backlog doctor:\n" + $doctor)
  }
}'
exit 0
