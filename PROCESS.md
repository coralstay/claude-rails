# claude-rails — 프로세스 & 동작 명세서

설치 완료 시점(2026-08-30) 기준, `~/.claude/`에 실제로 설치된 내용과 각 훅의 정확한 동작을
전부 명세한다. 개념 설계는 README.md, 여기서는 "실제로 무엇이 어떤 순서로 실행되는가"만
다룬다.

---

## 1. 현재 설치 상태

| 항목 | 경로 | 상태 |
|---|---|---|
| 훅 스크립트 | `~/.claude/hooks/claude-rails/*.sh` | 6개 파일, 실행권한(755) |
| 전역 설정 | `~/.claude/settings.json` | `hooks` 키 병합됨, 기존 키(`enabledPlugins`,`theme`,`model` 등) 보존 |
| 전역 지침 | `~/.claude/CLAUDE.md` | `<!-- CLAUDE-RAILS:BEGIN -->` ~ `END` 블록으로 신규 생성 |
| 설정 백업 | `~/.claude/settings.json.bak.<timestamp>` | 설치 직전 상태 스냅샷 (설치 시각 1개 존재) |
| 원본 저장소 | `/Users/flynn_macpro/githubs/usage` (github: `amosQP/claude-rails`, private) | 이 문서를 포함한 소스 |

설치된 훅 스크립트 6개:

```
~/.claude/hooks/claude-rails/
├── _lib.sh                    # 공용 함수 (직접 실행되지 않음)
├── session-start.sh           # SessionStart
├── require-active-task.sh     # PreToolUse: Edit|Write
├── pre-commit-check.sh        # PreToolUse: Bash, if git commit
├── pre-push-check.sh          # PreToolUse: Bash, if git push
└── block-stop-if-dirty.sh     # Stop
```

**이 훅들은 backlog.md가 초기화되지 않은 디렉토리(`backlog/config.yml`이 없는 곳)에서는
전부 즉시 `exit 0`으로 통과한다.** 즉 이 컴퓨터의 모든 Claude Code 세션에 걸려 있지만,
실제로 개입하는 건 `backlog init`이 된 프로젝트뿐이다.

---

## 2. 전체 프로세스 (Phase -1 ~ 5)

```
Phase -1  셋업 (프로젝트당 1회)
   │
   ▼
Phase 0   브리핑 & 현황 파악          (강제 없음)
   │
   ▼
Phase 0.5 드래프트 (선택적)           (강제 없음)
   │
   ▼
Phase 1   백로깅 (Epic/Story/Task 생성)
   │  ── 훅: require-active-task.sh가 이후 Edit/Write를 가드하기 시작
   ▼
Phase 2   검토 게이트 ★ 사람 개입      (훅 없음, 사람이 직접 승인)
   │
   ▼
Phase 3   실행 루프 (태스크당 반복)
   │  3-0 컨텍스트 로딩    ← require-active-task.sh
   │  3-1 활성화           ← pre-commit-check.sh (커밋 시점에 검사)
   │  3-2 리서치→계획      (강제 없음)
   │  3-3 승인 게이트       (Plan Mode 재사용, 훅 아님)
   │  3-4 구현 서브루프    ← pre-commit-check.sh
   │  3-4b 미커밋 종료 방지 ← block-stop-if-dirty.sh
   │  3-5 스코프 이탈 감지  (강제 없음, 아직 미구현)
   │  3-6 서브태스크 처리   (강제 없음)
   │  3-7 완료 전환         (강제 없음, 아직 미구현)
   ▼
Phase 4   완료 & 종결
   │  ── 훅: pre-push-check.sh가 push를 가드
   ▼
Phase 5   주기적 유지보수            (훅 아님, /loop 또는 cron 별도 구성 필요)
```

---

## 3. 훅 동작 명세 (스크립트별 정확한 로직)

### 3.1 공통: `_lib.sh`

다른 모든 스크립트가 `source`해서 쓰는 3개 함수. 그 자체로는 훅으로 등록되지 않는다.

```bash
deny(reason):
    stderr에 reason 출력
    exit 2                     # PreToolUse/Stop 등에서 "차단"으로 해석되는 유일한 신호

is_backlog_project(dir):
    dir/backlog/config.yml 파일 존재 여부 반환

no_active_task(dir):
    dir에서 `backlog task list --status "In Progress" --plain` 실행
    출력에 "No tasks found." 문자열이 있으면 참(=활성 태스크 없음)
```

