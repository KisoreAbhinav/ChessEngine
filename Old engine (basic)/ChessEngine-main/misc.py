import time
import sys

try:
    import select
except ImportError:
    select = None

try:
    import msvcrt
except ImportError:
    msvcrt = None


def GetTimeMs():
    """
    Cross-platform millisecond timer.
    Uses monotonic clock so elapsed-time calculations are stable.
    """
    return time.monotonic_ns() // 1_000_000


def InputWaiting():
    """
    Non-blocking check for pending console/stdin input.
    """
    if msvcrt is not None:
        return msvcrt.kbhit()

    if select is None:
        return False

    try:
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        return len(ready) > 0
    except Exception:
        return False


def _consume_command(info, command):
    command = command.strip().lower()
    if not command:
        return

    # On any incoming GUI/user command during search, stop current search.
    info.stopped = 1
    if "quit" in command:
        info.quit = 1


def ReadInput(info):
    """
    Poll input without blocking search; used by CheckUp().
    """
    if not getattr(info, "stdin_enabled", 0):
        return

    if msvcrt is not None:
        while msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                _consume_command(info, getattr(info, "stdin_buffer", ""))
                info.stdin_buffer = ""
            elif ch == "\b":
                if info.stdin_buffer:
                    info.stdin_buffer = info.stdin_buffer[:-1]
            else:
                info.stdin_buffer += ch
        return

    if InputWaiting():
        try:
            line = sys.stdin.readline()
        except Exception:
            return
        _consume_command(info, line)
