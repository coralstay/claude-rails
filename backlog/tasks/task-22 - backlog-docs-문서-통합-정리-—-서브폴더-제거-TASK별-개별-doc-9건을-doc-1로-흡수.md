---
id: TASK-22
title: 'backlog/docs 문서 통합 정리 — 서브폴더 제거, TASK별 개별 doc 9건을 doc-1로 흡수'
status: In Progress
assignee: []
created_date: '2026-09-19 13:05'
updated_date: '2026-09-19 13:05'
labels: []
dependencies: []
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 doc-3~11(TASK-13~21 개별 문서 9건)의 '왜 이 방법을 택했나' 내용을 doc-1의 해당 태스크 섹션에 흡수 통합
- [ ] #2 doc-3~11 파일 삭제(backlog doc에 delete 명령이 없어 git rm으로 제거, final_summary/doc-1에 이미 보존된 내용이라 정보 손실 없음)
- [ ] #3 backlog/docs 밑의 reference/retrospectives/tasks 서브폴더 제거하고 doc-1, doc-2를 backlog/docs/ 바로 아래로 이동
- [ ] #4 decision-8(태스크마다 개별 doc 생성)을 대체하는 decision-9 신설 — 같은 산출물(README 등)을 잇따라 손대는 태스크는 개별 doc 대신 doc-1에 통합하는 걸 기본으로 한다는 개정 원칙 기록
<!-- AC:END -->
