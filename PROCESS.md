# claude-rails — 프로세스 명세서

Claude Code와 backlog.md가 하나의 작업을 어떻게 함께 처리하는지, 그리고 그 과정의 어느
지점에 **HIL(Human-in-the-Loop, 사람 개입)**이 들어가는지를 명세하는 단일 문서.

## 범례

| 표시 | 의미 |
|---|---|
| 🧑 HIL | 사람이 반드시 개입해야 진행됨 (Claude 혼자 못 넘어감) |
| 🧑? HIL(조건부) | 특정 조건에서만 사람에게 멈춰서 확인함 |
| 🤖 강제 | 훅으로 물리적 차단됨 — 안 지키면 Claude가 그 액션을 못 함 |
| ⚙️ 자동 | Claude가 스스로 판단/수행, 강제 없음 (CLAUDE.md 안내에만 의존) |

---

## 1. 전체 흐름도

```
Phase -1  셋업                              🧑 (최초 1회, 사람이 직접 실행)
   │
   ▼
Phase 0   브리핑 & 현황 파악                  🧑 트리거 → ⚙️ Claude 자동 조회
   │
   ▼
Phase 0.5 드래프트 (선택적)                   ⚙️
   │
   ▼
Phase 1   백로깅 (Epic/Story/Task 생성)       ⚙️ 생성 + 🤖 이후 Edit/Write 가드 시작
   │
   ▼
Phase 2   검토 게이트                         🧑 ★★★ 유일한 순수 HIL 필수 게이트
   │        (유저가 백로그를 실제로 확인하기 전엔 절대 다음으로 못 넘어감)
   ▼
Phase 3   실행 루프 (태스크 단위, 반복)
   │  3-0  컨텍스트 로딩          🤖
   │  3-1  활성화                 🤖
   │  3-2  리서치 → 계획          ⚙️
   │  3-3  승인 게이트            🧑? (중대한 설계/아키텍처 결정일 때만)
   │  3-4  구현 서브루프          🤖
   │  3-4b 미커밋 종료 방지       🤖
   │  3-5  스코프 이탈 감지       🧑? (AC 밖 작업 발견 시 반드시 질문)
   │  3-6  서브태스크 처리        🧑? (서브태스크 1개만 할당됐을 때 다음으로 넘어가기 전)
   │  3-7  완료 전환              ⚙️ (증거 확인 후 AC 체크 — 아직 훅 미구현)
   ▼
Phase 4   완료 & 종결                        🤖 (push 게이트)
   │
   ▼
Phase 5   주기적 유지보수                     ⚙️ (훅 아님, /loop·cron 별도 구성)
```

**HIL이 걸리는 지점은 정확히 5곳뿐이다**: Phase -1(셋업), Phase 0(요청 트리거), **Phase 2
(검토 게이트 — 유일하게 강제로 막혀있는 필수 HIL)**, 3-3(조건부), 3-5(조건부), 3-6(조건부).
나머지는 전부 Claude 혼자 진행하거나(⚙️) 훅이 물리적으로 대신 막는다(🤖).

---

## 2. Phase별 상세

### Phase -1. 셋업 🧑 — 최초 1회

**HIL**: 전부. Claude가 스스로 시작하지 않고 사람이 프로젝트에 이 워크플로를 적용하기로
결정하고 직접 실행한다.

| 액션 | 커맨드 |
|---|---|
| 프로젝트 초기화 | `backlog init` |
| 상태/우선순위/타입/기본담당자 정의 | `backlog config set` |
| CLAUDE.md에 backlog 사용규칙 주입 | `backlog agents --update-instructions` |
| decision→`--ref`, doc→`--doc` 연결 규칙 명시 | CLAUDE.md에 문구 추가 |
| claude-rails 훅 전역 설치 | `install.sh` (이미 완료됨, `~/.claude/`) |

---