> **왜 exit 2인가**: Claude Code 훅 문서상 차단이 가능한 모든 이벤트(PreToolUse, Stop 등)에서
> 공통으로 동작이 보장되는 유일한 메커니즘이 exit code 2다. 이벤트별로 다른 JSON 필드
> (`permissionDecision` vs `decision`)를 요구하는 것보다 이 방식이 더 견고해서 전 스크립트가
> 이 방식 하나로 통일되어 있다.

---

### 3.2 `session-start.sh` — 이벤트: `SessionStart`

**등록**: 모든 세션 시작 시 무조건 실행 (matcher 없음)

**로직**:
```
1. stdin JSON에서 cwd 추출
2. backlog CLI가 없으면 → exit 0
3. cwd가 backlog 프로젝트가 아니면 → exit 0
4. `backlog instructions overview` 실행 결과를 additionalContext로,
   `backlog doctor` 실행 결과를 systemMessage로 담아 JSON 출력
5. exit 0
```

**차단 불가**: SessionStart는 Claude Code 사양상 차단을 지원하지 않는 이벤트다. 정보
주입(브리핑)만 한다 — 세션 시작마다 Claude가 backlog 사용법과 무결성 상태를 자동으로
인지하게 만드는 용도.

---

### 3.3 `require-active-task.sh` — 이벤트: `PreToolUse`, matcher: `Edit|Write`

**등록**: 모든 파일 Edit/Write 시도 전에 실행

**로직**:
```
1. stdin JSON에서 cwd, transcript_path 추출
2. backlog CLI 없음 → exit 0 (통과)
3. cwd가 backlog 프로젝트 아님 → exit 0 (통과)
4. "In Progress" 상태 태스크가 하나도 없으면
   → deny("In Progress 상태인 backlog 태스크가 없습니다...")
5. transcript_path 파일이 존재하고, 그 안에 "task view" 문자열이
   없으면 → deny("이 세션에서 아직 task view로 태스크를 읽지 않았습니다...")
6. 위 조건 다 통과 → exit 0 (Edit/Write 허용)
```

**판정 기준의 정확한 한계**:
- 4번은 상태 이름 `"In Progress"`가 하드코딩되어 있다. 프로젝트가 `backlog config`로
  상태명을 바꾸면 이 검사는 항상 실패(=항상 차단)한다.
- 5번은 이번 세션의 transcript 파일 전체를 `grep -q "task view"`로 검사하는 **휴리스틱**이다.
  세션 어느 시점에든 `backlog task view`를 한 번이라도 실행했다면 통과하며, "지금 편집하려는
  파일이 그 태스크와 실제로 관련 있는지"까지는 검증하지 않는다.

---

### 3.4 `pre-commit-check.sh` — 이벤트: `PreToolUse`, matcher: `Bash`, `if: "Bash(git commit *)"`

**등록**: Bash 도구 호출 중 명령어가 `git commit`으로 시작할 때만 실행 (`if` 필터가
매처 단계에서 걸러주므로 다른 Bash 명령에는 아예 스크립트가 뜨지 않는다)

**로직**:
```
1. stdin JSON에서 cwd 추출
2. cwd가 backlog 프로젝트 아님 → exit 0
3. In Progress 태스크가 하나라도 있으면 (no_active_task가 거짓이면):
   3a. 현재 브랜치명을 git rev-parse --abbrev-ref HEAD로 확인
   3b. 브랜치명이 "task/"로 시작하지 않으면
       → deny("커밋하기 전에 태스크 브랜치로 전환하세요. 현재 브랜치: <branch>")
   (In Progress 태스크가 없으면 이 브랜치 검사 자체를 건너뜀)
4. cwd/.claude-rails.json 파일이 있으면:
   4a. 그 파일의 .testCommand 값을 읽음
   4b. 값이 있으면 cwd에서 그 커맨드를 eval로 실행, 종료 코드와 출력을 캡처
   4c. 종료 코드가 0이 아니면
       → deny("커밋 전 테스트 실패 (...): <출력 마지막 800자>")
5. 위 조건 다 통과 → exit 0 (커밋 허용)
```

**중요한 설계 포인트**:
- 브랜치명 검사와 테스트 검사는 **서로 독립**이다 — In Progress 태스크가 없으면 브랜치
  검사만 건너뛰고, `.claude-rails.json`이 없으면 테스트 검사만 건너뛴다.
