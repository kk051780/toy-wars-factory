"""Trusted-base scope for one daily system improvement; protected policy stays fixed."""
import argparse
import fnmatch
import json
import re
from pathlib import PurePosixPath
from check_auto_diff import changed_entries


def safe_module_extension(before, after):
    old = before.get("additional_source_paths", [])
    new = after.get("additional_source_paths", [])
    if (not isinstance(new, list) or any(not isinstance(p, str) for p in new) or
            len(set(new)) != len(new) or not set(old).issubset(new)):
        return False
    if {k: v for k, v in before.items() if k != "additional_source_paths"} != {k: v for k, v in after.items() if k != "additional_source_paths"}:
        return False
    reserved = set(before["source_paths"]) | {"src/ToyWarsSmokeTest.server.lua"}
    return all(isinstance(p, str) and re.fullmatch(r"src/[A-Za-z0-9_]+(?:\.(?:server|client))?\.lua", p) and p not in reserved for p in new)


def violations(entries, policy, module_extension=None):
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
        if (status == "M" and path == "config/autonomous_repair.json" and module_extension and
                safe_module_extension(*module_extension) and ("M", "tools/build_installer.py") in entries):
            continue
        if status == "A" and PurePosixPath(path).parent.as_posix() == "tools" and fnmatch.fnmatchcase(path, "tools/system_*.py"):
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
    entries = changed_entries(args.base, args.head)
    extension = None
    if ("M", "config/autonomous_repair.json") in entries:
        import subprocess
        after = json.loads(subprocess.check_output(["git", "show", args.head + ":config/autonomous_repair.json"], text=True))
        extension = (policy, after)
    errors = violations(entries, policy, module_extension=extension)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: system review scope")


if __name__ == "__main__":
    main()
