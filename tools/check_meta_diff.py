"""Trusted-base scope for one daily system improvement; protected policy stays fixed."""
import argparse
import fnmatch
import json
from pathlib import PurePosixPath
from check_auto_diff import changed_entries


def violations(entries, policy):
    meta = policy["system_review"]
    errors, implementation = [], False
    for status, path in entries:
        parts = PurePosixPath(path).parts
        if path.startswith("/") or ".." in parts or "\\" in path:
            errors.append("unsafe path: " + path)
            continue
        if path in meta["allowed_tool_paths"] and status == "M":
            implementation = True
            continue
        if (status == "A" and PurePosixPath(path).parent.as_posix() == "tests" and
                fnmatch.fnmatchcase(path, "tests/test_system_*.py")):
            implementation = True
            continue
        if (status == "A" and PurePosixPath(path).parent.as_posix() == "history" and
                fnmatch.fnmatchcase(path, policy["new_history_pattern"])):
            continue
        if path in meta["allowed_document_paths"] and status in ("A", "M"):
            continue
        if status == "A" and PurePosixPath(path).parent.as_posix() == "docs/research" and path.endswith(".md"):
            continue
        errors.append("outside system-review scope: " + status + " " + path)
    if not implementation:
        errors.append("research-only output belongs in the coordinator report, not an implementation PR")
    if not any(status == "A" and path.startswith("tests/test_system_") and path.endswith(".py") for status, path in entries):
        errors.append("system improvement requires a new regression test")
    return errors


def main():
    parser = argparse.ArgumentParser()
    for name in ("policy", "base", "head", "branch"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    policy = json.loads(open(args.policy, encoding="utf-8").read())
    meta = policy["system_review"]
    from repair_control import canonical_id
    if not meta.get("enabled") or not args.branch.startswith(meta["branch_prefix"]):
        raise SystemExit("FAIL: system review disabled or wrong namespace")
    canonical_id(args.branch[len(meta["branch_prefix"]):])
    errors = violations(changed_entries(args.base, args.head), policy)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: system review scope")


if __name__ == "__main__":
    main()
