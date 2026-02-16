import io
import sys

from defs import AllInit, SearchInfo
import misc
import search


def run_latest_test():
    print("\n--- Part 70 Interrupt Thinking Test ---")

    # Force the non-msvcrt path so we can simulate stdin commands deterministically.
    old_msvcrt = misc.msvcrt
    old_input_waiting = misc.InputWaiting
    old_stdin = sys.stdin

    try:
        # 1) Simulate "stop" waiting in stdin.
        info = SearchInfo()
        info.stdin_enabled = 1
        misc.msvcrt = None
        misc.InputWaiting = lambda: True
        sys.stdin = io.StringIO("stop\n")

        misc.ReadInput(info)
        stop_ok = info.stopped == 1 and info.quit == 0
        print(f"ReadInput handles stop: {'PASS' if stop_ok else 'FAIL'}")

        # 2) Simulate "quit" waiting in stdin.
        info2 = SearchInfo()
        info2.stdin_enabled = 1
        sys.stdin = io.StringIO("quit\n")

        misc.ReadInput(info2)
        quit_ok = info2.stopped == 1 and info2.quit == 1
        print(f"ReadInput handles quit: {'PASS' if quit_ok else 'FAIL'}")

        # 3) CheckUp integrates both time and input checks.
        info3 = SearchInfo()
        info3.stdin_enabled = 1
        info3.time_set = 1
        info3.stop_time = 0  # definitely expired
        sys.stdin = io.StringIO("quit\n")

        search.CheckUp(info3)
        checkup_ok = info3.stopped == 1 and info3.quit == 1
        print(f"CheckUp integrates stop/quit polling: {'PASS' if checkup_ok else 'FAIL'}")

    finally:
        misc.msvcrt = old_msvcrt
        misc.InputWaiting = old_input_waiting
        sys.stdin = old_stdin


def main():
    print("Initializing Hydra 1.0")
    AllInit()
    run_latest_test()


if __name__ == "__main__":
    main()
