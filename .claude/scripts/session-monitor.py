#!/usr/bin/env python3
"""
session-monitor.py - Real-time parallel Claude session visualizer
Tamagotchi-style dashboard for TechWiki parallel sessions.

Run: python3 .claude/scripts/session-monitor.py
Press Q or ESC to quit.

No external dependencies - uses Python standard library only (curses).
"""

import curses
import time
import re
import subprocess
from pathlib import Path
from typing import List, Dict

# Resolve repo root from this script's location
try:
    REPO_ROOT = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(__file__).parent,
        stderr=subprocess.DEVNULL
    ).decode().strip())
except Exception:
    REPO_ROOT = Path(__file__).parent.parent.parent

WORK_LOG = REPO_ROOT / "docs" / "parallel-work-log.md"

# --- Mascot animation frames ---

WORKING_FRAMES = [
    # (label, lines)
    ("typing...", [
        " .------. ",
        " |o . o | ",
        " | \\__/ | ",
        " '------' ",
    ]),
    ("thinking.", [
        " .------. ",
        " |^ . ^ | ",
        " | \\__/ | ",
        " '------' ",
    ]),
    ("writing..", [
        " .------. ",
        " |- . - | ",
        " | .... | ",
        " '------' ",
    ]),
    ("coding...", [
        " .------. ",
        " |> . < | ",
        " | \\__/ | ",
        " '------' ",
    ]),
]

DONE_MASCOT = ("  DONE!  ", [
    " .------. ",
    " |^ u ^ | ",
    " | \\__/ | ",
    " '------' ",
])

IDLE_MASCOT = ("  zzz... ", [
    " .------. ",
    " |. _ .| ",
    " | ~~~  | ",
    " '------' ",
])


