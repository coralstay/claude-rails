---
id: TASK-8
title: 'block_dangerous_commands.py: rm -rf 플래그 변형 우회 수정'
status: To Do
assignee: []
created_date: '2026-09-19 01:25'
updated_date: '2026-09-19 01:26'
labels: []
dependencies: []
documentation:
  - hooks/block_dangerous_commands.py
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CRITICAL_PATTERNS/RM_RF_FLAGS 정규식이 결합된 소문자 -rf 토큰 하나만 본다. rm -Rf(macOS 표준 대문자), rm -r -f(분리 플래그), rm --recursive --force(GNU 롱플래그)가 critical/high/strict 전 레벨에서 미탐지 — 직접 재현 완료. 지난 작업에서 확장한 상위탈출/절대경로 패턴도 같은 RM_RF_FLAGS를 재사용해서 동일하게 뚫린다.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 RM_RF_FLAGS 정규식(또는 대체 로직)이 -Rf, -r -f(분리), --recursive --force(롱플래그) 조합을 전부 잡도록 수정 — critical/high 레벨의 루트/홈 규칙과 이번 확장된 상위탈출/절대경로 규칙 양쪽 다 적용
- [ ] #2 test_block_dangerous_commands.py에 -Rf/-r -f/--recursive --force 각각에 대한 positive 케이스 추가, 기존 정상 케이스(rm -rf ./dist 등) 회귀 테스트 유지
<!-- AC:END -->
