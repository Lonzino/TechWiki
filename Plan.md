# TechWiki 병렬 세션 워크플로우 - 구현 계획

## 개요
여러 Claude Code 세션이 TechWiki에서 병렬로 작업할 때 충돌을 방지하고 작업 가시성을 확보하기 위한 시스템.

---

## 구현 파일 (5개)

### 순서 중요: 아래 순서대로 생성

### 1. `.claude/scripts/work-status.sh` (먼저 생성)

**기능:**
- 현재 모든 `claude/*` 브랜치 목록 + 마지막 커밋
- 전체 브랜치 git log (최근 15개)
- `docs/parallel-work-log.md`에서 IN PROGRESS 세션 추출
- 현재 브랜치 working tree 상태
- `chmod +x` 필요

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
WORK_LOG="$REPO_ROOT/docs/parallel-work-log.md"
DIVIDER="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo && echo "$DIVIDER"
echo "  TECHWIKI PARALLEL SESSION STATUS"
printf "  Generated: %s\n" "$(date -Iseconds)"
echo "$DIVIDER"

echo && echo "ACTIVE BRANCHES (claude/*):"
CLAUDE_BRANCHES=$(git -C "$REPO_ROOT" branch -a --format='%(refname:short)' | grep 'claude/' | sort -u)
if [ -z "$CLAUDE_BRANCHES" ]; then
  echo "  (none)"
else
  while IFS= read -r branch; do
    display="${branch#remotes/origin/}"
    last_commit=$(git -C "$REPO_ROOT" log "$branch" --oneline -1 2>/dev/null || echo "(no commits)")
    last_time=$(git -C "$REPO_ROOT" log "$branch" --format="%ar" -1 2>/dev/null || echo "unknown")
    echo "  [$display]"
    echo "    Last: $last_commit ($last_time)"
  done <<< "$CLAUDE_BRANCHES"
fi

echo && echo "$DIVIDER"
echo && echo "RECENT COMMITS (all branches, last 15):"
git -C "$REPO_ROOT" log --all --oneline --graph --decorate -15

echo && echo "$DIVIDER"
echo && echo "WORK LOG - IN PROGRESS SESSIONS:"
if [ -f "$WORK_LOG" ]; then
  awk '/^## Session:/{if(block!=""&&in_progress)print block; block=$0"\n"; in_progress=0; next} /\*\*Status:\*\* IN PROGRESS/{in_progress=1} {block=block$0"\n"} END{if(block!=""&&in_progress)print block}' "$WORK_LOG"
  IN_PROGRESS_COUNT=$(grep -c '\*\*Status:\*\* IN PROGRESS' "$WORK_LOG" 2>/dev/null || echo 0)
  DONE_COUNT=$(grep -c '\*\*Status:\*\* DONE' "$WORK_LOG" 2>/dev/null || echo 0)
  echo "  Summary: $IN_PROGRESS_COUNT IN PROGRESS, $DONE_COUNT DONE total"
else
  echo "  (docs/parallel-work-log.md not found)"
fi

echo && echo "$DIVIDER"
echo && echo "WORKING TREE (current session):"
CURRENT_BRANCH=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || echo "detached")
echo "  Branch: $CURRENT_BRANCH"
STATUS_OUTPUT=$(git -C "$REPO_ROOT" status --short 2>/dev/null)
if [ -z "$STATUS_OUTPUT" ]; then
  echo "  Clean."
else
  while IFS= read -r line; do echo "    $line"; done <<< "$STATUS_OUTPUT"
fi
echo && echo "$DIVIDER" && echo
```

---

### 2. `.claude/settings.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "bash .claude/scripts/work-status.sh"
      }
    ]
  }
}
```

---

### 3. `docs/parallel-work-log.md`

```markdown
# Parallel Work Log

세션들이 작업 시작/완료 시 여기에 append한다. 다른 세션의 항목은 수정하지 않는다.

---

## 읽는 법
- **IN PROGRESS**: 현재 진행 중 (세션이 중단됐으면 stale일 수 있음)
- **DONE**: 완료됨, 브랜치명으로 커밋 확인 가능

---

