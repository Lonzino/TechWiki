# TechWiki - Claude 세션 컨텍스트

## 이 리포가 뭔지
개인 테크 위키. 순수 Markdown, 빌드 시스템 없음, CI/CD 없음.
모든 콘텐츠는 `docs/` 아래. 새 문서용 템플릿은 `templates/`에 있음.

## 파일 컨벤션
- 파일명: lowercase-kebab (예: `deploy-api.md`, `postgres-backup.md`)
- 파일 하나에 토픽 하나
- 모든 문서 첫 줄은 한 문장 요약
- 새 문서는 적절한 카테고리 서브디렉토리에:
  - `docs/backend/`, `docs/frontend/`, `docs/infra/`, `docs/ops/`
- 문서 추가 후 `docs/index.md`에도 해당 카테고리 아래 링크 추가

## 사용 가능한 템플릿
| 템플릿 | 사용 시기 |
|---|---|
| `templates/adr.md` | 아키텍처 결정 기록 |
| `templates/howto.md` | 단계별 작업 가이드 |
| `templates/runbook.md` | 인시던트 대응 / 운영 절차 |
| `templates/glossary.md` | 용어 정의 |

---

## 병렬 세션 프로토콜 (중요)

이 리포는 여러 Claude Code 세션이 병렬로 작업한다.
충돌 방지와 작업 가시성을 위해 각 세션은 아래 프로토콜을 따른다.

### 세션 시작 시
1. `docs/parallel-work-log.md` 읽기 → 다른 세션이 뭘 하고 있는지 파악
2. 다른 활성 세션이 작업 중인 파일은 피하기
3. `docs/parallel-work-log.md` 끝에 아래 형식으로 자기 항목 append:

```
## Session: [브랜치 suffix] | [ISO timestamp] | Branch: [브랜치명]
**Task:** [이 세션이 할 작업 한 줄]
**Files planned:** [작업할 파일 목록, 쉼표 구분]
**Status:** IN PROGRESS
```

예시:
```
## Session: 6VyQs | 2026-02-18T06:00:00+09:00 | Branch: claude/workflow-tracking-setup-6VyQs
**Task:** PostgreSQL 백업/복원 runbook 작성
**Files planned:** docs/ops/postgres-backup-restore.md, docs/index.md
**Status:** IN PROGRESS
```

### 세션 종료 / 작업 완료 시
자기 항목의 Status 줄을 업데이트:
```
**Status:** DONE
**Completed:** [ISO timestamp] - [실제로 한 것 한 줄]
```

### 브랜치 전략
- 각 세션은 `claude/<task-slug>-<suffix>` 브랜치에서 작업
- master/main에 직접 커밋 금지
- 완료 후 브랜치명을 로그 항목에 남겨두면 사용자가 merge 가능

---

## 현재 상태 확인 방법

```bash
# 전체 상태 텍스트 요약
bash .claude/scripts/work-status.sh

# 실시간 다마고치 대시보드 (별도 터미널)
python3 .claude/scripts/session-monitor.py
```

---

## 하지 말 것
- `docs/parallel-work-log.md`에서 다른 세션 항목 수정/삭제 금지
- `docs/`, `templates/`, `.claude/` 외부에 파일 추가할 때는 이유 필요
- `README.md` 또는 `docs/index.md` 수정 시 다른 세션도 편집 중인지 먼저 확인
