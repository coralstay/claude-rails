---
id: DRAFT-3
title: dedup_drift_guard.py REGISTRY 확장
status: Draft
assignee: []
created_date: '2026-09-19 01:25'
updated_date: '2026-09-19 01:26'
labels: []
dependencies: []
documentation:
  - hooks/dedup_drift_guard.py
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
grep으로 전수조사한 결과 REGISTRY에 is_backlog_project만 등록돼 있고, 실제로는 command_invokes_git_subcommand(5개 파일), has_command(5개 파일), has_active_task(3개 파일), run_shell(2개 파일)도 동일해야 하는 복붙 함수다. TASK-7에서 verb 정규화 로직이 command_invokes_git_subcommand 등에 새로 들어가면 그 변경도 5곳에 동시에 반영해야 하므로, 이 태스크는 TASK-7 이후에 진행해서 새 상태 기준으로 REGISTRY를 넓힌다. current_branch는 파일마다 반환값 계약이 달라(빈 문자열 vs None) 의도적으로 다른 구현으로 보이므로 REGISTRY 대상에서 제외한다.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 REGISTRY에 command_invokes_git_subcommand(5개 파일), has_command(5개 파일), has_active_task(3개 파일), run_shell(2개 파일) 추가
- [ ] #2 TASK-7에서 basename 정규화가 반영된 이후의 최신 command_invokes_git_subcommand 기준으로 5개 파일이 실제로 AST 동일한지 확인 후 등록
- [ ] #3 test_dedup_drift_guard.py에 새로 등록된 함수들에 대한 drift 탐지 케이스 추가(최소 1개 함수는 일부러 다르게 만들어서 차단되는지 확인)
<!-- AC:END -->
