#!/usr/bin/env bash
# work-status.sh - Parallel Claude session status report
# Run manually: bash .claude/scripts/work-status.sh
# Run automatically: SessionStart hook in .claude/settings.json

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
WORK_LOG="$REPO_ROOT/docs/parallel-work-log.md"
DIVIDER="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "$DIVIDER"
echo "  TECHWIKI PARALLEL SESSION STATUS"
printf "  Generated: %s\n" "$(date -Iseconds)"
echo "$DIVIDER"

# --- Section 1: Active branches ---
echo ""
echo "ACTIVE BRANCHES (claude/*):"
echo ""
CLAUDE_BRANCHES=$(git -C "$REPO_ROOT" branch -a --format='%(refname:short)' | grep 'claude/' | sort -u)
if [ -z "$CLAUDE_BRANCHES" ]; then
  echo "  (none - no claude/* branches found)"
else
  while IFS= read -r branch; do
    display="${branch#remotes/origin/}"
    last_commit=$(git -C "$REPO_ROOT" log "$branch" --oneline -1 2>/dev/null || echo "(no commits)")
    last_time=$(git -C "$REPO_ROOT" log "$branch" --format="%ar" -1 2>/dev/null || echo "unknown")
    echo "  [$display]"
    echo "    Last: $last_commit  ($last_time)"
  done <<< "$CLAUDE_BRANCHES"
fi

# --- Section 2: Git log ---
echo ""
echo "$DIVIDER"
echo ""
echo "RECENT COMMITS (all branches, last 15):"
echo ""
git -C "$REPO_ROOT" log --all --oneline --graph --decorate -15 2>/dev/null || echo "  (no commits yet)"

# --- Section 3: Work log ---
echo ""
echo "$DIVIDER"
echo ""
echo "WORK LOG - IN PROGRESS SESSIONS:"
echo ""
if [ -f "$WORK_LOG" ]; then
  awk '
    /^## Session:/ {
      if (block != "" && in_progress) print block
      block = $0 "\n"; in_progress = 0; next
    }
    /\*\*Status:\*\* IN PROGRESS/ { in_progress = 1 }
    { block = block $0 "\n" }
    END { if (block != "" && in_progress) print block }
  ' "$WORK_LOG"

  IN_PROGRESS_COUNT=$(grep -c '\*\*Status:\*\* IN PROGRESS' "$WORK_LOG" 2>/dev/null || true)
  DONE_COUNT=$(grep -c '\*\*Status:\*\* DONE' "$WORK_LOG" 2>/dev/null || true)
  IN_PROGRESS_COUNT=${IN_PROGRESS_COUNT:-0}
  DONE_COUNT=${DONE_COUNT:-0}
  echo "  Summary: $IN_PROGRESS_COUNT session(s) IN PROGRESS, $DONE_COUNT session(s) DONE"
else
  echo "  (docs/parallel-work-log.md not found yet)"
fi

# --- Section 4: Working tree ---
echo ""
echo "$DIVIDER"
echo ""
echo "WORKING TREE (this session):"
echo ""
CURRENT_BRANCH=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || echo "detached")
echo "  Branch: $CURRENT_BRANCH"
STATUS_OUTPUT=$(git -C "$REPO_ROOT" status --short 2>/dev/null)
if [ -z "$STATUS_OUTPUT" ]; then
  echo "  Working tree clean."
else
  while IFS= read -r line; do echo "    $line"; done <<< "$STATUS_OUTPUT"
fi

echo ""
echo "$DIVIDER"
echo ""
