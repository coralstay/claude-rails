---
id: doc-11
title: 'TASK-21: README 한국어 훅 문서 링크 + 수명주기 다이어그램'
type: guide
created_date: '2026-09-19 12:50'
updated_date: '2026-09-19 12:50'
---
# TASK-21: README 한국어 훅 문서 링크 + 수명주기 다이어그램

## 문제

README가 Claude Code hooks 공식 문서를 영어판(`/docs/en/hooks`)으로 링크하고
있었다. README 본문이 한국어인데 링크는 영어판이라 일관성이 없었다. 또한 28개
훅을 나열한 표(생애주기 표)만 있고, 전체 이벤트 흐름을 한눈에 보여주는 그림이
없어서 표를 보기 전에 "이게 어떤 순서로 도는지" 감을 잡기 어려웠다.

## 무엇을 했나

- hooks 공식 문서 링크를 한국어판(`https://code.claude.com/docs/ko/hooks`)으로
  두 곳(첫 언급, 생애주기 섹션 도입부) 모두 갱신했다.
- 훅 생애주기 표 바로 앞에 Mermaid flowchart를 추가했다 — 세션 생애주기
  (SessionStart/SessionEnd), 대화 루프(UserPromptSubmit → Claude 처리 → 도구
  호출 서브그래프[PreToolUse → PermissionRequest → 도구 실행 → PostToolUse/
  PostToolUseFailure] → Stop), 그 외 이벤트(PreCompact/InstructionsLoaded/
  ConfigChange) 세 그룹으로 Claude Code의 11개 공식 이벤트 전체 흐름을 표현했다.

## 왜 이 방법을 택했나

GitHub는 마크다운 안의 ```mermaid``` 코드 블록을 별도 이미지 파일 없이 그대로
그림으로 렌더링하므로, 정적 이미지 파일을 만들어 관리하는 것보다 Mermaid를
텍스트로 유지하는 쪽이 훨씬 가볍고 diff로 추적하기도 쉽다.

다이어그램 그룹 구조(세션 생애주기 / 대화 루프+도구 호출 서브그래프 / 그 외
이벤트)는 이전 세션에서 리서치했던 disler/claude-code-hooks-mastery의 다이어그램
형태를 참고해, 이 저장소의 실제 11개 이벤트에 맞게 새로 그렸다.

작업 중 발견한 것: Mermaid의 점선 화살표 라벨 문법(`-.라벨.->`)은 라벨 안에
마침표가 있으면 닫는 구분자(`.->`)와 충돌할 수 있다. 처음에는
"CLAUDE.md 로드 시"라고 썼다가, 안전하게 "지침 파일 로드 시"로 바꿨다.

## 결과

README.md 수정(링크 2곳 + 다이어그램 추가). 전체 테스트 438 passed(코드 변경
없음). 커밋: `894e5fd`.
