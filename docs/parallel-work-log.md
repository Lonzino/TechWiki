# Parallel Work Log

세션들이 작업 시작/완료 시 여기에 append한다. 다른 세션의 항목은 수정하지 않는다.

---

## 읽는 법
- **IN PROGRESS**: 현재 진행 중 (세션이 중단됐으면 stale일 수 있음)
- **DONE**: 완료됨, 브랜치명으로 커밋 확인 가능
- Short-id = 브랜치명 suffix 마지막 4~5자 (예: 브랜치 `claude/foo-6VyQs` → id `6VyQs`)

---

## 항목 형식 (세션이 시작 시 append)

시작 시:

    # Session: [id] | [ISO timestamp] | Branch: [branch-name]
    Task: [이 세션이 할 작업 한 줄]
    Files planned: [작업할 파일들, 쉼표 구분]
    Status: IN PROGRESS

완료 시 Status 줄 업데이트 (실제 마크다운 헤더 `##` 사용):

    Status: DONE
    Completed: [ISO timestamp] - [실제로 한 것 한 줄]

---

<!-- 세션들은 이 줄 아래에 append한다. Do not remove this comment. -->

## Session: 6VyQs | 2026-02-18T00:00:00+00:00 | Branch: claude/workflow-tracking-setup-6VyQs
**Task:** 병렬 세션 워크플로우 트래킹 시스템 구축 (CLAUDE.md, settings.json, work-status.sh, session-monitor.py, parallel-work-log.md)
**Files planned:** CLAUDE.md, .claude/settings.json, .claude/scripts/work-status.sh, .claude/scripts/session-monitor.py, docs/parallel-work-log.md
**Status:** IN PROGRESS
