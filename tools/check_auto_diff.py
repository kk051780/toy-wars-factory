"""Bound scheduled repair PR edits; this does not grant merge or provider access."""
import argparse
import fnmatch
import json
import re
import subprocess
from pathlib import PurePosixPath


def is_worker_branch(branch, policy):
    if not isinstance(branch, str):
        return False
    if branch == policy.get("branch"):
        return True
    prefix = policy.get("branch_prefix")
    suffix = r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
    return isinstance(prefix, str) and bool(prefix) and re.fullmatch(re.escape(prefix) + suffix, branch) is not None


def violations(entries, policy):
    errors = []
    implementation = False
    source_changed = False
    new_test = False
    for status, path in entries:
        parts = PurePosixPath(path).parts
        if path.startswith("/") or ".." in parts or "\\" in path:
            errors.append("unsafe path: " + path)
            continue
        if path in policy["source_paths"] and status == "M":
            implementation = source_changed = True
            continue
        new_native = (PurePosixPath(path).parent.as_posix() == "tests/auto" and
                      fnmatch.fnmatchcase(path, policy["new_native_test_pattern"]))
        new_python = (PurePosixPath(path).parent.as_posix() == "tests" and
                      fnmatch.fnmatchcase(path, policy["new_python_test_pattern"]))
        if status == "A" and (new_native or new_python):
            implementation = new_test = True
            continue
        if (status == "A" and PurePosixPath(path).parent.as_posix() == "history" and
                fnmatch.fnmatchcase(path, policy["new_history_pattern"])):
            continue
        if path == policy["experiment_log"] and status in ("A", "M"):
            continue
        errors.append("outside repair scope: " + status + " " + path)
    if not implementation:
        errors.append("no game source or executable regression test change")
    if source_changed and not new_test:
        errors.append("game source change requires a new regression test")
    return errors


def changed_entries(base, head):
    raw = subprocess.check_output([
        "git", "diff", "--name-status", "--no-renames", "-z", base, head, "--"
    ]).decode("utf-8").split("\0")
    if raw[-1] == "":
        raw.pop()
    if len(raw) % 2:
        raise ValueError("unexpected Git diff format")
    return list(zip(raw[::2], raw[1::2]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--policy", required=True)
    parser.add_argument("--branch")
    args = parser.parse_args()
    with open(args.policy, encoding="utf-8") as file:
        policy = json.load(file)
    if policy.get("enabled") is not True or policy.get("mode") != "DRAFT_PR_ONLY":
        raise SystemExit("FAIL: scheduled repair is disabled or outside draft-only mode")
    if args.branch is not None and not is_worker_branch(args.branch, policy):
        raise SystemExit("FAIL: branch is outside the scheduled repair namespace")
    entries = changed_entries(args.base, args.head)
    errors = violations(entries, policy)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: scheduled repair scope; " + str(len(entries)) + " changed files")


if __name__ == "__main__":
    main()