def parse_work_log() -> List[Dict]:
    """Parse parallel-work-log.md and return list of session dicts."""
    if not WORK_LOG.exists():
        return []

    try:
        content = WORK_LOG.read_text(encoding="utf-8")
    except Exception:
        return []

    sessions = []
    # Split on session headers
    blocks = re.split(r'(?=^## Session:)', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.startswith("## Session:"):
            continue

        session: Dict = {}

        # Header: ## Session: ID | timestamp | Branch: branch-name
        header_match = re.match(
            r'^## Session:\s*(\S+)\s*\|\s*([^|]+)\s*\|\s*Branch:\s*(\S+)',
            block.split('\n')[0]
        )
        if not header_match:
            continue

        session['id'] = header_match.group(1).strip()
        session['timestamp'] = header_match.group(2).strip()
        session['branch'] = header_match.group(3).strip()

        task_m = re.search(r'\*\*Task:\*\*\s*(.+)', block)
        files_m = re.search(r'\*\*Files planned:\*\*\s*(.+)', block)
        status_m = re.search(r'\*\*Status:\*\*\s*(.+)', block)
        completed_m = re.search(r'\*\*Completed:\*\*\s*(.+)', block)

        session['task'] = task_m.group(1).strip() if task_m else '(unknown)'
        session['files'] = files_m.group(1).strip() if files_m else ''
        session['status'] = status_m.group(1).strip() if status_m else 'UNKNOWN'
        session['completed'] = completed_m.group(1).strip() if completed_m else ''

        sessions.append(session)

    return sessions


def truncate(s: str, width: int) -> str:
    if len(s) <= width:
        return s
    return s[:width - 1] + "…"


def draw_session_box(win, session: Dict, frame_idx: int,
                     y: int, x: int, box_w: int, box_h: int):
    """Draw a single session box at (y, x)."""
    max_y, max_x = win.getmaxyx()

    if y + box_h >= max_y or x + box_w >= max_x:
        return

    is_done = 'DONE' in session.get('status', '').upper()
    session_id = session.get('id', '???')

    # Choose mascot
    if is_done:
        label, mascot_lines = DONE_MASCOT
        mascot_color = curses.color_pair(2)  # green
        status_icon = "✓"
        border_color = curses.color_pair(2)
    else:
        frame = WORKING_FRAMES[frame_idx % len(WORKING_FRAMES)]
        label, mascot_lines = frame
        mascot_color = curses.color_pair(3)  # yellow
        status_icon = "⚡"
        border_color = curses.color_pair(3)

    inner_w = box_w - 2  # inside the border

    try:
        # Top border with session ID
        title = f" {session_id} "
        top_fill = box_w - len(title) - 2
        left_fill = top_fill // 2
        right_fill = top_fill - left_fill
        win.addstr(y, x,
                   "┌" + "─" * left_fill + title + "─" * right_fill + "┐",
                   border_color)

        row = y + 1

        # Mascot (4 lines) + label
        for i, mline in enumerate(mascot_lines):
            padded = mline.ljust(inner_w)[:inner_w]
            win.addstr(row + i, x, "│", border_color)
            win.addstr(row + i, x + 1, padded, mascot_color | curses.A_BOLD)
            win.addstr(row + i, x + box_w - 1, "│", border_color)
        row += 4

        # Label line (typing... / DONE! etc)
        label_line = label.center(inner_w)[:inner_w]
        win.addstr(row, x, "│", border_color)
        win.addstr(row, x + 1, label_line, mascot_color)
        win.addstr(row, x + box_w - 1, "│", border_color)
        row += 1

        # Separator
        sep = "├" + "─" * inner_w + "┤"
        win.addstr(row, x, sep, border_color)
        row += 1

        # Task
        task_text = truncate(session.get('task', ''), inner_w - 8)
        task_line = f" Task: {task_text}".ljust(inner_w)[:inner_w]
        win.addstr(row, x, "│", border_color)
        win.addstr(row, x + 1, task_line)
        win.addstr(row, x + box_w - 1, "│", border_color)
        row += 1

        # Branch
        branch = session.get('branch', '').replace('claude/', '')
        branch_text = truncate(branch, inner_w - 10)
        branch_line = f" Branch: {branch_text}".ljust(inner_w)[:inner_w]
        win.addstr(row, x, "│", border_color)
        win.addstr(row, x + 1, branch_line)
        win.addstr(row, x + box_w - 1, "│", border_color)
        row += 1

        # Status
        status_val = session.get('status', 'UNKNOWN')
        status_text = truncate(f" {status_icon} {status_val}", inner_w)
        status_line = status_text.ljust(inner_w)[:inner_w]
        win.addstr(row, x, "│", border_color)
        win.addstr(row, x + 1, status_line, mascot_color)
        win.addstr(row, x + box_w - 1, "│", border_color)
        row += 1

        # Files
        files_text = truncate(session.get('files', '(none)'), inner_w - 9)
        files_line = f" Files: {files_text}".ljust(inner_w)[:inner_w]
        win.addstr(row, x, "│", border_color)
        win.addstr(row, x + 1, files_line)
        win.addstr(row, x + box_w - 1, "│", border_color)
        row += 1

        # Timestamp
        ts_text = truncate(session.get('timestamp', ''), inner_w - 7)
        ts_line = f" Time: {ts_text}".ljust(inner_w)[:inner_w]
        win.addstr(row, x, "│", border_color)
        win.addstr(row, x + 1, ts_line)
        win.addstr(row, x + box_w - 1, "│", border_color)
        row += 1

        # Bottom border
        win.addstr(row, x, "└" + "─" * inner_w + "┘", border_color)

    except curses.error:
        pass  # Box goes off screen edge - skip gracefully


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    # Color pairs
    curses.init_pair(1, curses.COLOR_CYAN, -1)     # header / borders neutral
    curses.init_pair(2, curses.COLOR_GREEN, -1)    # done
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # working
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)   # header bar
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)  # footer bar

    BOX_W = 42      # width of each session box
    BOX_H = 13      # height of each session box
    COLS = 2        # number of columns in grid
    REFRESH_S = 2   # seconds between log re-reads
    FRAME_S = 0.4   # seconds between animation frames

    frame_idx = 0
    last_parse = 0.0
    last_frame = time.time()
    sessions: List[Dict] = []

    while True:
        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):
            break

        now = time.time()

        # Advance animation
        if now - last_frame >= FRAME_S:
            frame_idx += 1
            last_frame = now

        # Re-read log
        if now - last_parse >= REFRESH_S:
            sessions = parse_work_log()
            last_parse = now

        max_y, max_x = stdscr.getmaxyx()
        stdscr.erase()

        # Header bar
        time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        title = " TECHWIKI PARALLEL SESSION MONITOR "
        padding = max(0, max_x - len(title) - len(time_str) - 1)
        header = title + " " * padding + time_str
        try:
            stdscr.addstr(0, 0, header[:max_x], curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

        # Summary line
        in_progress = sum(1 for s in sessions if 'DONE' not in s.get('status', '').upper())
        done_count = sum(1 for s in sessions if 'DONE' in s.get('status', '').upper())
        summary = (f" Sessions: {len(sessions)} total  |  "
                   f"⚡ {in_progress} working  |  "
                   f"✓ {done_count} done  |  "
                   f"Refresh: {REFRESH_S}s  |  "
                   f"Log: docs/parallel-work-log.md")
        try:
            stdscr.addstr(1, 0, summary[:max_x], curses.color_pair(1))
        except curses.error:
            pass

        # Grid of session boxes
        if not sessions:
            msg = "No sessions found in docs/parallel-work-log.md"
            hint = "Sessions will appear here when Claude sessions start and append their entries."
            try:
                stdscr.addstr(max_y // 2 - 1,
                              max(0, (max_x - len(msg)) // 2), msg[:max_x])
                stdscr.addstr(max_y // 2 + 1,
                              max(0, (max_x - len(hint)) // 2), hint[:max_x])
            except curses.error:
                pass
        else:
            for idx, session in enumerate(sessions):
                col = idx % COLS
                row_num = idx // COLS
                sx = col * (BOX_W + 2) + 1
                sy = 3 + row_num * (BOX_H + 1)
                draw_session_box(stdscr, session, frame_idx, sy, sx, BOX_W, BOX_H)

        # Footer bar
        footer = " Q: quit  |  Auto-refreshes every 2s  |  Animation 0.4s/frame "
        try:
            stdscr.addstr(max_y - 1, 0,
                          footer[:max_x].ljust(max_x - 1),
                          curses.color_pair(5))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.05)  # ~20fps event loop


if __name__ == "__main__":
    curses.wrapper(main)
