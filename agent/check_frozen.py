"""Checks a frozen agent (`just agent freeze`) runs: the probe answers, and the worker starts
a job process and stops with its whole group when the app's pipe closes. It never reaches
LiveKit: the worker is pointed at a local port where nothing listens.

    python check_frozen.py dist/bomby-agent/bomby-agent

CI runs it on the signed agent inside the app (.github/workflows/release.yml), where it
also shows that hardened runtime loads every library.
"""

import os
import queue
import signal
import subprocess
import sys
import threading
import time
from typing import IO

# A job process on macOS; on Windows, LiveKit runs jobs in a thread of the worker.
READY_LINE = (
    "job runner initialized" if sys.platform == "win32" else "process initialized"
)
READY_TIMEOUT_S = 90
EXIT_TIMEOUT_S = 10


def check_probe(program: str) -> None:
    out = subprocess.run(
        [program, "probe", '{"agents": {}}'],
        capture_output=True,
        text=True,
        timeout=READY_TIMEOUT_S,
        check=True,
    ).stdout.strip()
    if out != "{}":
        raise SystemExit(f"The probe answered {out!r}, not {{}}")
    print("probe: answers")


WINDOWS = sys.platform == "win32"


def group_size(pgid: int) -> int:
    # pgrep exits 1 when it finds none, which is the answer, not a failure.
    found = subprocess.run(
        ["pgrep", "-g", str(pgid)], capture_output=True, text=True, check=False
    )
    return len(found.stdout.split())


def tree(root: int) -> set[int]:
    """Windows has no process groups: `root` and every process under it, by parent pid."""
    listed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | "
            + 'ForEach-Object { "$($_.ProcessId) $($_.ParentProcessId)" }',
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    parents = {int(pid): int(ppid) for pid, ppid in zip(listed[::2], listed[1::2])}
    found = {root}
    while more := {p for p, pp in parents.items() if pp in found} - found:
        found |= more
    return found


def alive(pids: set[int]) -> set[int]:
    """Which of `pids` still run (Windows)."""
    listed = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True
    ).stdout
    running = {int(row.split('","')[1]) for row in listed.splitlines() if '","' in row}
    return pids & running


def left_running(worker: int, tracked: set[int]) -> int:
    """How many of the worker's processes are still running."""
    return len(alive(tracked)) if WINDOWS else group_size(worker)


def check_worker(program: str) -> None:
    env = os.environ | {
        "LIVEKIT_URL": "ws://127.0.0.1:9",
        "LIVEKIT_API_KEY": "check",
        "LIVEKIT_API_SECRET": "check",
        "GOOGLE_API_KEY": "check",
        "BOMBY_EXIT_WITH_APP": "1",
    }
    worker = subprocess.Popen(
        [program, "start"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        process_group=None if WINDOWS else 0,
    )
    tracked: set[int] = {worker.pid}
    try:
        assert worker.stdin and worker.stdout
        wait_for_job_process(worker.stdout)
        print("worker: starts a job process")
        if WINDOWS:
            # Once the worker is gone its children have no parent to be found by.
            tracked = tree(worker.pid)

        worker.stdin.close()  # what the app quitting looks like to the worker
        deadline = time.monotonic() + EXIT_TIMEOUT_S
        while left_running(worker.pid, tracked) and time.monotonic() < deadline:
            time.sleep(0.5)
        if left := left_running(worker.pid, tracked):
            raise SystemExit(f"{left} of the worker's processes outlived the app")
        print("worker: stops with the app")
    finally:
        # Whatever happened, nothing of the worker is left running.
        if WINDOWS:
            for pid in alive(tracked):
                _ = subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(pid)], check=False
                )
        elif group_size(worker.pid):
            os.killpg(worker.pid, signal.SIGKILL)
        _ = worker.wait(timeout=EXIT_TIMEOUT_S)


def wait_for_job_process(stdout: IO[str]) -> None:
    """Waits, up to READY_TIMEOUT_S even when the worker goes quiet, for its job process."""
    lines: queue.Queue[str | None] = queue.Queue()

    def read() -> None:
        for line in stdout:
            lines.put(line)
        lines.put(None)  # the worker closed its output

    threading.Thread(target=read, daemon=True).start()
    seen: list[str] = []
    deadline = time.monotonic() + READY_TIMEOUT_S
    while (left := deadline - time.monotonic()) > 0:
        try:
            line = lines.get(timeout=left)
        except queue.Empty:
            break
        if line is None:
            break
        seen.append(line)
        if READY_LINE in line:
            return
    raise SystemExit("The worker started no job process:\n" + "".join(seen[-30:]))


if __name__ == "__main__":
    check_probe(sys.argv[1])
    check_worker(sys.argv[1])
