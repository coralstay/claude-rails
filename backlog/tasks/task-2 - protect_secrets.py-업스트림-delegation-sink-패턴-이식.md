---
id: TASK-2
title: 'protect_secrets.py: 업스트림 delegation-sink 패턴 이식'
status: To Do
assignee: []
created_date: '2026-09-18 16:12'
updated_date: '2026-09-18 16:12'
labels: []
dependencies: []
documentation:
  - hooks/protect_secrets.py
  - ../claude-code-hooks/plugins/protect-secrets/protect-secrets.js
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
karanb192/claude-code-hooks 업스트림(main)이 이 저장소가 포팅한 시점보다 훨씬 앞서 있다 — delegation-sink 탐지(시크릿 파일/변수가 gemini/codex/llm 등 외부 모델 CLI나 알려진 모델 API 호스트로 흘러가는 패턴)가 추가됐는데 claude-rails의 protect_secrets.py에는 없다. 단, 인터프리터로 파일을 읽어 Claude 자신의 컨텍스트로만 흘려보내는 패턴(외부 유출 아님, 예: python3 -c "print(open('.env').read())")은 업스트림 최신판도 문자열 매칭 구조상 못 막는 구조적 한계로 확인됨 — 이건 고칠 버그가 아니라 문서화 대상.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 karanb192 업스트림 protect-secrets.js(main)의 delegation-sink 정규식 로직을 Python으로 이식
- [ ] #2 test_protect_secrets.py에 이식된 패턴에 대한 회귀 테스트 추가
- [ ] #3 README 8장 훅 스펙 테이블에 업스트림 포팅 시점과 이번에 반영한 버전 명시
- [ ] #4 인터프리터로 파일을 읽어 Claude 자신의 컨텍스트로만 흘려보내는 패턴은 구조적 한계로 README 10장에 명시
<!-- AC:END -->
