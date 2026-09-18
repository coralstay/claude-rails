---
id: DRAFT-1
title: is_backlog_project() 중복 버그 수정 + drift 방지 테스트
status: Draft
assignee: []
created_date: '2026-09-18 16:12'
updated_date: '2026-09-18 16:12'
labels: []
dependencies: []
documentation:
  - 삽질기록.md
  - hooks/require_active_task.py
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
삽질기록.md(2026-09-10)에 기록된 "서브폴더 존재만으로 backlog 프로젝트라고 오판하면 안 된다" 교훈이 require_active_task.py 1곳에만 반영되고, 동일 is_backlog_project() 로직이 복붙된 나머지 4개 훅(pre_commit_check.py, pre_push_check.py, block_stop_if_dirty.py, session_start.py)에는 .git 체크가 빠져 있다. 훅이 완전 독립형(공용 import 없음)으로 설계된 데서 오는 부작용 — 한 곳에서 고친 버그가 복붙된 다른 곳에 전파 안 됨.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pre_commit_check.py, pre_push_check.py, block_stop_if_dirty.py, session_start.py의 is_backlog_project()에 require_active_task.py와 동일한 .git 존재 체크 추가
- [ ] #2 5개 훅의 is_backlog_project() 구현이 전부 동일한지 비교하는 테스트 추가 (drift 재발 방지)
- [ ] #3 각 훅의 기존 test_*.py에 backlog/config.yml만 있고 .git 없는 폴더에서는 검사가 스킵되는 케이스 추가
<!-- AC:END -->