### Phase 0. 브리핑 & 현황 파악 🧑 트리거 → ⚙️ 자동 조회

**HIL**: 요청 자체가 사람에게서 나온다 (프롬프트). 그 이후 정보 수집은 Claude가 자동으로
한다 — 강제는 없지만 CLAUDE.md 지침에 따라 관행적으로 수행.

| # | 액션 | 커맨드 |
|---|---|---|
| 0.1 | 프로젝트 통계 | `backlog overview` |
| 0.2 | 칸반 스캔 | `backlog board view` |
| 0.3 | 통합 검색(중복 방지) | `backlog search "<키워드>" --plain` |
| 0.4 | 진행중 작업 확인 | `backlog task list --status "<active>" --plain` |
| 0.5 | 기존 결정 확인 | `backlog decision list` |

---

### Phase 0.5. 드래프트 ⚙️ — 선택적

**HIL**: 없음. 요구사항이 불확실할 때만 Claude가 거치는 선택적 단계.

| # | 액션 | 커맨드 |
|---|---|---|
| 0.5.1 | 초안 생성/조회 | `draft create/list/view` |
| 0.5.2 | 확정 → 승격 | `draft promote <id>` |
| 0.5.3 | 폐기 | `draft archive <id>` |

---

### Phase 1. 백로깅 (Epic/Story/Task 생성) ⚙️ + 🤖

**HIL**: 생성 행위 자체는 없음(Claude가 자율 판단). 단, 이 Phase를 지나는 순간부터
**🤖 훅이 걸리기 시작**한다 — In Progress 태스크 없이는 이후 어떤 Edit/Write도 불가.

| # | 액션 | 커맨드 |
|---|---|---|
| 1.1 | 중복 확인 | `search`, `task list --search` |
| 1.2 | Epic 생성 | `milestone add <name>` |
| 1.3 | 구조 결정 (단일/부모-자식/독립+의존성) | — |
| 1.4 | 태스크 생성 | `task create --ac --dod --priority --type --milestone --parent --labels` |
| 1.5 | 관련 decision 연결 | `--ref decision-N` → frontmatter `references:` |
| 1.6 | 관련 doc/외부링크 연결 | `--doc <path\|url>` → frontmatter `documentation:` |
| 1.7 | 결과 보고 | (태스크 ID/제목/AC 리스트업) |

---

### Phase 2. 검토 게이트 🧑 ★★★ — 유일한 순수 필수 HIL

**HIL**: **전체 프로세스에서 훅으로 대체할 수 없는 유일한 지점.** 사람이 실제로 백로그를
보고 승인해야만 Phase 3가 시작된다. 다른 모든 HIL은 조건부(특정 상황에만 발생)이지만
여기는 **항상, 무조건** 발생한다.

| # | 액션 | 커맨드 |
|---|---|---|
| 2.1 | 전체 조망 제시 | `board view` / `board export` / `browser` |
| 2.2 | 승인 | → Phase 3 진행 |
| 2.3 | 수정 요청 | `task edit` |
| 2.4 | 반려 | `task demote <id>` (Draft로 되돌림) |

---

### Phase 3. 실행 루프 (태스크 단위, 반복)

#### 3-0. 컨텍스트 로딩 🤖
- 액션: `backlog task view TASK-ID --plain` 로 태스크 전체(설명/AC/DoD/plan/notes/
  `references:`/`documentation:`)를 읽음. 미승격 draft는 `draft list`로 별도 확인
  (검색 색인에 안 잡히므로 수동 필요).
- **강제**: 이걸 하기 전에는 Edit/Write 자체가 불가능 (훅이 세션 transcript에서 `task view`
  호출 이력을 확인).

#### 3-1. 활성화 🤖
- 액션: `task edit -s "In Progress" -a @이름` + `git checkout -b task/TASK-ID`
- **강제**: 커밋 시점에 브랜치명이 `task/TASK-ID` 패턴인지 검사.

