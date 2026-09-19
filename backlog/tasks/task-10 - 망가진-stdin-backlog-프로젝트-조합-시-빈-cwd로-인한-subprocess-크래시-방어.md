---
id: TASK-10
title: 망가진 stdin + backlog 프로젝트 조합 시 빈 cwd로 인한 subprocess 크래시 방어
status: To Do
assignee: []
created_date: '2026-09-19 01:25'
updated_date: '2026-09-19 01:26'
labels: []
dependencies: []
documentation:
  - hooks/block_stop_if_dirty.py
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
block_stop_if_dirty.py/session_start.py/require_active_task.py는 stdin이 JSON이 아니면 cwd를 빈 문자열로 폴백한다. is_backlog_project("")가 os.path.join("", ...)을 pytest/Claude Code 프로세스의 실제 OS cwd 기준 상대경로로 평가하는데, 이 레포처럼 실제 cwd 자체가 backlog 프로젝트면 우연히 True가 되어 has_active_task("")/is_dirty("") 안의 subprocess.run(cwd="")이 FileNotFoundError로 죽는다(빈 문자열은 유효한 cwd가 아님). pre_commit_check.py/pre_push_check.py는 커맨드가 git commit인지부터 먼저 확인하는 게이트 순서 덕에 우연히 안 죽었을 뿐 — 이번 세션에 backlog init을 하면서 처음 드러난 실제 버그이지 기존부터 있던 무관한 실패가 아니다. cwd가 falsy면 is_backlog_project가 항상 False를 반환하도록 방어하고, pre_merge_check.py/pre_push_coverage_check.py/dedup_drift_guard.py도 같은 패턴이 있는지 점검해 필요하면 같이 고친다.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 block_stop_if_dirty.py, session_start.py, require_active_task.py의 is_backlog_project()가 cwd가 falsy(빈 문자열 등)면 즉시 False를 반환하도록 가드 추가
- [ ] #2 pre_merge_check.py, pre_push_coverage_check.py, dedup_drift_guard.py도 동일 패턴(빈 cwd + subprocess) 위험이 있는지 점검하고 필요하면 같은 가드 적용
- [ ] #3 test_main_exits_cleanly_on_malformed_stdin이 3개 파일 모두 이 레포처럼 backlog/config.yml이 실제로 존재하는 상태에서도(즉 cwd='' 트릭 없이) 통과하는지 확인하는 회귀 테스트로 보강
<!-- AC:END -->
