#!/usr/bin/env python3
"""Reproduce, verify, and inverse one Guardian repair with pinned current69 inputs.

This is an isolated source/native experiment, not an official profile producer.
The original current-RC runner builds Luau from its pinned, verified source tree.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from apply_role_snapshot import apply, identity

HERE = Path(__file__).resolve().parent
PACKAGE = ("apply_role_snapshot.py", "INPUT_LOCK.json", "case.luau",
           "fixture_boundary.luau", "run.py", "README.md")


def require(ok, reason):
    if not ok:
        raise ValueError("GQ815_ROLE_" + reason)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def record_failure(owned_output, exc):
    """Write only inside the directory this invocation exclusively created."""
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
                       "official_rc_adopted": False}, output, indent=2, sort_keys=True)
            output.write("\n")
    except OSError:
        # Do not overwrite an existing record or hide the original gate error.
        pass
    finally:
        if directory is not None:
            os.close(directory)


def snapshot(root):
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "SOURCE_SYMLINK")
        if path.is_file():
            require(path.suffix == ".luau", "EXTRA_SOURCE_FILE")
            result[path.relative_to(root).as_posix()] = identity(path.read_bytes())
    return result


def load_native(native, lock):
    path = native / "run_profile.py"
    require(identity(path.read_bytes()) == lock["original_native_runner"], "ORIGINAL_RUNNER_DRIFT")
    require(identity((native / "INPUT_LOCK.json").read_bytes()) == lock["original_native_lock"],
            "ORIGINAL_LOCK_DRIFT")
    spec = importlib.util.spec_from_file_location("original_union22_native", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_lock = module.load_lock()
    module.fixture_snapshot(original_lock)
    return module, original_lock


def assemble_role(root, native, lock, scenario):
    code = b"".join((native / "fixtures" / name).read_bytes() + b"\n"
                    for name in lock["fixture_order"])
    code += (HERE / "fixture_boundary.luau").read_bytes() + b"\n"
    ranges = {}
    for module in lock["modules_in_load_order"]:
        rel = "ServerScriptService/EGGRUMBLE_" + module + ".luau"
        raw = (root / rel).read_bytes()
        if module == "LobbyCastleModesPreview.server":
            code += b"\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n"
        else:
            code += f"\nloadingModule='{module}'\n".encode()
            line = code.count(b"\n") + 3
            code += f"fullSourceRanges.{module}={{first={line},last={line+raw.count(bytes([10]))}}}\n".encode()
            code += f"dependencies.EGGRUMBLE_{module}=(function()\n".encode()
            require(code.count(b"\n") + 1 == line, "SOURCE_LINE_RANGE")
        start = len(code)
        code += raw
        ranges[rel] = {"start": start, "end": len(code), **identity(raw)}
        code += b"\nend)()end\n" if module == "LobbyCastleModesPreview.server" else b"\nend)()\n"
    code += f"\nlocal ROLE_CASE='{scenario}'\n".encode() + (HERE / "case.luau").read_bytes()
    require(len(ranges) == 32, "FULL_BODY_COUNT")
    for rel, row in ranges.items():
        require(code[row["start"]:row["end"]] == (root / rel).read_bytes(), "FULL_BODY_CHANGED")
    return code, ranges


def execute(binary, code, ranges, destination, names, expected_failures, error_marker=None):
    destination.mkdir()
    program = destination / "generated.luau"
    program.write_bytes(code)
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(binary), str(program)], capture_output=True, timeout=90)
    (destination / "stdout.log").write_bytes(result.stdout)
    (destination / "stderr.log").write_bytes(result.stderr)
    lines = [line for line in result.stdout.decode("utf-8").splitlines() if line.startswith("CASE\t")]
    rows = [line.split("\t", 3) for line in lines]
    vector_ok = (all(len(row) == 4 for row in rows)
                 and [row[1] for row in rows] == names
                 and all(row[2] == ("FAIL" if row[1] in expected_failures else "PASS") for row in rows))
    process_ok = (result.returncode == (1 if expected_failures else 0)
                  and ((error_marker.encode() in result.stderr) if expected_failures else not result.stderr))
    receipt = {"started_at_utc": started, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
               "exit": result.returncode, "expected_failure_names": expected_failures,
               "exact_expected_vector": vector_ok, "expected_process_result": process_ok,
               "cases": lines, "generated": identity(code), "full_body_count": len(ranges),
               "full_body_ranges": ranges, "stdout": identity(result.stdout), "stderr": identity(result.stderr)}
    write_json(destination / "receipt.json", receipt)
    require(program.read_bytes() == code and vector_ok and process_ok, "CASE_VECTOR:" + destination.name)
    print(destination.name + ": " + str(len(rows)) + " exact cases; "
          + ("EXPECTED_BASELINE_RED" if expected_failures else "PASS"), flush=True)
    return {"receipt": identity((destination / "receipt.json").read_bytes()),
            "case_count": len(rows), "expected_failure_count": len(expected_failures), "exit": result.returncode}


def compile_sources(compiler, source, output, module):
    records = {}
    for rel in sorted(snapshot(source)):
        result = subprocess.run([str(compiler), "--text", str(source / rel)],
                                capture_output=True, env=module.clean_environment(), timeout=30)
        records[rel] = {"exit": result.returncode, "stdout": identity(result.stdout),
                        "stderr": result.stderr.decode("utf-8", errors="replace")}
    write_json(output, records)
    require(len(records) == 69 and all(row["exit"] == 0 for row in records.values()), "NATIVE_COMPILE")


def run(args):
    lock = json.loads((HERE / "INPUT_LOCK.json").read_text())
    require(lock["schema"] == "GQ815_CURRENT69_GUARDIAN_ROLE_SESSION_V1", "LOCK_SCHEMA")
    root, rc, output, build, luau_source = [path.resolve() for path in
        (args.sources, args.rc_root, args.output, args.build_dir, args.luau_source)]
    require(not output.exists() and not build.exists(), "NEW_OUTPUT_AND_BUILD_REQUIRED")
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for a in (output, build) for b in (root, rc, luau_source)), "DIRECTORY_OVERLAP")
    require(not output.is_relative_to(build) and not build.is_relative_to(output), "OUTPUT_BUILD_OVERLAP")
    original_snapshot = snapshot(root)
    require(original_snapshot == lock["sources"] and len(original_snapshot) == 69, "OFFICIAL69_IDENTITY")
    package_before = {name: identity((HERE / name).read_bytes()) for name in PACKAGE}
    require(all(package_before[name] == expected for name, expected in lock["package_cases"].items()),
            "INDEPENDENT_CASE_DRIFT")
    native = rc / lock["native_relative_path"]
    module, original_lock = load_native(native, lock)
    output.mkdir(parents=True)
    created = output.stat()
    args.owned_output = (output, created.st_dev, created.st_ino)
    for name in PACKAGE:
        shutil.copyfile(HERE / name, output / name)
    tool_output = output / "toolchain"
    tool_output.mkdir()
    binary, built, tree_before = module.build_repl(luau_source, build, tool_output, original_lock,
        args.cmake, args.ninja, args.git, args.cc, args.cxx)
    module.command_log([args.cmake, "--build", build, "--target", "Luau.Compile.CLI", "--parallel", "2"],
                       tool_output, "compile_target", 900)
    compiler = build / "luau-compile"
    original = (root / lock["guardian"]["path"]).read_bytes()
    candidate = apply(original)
    restored = apply(candidate, reverse=True)
    require(restored == original, "INVERSE_NOT_EXACT")
    rejected = []
    for name, raw in (("already_applied", candidate), ("unrelated_append", original + b"\n"),
                      ("truncated", original[:-1])):
        try:
            apply(raw)
        except ValueError:
            rejected.append(name)
    require(len(rejected) == 3, "PATCH_FAIL_CLOSED")
    (output / "candidate_guardian.luau").write_bytes(candidate)
    (output / "restored_guardian.luau").write_bytes(restored)
    results = {}
    with tempfile.TemporaryDirectory(prefix="gq815-role-verification-") as temporary:
        selected = Path(temporary) / "sources"
        shutil.copytree(root, selected)
        for variant, body in (("baseline", original), ("candidate", candidate), ("inverse", restored)):
            (selected / lock["guardian"]["path"]).write_bytes(body)
            expected = dict(original_snapshot)
            expected[lock["guardian"]["path"]] = identity(body)
            require(snapshot(selected) == expected, "ONLY_GUARDIAN_MAY_CHANGE")
            if variant != "inverse":
                compile_sources(compiler, selected, output / (variant + "_compile69.json"), module)
            for scenario, contract in lock["role_cases"].items():
                code, ranges = assemble_role(selected, native, lock, scenario)
                failures = [] if variant == "candidate" else contract["baseline_fail_names"]
                key = variant + "_" + scenario
                results[key] = execute(binary, code, ranges, output / key, contract["expected_names"],
                                       failures, contract["baseline_error"])
            for suite in lock["official_regressions"]:
                code, _, ranges = module.assemble(selected, original_lock, suite)
                key = variant + "_" + suite
                results[key] = execute(binary, code, ranges, output / key,
                    original_lock["suites"][suite]["expected_case_names"], [])
            require(snapshot(selected) == expected, "SELECTED_SOURCES_MUTATED")
    require(snapshot(root) == original_snapshot, "ORIGINAL69_MUTATED")
    require({name: identity((HERE / name).read_bytes()) for name in PACKAGE} == package_before, "PACKAGE_MUTATED")
    module.fixture_snapshot(original_lock)
    require(identity(binary.read_bytes()) == built["binary_before_suites"], "NATIVE_BINARY_CHANGED")
    require(module.verify_clean_source(luau_source, Path(built["tools"]["git"]["path"]),
                                      original_lock["toolchain"]) == tree_before, "LUAU_SOURCE_CHANGED")
    built["binary_after_suites"] = identity(binary.read_bytes())
    built["compile_binary"] = identity(compiler.read_bytes())
    write_json(tool_output / "receipt.json", built)
    receipt = {"schema": "GQ815_ROLE_SESSION_SOURCE_NATIVE_RESULT_V1", "status": "PASS_ISOLATED_SOURCE_NATIVE",
               "official_rc_input": lock["official_rc"], "official_rc_adopted": False,
               "guardian": lock["guardian"], "other68_byte_exact": True, "inverse_exact": True,
               "package": package_before, "source69_unchanged": True, "results": results,
               "negative_patch_inputs_rejected": rejected,
               "toolchain": identity((tool_output / "receipt.json").read_bytes()),
               "studio": "NOT_TESTED", "android": "NOT_TESTED", "fun": "NOT_TESTED",
               "art": "ART_NO_GO", "limitations": lock["limitations"]}
    write_json(output / "RESULT.json", receipt)
    print(json.dumps({"status": receipt["status"], "guardian": lock["guardian"],
                      "native_suites": len(results), "official_rc_adopted": False}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sources", "rc-root", "output", "build-dir", "luau-source"):
        parser.add_argument("--" + name, required=True, type=Path)
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
