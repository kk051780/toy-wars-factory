"""Bounded scheduler for isolated Native CLI cases, not an acceptance gate."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sys


def hosted_workers():
    # Keep Windows/local behavior exactly serial. Opt in only on a hosted Linux
    # runner with demonstrable CPU and memory headroom. Uncertain -> serial.
    if sys.platform != "linux" or os.environ.get("GITHUB_ACTIONS") != "true":
        return 1
    try:
        if len(os.sched_getaffinity(0)) < 2:
            return 1
        entries = Path("/proc/self/cgroup").read_text().splitlines()
        relative, = (line.split(":", 2)[2] for line in entries if line.startswith("0::"))
        root = Path("/sys/fs/cgroup")
        group = root / relative.lstrip("/")
        if not group.is_relative_to(root) or not group.is_dir():
            return 1
        available, = (int(line.split()[1]) * 1024 for line in
                      Path("/proc/meminfo").read_text().splitlines()
                      if line.startswith("MemAvailable:"))
        if available < 2 * 1024**3:
            return 1
        # Honor ancestor limits as well as the current cgroup. No speculative
        # parallelism if the host's quota or memory information is unavailable.
        for path in (group, *group.parents):
            if not path.is_relative_to(root):
                break
            quota, period = (path / "cpu.max").read_text().split()
            if quota != "max" and int(quota) < 2 * int(period):
                return 1
            limit = (path / "memory.max").read_text().strip()
            if limit != "max" and int(limit) - int((path / "memory.current").read_text()) < 2 * 1024**3:
                return 1
        return 2
    except (OSError, ValueError, AttributeError):
        return 1


def run_cases(cases, run_case, *, workers=None):
    """Preserve one invocation per case, original failure order, and serial fallback.

    Caller owns the binary checks, timeouts, unique evidence filenames and receipts.
    Cases must be isolated subprocesses, with no shared mutable fixture/output.
    No new batch starts after an error; any already-running sibling is joined.
    """
    names = tuple(cases)
    if len(set(names)) != len(names):
        raise ValueError("NATIVE_CASE_NAMES_NOT_UNIQUE")
    workers = hosted_workers() if workers is None else workers
    if type(workers) is not int or workers not in (1, 2):
        raise ValueError("NATIVE_CASE_WORKER_LIMIT")
    if not names:
        return
    # Fail on first case before doing any parallel work; useful for new adapters.
    run_case(names[0])
    if workers == 1:
        for case in names[1:]:
            run_case(case)
        return
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="native-case") as pool:
        for index in range(1, len(names), 2):
            futures = [pool.submit(run_case, case) for case in names[index:index + 2]]
            try:
                for future in futures:
                    future.result()
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
