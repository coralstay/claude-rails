# claude-rails

Claude Code로 프로젝트를 진행할 때 [Backlog.md](https://github.com/MrLesk/Backlog.md)를
함께 쓰면서 지키고 싶은 개인 작업 흐름을, "매번 까먹지 않고" 적용되도록 만든 전역 설정
저장소. 이 문서 하나만 읽으면 이게 뭔지, 왜 있는지, 지금 뭐가 어떻게 동작하는지, 실제로
어떻게 쓰는지 전부 알 수 있게 쓴다.

---

## 1. 왜 이게 있는가

Claude에게 "이 순서로 작업해줘"라고 CLAUDE.md에 적어두는 것만으로는 매번 지켜지지
않는다. 그래서 두 가지로 나눴다:

- **실제로 반드시 막아야 하는 지점** (태스크 없이 코드부터 수정, 테스트 없이 커밋, 커밋
  안 하고 턴 종료, 미완료 상태로 push) → Claude Code의 [hooks](https://code.claude.com/docs/en/hooks)로
  **물리적으로 차단**한다. Claude가 어겨도 액션 자체가 실행되지 않는다.
- **판단이 필요한 지점** (계획이 충분히 조사됐는지, 지금 하는 일이 스코프를 벗어났는지) →
  훅으로 강제할 수 없으므로 CLAUDE.md 안내에 맡기고, 대신 **사람에게 반드시 물어보게**
  설계했다 (HIL, 7장 "HIL 지점 총정리" 참고).

이 둘을 구분하지 않으면 "강제한다고 해놓고 사실은 안 지켜지는" 문서만 늘어난다. 이
저장소는 그 구분을 실제 코드(훅 스크립트)로 못박아 둔 것이다.

---

## 2. 지금 이 컴퓨터에 뭐가 설치돼 있는가

전역 설치되어 있어 **backlog.md가 초기화된 모든 프로젝트에서, 매 세션 자동으로 적용**된다.
설치 안 된 프로젝트(backlog.md 안 쓰는 프로젝트)는 전혀 영향받지 않는다.

| 항목 | 경로 |
|---|---|
| 훅 스크립트 | `~/.claude/hooks/claude-rails/*.sh` (6개, 실행권한 있음) |
| 전역 설정 | `~/.claude/settings.json` (`hooks` 키만 병합됨, 기존 설정 보존) |
| 전역 지침 | `~/.claude/CLAUDE.md` (`<!-- CLAUDE-RAILS:BEGIN -->` 블록) |
| 설치 전 백업 | `~/.claude/settings.json.bak.<timestamp>` |
| 원본 소스 | `~/githubs/usage` ([github.com/amosQP/claude-rails](https://github.com/amosQP/claude-rails), private) |

재설치/업데이트하려면: 저장소에서 `git pull` 후 `./install.sh` 다시 실행 (재실행 안전,
CLAUDE.md는 마커로 중복 방지).

---

## 3. 어떻게 동작하는가 — 메커니즘 한눈에

1. Claude Code가 세션마다 `~/.claude/settings.json`의 `hooks` 설정을 읽는다.
2. 특정 이벤트(파일 편집 전, 커밋 전, 턴 종료 시, push 전, 세션 시작 시)마다 등록된
   스크립트가 자동 실행된다.
3. 각 스크립트는 **가장 먼저 "지금 이 디렉토리가 backlog.md 프로젝트인가
   (`backlog/config.yml` 존재 여부)"부터 확인**하고, 아니면 즉시 통과(`exit 0`)한다 —
   그래서 이 설정이 전역이어도 관계없는 프로젝트를 방해하지 않는다.
4. backlog 프로젝트라면 조건을 검사해서, 어기면 **exit code 2**로 그 액션 자체를 막는다
   (편집 불가, 커밋 불가, 턴 종료 불가, push 불가). exit 2는 Claude Code 훅 사양상
   모든 차단 가능 이벤트에서 공통으로 통하는 유일한 방식이라 이 하나로 통일했다.
5. 막히면 Claude는 그 이유(스크립트가 stderr로 낸 한국어 메시지)를 그대로 보고, 조건을
   충족시킨 뒤 다시 시도한다.

즉 이 저장소가 하는 일은 **"Claude Code 세션 중간중간에 끼어들어서, backlog 프로젝트일
때만, 정해진 조건이 아니면 액션을 거부하는 차단 스크립트 4개 + 세션 시작 시 브리핑만
하는 스크립트 1개(+ 둘 다 쓰는 공용 함수 파일 1개)"**다.

---

## 4. 표기 범례

이 문서 전체(아래 사용 흐름, Phase 표, HIL 표)에서 공통으로 쓰는 기호. 여기서 한 번만
정의하고 이후로는 재정의하지 않는다.

| 기호 | 의미 |
|---|---|
| 🧑 | 필수 HIL — 사람이 반드시 개입해야 진행됨 |
| 🧑? | 조건부 HIL — 특정 상황에서만 Claude가 사람에게 멈춰서 물어봄 |
| 🤖 | 훅으로 강제됨 — 어기면 그 액션 자체가 차단됨 |
| ⚙️ | 자동(강제 없음) — Claude가 스스로 판단/수행, 강제는 없음 |

---

## 5. 사용 흐름 — 태스크 하나 따라가기

까먹고 다시 왔을 때 이 섹션만 봐도 바로 쓸 수 있게, 실제로 손으로 치는 순서를 그대로
적는다.

```
🧑  "이 프로젝트에 로그인 기능 추가해줘" 라고 프롬프트

⚙️  Claude가 backlog overview / board view / search 로 현황 파악

⚙️  Claude가 backlog task create "로그인 기능" --ac "..." --ref decision-3 --doc docs/auth.md
    (관련 결정/문서가 있으면 --ref/--doc으로 반드시 연결)

🧑  ★ Claude가 board를 보여주면, 사람이 실제로 보고 승인/수정 지시
    (여기서 멈추지 않으면 Claude가 다음으로 못 넘어감 — 유일한 필수 HIL)

⚙️  Claude가 backlog task view TASK-12 --plain 으로 태스크 정독
🤖  이걸 안 하면 다음 Edit/Write가 훅에 막힘

⚙️  Claude가 backlog task edit TASK-12 -s "In Progress" -a @me
⚙️  Claude가 git checkout -b task/TASK-12

🤖  이제부터 Edit/Write 가능 (In Progress 태스크 있음 + task view 읽음)

⚙️  Claude가 작은 단위로 구현 → 테스트 → git commit
🤖  커밋 시점에 브랜치명(task/TASK-12)과 (설정했다면) 테스트 통과 여부를 훅이 확인
🤖  커밋 안 하고 턴을 끝내려 하면 훅이 막아서 계속 진행됨

    (위 사이클을 AC 단위로 반복)

🧑? 작업 중 AC 밖의 일을 발견하면 Claude가 반드시 먼저 물어봄
    (스코프를 넓힐지, 별도 태스크로 뺄지 — 조용히 확장 안 함)

⚙️  Claude가 backlog task edit --check-ac 1 --final-summary "..." -s Done
⚙️  Claude가 git push
🤖  push 시점에 태스크가 Done 상태이고 final summary가 있는지 훅이 확인
```

이 흐름에서 **사람이 반드시 해야 하는 일은 딱 하나**다 — 백로그를 만들었을 때 보고
승인하는 것. 나머지는 Claude가 알아서 하거나, 어기면 훅이 막는다.

---

## 6. 전체 프로세스 명세 (Phase -1 ~ 5)

기호는 4장 표기 범례와 동일.

### Phase -1. 셋업 🧑 (프로젝트당 최초 1회)

| # | 액션 | 커맨드 |
|---|---|---|
| -1.1 | 초기화 | `backlog init` |
| -1.2 | 상태/우선순위/타입/기본담당자 정의 | `backlog config set` |
| -1.3 | CLAUDE.md에 backlog 사용규칙 주입 | `backlog agents --update-instructions` |
| -1.4 | decision→`--ref`, doc→`--doc` 연결 규칙 명시 | (이 저장소의 CLAUDE.md 스니펫) |

### Phase 0. 브리핑 & 현황 파악 🧑 트리거 → ⚙️ 자동

| # | 액션 | 커맨드 |
|---|---|---|
| 0.1 | 프로젝트 통계 | `backlog overview` |
| 0.2 | 칸반 스캔 | `backlog board view` |
| 0.3 | 통합 검색(중복 방지) | `backlog search "<키워드>" --plain` |
| 0.4 | 진행중 작업 확인 | `backlog task list --status "<active>" --plain` |
| 0.5 | 기존 결정 확인 | `backlog decision list` |

### Phase 0.5. 드래프트 ⚙️ (선택적)

| # | 액션 | 커맨드 |
|---|---|---|
| 0.5.1 | 초안 생성/조회 | `draft create/list/view` |
| 0.5.2 | 확정 → 승격 | `draft promote <id>` |
| 0.5.3 | 폐기 | `draft archive <id>` |

### Phase 1. 백로깅 (Epic/Story/Task 생성) ⚙️ + 🤖

이 Phase를 지나는 순간부터 🤖 `require-active-task.sh` 훅이 걸리기 시작한다 — In
Progress 태스크 없이는 이후 어떤 Edit/Write도 불가.

| # | 액션 | 커맨드 |
|---|---|---|
| 1.1 | 중복 확인 | `search`, `task list --search` |
| 1.2 | Epic 생성 | `milestone add <name>` |
| 1.3 | 구조 결정 (단일/부모-자식/독립+의존성) | — |
| 1.4 | 태스크 생성 | `task create --ac --dod --priority --type --milestone --parent --labels` |
| 1.5 | 관련 decision 연결 | `--ref decision-N` → frontmatter `references:` |
| 1.6 | 관련 doc/외부링크 연결 | `--doc <path\|url>` → frontmatter `documentation:` |
| 1.7 | 결과 보고 | 태스크 ID/제목/AC 리스트업 |

### Phase 2. 검토 게이트 🧑 ★★★ — 유일한 필수 HIL

전체 프로세스에서 **훅으로 대체 불가능한 유일한 지점**. 사람이 실제로 백로그를 보고
승인해야만 Phase 3가 시작된다.

| # | 액션 | 커맨드 |
|---|---|---|
| 2.1 | 전체 조망 제시 | `board view` / `board export` / `browser` |
| 2.2 | 승인 | → Phase 3 진행 |
| 2.3 | 수정 요청 | `task edit` |
| 2.4 | 반려 | `task demote <id>` (Draft로 되돌림) |

### Phase 3. 실행 루프 (태스크 단위, 반복)

| 서브단계 | 액션 | HIL/강제 |
|---|---|---|
| 3-0 컨텍스트 로딩 | `task view <ID> --plain` 먼저 읽기 (미승격 draft는 `draft list`로 수동 확인) | 🤖 안 읽으면 Edit/Write 차단 |
| 3-1 활성화 | `task edit -s "In Progress"` + `task/<ID>` 브랜치 전환 | 🤖 커밋 시 브랜치명 검사 |
| 3-2 리서치 → 계획 | 코드베이스 재조사 후 `task edit --plan` (생성 시점 접근법을 그대로 믿지 않음) | ⚙️ 판단 영역, 강제 없음 |
| 3-3 승인 게이트 | 중대한 설계/아키텍처 결정 포함 시 구현 전 승인 대기 | 🧑? Claude Code Plan Mode 재사용 |
| 3-4 구현 서브루프 | 슬라이스 구현→테스트→`--append-notes`→원자적 커밋→반복 | 🤖 `.claude-rails.json`에 testCommand 설정 시 테스트 실패면 커밋 차단 |
| 3-4b 미커밋 종료 방지 | — | 🤖 dirty tree + In Progress면 턴 종료 차단 |
| 3-5 스코프 이탈 감지 | AC 밖 발견 시 조용히 확장 않고 질문 | 🧑? 발견 시에만, 자동 검증은 미구현 |
| 3-6 서브태스크 처리 | 서브태스크 1개만 할당 시 다음으로 자동 진행 금지 | 🧑? 1개만 할당된 경우에만 |
| 3-7 완료 전환 | 증거(테스트 통과 로그 등) 확보 후에만 AC 체크 | ⚙️ 판단 영역, 자동 검증 미구현 |

### Phase 4. 완료 & 종결 🤖

| # | 액션 | 커맨드/강제 |
|---|---|---|
| 4.1 | AC/DoD 체크, final-summary 작성 | `task edit --check-ac/--check-dod/--final-summary` |
| 4.2 | 상태 전환 | `task edit -s Done` |
| 4.3 | push 전 상태 확인 | 🤖 `task/<ID>` 브랜치 push 시 status=Done && final summary 존재 확인 |
| 4.4 | Push (기능/Story 단위) | `git push` |
| 4.5 | 태스크 아카이브 | `task complete TASK-ID` |
| 4.6 | Epic 완료 시 | `milestone archive` |
| 4.7 | (대안) 취소 경로 | `task archive` / `milestone remove/rename` |

### Phase 5. 주기적 유지보수 ⚙️

훅은 세션 이벤트 기반이라 "며칠마다" 같은 진짜 주기 실행은 대상이 아니다 — `/loop`나
시스템 cron으로 별도 구성해야 한다.

| # | 액션 | 커맨드 |
|---|---|---|
| 5.1 | 무결성 점검 | `doctor --fix --yes` |
| 5.2 | 완료 태스크 정리 | `cleanup` |
| 5.3 | 정기 리포팅 | `overview` |

---

## 7. HIL 지점 총정리

| 위치 | 필수/조건부 | 트리거 조건 | 훅으로 대체 가능? |
|---|---|---|---|
| Phase -1 셋업 | 필수 | 항상 (최초 1회) | 대체 불가 — 사람의 결정 |
| Phase 0 브리핑 | 필수 | 항상 (요청 자체가 사람에게서 시작) | 대체 불가 |
| **Phase 2 검토 게이트** | **필수** | **항상, 예외 없음** | **대체 불가 — 프로세스의 핵심 HIL** |
| 3-3 승인 게이트 | 조건부 | 중대 설계/아키텍처 결정 포함 시 | Plan Mode로 흡수(이미 존재) |
| 3-5 스코프 이탈 | 조건부 | AC 밖 작업 발견 시 | 부분 대체 가능(LLM 판단형 훅, 미구현) |
| 3-6 서브태스크 | 조건부 | 서브태스크 1개만 할당 시 | 대체 어려움(판단 영역) |

---

## 8. 훅 상세 스펙 (스크립트별 정확한 로직)

### 공통 — `_lib.sh`

```
deny(reason):  stderr에 reason 출력 후 exit 2
is_backlog_project(dir):  dir/backlog/config.yml 존재 여부
no_active_task(dir):  `backlog task list --status "In Progress" --plain` 결과에
                       "No tasks found." 포함 여부
```

### `session-start.sh` — 이벤트 `SessionStart`
```
1. backlog CLI 없음 또는 backlog 프로젝트 아님 → exit 0
2. `backlog instructions overview` → additionalContext로 주입
3. `backlog doctor` → systemMessage로 주입
```
차단 불가 이벤트(SessionStart는 차단 미지원) — 정보 브리핑 전용.

### `require-active-task.sh` — `PreToolUse`, matcher `Edit|Write`
```
1. backlog 프로젝트 아님 → exit 0
2. In Progress 태스크 없음 → deny
3. transcript_path 안에 "task view" 문자열 없음 → deny
4. 통과 → exit 0
```
한계: 상태명 `"In Progress"` 하드코딩, 3번은 문자열 검색 기반 휴리스틱(어떤 태스크를
읽었는지까지는 검증 안 함).

### `pre-commit-check.sh` — `PreToolUse`, matcher `Bash`, `if: "Bash(git commit *)"`
```
1. backlog CLI 없음 또는 backlog 프로젝트 아님 → exit 0
2. In Progress 태스크 있음 && 브랜치명이 "task/"로 시작 안 함 → deny
3. .claude-rails.json 있고 testCommand 설정됨 && 그 커맨드 exit≠0 → deny
4. 통과 → exit 0
```
`testCommand`는 `eval`로 실행됨 — 신뢰할 수 있는 값만 넣을 것.

### `block-stop-if-dirty.sh` — `Stop`
```
1. backlog CLI 없음 또는 backlog 프로젝트 아님 또는 In Progress 태스크 없음 → exit 0
2. git status --porcelain 결과 있음(커밋 안 된 변경) → deny (턴 종료 차단)
3. 통과 → exit 0
```

### `pre-push-check.sh` — `PreToolUse`, matcher `Bash`, `if: "Bash(git push *)"`
```
1. backlog CLI 없음 또는 backlog 프로젝트 아님 → exit 0
2. 브랜치명이 "task/"로 시작 안 함 → exit 0 (이 훅은 task 브랜치만 검사)
3. task_id = 브랜치명에서 "task/" 뗀 나머지
4. `backlog task view <task_id> --json` 조회 실패 → exit 0
5. status ≠ "Done" → deny
6. finalSummary 비어있음 → deny
7. 통과 → exit 0
```
필드명(`status`, `finalSummary`)은 실제 프로젝트에서 `task view --json` 출력을 직접
확인해 검증된 값.

모든 스크립트는 **backlog 프로젝트가 아닌 곳에서는 즉시 통과**하며, 차단은 예외 없이
**exit code 2**로 통일(이벤트별로 다른 JSON 필드를 요구하지 않는 가장 견고한 방식).

---

## 9. 프로젝트별 설정 — `.claude-rails.json`

프로젝트 루트에 두면 `pre-commit-check.sh`가 커밋 전 테스트를 강제한다:

```json
{ "testCommand": "npm test" }
```

없으면 테스트 검사는 건너뛰고 브랜치명 검사만 수행한다. 예시는
`.claude-rails.json.example` 참고.

---

## 10. 알려진 한계 / 다음 단계

- **상태 이름 고정**: `"In Progress"`를 하드코딩. 프로젝트가 `backlog config`로 상태명을
  바꾸면 훅이 오작동한다.
- **`task view` 확인이 휴리스틱**: transcript를 `grep "task view"`로만 확인, 완벽하지 않음.
- **3-5 스코프 이탈 감지 미구현**: `prompt`/`agent` 타입 훅으로 LLM 판단을 걸 수 있지만
  아직 추가하지 않음 (오탐/누락 검증 필요).
- **3-7 AC 체크 전 증거 확인 미구현**: `PostToolUse`로 테스트 결과를 상태 파일에 남기고
  `--check-ac` 직전 `PreToolUse`가 그 파일을 확인하는 2단 구조 필요, 미구현.
- **Phase 5 주기 실행 없음**: 훅은 세션 이벤트 기반이라 "N일마다" 실행은 `/loop`/cron으로
  별도 구성해야 함.

---

## 11. 설치 / 재설치 / 삭제

**설치/재설치**:
```bash
cd ~/githubs/usage   # 이 저장소
./install.sh
```
전제조건: `backlog` CLI (`npm i -g backlog.md`), `jq`. 재실행 안전 (settings.json은
매번 백업 후 병합, CLAUDE.md는 마커로 중복 방지).

**삭제**:
- `~/.claude/settings.json`에서 병합된 `hooks` 블록 제거
- `~/.claude/CLAUDE.md`의 `<!-- CLAUDE-RAILS:BEGIN -->` ~ `END` 블록 제거
- `~/.claude/hooks/claude-rails/` 삭제

**검증**:
```bash
jq empty ~/.claude/settings.json && echo OK
echo '{"cwd":"<backlog 프로젝트 경로>","transcript_path":"/nonexistent"}' \
  | bash ~/.claude/hooks/claude-rails/require-active-task.sh; echo "exit: $?"
```
훅 변경 후 반영이 안 되면 `/hooks` 메뉴를 한 번 열거나 세션을 재시작.

---

## 12. 파일 구성

```
claude-rails/
├── README.md                # 이 문서 (단일 소스)
├── install.sh                # ~/.claude/에 설치하는 스크립트
├── settings.hooks.json       # ~/.claude/settings.json에 병합되는 hooks 블록
├── CLAUDE.md.snippet         # ~/.claude/CLAUDE.md에 추가되는 워크플로 안내
├── .claude-rails.json.example
└── hooks/
    ├── _lib.sh
    ├── session-start.sh
    ├── require-active-task.sh
    ├── pre-commit-check.sh
    ├── block-stop-if-dirty.sh
    └── pre-push-check.sh
```