- 테스트 커맨드는 `.claude-rails.json`이 없는 프로젝트에서는 **아예 실행되지 않는다** —
  즉 이 프로젝트별 옵트인 파일을 만들지 않으면 이 훅은 브랜치명만 강제한다.
- `eval`로 테스트 커맨드를 실행하므로 `.claude-rails.json`의 `testCommand` 값은 임의 셸
  명령으로 해석된다. 이 파일은 신뢰할 수 있는 값만 넣어야 한다 (프로젝트 루트에 커밋되는
  파일이므로 사실상 저장소를 신뢰하는 것과 같은 수준).

---

### 3.5 `block-stop-if-dirty.sh` — 이벤트: `Stop`

**등록**: Claude가 턴을 끝내려 할 때마다 실행 (matcher 없음)

**로직**:
```
1. stdin JSON에서 cwd 추출
2. cwd가 backlog 프로젝트 아님 → exit 0
3. In Progress 태스크가 없으면 → exit 0
4. `git status --porcelain` 결과가 비어있지 않으면(=커밋 안 된 변경 있음)
   → deny("커밋하지 않은 변경사항이 있습니다...")
5. 위 조건 다 통과 → exit 0 (턴 종료 허용)
```

**동작 특성**: exit 2로 차단되면 Claude Code는 턴을 끝내지 않고 계속 진행한다(재개
사유로 stderr 메시지가 전달됨). 즉 Claude가 "변경사항을 만들어놓고 커밋 안 한 채
말을 끝내려는" 매 순간마다 이 훅이 반복적으로 개입해서, 결과적으로 커밋을 하거나
사용자에게 상황을 설명할 때까지 턴이 안 끝난다.

**리스크**: staged 안 된 실험적 변경이나 스크래치 파일이 backlog 프로젝트 루트 안에
있으면(`.gitignore` 처리 안 된 임시 파일 등) 이 훅이 계속 차단할 수 있다. `git status
--porcelain`은 untracked 파일도 잡아낸다.

---

### 3.6 `pre-push-check.sh` — 이벤트: `PreToolUse`, matcher: `Bash`, `if: "Bash(git push *)"`

**등록**: Bash 명령이 `git push`로 시작할 때만 실행

**로직**:
```
1. stdin JSON에서 cwd 추출
2. cwd가 backlog 프로젝트 아님 → exit 0
3. 현재 브랜치명 확인. "task/"로 시작하지 않으면 → exit 0 (이 훅은 task 브랜치만 검사)
4. 브랜치명에서 "task/" 접두어를 뗀 나머지를 task_id로 사용
   (예: 브랜치 "task/TASK-42" → task_id = "TASK-42")
5. `backlog task view <task_id> --json` 실행. 실패하거나 빈 결과면 → exit 0
6. JSON에서 .task.status, .task.finalSummary 추출
7. status가 "Done"이 아니면
   → deny("<task_id>가 아직 Done 상태가 아닙니다 (현재: <status>)...")
8. finalSummary가 공백만 있거나 비어있으면
   → deny("<task_id>의 final summary가 비어있습니다...")
9. 위 조건 다 통과 → exit 0 (push 허용)
```

**정확도**: 이 검사는 JSON 필드명(`status`, `finalSummary`)을 실제 `backlog task view
--json` 출력을 대상 프로젝트에서 직접 실행해 확인한 값이다 (추측 아님, 설치 전
`pathFinder-spring-backend` 프로젝트의 실제 태스크로 검증).

---

## 4. 실행 순서 예시 (하나의 태스크를 처음부터 끝까지)

실제 backlog 프로젝트에서 Claude가 태스크 하나를 처리할 때 훅이 개입하는 순서:

