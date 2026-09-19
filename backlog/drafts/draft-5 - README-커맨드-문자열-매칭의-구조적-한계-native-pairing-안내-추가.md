---
id: DRAFT-5
title: 'README: 커맨드 문자열 매칭의 구조적 한계 + native pairing 안내 추가'
status: Draft
assignee: []
created_date: '2026-09-19 01:26'
updated_date: '2026-09-19 01:26'
labels: []
dependencies: []
documentation:
  - README.md
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
리서치 결과, 정규식/토큰 기반 커맨드 매칭은 절대경로·래퍼·인코딩·간접실행으로 우회 가능하다는 게 보안 커뮤니티의 일반적 결론이다(One Goal Many Commands: Denylist Fragility in AI Agents 등). TASK-7로 지금 발견된 절대경로 우회는 막지만, "정규식으로 완벽히 막을 수 있다"는 인상을 주면 안 된다. 업스트림 protect-secrets.js README의 "Native pairing" 섹션(permissions.deny + sandbox.network.allowedDomains를 같이 쓰라는 안내)을 참고해 README 10장에 이 구조적 한계와 권장 조합을 명시한다. 8장 dedup_drift_guard.py 설명의 "is_backlog_project() 등" 표현도 TASK-9 완료 후 실제 REGISTRY 내용(4~5개 함수)에 맞게 고친다. TASK-9까지 끝난 뒤 마지막에 진행한다.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 README 10장에 커맨드 문자열 정규식/토큰 매칭의 구조적 한계(절대경로·래퍼·인코딩·간접실행 우회 가능성)와 Claude Code 자체 permissions.deny/sandbox와 병행 사용을 권장하는 내용 추가 — 업스트림 protect-secrets.js Native pairing 섹션 인용
- [ ] #2 README 8장 dedup_drift_guard.py 설명 문구를 TASK-9 완료 후 실제 REGISTRY 함수 목록에 맞게 수정
<!-- AC:END -->
