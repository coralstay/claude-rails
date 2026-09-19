# claude-rails

Claude Code와 함께 작업할 때, Claude가 내가 의도한 대로 행동하도록 만들기 위해 만든 훅
모음이다.

## 왜

CLAUDE.md에 "이렇게 해줘"라고 적어두는 약속만으로는 매번 지켜지기 어렵다 — 프롬프트
인젝션이나 컨텍스트 압축처럼, 의도와 다르게 흘러갈 수 있는 지점들이 있어서다. 그래서
기계적으로 검증 가능한 규칙은 훅(코드)으로 물리적으로 강제하고, 결국 사람의 판단이
필요한 두 지점(백로그 승인, push 전 코드 리뷰)은 정직하게 사람에게 남긴다. 규칙을
벗어나는 순간 액션 자체가 실행되지 않는다는 게 핵심이다.

## 뭐가 있나

28개 훅 — backlog.md 워크플로 전용 5개 + 프로젝트 종류와 무관하게 항상 켜져 있는 범용
안전/관측 23개. 전부 개인 fork 안에서만 강하게 적용되고, 운영 레포로의 PR은 항상 사람이
직접 연다.

## 설치

```bash
cd ~/githubs/claude-rails && ./install.sh
```

## 더 알고 싶으면

- **전체 스펙**(Phase 명세, HIL 표, 훅 28개 하나하나, 설치/삭제, 파일 구성) →
  `backlog doc view doc-2`
- **세션 회고** → `backlog doc list`
- **핵심 의사결정** → `backlog decision list`
- **알려진 한계 / 다음 단계 후보** → `backlog draft list`

## 훅 목록

| 범위            | 훅                            | 하는 일                                                   |
| --------------- | ----------------------------- | --------------------------------------------------------- |
| 🔒 backlog 전용 | `session_start.py`            | 세션 시작 시 backlog 워크플로 가이드/무결성 이슈 주입     |
| 🔒 backlog 전용 | `require_active_task.py`      | In Progress 태스크 + task view 확인 없인 Edit/Write 차단  |
| 🔒 backlog 전용 | `pre_commit_check.py`         | `task/<ID>` 브랜치에서만 커밋 허용, testCommand 통과 필수 |
| 🔒 backlog 전용 | `pre_push_check.py`           | Done + final summary 있어야 push 허용                     |
| 🔒 backlog 전용 | `block_stop_if_dirty.py`      | 커밋 안 된 변경 있으면 턴 종료 차단                       |
| 범용            | `protect_secrets.py`          | 시크릿 파일 읽기/수정/유출 차단 + delegation-sink 탐지    |
| 범용            | `block_dangerous_commands.py` | `rm -rf`, fork bomb 등 위험 명령 차단                     |
| 범용            | `config_guard.py`             | 자기 자신의 훅/설정 파일 변조 차단                        |
| 범용            | `config_watch.py`             | 세션 중 설정 변경을 아웃오브밴드로 감지                   |
| 범용            | `case_insensitive_guard.py`   | 대소문자만 다른 경로 삭제 오발사 방지                     |
| 범용            | `protect_tests.py`            | 테스트 삭제/skip으로 "가짜 그린" 만드는 것 방지           |
| 범용            | `pre_git_safety_check.py`     | main 직접 push, 파괴적 `gh` 명령 차단                     |
| 범용            | `pre_merge_check.py`          | fast-forward-only 병합 강제                               |
| 범용            | `pre_push_coverage_check.py`  | push 전 커버리지 실행/확인                                |
| 범용            | `dedup_drift_guard.py`        | 복붙된 함수가 사본 간에 어긋나면 커밋 차단                |
| 범용            | `instructions_audit.py`       | CLAUDE.md 등에서 적대적 지시 탐지 시 세션 잠금            |
| 범용            | `dead_end_registry.py`        | 이전에 되돌린 접근을 다시 건드리면 경고                   |
| 범용            | `dead_rules_audit.py`         | CLAUDE.md 규칙 준수 스코어카드                            |
| 범용            | `session_logger.py`           | 세션 전체를 JSONL로 기록                                  |
| 범용            | `standup_autopilot.py`        | 전날 미해결 항목을 다음 세션에 재주입                     |
| 범용            | `bounty_board.py`             | TODO/FIXME/HACK 부채를 XP로 게임화                        |
| 범용            | `nerf_receipts.py`            | 실패율/토큰 사용량 등을 기록, 모델 교체 시 변화 표시      |
| 범용            | `auto_stage.py`               | 수정한 파일을 자동으로 `git add`                          |
| 범용            | `format_code.py`              | 편집 후 포매터/린트 실행(차단 없이 피드백만)              |
| 범용            | `context_hogs.py`             | 컨텍스트를 가장 많이 먹은 파일 리더보드                   |
| 범용            | `pre_compact_backup.py`       | 압축 직전 transcript 백업                                 |
| 범용            | `permission_auto_allow.py`    | 위험 없는 권한 요청만 자동 승인                           |
| 범용            | `pr_provenance_stamp.py`      | `gh pr create` 시 PR 본문에 provenance 정보 삽입          |
