#!/usr/bin/env python3
"""Run the frozen cloak matrix against two pinned Guardian bases, without RC adoption.

Builds a fresh F46 Luau Repl through the verified H93 native helper. The existing
233684a role_session/role_los package, H93 sources and all fixtures stay read-only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
INPUT_LOCK_SHA256 = "f37a9500da30d08fcd1baf30fec340d86733b18fd9c9d34f5e5917f271347dcb"
PACKAGE = {"apply_stealth_target.py", "INPUT_LOCK.json", "case.luau",
           "fixture_boundary.luau", "run.py", "README.md"}


def require(ok, reason):
    if not ok:
        raise ValueError("GQ815_STEALTH_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file() and stat.S_ISREG(path.stat().st_mode),
            "REGULAR_FILE_REQUIRED:" + str(path))
    return path.read_bytes()


def safe_root(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), "SYMLINK_ROOT")
    return path.resolve()


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def write_json(path, value):
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True, ensure_ascii=False)
        output.write("\n")


def record_failure(owned_output, exc):
    if owned_output is None:
        return
    path, device, inode = owned_output
    directory = None
    try:
        directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        current = os.fstat(directory)
        if (current.st_dev, current.st_ino) != (device, inode):
            return
        descriptor = os.open("FAILED.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
        with os.fdopen(descriptor, "w") as output:
            json.dump({"status": "FAIL", "error": str(exc), "error_type": type(exc).__name__,
                       "source_status": "PINNED_H93_SOURCE_CANDIDATE_ONLY",
                       "official_rc_adopted": False}, output, indent=2, sort_keys=True)
            output.write("\n")
    except OSError:
        pass
    finally:
        if directory is not None:
            os.close(directory)


def directory_snapshot(root, luau_only=False):
    require(root.is_dir(), "INPUT_DIRECTORY")
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "INPUT_SYMLINK")
        if path.is_file():
            require(not luau_only or path.suffix == ".luau", "EXTRA_SOURCE_FILE")
            result[path.relative_to(root).as_posix()] = identity(read(path))
        else:
            require(path.is_dir(), "SPECIAL_INPUT_FILE")
    return result


def package_snapshot(lock):
    require({path.name for path in HERE.iterdir()} == PACKAGE, "SIX_PACKAGE_FILES_REQUIRED")
    snapshot = {name: identity(read(HERE / name)) for name in sorted(PACKAGE)}
    require(snapshot["INPUT_LOCK.json"]["sha256"] == INPUT_LOCK_SHA256, "INPUT_LOCK_CHANGED")
    require(set(lock["package_pins"]) == PACKAGE - {"INPUT_LOCK.json", "run.py"}, "PACKAGE_PIN_SET")
    require(all(snapshot[name] == pin for name, pin in lock["package_pins"].items()), "PACKAGE_INPUT_DRIFT")
    return snapshot


def frozen_snapshot(pr_root, lock):
    actual = {}
    prefix = lock["existing_package_relative_path"]
    for folder in ("role_session", "role_los"):
        base = pr_root / prefix / folder
        for relative, pin in directory_snapshot(base).items():
            actual[(Path(prefix) / folder / relative).as_posix()] = pin
    require(actual == lock["existing_pr_files"] and len(actual) == 12, "EXISTING_TWELVE_FILES_DRIFT")
    return actual


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "MODULE_LOADER")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_native(native, lock):
    before = directory_snapshot(native)
    require(before == lock["h93_native_files"], "H93_NATIVE_FILES_DRIFT")
    module = load_module("gq815_stealth_verified_h93_native", native / "run_profile.py")
    native_lock = module.load_lock()
    module.fixture_snapshot(native_lock)
    require(native_lock["sources"] == lock["sources"] and native_lock["toolchain"] == lock["toolchain"],
            "NATIVE_H93_SOURCE_OR_TOOLCHAIN_CONTRACT")
    return module, native_lock, before


def assemble(sources, native, pr_root, lock, guardian, role, mode):
    code = b""
    for fixture in lock["execution_fixture_order"]:
        root = native if fixture["root"] == "h93_native" else pr_root
        raw = read(root / fixture["path"])
        require(identity(raw) == fixture["identity"], "EXECUTION_FIXTURE_DRIFT")
        code += raw + b"\n"
    ranges = {}
    for name in lock["modules_in_load_order"]:
        relative = "ServerScriptService/EGGRUMBLE_" + name + ".luau"
        raw = guardian if relative == lock["guardian"]["path"] else sources[relative]
        if name == "LobbyCastleModesPreview.server":
            code += b"\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n"
            label = "Host"
        else:
            code += ("\nloadingModule='" + name + "'\n").encode()
            first = code.count(b"\n") + 3
            code += f"fullSourceRanges.{name}={{first={first},last={first+raw.count(bytes([10]))}}}\n".encode()
            code += ("dependencies.EGGRUMBLE_" + name + "=(function()\n").encode()
            require(code.count(b"\n") + 1 == first, "SOURCE_LINE_RANGE")
            label = name
        first_byte, first_line = len(code), code.count(b"\n") + 1
        code += raw
        ranges[label] = {"path": relative, "byte_start": first_byte, "byte_end_exclusive": len(code),
                         "line_first": first_line, "line_last": first_line + raw.count(b"\n"), **identity(raw)}
        code += b"\nend)()end\n" if label == "Host" else b"\nend)()\n"
    expected = lock["guardian_roles"][role]
    code += (f"\nlocal GUARDIAN_ROLE='{role}'\n"
             f"local GUARDIAN_EXPECT={{hp={expected['hp']},damage={expected['damage']}}}\n").encode()
    code += read(HERE / "fixture_boundary.luau") + b"\n"
    code += ("\nlocal MODE='" + mode + "'\n").encode() + read(HERE / "case.luau")
    require(len(ranges) == 28, "FULL_BODY_COUNT")
    for row in ranges.values():
        raw = guardian if row["path"] == lock["guardian"]["path"] else sources[row["path"]]
        require(code[row["byte_start"]:row["byte_end_exclusive"]] == raw, "FULL_BODY_CHANGED")
    return code, ranges


def execute(binary, environment, code, ranges, destination, contract):
    destination.mkdir(parents=True)
    program = destination / "generated.luau"
    with program.open("xb") as output:
        output.write(code)
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(binary), str(program)], capture_output=True, env=environment, timeout=90)
    (destination / "stdout.log").write_bytes(result.stdout)
    (destination / "stderr.log").write_bytes(result.stderr)
    stdout = result.stdout.decode("utf-8")
    cases = [line for line in stdout.splitlines() if line.startswith("CASE\t")]
    rows = [line.split("\t", 3) for line in cases]
    vector_ok = (all(len(row) == 4 for row in rows)
                 and [[row[1], row[2]] for row in rows] == contract["expected_case_vector"])
    expected_red = contract["expected_exit"] == 1
    marker = contract["baseline_error"]
    process_ok = (result.returncode == contract["expected_exit"]
                  and ((marker.encode() in result.stderr and marker in cases[-1])
                       if expected_red and cases else (not expected_red and not result.stderr)))
    receipt = {"started_at_utc": started, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
               "group": contract["group"], "role": contract["role"], "mode": contract["mode"],
               "native_exit_code": result.returncode, "expected_exit_code": contract["expected_exit"],
               "expected_baseline_red": expected_red, "exact_case_vector": vector_ok,
               "expected_process_result": process_ok, "cases": cases,
               "observations": [line for line in stdout.splitlines()
                                if line.startswith(("OBSERVATION\t", "TRACE\tNINJA_B"))],
               "generated": identity(code), "full_source_body_count": len(ranges),
               "full_source_ranges": ranges, "stdout": identity(result.stdout), "stderr": identity(result.stderr)}
    write_json(destination / "receipt.json", receipt)
    require(read(program) == code and vector_ok and process_ok, "CASE_VECTOR:" + str(destination))
    print("/".join((contract["group"], contract["role"], contract["mode"])) + ": "
          + ("EXPECTED_BASELINE_RED" if expected_red else "PASS"), flush=True)
    return {"group": contract["group"], "role": contract["role"], "mode": contract["mode"],
            "expected_baseline_red": expected_red, "native_exit_code": result.returncode,
            "receipt": identity(read(destination / "receipt.json"))}


def run(args):
    raw_lock = read(HERE / "INPUT_LOCK.json")
    require(identity(raw_lock)["sha256"] == INPUT_LOCK_SHA256, "INPUT_LOCK_IDENTITY")
    lock = strict_json(raw_lock)
    require(lock["schema"] == "GQ815_PINNED_H93_GUARDIAN_STEALTH_TARGET_V1", "LOCK_SCHEMA")
    require(re.fullmatch(r"[0-9a-f]{40}", args.latest_rc_head) is not None, "OBSERVED_LATEST_RC_SHA_REQUIRED")
    root, rc, pr_root, luau_source, output, build = [safe_root(path) for path in
        (args.sources, args.rc_root, args.pr_root, args.luau_source, args.output, args.build_dir)]
    protected = (root, rc, pr_root, luau_source, safe_root(HERE))
    require(not output.exists() and not build.exists(), "NEW_OUTPUT_AND_BUILD_REQUIRED")
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for a in (output, build) for b in protected), "DIRECTORY_OVERLAP")
    require(not output.is_relative_to(build) and not build.is_relative_to(output), "OUTPUT_BUILD_OVERLAP")
    source_before = directory_snapshot(root, luau_only=True)
    require(source_before == lock["sources"] and len(source_before) == 69, "PINNED_H93_69_IDENTITY")
    package_before = package_snapshot(lock)
    frozen_before = frozen_snapshot(pr_root, lock)
    native = rc / lock["native_relative_path"]
    native_module, native_lock, native_before = load_native(native, lock)
    repair = load_module("gq815_stealth_exact_294", HERE / "apply_stealth_target.py")
    require(repair.IDENTITIES == lock["guardian"]["variants"], "GUARDIAN_HELPER_IDENTITIES")
    old_path = pr_root / lock["existing_package_relative_path"] / "role_los" / "apply_existing_repairs.py"
    old_repair = load_module("gq815_stealth_frozen233_composer", old_path)
    sources = {relative: read(root / relative) for relative in lock["sources"]}
    require({relative: identity(raw) for relative, raw in sources.items()} == source_before, "SOURCE_READ_DRIFT")
    h93 = sources[lock["guardian"]["path"]]
    pr796 = old_repair.transform(h93, "baseline", "combined")
    require(identity(pr796) == lock["guardian"]["variants"]["pr796"]["input"], "FROZEN_PR796_COMPOSITION")
    require(old_repair.transform(pr796, "combined", "baseline") == h93, "FROZEN_PR796_INVERSE")
    variants = {"baseline_h93": h93, "baseline_pr796": pr796}
    transforms = {}
    for base, original in (("h93", h93), ("pr796", pr796)):
        candidate = repair.apply(original, base)
        restored = repair.apply(candidate, base, inverse=True)
        require(restored == original, "INVERSE_NOT_BYTE_EXACT:" + base)
        variants["candidate_" + base] = candidate
        transforms[base] = {"input": identity(original), "candidate": identity(candidate),
                            "restored": identity(restored), "delta_bytes": len(candidate) - len(original),
                            "three_frozen_replacements": True, "inverse_byte_exact": True}
    output.mkdir(parents=True)
    created = output.stat()
    args.owned_output = (output, created.st_dev, created.st_ino)
    for name in sorted(PACKAGE):
        shutil.copyfile(HERE / name, output / name)
    write_json(output / "GUARDIAN_TRANSFORMS.json", transforms)
    (output / "original_pr796_guardian.luau").write_bytes(pr796)
    for base in ("h93", "pr796"):
        (output / ("candidate_" + base + "_guardian.luau")).write_bytes(variants["candidate_" + base])
        (output / ("restored_" + base + "_guardian.luau")).write_bytes(
            repair.apply(variants["candidate_" + base], base, inverse=True))
    tool_output = output / "toolchain"
    tool_output.mkdir()
    binary, built, tree_before = native_module.build_repl(luau_source, build, tool_output, native_lock,
        args.cmake, args.ninja, args.git, args.cc, args.cxx)
    binary_pin = identity(read(binary))
    require(binary_pin == built["binary_before_suites"], "NEW_NATIVE_BINARY_IDENTITY")
    results = []
    for contract in lock["matrix"]:
        require(package_snapshot(lock) == package_before, "PACKAGE_MUTATED")
        require(frozen_snapshot(pr_root, lock) == frozen_before, "EXISTING_PR_PACKAGE_MUTATED")
        require(directory_snapshot(native) == native_before, "H93_NATIVE_MUTATED")
        require(directory_snapshot(root, luau_only=True) == source_before, "SOURCE69_MUTATED")
        require(identity(read(binary)) == binary_pin, "NATIVE_BINARY_MUTATED")
        group, role, mode = (contract[key] for key in ("group", "role", "mode"))
        code, ranges = assemble(sources, native, pr_root, lock, variants[group], role, mode)
        destination = output / "matrix" / group / role / mode
        row = execute(binary, native_module.clean_environment(), code, ranges, destination, contract)
        row["receipt_path"] = (destination / "receipt.json").relative_to(output).as_posix()
        results.append(row)
    require(len(results) == 40, "EXACT_FORTY_NATIVE_PROCESSES")
    require(sum(row["expected_baseline_red"] for row in results) == 8, "EXACT_EIGHT_BASELINE_RED")
    require(sum(row["group"].startswith("candidate_") and row["native_exit_code"] == 0
                for row in results) == 26, "EXACT_TWENTY_SIX_CANDIDATE_PASS")
    require(len({(row["role"], row["mode"]) for row in results}) == 13, "EXACT_THIRTEEN_SCENARIOS")
    require(package_snapshot(lock) == package_before, "PACKAGE_MUTATED_AFTER_MATRIX")
    require(frozen_snapshot(pr_root, lock) == frozen_before, "EXISTING_PR_PACKAGE_MUTATED_AFTER_MATRIX")
    require(directory_snapshot(root, luau_only=True) == source_before, "SOURCE69_MUTATED_AFTER_MATRIX")
    require(directory_snapshot(native) == native_before, "H93_NATIVE_MUTATED_AFTER_MATRIX")
    native_module.fixture_snapshot(native_lock)
    require(identity(read(binary)) == binary_pin, "NATIVE_BINARY_MUTATED_AFTER_MATRIX")
    require(native_module.verify_clean_source(luau_source, Path(built["tools"]["git"]["path"]),
                                             native_lock["toolchain"]) == tree_before, "LUAU_SOURCE_MUTATED")
    built["binary_after_suites"] = identity(read(binary))
    write_json(tool_output / "receipt.json", built)
    result = {"schema": "GQ815_GUARDIAN_STEALTH_SOURCE_NATIVE_RESULT_V1",
              "status": "PASS_PINNED_SOURCE_NATIVE_MATRIX",
              "source_status": "PINNED_H93_SOURCE_CANDIDATE_ONLY", "pinned_source_head": lock["pinned_source_head"],
              "observed_latest_rc_head": args.latest_rc_head, "latest_rc_is_pinned_source": args.latest_rc_head == lock["pinned_source_head"],
              "latest_rc_observation_source": "caller supplied; runner performs no network lookup",
              "source_artifact": lock["source_artifact"], "existing_pr_head": lock["existing_pr_head"],
              "official_rc_adopted": False, "registered_approval": False, "whole_workflow_green": False,
              "unique_scenarios": 13, "native_processes": 40, "expected_baseline_red_processes": 8,
              "candidate_success_processes": 26, "results": results, "source69_unchanged": True,
              "other27_loaded_bodies_exact_h93": True, "existing12_files_unchanged": True,
              "case_and_fixture_boundary_byte_exact": True, "inputs_unchanged_after_matrix": True,
              "package": package_before, "existing_pr_files": frozen_before, "h93_native_files": native_before,
              "transforms": identity(read(output / "GUARDIAN_TRANSFORMS.json")),
              "toolchain": identity(read(tool_output / "receipt.json")),
              "studio": "NOT_TESTED", "android": "NOT_TESTED", "fun": "NOT_TESTED",
              "limitations": lock["limitations"]}
    write_json(output / "RESULT.json", result)
    print(json.dumps({key: result[key] for key in ("status", "source_status", "unique_scenarios",
          "native_processes", "expected_baseline_red_processes", "candidate_success_processes",
          "official_rc_adopted")}, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sources", "rc-root", "luau-source", "build-dir", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--pr-root", default=HERE.parents[2], type=Path)
    parser.add_argument("--latest-rc-head", required=True)
    for name, default in (("cmake", "cmake"), ("ninja", "ninja"), ("git", "git"), ("cc", "cc"), ("cxx", "c++")):
        parser.add_argument("--" + name, default=shutil.which(default), type=Path)
    args = parser.parse_args()
    args.owned_output = None
    try:
        run(args)
    except Exception as exc:
        record_failure(args.owned_output, exc)
        raise


if __name__ == "__main__":
    main()