#### 3-2. 리서치 → 계획 ⚙️
- 액션: 태스크 생성 시점 접근법을 그대로 믿지 않고 코드베이스를 재조사 → `task edit
  --plan "..."`
- **HIL 없음**: 조사가 충분한지는 강제로 검증할 수 없는 판단 영역.

#### 3-3. 승인 게이트 🧑? (조건부)
- **HIL 조건**: 계획에 중대한 설계/아키텍처/제품 결정이 포함되어 있거나, 프로젝트/유저가
  리뷰를 요구할 때만 발생. 일상적인 스코프 내 작업이면 승인 없이 바로 진행.
- 메커니즘: 별도 훅이 아니라 **Claude Code의 Plan Mode를 그대로 재사용**.

#### 3-4. 구현 서브루프 🤖
- 액션: 슬라이스 구현 → 테스트 실행 → `task edit --append-notes` → 원자적 커밋 → 반복.
- **강제**: 커밋 전 브랜치명 검사(항상) + `.claude-rails.json`에 `testCommand`가
  설정된 프로젝트라면 테스트 실패 시 커밋 자체가 막힘(옵트인).

#### 3-4b. 미커밋 종료 방지 🤖
- **강제**: 커밋 안 된 변경사항(`git status --porcelain` 결과 있음)이 있고 In Progress
  태스크가 있는 상태로 턴을 끝내려 하면 차단 — 커밋을 마무리하거나 사람에게 설명할
  때까지 턴이 안 끝남.

#### 3-5. 스코프 이탈 감지 🧑? (조건부)
- **HIL 조건**: 작업 중 AC 범위 밖의 일을 발견했을 때만 발생. 발견되면 **조용히 확장하지
  않고 반드시 사람에게 물어봄** ("이 태스크 범위를 넓힐지, 별도 태스크로 뺄지").
- **HIL 없음(현재)**: 이 판단 자체를 훅이 자동으로 검증해주진 않는다 (Claude의 자체
  판단 + CLAUDE.md 지침에 의존). LLM 판단형 훅(`prompt`/`agent` 타입)으로 자동화하는
  안은 있으나 아직 미구현.

#### 3-6. 서브태스크 처리 🧑? (조건부)
- **HIL 조건**: 서브태스크 1개만 할당된 경우, 그것을 끝낸 뒤 **다음 서브태스크로 넘어가기
  전에 반드시 사람에게 확인**. (부모+전체 서브태스크가 한 번에 할당된 경우는 순서대로
  자동 진행, 이 경우엔 HIL 없음.)

#### 3-7. 완료 전환 ⚙️
- 액션: finalization 가이드로 전환 → 테스트 통과 로그 등 객관적 증거 확보 후에만 AC 체크
  (코드가 있어 보인다고, grep 결과만 보고 체크 금지).
- **HIL 없음(현재)**: 증거 확인 자체를 자동 검증하는 훅은 미구현 (설계는 있음: PostToolUse가
  테스트 결과를 상태 파일에 남기고 `--check-ac` 직전 PreToolUse가 그 파일을 확인하는
  2단 구조).

---

### Phase 4. 완료 & 종결 🤖

**HIL**: 없음(단, 결과가 Phase 2에서 승인받은 범위인지에 대한 최종 확인은 암묵적으로
사람 몫).

| # | 액션 | 커맨드/강제 |
|---|---|---|
| 4.1 | AC/DoD 체크, final-summary 작성 | `task edit --check-ac/--check-dod/--final-summary` |
| 4.2 | 상태 전환 | `task edit -s Done` |
| 4.3 | push 전 상태 확인 | 🤖 강제 — `task/<ID>` 브랜치에서 push 시 status=Done && final summary 존재 확인 |
| 4.4 | Push (기능/Story 단위) | `git push` |
| 4.5 | 태스크 아카이브 | `task complete TASK-ID` |
| 4.6 | Epic 완료 시 | `milestone archive` |
| 4.7 | (대안) 취소 경로 | `task archive` / `milestone remove/rename` |

