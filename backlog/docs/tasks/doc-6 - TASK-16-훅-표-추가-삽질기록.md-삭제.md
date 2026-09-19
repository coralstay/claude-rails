---
id: doc-6
title: 'TASK-16: 훅 표 추가 + 삽질기록.md 삭제'
type: guide
created_date: '2026-09-19 05:07'
updated_date: '2026-09-19 05:08'
---
# TASK-16: 훅 표 추가 + 삽질기록.md 삭제

## 문제

두 가지 요청이 묶여 있었다: (1) README 끝에 만든 훅들을 표로 리스트업, (2) "삽질기록.md
같은건 지우고. 필요없는 내용."

## 무엇을 했나

- README.md 끝에 28개 훅(backlog 전용 5 + 범용 23)을 이름+한줄설명 표로 추가.
- `삽질기록.md`를 `git rm`으로 삭제.
- README.md와 doc-2의 삽질기록.md에 대한 **살아있는** 링크/포인터를 제거.
- `hooks/dedup_drift_guard.py`, `hooks/test_dedup_registry.py`의 주석/assert 메시지가
  "(see 삽질기록.md)"를 가리키던 걸, 파일이 사라져도 뜻이 통하도록 "decision-2를 참고"로
  바꿨다.
- `doc-1`, `decision-2`의 회고성 언급("삽질기록.md 2026-09-10 교훈이...")은 **당시 사실을
  기록한 것**이라 그대로 유지 — 역사적 기록과 살아있는 링크를 구분했다.

## 왜 이 방법을 택했나

파일을 지울 때 가장 흔한 실수는 "그 파일을 가리키던 다른 곳"을 안 고치고 dangling
reference를 남기는 것이다. 그래서 삭제 전에 `grep -rln "삽질기록"`으로 전체 참조를
먼저 찾고, **살아있는 문서(README, doc-2, 활성 코드 주석)만** 고치고 **과거 기록
(doc-1, decision-2)은 그대로 뒀다** — 회고는 "그때 있었다"는 사실을 보존해야 하는
장르이기 때문이다.

## 결과

README.md에 훅 표 추가(65줄), `삽질기록.md` 삭제, doc-2/dedup_drift_guard.py/
test_dedup_registry.py 참조 정리. 전체 테스트 438 passed. 커밋: `673822d`(수정),
`b74c820`(Done). PR #10.