<!-- 세션들은 이 줄 아래에 append한다. -->
```

---

### 4. `CLAUDE.md` (마지막 생성)

모든 세션이 시작 시 자동으로 읽는 파일. 핵심 내용:
- 위키 컨벤션 (파일명, 디렉토리 구조, 템플릿 목록)
- **병렬 세션 프로토콜**: 세션 시작 시 로그 확인 + append, 종료 시 DONE으로 업데이트
- 로그 항목 형식:

```
## Session: [브랜치 suffix 4자] | [ISO timestamp] | Branch: [브랜치명]
**Task:** [이 세션이 할 작업 한 줄]
**Files planned:** [작업할 파일 목록]
**Status:** IN PROGRESS
```

---

### 5. `.claude/scripts/session-monitor.py` (다마고치 시각화)

별도 터미널에서 실행하는 실시간 대시보드. Python curses 사용 (표준 라이브러리, pip install 없음).

**화면 구성:**
```
 TECHWIKI PARALLEL SESSION MONITOR              2026-02-18 06:15:30
 Sessions: 3 total  |  ⚡ 2 working  |  ✓ 1 done  |  Refresh: 2s
┌─ 6VyQs ────────────────────────┐  ┌─ aB3x ─────────────────────────┐
│  .------.                      │  │  .------.                       │
│  |◕ . ◕ |   typing...         │  │  |^ . ^ |   thinking...        │
│  | \__/ |                      │  │  | \__/ |                       │
│  '------'                      │  │  '------'                       │
│                                 │  │                                 │
│  Task: Create tracking system   │  │  Task: Postgres backup runbook  │
│  Branch: workflow-tracking      │  │  Branch: postgres-runbook       │
│  ✓ DONE                        │  │  ⚡ IN PROGRESS                 │
│  Files: CLAUDE.md, .claude/     │  │  Files: docs/ops/postgres-...   │
│  Time: 2026-02-18T05:55:00     │  │  Time: 2026-02-18T06:01:00     │
└─────────────────────────────────┘  └─────────────────────────────────┘
 Q: quit  |  Auto-refreshes every 2s from docs/parallel-work-log.md
```

**마스코트 애니메이션 프레임** (0.4초마다 순환):
```
Frame 1 (typing)   Frame 2 (thinking)  Frame 3 (writing)  Frame 4 (coding)
 .------.            .------.            .------.            .------.
 |o . o |            |^ . ^ |            |- . - |            |> . < |
 | \__/ |            | \__/ |            | .... |            | \__/ |
 '------'            '------'            '------'            '------'
  typing              thinking            writing              coding
```

**Done 마스코트:**
```
 .------.
 |^ u ^ |
 | \__/ |
 '------'
   DONE!
```

**핵심 동작:**
- `docs/parallel-work-log.md`를 2초마다 다시 파싱
- 세션마다 박스 하나, 2열 그리드 레이아웃
- IN PROGRESS 세션 = 노란색 + 애니메이션 순환
- DONE 세션 = 초록색 + done 마스코트
- `q` 또는 ESC로 종료

**실행 방법:** `python3 .claude/scripts/session-monitor.py`

---

## 최종 디렉토리 구조

```
TechWiki/
├── CLAUDE.md                        ← 신규
├── README.md
├── Plan.md                          ← 이 문서
├── .claude/
│   ├── settings.json                ← 신규
│   └── scripts/
│       ├── work-status.sh           ← 신규 (chmod +x)
│       └── session-monitor.py       ← 신규 (chmod +x)
├── docs/
│   ├── index.md
│   └── parallel-work-log.md         ← 신규
└── templates/
    ├── adr.md, glossary.md, howto.md, runbook.md
```

---

## 동작 원리 요약

1. 새 세션 시작 → `settings.json` 훅이 `work-status.sh` 자동 실행
2. 터미널에 출력: 모든 `claude/*` 브랜치, 최근 커밋, 현재 IN PROGRESS 세션 목록
3. Claude가 `CLAUDE.md` 읽음 → 프로토콜 지시에 따라 `parallel-work-log.md`에 자신의 항목 append
4. 작업 완료 → Status를 DONE으로 업데이트 후 커밋
5. 언제든 수동 확인: `bash .claude/scripts/work-status.sh`
6. 실시간 시각화: 별도 터미널에서 `python3 .claude/scripts/session-monitor.py` 상시 실행

---

## 검증 방법

1. 파일 5개 생성 후 단일 커밋으로 `claude/workflow-tracking-setup-6VyQs`에 push
2. 새 Claude Code 세션을 TechWiki 디렉토리에서 열어서 SessionStart 훅이 자동 실행되는지 확인
3. `bash .claude/scripts/work-status.sh` 수동 실행해서 출력 확인
4. 세션이 `docs/parallel-work-log.md`에 항목을 append하는지 확인
5. `python3 .claude/scripts/session-monitor.py` 실행 후 다마고치 대시보드 확인

---

## 브랜치

`claude/workflow-tracking-setup-6VyQs`에 커밋 후 push
