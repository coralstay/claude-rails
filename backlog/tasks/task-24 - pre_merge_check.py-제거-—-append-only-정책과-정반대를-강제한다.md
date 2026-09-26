---
id: TASK-24
title: pre_merge_check.py 제거 — append-only 정책과 정반대를 강제한다
status: To Do
assignee: []
created_date: '2026-09-26 13:11'
updated_date: '2026-09-26 13:11'
labels:
  - hooks
  - policy
dependencies: []
priority: high
type: chore
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
pre_merge_check.py는 fast-forward 전용 병합을 강제한다 — 주석 그대로 "no merge commits, no squash"다. git-format이 2026-09-26에 이력 정책을 append-only로 정하면서(git-format decision-24) 이 훅이 강제하는 것이 **정책의 정반대**가 됐다.

## 근거

git-format의 전제는 "에이전트가 프로그래밍하고 git이 그 작업의 로그로 동작한다"다. rebase-merge가 실제로 기록을 거짓으로 만들고 있었다 — 실측: main의 커밋들이 Signed-off-by: cpu-once를 달고 있는데 실제 committer는 coralstay(GitHub)다. post-commit이 로컬 커미터로 트레일러를 쓴 뒤 GitHub이 rebase로 커밋을 다시 만들어서다. %G?도 전부 N이다.

외부 근거: Linux 커널 메인테이너 문서("공개된 이력은 바꾸지 말 것", "reparenting은 그때의 검증을 무효화한다", "커널 커뮤니티는 merge commit을 두려워하지 않는다"), 서명이 rebase로 깨진다는 사실, force-push 1.6억 건 규모의 provenance 연구(arXiv 2607.02774).

## 실제로 막고 있던 것

이 훅이 조사 중 두 번 작업을 차단했다. git merge를 --ff-only 없이 쓰는 것도, 압축 병합 옵션을 문자열로 포함한 명령도 막았다 — 후자는 그 옵션명이 무관한 heredoc 안에 있었을 때도 막혔다(명령 문자열 전체를 부분 문자열로 매칭한다). append-only 정책에서는 merge 커밋이 유일하게 허용되는 병합 방식이므로 이 훅은 정상 작업을 막는 장애물이다.

## 제거 범위

- hooks/pre_merge_check.py, hooks/test_pre_merge_check.py
- settings.hooks.json의 PreToolUse(Bash) 항목
- hooks/dedup_drift_guard.py의 REGISTRY 목록에서 제거 (안 지우면 드리프트 가드가 없는 파일을 찾는다)
- hooks/test_dedup_drift_guard.py의 기대값
- README.md, backlog/docs/doc-2의 서술
- 설치된 사본 ~/.claude/hooks/claude-rails/pre_merge_check.py와 ~/.claude/settings.json 항목

## 함께 대체해야 하는 결정

decision-5("GitHub PR은 항상 rebase-merge로 병합")가 git-format decision-24와 정면 충돌한다. 대체하는 새 decision이 필요하다.

decision-4("push·원격 병합은 항상 사람이 최종 승인 — 로컬 fast-forward까지만 자동화")도 "로컬 fast-forward까지만" 부분이 어긋난다 — 검토 필요.

git config merge.ff는 전역·로컬 모두 설정돼 있지 않아 되돌릴 것이 없다(확인).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 hooks/pre_merge_check.py와 hooks/test_pre_merge_check.py를 삭제한다
- [ ] #2 settings.hooks.json에서 해당 PreToolUse 항목을 제거한다
- [ ] #3 hooks/dedup_drift_guard.py의 REGISTRY에서 제거하고 test_dedup_drift_guard.py의 기대값을 맞춘다
- [ ] #4 README.md와 backlog/docs/doc-2에서 fast-forward 전용 강제 서술을 제거한다
- [ ] #5 설치된 사본과 ~/.claude/settings.json 항목을 제거한다
- [ ] #6 decision-5(PR은 항상 rebase-merge)를 대체하는 새 decision을 만든다 — git-format decision-24를 따른다
- [ ] #7 decision-4의 '로컬 fast-forward까지만 자동화' 부분이 어긋나는지 검토해 결과를 기록한다
- [ ] #8 제거 후 git merge가 --ff-only 없이도 통과하는지 확인한다
- [ ] #9 나머지 훅들이 그대로 동작하는지 확인한다 (드리프트 가드 포함)
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 훅 테스트 스위트 통과
- [ ] #2 실제로 merge 커밋을 만들어 차단되지 않는지 확인
<!-- DOD:END -->
