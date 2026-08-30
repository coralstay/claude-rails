# claude-rails

Claude Code + [Backlog.md](https://github.com/MrLesk/Backlog.md)를 쓰는 개인 워크플로를
훅(hooks)으로 강제하는 전역 설정. `~/.claude/`에 설치하면 backlog.md가 초기화된 모든
프로젝트에서 매 세션 자동으로 적용된다.

## 왜

Claude에게 "이 순서로 작업해줘"라고 CLAUDE.md에 적어두는 것만으로는 지켜지지 않는 경우가
있다. 실제로 막아야 하는 지점(태스크 없이 코드 수정, 테스트 없이 커밋, 커밋 안 하고 턴
종료, 미완료 상태로 push)은 Claude Code의 [hooks](https://code.claude.com/docs/en/hooks)로
강제하고, 판단이 필요한 지점(스코프 이탈 여부, 계획의 충실도)은 CLAUDE.md 안내에 맡긴다.

## 설치

```bash
git clone <this-repo> ~/githubs/claude-rails
cd ~/githubs/claude-rails
./install.sh
```

`install.sh`가 하는 일:
- `hooks/*.sh` → `~/.claude/hooks/claude-rails/`로 복사
- `settings.hooks.json`의 `hooks` 블록을 `~/.claude/settings.json`에 병합 (병합 전 백업 생성)
- `CLAUDE.md.snippet`을 `~/.claude/CLAUDE.md`에 추가 (마커로 중복 방지, 재실행 안전)

전제조건: `backlog` CLI (`npm i -g backlog.md`), `jq`.

훅은 **backlog.md가 초기화된 프로젝트(`backlog/config.yml` 존재)에서만** 동작한다. 그 외
프로젝트에서는 모든 훅이 조용히 통과(exit 0)한다.

### 삭제

`~/.claude/settings.json`에서 병합된 `hooks` 블록을 제거하고, `~/.claude/CLAUDE.md`의
`<!-- CLAUDE-RAILS:BEGIN -->` ~ `END` 블록을 지우고, `~/.claude/hooks/claude-rails/`를
삭제하면 된다.

## 프로세스 정의

### Phase -1. 셋업 (프로젝트당 1회)
| # | 액션 | 커맨드 |
|---|---|---|
| -1.1 | 초기화 | `backlog init` |
| -1.2 | 상태/우선순위/타입/기본담당자 정의 | `backlog config set` |
| -1.3 | CLAUDE.md에 backlog 사용규칙 주입 | `backlog agents --update-instructions` |
| -1.4 | decision→`--ref`, doc→`--doc` 연결 규칙 명시 | (본 저장소의 CLAUDE.md.snippet) |
| -1.5 | 세션마다 가이드 자동 브리핑 | 훅: `session-start.sh` |
| -1.6 | 세션 시작 시 무결성 확인 | 훅: `session-start.sh` (`backlog doctor`) |

### Phase 0. 브리핑 & 현황 파악
`backlog overview` / `backlog board view` / `backlog search` / `backlog task list --status
"<active>"` / `backlog decision list`. 강제 없음 — 정보 수집 단계.

### Phase 0.5. 드래프트 (선택적)
`draft create/list/view` → 확정 시 `draft promote`, 폐기 시 `draft archive`. 강제 없음.

### Phase 1. 백로깅
`search`로 중복 확인 → `milestone add`(Epic) → `task create --ac --dod --milestone --parent
--labels` → 관련 decision은 `--ref decision-N`, 관련 문서는 `--doc <path|url>`으로 연결.

**강제**: In Progress 태스크가 하나도 없는 상태에서 Edit/Write 시도 → 훅 `require-active-task.sh`가 차단.

### Phase 2. 검토 게이트 (사람 개입, 훅 대체 불가)
`board view` / `board export` / `browser`로 제시 → 승인 / `task edit`으로 수정 / `task demote`로
반려.

### Phase 3. 실행 루프 (태스크 단위, 반복)
| 서브단계 | 액션 | 강제 |
|---|---|---|
| 3-0 컨텍스트 로딩 | `task view <ID> --plain` 먼저 읽기 | 훅 `require-active-task.sh` (transcript에 `task view` 호출 이력 없으면 차단) |
| 3-1 활성화 | `task edit -s "In Progress"` + `task/<ID>` 브랜치 | 훅 `pre-commit-check.sh` (커밋 시 브랜치명 검사) |
| 3-2 리서치 → 계획 | 코드베이스 재조사 후 `task edit --plan` | 판단 영역, 강제 없음 |
| 3-3 승인 게이트 | 중대 결정 시 구현 전 승인 대기 | Claude Code Plan Mode 재사용 |
| 3-4 구현 서브루프 | 슬라이스 구현→테스트→`--append-notes`→원자적 커밋 | 훅 `pre-commit-check.sh` (`.claude-rails.json`의 `testCommand` 설정 시 테스트 실패면 차단) |
| 3-4b 미커밋 종료 방지 | — | 훅 `block-stop-if-dirty.sh` (dirty tree + In Progress면 턴 종료 차단) |
| 3-5 스코프 이탈 감지 | 발견 시 멈추고 질문 | 판단 영역, 강제 없음 (아래 "다음 단계" 참고) |
| 3-6 서브태스크 처리 | 1개만 할당 시 자동 진행 금지 | 판단 영역, 강제 없음 |
| 3-7 완료 전환 | 증거 확보 후 AC 체크 | 판단 영역, 강제 없음 (아래 "다음 단계" 참고) |

### Phase 4. 완료 & 종결
`--check-ac`/`--check-dod`/`--final-summary` → `-s Done` → push → `task complete`.

**강제**: `task/<ID>` 브랜치에서 push 시 훅 `pre-push-check.sh`가 해당 태스크의 상태가
`Done`이고 `finalSummary`가 비어있지 않은지 확인, 아니면 차단.

### Phase 5. 주기적 유지보수
`doctor --fix --yes` / `cleanup` / `overview`. 훅은 세션 이벤트 기반이라 "며칠마다" 같은
진짜 주기 실행은 대상이 아님 — Claude Code `/loop` 스킬이나 시스템 cron으로 별도 구성.

## 프로젝트별 설정: `.claude-rails.json`

프로젝트 루트에 두면 `pre-commit-check.sh`가 커밋 전 테스트를 강제한다. 예시는
`.claude-rails.json.example` 참고:

```json
{ "testCommand": "npm test" }
```

없으면 테스트 검사는 건너뛰고 브랜치명 검사만 수행한다.

## 알려진 한계 / 다음 단계

- **상태 이름 고정**: 훅이 `"In Progress"`라는 상태 이름을 하드코딩하고 있다. 프로젝트가
  `backlog config`로 상태명을 바꾸면 훅이 오작동한다.
- **3-5 스코프 이탈 감지**: Claude Code의 `prompt`/`agent` 타입 훅으로 LLM 판단을 걸 수 있지만
  아직 구현하지 않았다 — 결정적이지 않아 오탐/누락 가능성을 검증한 뒤 추가할 예정.
- **3-7 AC 체크 전 증거 확인**: `PostToolUse`로 테스트 실행 결과를 상태 파일에 남기고
  `--check-ac` 직전 `PreToolUse`가 그 상태 파일을 확인하는 2단 구조가 필요한데, 아직
  구현하지 않았다.
- **`task view` 호출 확인이 휴리스틱**: transcript를 `grep "task view"`로만 확인한다. 오탐
  가능성은 낮지만 완벽하지 않다.

## 파일 구성

```
claude-rails/
├── install.sh              # ~/.claude/에 설치하는 스크립트
├── settings.hooks.json     # ~/.claude/settings.json에 병합되는 hooks 블록
├── CLAUDE.md.snippet       # ~/.claude/CLAUDE.md에 추가되는 워크플로 안내
├── .claude-rails.json.example
└── hooks/
    ├── _lib.sh
    ├── session-start.sh
    ├── require-active-task.sh
    ├── pre-commit-check.sh
    ├── block-stop-if-dirty.sh
    └── pre-push-check.sh
```