---

### Phase 5. 주기적 유지보수 ⚙️

**HIL**: 없음. 단, 훅 대상이 아니므로(세션 이벤트 기반, 시계 기반 아님) `/loop`나
시스템 cron으로 별도 트리거를 구성해야 실제로 "주기적"이게 된다.

| # | 액션 | 방식 |
|---|---|---|
| 5.1 | 무결성 점검 | `doctor --fix --yes` |
| 5.2 | 완료 태스크 정리 | `cleanup` |
| 5.3 | 정기 리포팅 | `overview` |

---

## 3. HIL 지점 총정리

| 위치 | 필수/조건부 | 트리거 조건 | 훅으로 대체 가능? |
|---|---|---|---|
| Phase -1 셋업 | 필수 | 항상 (최초 1회) | 대체 불가 — 사람의 결정 |
| Phase 0 브리핑 | 필수 | 항상 (요청 자체가 사람에게서 시작) | 대체 불가 |
| **Phase 2 검토 게이트** | **필수** | **항상, 예외 없음** | **대체 불가 — 프로세스의 핵심 HIL** |
| 3-3 승인 게이트 | 조건부 | 중대 설계/아키텍처 결정 포함 시 | Plan Mode로 흡수(이미 존재하는 메커니즘) |
| 3-5 스코프 이탈 | 조건부 | AC 밖 작업 발견 시 | 부분 대체 가능(LLM 판단형 훅, 미구현) |
| 3-6 서브태스크 | 조건부 | 서브태스크 1개만 할당 시 | 대체 어려움(판단 영역) |

---

## 4. 훅 동작 명세 (부록 — 스크립트 레벨 상세)

이 섹션은 위 Phase 흐름 중 🤖로 표시된 지점을 실제로 어떤 스크립트가, 어떤 조건으로
차단하는지에 대한 구현 레벨 참고 자료다. 설치 위치와 전체 코드는 저장소의
`hooks/*.sh`, 병합 대상은 `~/.claude/settings.json` 참고.

| 🤖 지점 | 이벤트 | 스크립트 | 핵심 조건 |
|---|---|---|---|
| Phase 1 / 3-0 | `PreToolUse`(`Edit\|Write`) | `require-active-task.sh` | In Progress 태스크 존재 && transcript에 `task view` 호출 이력 존재 |
| 3-1 / 3-4 | `PreToolUse`(`Bash`, `if:"Bash(git commit *)"`) | `pre-commit-check.sh` | 브랜치명이 `task/*` && (옵트인 시) 테스트 커맨드 exit 0 |
| 3-4b | `Stop` | `block-stop-if-dirty.sh` | In Progress 태스크 있는데 `git status --porcelain` 결과 있으면 차단 |
| 4.3 | `PreToolUse`(`Bash`, `if:"Bash(git push *)"`) | `pre-push-check.sh` | `task/<ID>` 브랜치의 태스크가 status=Done && finalSummary 비어있지 않음 |
| -1.5 (참고용, 차단 아님) | `SessionStart` | `session-start.sh` | backlog 프로젝트면 `instructions overview`/`doctor` 자동 브리핑 |

모든 스크립트는 backlog 프로젝트(`backlog/config.yml` 존재)가 아닌 곳에서는 즉시
`exit 0`으로 통과하며, 차단은 예외 없이 **exit code 2**로 통일되어 있다(이벤트별로
다른 JSON 필드를 요구하지 않는, Claude Code 훅 사양상 가장 견고한 방식).

**현재 알려진 한계**: 상태 이름 `"In Progress"` 하드코딩, `task view` 확인이 transcript
문자열 검색 기반 휴리스틱, 3-5/3-7의 훅 미구현. 상세는 저장소 README.md 참고.
