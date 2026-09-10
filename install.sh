#!/bin/bash
# Installs claude-rails globally: copies hook scripts to ~/.claude/hooks/claude-rails,
# merges settings.hooks.json into ~/.claude/settings.json, and appends the
# workflow snippet to ~/.claude/CLAUDE.md. Safe to re-run.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_HOOKS_DIR="$HOME/.claude/hooks/claude-rails"
SETTINGS_FILE="$HOME/.claude/settings.json"
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

command -v jq >/dev/null 2>&1 || { echo "jq가 필요합니다 (brew install jq)"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3가 필요합니다"; exit 1; }
command -v backlog >/dev/null 2>&1 || echo "경고: backlog CLI가 안 보입니다 (npm i -g backlog.md)"

echo "==> hooks 스크립트 설치: $TARGET_HOOKS_DIR"
mkdir -p "$TARGET_HOOKS_DIR"
cp "$REPO_DIR"/hooks/*.py "$TARGET_HOOKS_DIR/"
echo "    훅 본체 + 테스트(test_*.py)를 같은 디렉토리에 나란히 설치함 (로컬 실제 구성과 동일)"

echo "==> settings.json에 hooks 병합"
[ -f "$SETTINGS_FILE" ] || echo '{}' > "$SETTINGS_FILE"
cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak.$(date +%s)"
jq -s '.[0] * .[1]' "$SETTINGS_FILE" "$REPO_DIR/settings.hooks.json" > "$SETTINGS_FILE.tmp"
mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
echo "    기존 settings.json은 $SETTINGS_FILE.bak.* 로 백업됨"
echo "    주의: 이미 PreToolUse/Stop/SessionStart 훅이 있었다면 jq의 객체 병합 특성상"
echo "    같은 이벤트의 배열이 새 값으로 대체될 수 있습니다. 백업과 비교해 확인하세요."

echo "==> CLAUDE.md에 워크플로 규칙 추가"
MARKER="<!-- CLAUDE-RAILS:BEGIN -->"
if [ -f "$CLAUDE_MD" ] && grep -q "$MARKER" "$CLAUDE_MD"; then
  echo "    이미 설치되어 있어 건너뜀 (갱신하려면 마커 블록을 지우고 다시 실행)"
else
  cat "$REPO_DIR/CLAUDE.md.snippet" >> "$CLAUDE_MD"
  echo "    추가 완료: $CLAUDE_MD"
fi

echo "==> 설치 완료."
