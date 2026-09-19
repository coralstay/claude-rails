---
id: decision-5
title: GitHub PR은 항상 rebase merge로 병합 (PR #5는 merge commit 예외)
date: '2026-09-19 01:59'
status: accepted
---
## Context

PR #5(TASK-1~12, 훅 안전장치 12건 수정)를 사용자가 GitHub에서 직접 "Create a merge
commit" 방식으로 병합했다. 병합 후 로컬 `main`을 `origin/main`에 맞추려 하니 히스토리가
갈라져 있었다 — GitHub가 PR을 병합하면서 커밋 메시지는 동일하지만 committer 정보가
바뀐 새 커밋 객체를 만들었기 때문(author는 `cpu-once` 유지, committer는 `coralstay`로
재작성됨). 이 시점에 사용자가 "리베이스 머지는 늘 지켜야 한다"고 명시적으로 정책을
세웠다.

## Decision

이후 이 저장소의 모든 PR은 rebase merge로 병합한다(`gh pr merge --rebase` 또는 GitHub
UI의 "Rebase and merge"). PR #5는 이 정책이 세워지기 전에 merge commit으로 병합된
1회성 예외로 기록만 해둔다.

## Consequences

- 앞으로 로컬에서 `gh pr merge`를 실행할 일이 있으면 반드시 `--rebase` 플래그를 붙여야
  한다.
- GitHub이 병합 시 커밋을 재작성(새 해시)한다는 걸 알게 됐으므로, 원격 병합 직후에는
  `git fetch` + (내용이 동일함을 확인한 뒤) `git reset --hard origin/<branch>`로 로컬을
  동기화해야 한다 — 단순 `git merge --ff-only`가 실패할 수 있다(실제로 PR #5 이후
  발생).
- 이 정책은 세션 메모리(`feedback_always_rebase_merge.md`)에도 저장해 다음 세션에서도
  자동으로 지켜지게 했다.
