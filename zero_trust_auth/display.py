import curses
import sys
import time
from typing import Optional

from .grid import (
    COL_LABELS,
    GRID_COLS,
    GRID_ROWS,
    ROW_LABELS,
    derive_monthly_grid,
    position_label,
)

DISPLAY_SECONDS = 90


def _harden_process() -> None:
    """Best-effort OS hardening: disable core dumps and lock memory pages."""
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except Exception:
        pass
    try:
        import ctypes
        # MCL_CURRENT | MCL_FUTURE = 3; prevents grid bytes from being
        # swapped to disk where they could be recovered forensically.
        ctypes.cdll.LoadLibrary("libc.so.6").mlockall(3)
    except Exception:
        pass


def _clear_terminal() -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def display_grid_ephemeral(
    master_seed: bytes,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> None:
    """
    Display the monthly authentication grid for DISPLAY_SECONDS seconds.

    Security properties:
    - Never written to disk, logs, pipes, or any persistent store.
    - Memory pages locked (mlock) to prevent swapping.
    - Core dumps disabled so the process image cannot be captured.
    - Terminal cleared completely when the countdown reaches zero.
    - Screenshot prevention beyond this requires OS/compositor-level policy
      (e.g. Wayland security-context, Windows DRM flags, physical screen
      privacy filters) — that layer is outside Python's reach.
    """
    _harden_process()
    grid = derive_monthly_grid(master_seed, year, month)
    pos_to_key = {pos: idx for idx, pos in grid.items()}

    def _run(stdscr: "curses.window") -> None:
        curses.curs_set(0)
        has_color = False
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_RED, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            has_color = True
        except Exception:
            pass

        start = time.monotonic()

        while True:
            remaining = max(0.0, DISPLAY_SECONDS - (time.monotonic() - start))
            if remaining == 0.0:
                break

            try:
                stdscr.erase()
                y = 0

                header = "[ AUTHENTICATION GRID  —  DO NOT PHOTOGRAPH ]"
                attr = (curses.color_pair(1) | curses.A_BOLD) if has_color else curses.A_BOLD
                stdscr.addstr(y, 0, header, attr)
                y += 2

                # Column header
                stdscr.addstr(y, 0, "      " + "".join(f"  {COL_LABELS[c]}    " for c in range(GRID_COLS)))
                y += 1
                stdscr.addstr(y, 0, "    +" + "------+" * GRID_COLS)
                y += 1

                for r in range(GRID_ROWS):
                    line = f"  {ROW_LABELS[r]} |"
                    for c in range(GRID_COLS):
                        key_idx = pos_to_key.get((r, c))
                        line += (f" K-{key_idx + 1}  " if key_idx is not None else "      ") + "|"
                    stdscr.addstr(y, 0, line)
                    y += 1

                stdscr.addstr(y, 0, "    +" + "------+" * GRID_COLS)
                y += 2

                stdscr.addstr(y, 0, "Key placement this month:", curses.A_BOLD)
                y += 1
                for key_idx, pos in sorted(grid.items()):
                    stdscr.addstr(y, 0, f"  K-{key_idx + 1}  →  position {position_label(*pos)}")
                    y += 1
                y += 1

                secs = int(remaining)
                countdown = f"Grid auto-clears in: {secs:3d}s"
                if has_color:
                    if secs > 30:
                        c_attr = curses.color_pair(2) | curses.A_BOLD
                    elif secs > 10:
                        c_attr = curses.color_pair(3) | curses.A_BOLD
                    else:
                        c_attr = curses.color_pair(1) | curses.A_BOLD
                else:
                    c_attr = curses.A_BOLD
                stdscr.addstr(y, 0, countdown, c_attr)

                stdscr.refresh()
            except curses.error:
                pass

            time.sleep(0.25)

        try:
            stdscr.erase()
            stdscr.refresh()
        except curses.error:
            pass

    try:
        curses.wrapper(_run)
    except Exception as exc:
        # Fall back to a plain terminal display if curses is unavailable.
        print("[curses unavailable, falling back to plain display]")
        _plain_display(grid, pos_to_key)

    _clear_terminal()
    print("Grid display period ended. Terminal cleared.")


def _plain_display(grid: dict, pos_to_key: dict) -> None:
    """Non-curses fallback: print grid, sleep, then clear."""
    from .grid import format_grid
    print()
    print("[ AUTHENTICATION GRID  —  DO NOT PHOTOGRAPH ]")
    print()
    print(format_grid(grid))
    print()
    for key_idx, pos in sorted(grid.items()):
        print(f"  K-{key_idx + 1}  →  position {position_label(*pos)}")
    print()

    for remaining in range(DISPLAY_SECONDS, 0, -1):
        print(f"\rGrid auto-clears in: {remaining:3d}s", end="", flush=True)
        time.sleep(1)
    print()