```
1. [세션 시작]
   → session-start.sh 발동 (SessionStart)
     backlog instructions overview + backlog doctor 결과가 컨텍스트에 주입됨

2. Claude가 아직 아무 태스크도 안 읽고 파일을 Edit하려 시도
   → require-active-task.sh 발동 (PreToolUse: Edit)
     In Progress 태스크 없음 → deny, Edit 차단됨

3. Claude가 `backlog task edit TASK-7 -s "In Progress"` 실행 (Bash, 훅 미적용 대상)
   Claude가 `git checkout -b task/TASK-7` 실행 (Bash, 훅 미적용 대상)
   Claude가 `backlog task view TASK-7 --plain` 실행 (Bash, 훅 미적용 대상)

4. Claude가 다시 파일을 Edit
   → require-active-task.sh 발동
     In Progress 태스크 있음 + transcript에 "task view" 있음 → exit 0, Edit 허용

5. Claude가 구현 후 `git commit -m "..."` 실행
   → pre-commit-check.sh 발동 (PreToolUse: Bash, if git commit)
     브랜치 "task/TASK-7" → 통과
     .claude-rails.json 있으면 테스트 실행 → 실패 시 deny, 성공 시 통과
     커밋 진행됨

6. Claude가 커밋 안 한 변경사항을 남긴 채 턴을 끝내려 함
   → block-stop-if-dirty.sh 발동 (Stop)
     dirty tree 감지 → deny, 턴이 안 끝나고 계속됨 (커밋을 마저 하게 됨)

7. (3~6을 여러 번 반복 — 작은 단위 구현 루프)

8. Claude가 AC/DoD 체크 후 `-s Done`, `--final-summary` 기록,
   `git push` 실행
   → pre-push-check.sh 발동 (PreToolUse: Bash, if git push)
     status=Done, finalSummary 있음 → exit 0, push 허용
```

---

## 5. 강제 vs 비강제 대응표 (재확인)

| Phase | 항목 | 강제 방식 | 스크립트 |
|---|---|---|---|
| -1 | 세션마다 가이드 브리핑 | 자동 컨텍스트 주입 (차단 아님) | `session-start.sh` |
| 1 | In Progress 없이 편집 금지 | PreToolUse 차단 | `require-active-task.sh` |
| 3-0 | task view 안 읽고 편집 금지 | PreToolUse 차단 (transcript 검사) | `require-active-task.sh` |
| 3-1 | task/ID 브랜치 강제 | PreToolUse 차단 (커밋 시점) | `pre-commit-check.sh` |
| 3-4 | 테스트 통과 후 커밋 | PreToolUse 차단 (옵트인, `.claude-rails.json` 필요) | `pre-commit-check.sh` |
| 3-4b | 미커밋 상태로 턴 종료 금지 | Stop 차단 | `block-stop-if-dirty.sh` |
| 4 | Done+summary 없이 push 금지 | PreToolUse 차단 | `pre-push-check.sh` |
| 0, 0.5, 2, 3-2, 3-3, 3-5, 3-6, 3-7, 5 | — | 강제 없음 (판단 영역이거나 훅 대상 아님) | — |

---

## 6. 알려진 한계 (README.md와 동일, 재확인용)

1. **상태 이름 하드코딩**: `"In Progress"` 문자열에 의존. 프로젝트가 상태명을 바꾸면
   오작동.
2. **`task view` 확인이 휴리스틱**: transcript 전체에서 문자열 `"task view"`를 찾을
   뿐, 시점이나 대상 태스크 일치는 검사하지 않음.
3. **3-5 스코프 이탈 감지 미구현**: `prompt`/`agent` 타입 훅으로 자동화 가능하나 아직
   추가 안 함.
4. **3-7 AC 증거 확인 미구현**: PostToolUse로 테스트 결과를 상태 파일에 남기고
   `--check-ac` 직전 PreToolUse가 그 파일을 확인하는 2단 구조가 필요하나 미구현.
5. **Phase 5 주기 실행 없음**: 훅은 세션 이벤트 기반이라 "N일마다"류 실행은 대상 밖.
   `/loop` 또는 cron으로 별도 구성 필요.
6. **`.claude-rails.json`의 testCommand는 `eval`로 실행됨** — 신뢰 경계에 대한 주의
   필요(§3.4 참고).

---

## 7. 검증 방법 (재현 가능한 절차)

```bash
# 설정이 정상 병합됐는지
jq empty ~/.claude/settings.json && echo OK

# 특정 훅이 실제로 등록돼 있는지
jq -e '.hooks.PreToolUse[] | select(.matcher=="Edit|Write")' ~/.claude/settings.json

# 훅 스크립트를 실제 backlog 프로젝트 대상으로 직접 실행 (읽기 전용, 부작용 없음)
echo '{"cwd":"<backlog 프로젝트 경로>","transcript_path":"/nonexistent"}' \
  | bash ~/.claude/hooks/claude-rails/require-active-task.sh; echo "exit: $?"
```

Claude Code가 훅 변경사항을 감지하려면 `/hooks` 메뉴를 한 번 열거나 세션을 재시작해야
할 수 있다 (설정 워처가 세션 시작 시 존재했던 디렉토리만 감시하는 경우).
