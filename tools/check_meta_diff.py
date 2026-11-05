"""Trusted-base scope for one daily system improvement; protected policy stays fixed."""
import argparse
import fnmatch
import json
import re
import subprocess
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



# Trusted-base maintenance admission: never treat PR-author policy as an authority.
_SYSTEM_MODULE = re.compile(r"tools/system_[A-Za-z0-9_]+[.]py\Z")
_NEW_SYSTEM_TEST = re.compile(r"tests/test_system_[A-Za-z0-9_]+[.]py\Z")
_NEW_HISTORY = re.compile(r"history/C[0-9]{5}_[A-Za-z0-9_]+[.]json\Z")


def ordinary_system_modules_at(ref):
    """Read committed 100644 blobs, never the mutable worktree or file claims."""
    if (not isinstance(ref, str) or
            (ref != "HEAD" and not re.fullmatch(r"[0-9a-f]{40}", ref))):
        return set()
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--verify", ref + "^{commit}"],
            stderr=subprocess.DEVNULL, text=True).strip()
        if (not re.fullmatch(r"[0-9a-f]{40}", commit) or
                (ref != "HEAD" and commit != ref)):
            return set()
        raw = subprocess.check_output(
            ["git", "ls-tree", "-r", "-z", commit, "--", "tools/"],
            stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return set()
    safe = set()
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, path_bytes = record.split(b"\t", 1)
            mode, typ, sha = metadata.split(b" ")
            if not re.fullmatch(rb"[0-9a-f]{40}", sha):
                return set()
            path = path_bytes.decode("utf-8", "strict")
        except (ValueError, UnicodeDecodeError):
            return set()
        if (mode == b"100644" and typ == b"blob" and
                _SYSTEM_MODULE.fullmatch(path)):
            safe.add(path)
    return safe


def trusted_base_system_modules(base, trusted_main_ref="refs/remotes/origin/main"):
    """Only existing ordinary modules in an authenticated main ancestor.

    The caller must execute this checker from its trusted-base checkout.
    A PR-head module set supplies mode restrictions, never base authority.
    """
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
        return set()
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, trusted_main_ref],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return set()
    return ordinary_system_modules_at(base)


def violations(entries, policy, module_extension=None, trusted_base_modules=None):
    meta = policy["system_review"]
    errors, implementation, maintenance = [], False, False
    known = trusted_base_modules if isinstance(trusted_base_modules, set) else set()
    for status, path in entries:
        parts = PurePosixPath(path).parts
        if path.startswith("/") or ".." in parts or "\\" in path:
            errors.append("unsafe path: " + path)
            continue
        if path in meta["allowed_tool_paths"] and status == "M":
            implementation = True
            continue
        if status == "M" and _SYSTEM_MODULE.fullmatch(path) and path in known:
            implementation = maintenance = True
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
    if maintenance:
        # The critical checker and the user's accepted tests are never edited.
        new_test = any(status == "A" and _NEW_SYSTEM_TEST.fullmatch(path)
                       for status, path in entries)
        new_history = any(status == "A" and _NEW_HISTORY.fullmatch(path) and
                          fnmatch.fnmatchcase(path, policy["new_history_pattern"])
                          for status, path in entries)
        paths = [p for _, p in entries]
        if len(paths) != len(set(paths)):
            errors.append("duplicate path in maintenance proposal")
        if not new_test or not new_history:
            errors.append("trusted system maintenance requires new regression AND history")
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
    trusted_modules = (trusted_base_system_modules(args.base) &
                       ordinary_system_modules_at(args.head))
    errors = violations(entries, policy, module_extension=extension,
                        trusted_base_modules=trusted_modules)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: system review scope")


if __name__ == "__main__":
    main()
