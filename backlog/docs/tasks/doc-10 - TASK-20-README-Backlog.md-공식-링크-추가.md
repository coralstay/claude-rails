---
id: doc-10
title: 'TASK-20: README Backlog.md 공식 링크 추가'
type: guide
created_date: '2026-09-19 12:42'
updated_date: '2026-09-19 12:42'
---
# TASK-20: README Backlog.md 공식 링크 추가

## 문제

README가 "backlog.md 워크플로 전용 5개"처럼 이름만 언급할 뿐, 그게 무엇인지(외부
오픈소스 프로젝트) 설명하거나 링크하지 않았다. 처음 이 저장소를 보는 사람은
"backlog.md"가 무엇인지 모른 채 읽게 된다.

## 무엇을 했나

"무엇을 만들었는지 말씀드립니다" 문단에서 backlog.md가 처음 등장하는 지점에
공식 저장소 링크([MrLesk/Backlog.md](https://github.com/MrLesk/Backlog.md))와
"Git 저장소 안에 마크다운 파일로 태스크·문서·의사결정을 관리하는 CLI 기반 프로젝트
관리 도구"라는 한 줄 설명을 괄호로 삽입했다.

## 왜 이 방법을 택했나

새 섹션을 만들지 않고 기존 문장 안에 설명을 끼워 넣는 방식을 택했다 — 이미 짧은
README에 섹션을 더 늘리는 것보다, 처음 등장하는 자리에서 바로 설명하는 편이 읽는
흐름을 안 끊는다고 판단했다.

## 결과

README.md 수정. 전체 테스트 438 passed(코드 변경 없음). 커밋: `1eb83fe`.
