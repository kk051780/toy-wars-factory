#!/usr/bin/env python3
"""Fixed-HEAD seven-body Native gate. Fresh F46 build is required for CI evidence."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types

sys.dont_write_bytecode = True
HERE = Path(__file__).absolute().parent
PACKAGE = HERE.parent
ROOT = HERE.parents[2]
LOCK_SHA256 = "be6dcffd88e041a5ab51e1591e7c2151c8d4d6b212fee01f9ce71eba59f1eb10"

# Explicit Engine boundary, never a claim to execute a real Roblox Player/Studio.
BOUNDARY = '''-- Native boundary only; fake Instances and Host predicates are not Studio evidence.
local fakePlayers = {}
local nativeTypeof = typeof
local function typeof(value)
    if type(value) == "table" and fakePlayers[value] then return "Instance" end
    return nativeTypeof(value)
end
local factories, modules, loading = {}, {}, {}
local script = {Parent = {WaitForChild = function(_, name) return name end}}
local function require(name)
    assert(type(name) == "string" and factories[name], "unknown sibling module")
    if modules[name] ~= nil then return modules[name] end
    assert(not loading[name], "circular fixture dependency")
    loading[name] = true
    modules[name] = factories[name]()
    loading[name] = nil
    return modules[name]
end
'''


def require(condition, reason):
    if not condition:
        raise ValueError("PERSISTENT_BASE_NATIVE_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)) and path.is_file(), "REGULAR_INPUT")
    return path.read_bytes()


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError("PERSISTENT_BASE_NATIVE_NONFINITE_JSON")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def git_output(git, *args):
    command = [str(git), "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-C", str(ROOT), *args]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    result = subprocess.run(command, capture_output=True, env=env, timeout=60)
    require(result.returncode == 0, "GIT_FAILED:" + " ".join(args))
    return result.stdout


def verify_head(git, expected, lock):
    require(re.fullmatch(r"[0-9a-f]{40}", expected or ""), "EXACT_HEAD_REQUIRED")
    require(git_output(git, "rev-parse", "HEAD").decode().strip() == expected, "HEAD_MISMATCH")
    require(not git_output(git, "status", "--porcelain=v1", "--untracked-files=all"), "WORKTREE_NOT_CLEAN")
    base = lock["base_rc"]
    git_output(git, "merge-base", "--is-ancestor", base, expected)
    rows = git_output(git, "diff", "--no-renames", "--name-status", base, expected).decode().splitlines()
    observed = {}
    for row in rows:
        kind, path = row.split("\t", 1)
        require(kind == "A" and path not in observed, "ONLY_NINE_NEW_PATHS")
        observed[path] = kind
    require(set(observed) == set(lock["repository_files"]) and len(observed) == 9, "EXACT_SCOPE")
    files = {}
    for relative in lock["repository_files"]:
        raw = read(ROOT / relative)
        require(raw == git_output(git, "show", expected + ":" + relative), "PHYSICAL_HEAD_BYTES:" + relative)
        files[relative] = identity(raw)
    for relative, pin in lock["file_pins"].items():
        require(files[relative] == pin, "LOCKED_FILE_CHANGED:" + relative)
    return {"head": expected, "tree": git_output(git, "rev-parse", "HEAD^{tree}").decode().strip(),
            "base_rc": base, "changed_files": files, "only_nine_additions": True, "clean": True}


def command_log(command, output, name, timeout):
    result = subprocess.run([str(x) for x in command], capture_output=True, timeout=timeout)
    (output / (name + ".stdout.log")).write_bytes(result.stdout)
    (output / (name + ".stderr.log")).write_bytes(result.stderr)
    entry = {"command": [str(x) for x in command], "exit": result.returncode,
             "stdout": identity(result.stdout), "stderr": identity(result.stderr)}
    write_json(output / (name + ".command.json"), entry)
    require(result.returncode == 0, "COMMAND_FAILED:" + name)
    return result


def assemble(module_root, cases, lock):
    program = BOUNDARY.encode()
    ranges = {}
    for name in sorted(lock["module_names"]):
        raw = read(module_root / (name + ".luau"))
        program += ("\nfactories[" + json.dumps(name) + "] = function()\n").encode()
        first = len(program)
        program += raw
        ranges[name] = {"start": first, "end": len(program), **identity(raw)}
        program += b"\nend\n"
    program += b"\n" + cases
    require(len(ranges) == 7 and len(lock["module_names"]) == 7, "SEVEN_FULL_BODIES")
    for name, row in ranges.items():
        require(program[row["start"]:row["end"]] == read(module_root / (name + ".luau")),
                "FULL_BODY_MODIFIED:" + name)
    return program, ranges


def check_vector(stdout, lock):
    lines = stdout.decode("utf-8").splitlines()
    cases, checks, metrics = [], [], {}
    for line in lines:
        fields = line.split("\t")
        if fields[0] == "CASE":
            require(len(fields) == 4 and fields[2] == "PASS", "CASE_FAILURE")
            cases.append(fields[1])
        elif fields[0] == "CHECK":
            require(len(fields) == 3 and fields[2] == "PASS", "CHECK_FAILURE")
            checks.append(fields[1])
        elif fields[0] == "METRIC":
            require(len(fields) == 3 and fields[1] not in metrics, "METRIC_SHAPE")
            metrics[fields[1]] = int(fields[2])
        else:
            raise ValueError("PERSISTENT_BASE_NATIVE_UNEXPECTED_OUTPUT")
    require(cases == lock["expected_cases"] and checks == lock["expected_checks"], "EXACT_ORDERED_VECTOR")
    require(metrics == lock["expected_metrics"], "EXACT_READ_WRITE_COUNTS")
    return {"cases": len(cases), "checks": len(checks), "metrics": metrics, "all_pass": True}


def build_tools(args, lock, output, prep):
    if args.debug_runtime or args.debug_compiler:
        require(args.debug_runtime and args.debug_compiler and not args.luau_source,
                "DEBUG_REQUIRES_BOTH_BINARIES_NO_SOURCE_BUILD")
        runtime, compiler = prep.safe_path(args.debug_runtime), prep.safe_path(args.debug_compiler)
        require(os.access(runtime, os.X_OK) and os.access(compiler, os.X_OK), "DEBUG_TOOLS_NOT_EXECUTABLE")
        return runtime, compiler, {"mode": "AUTHOR_DEBUG_EXISTING_BINARIES_NOT_FRESH_BUILD_ACCEPTANCE",
                                   "runtime": identity(read(runtime)), "compiler": identity(read(compiler))}, None
    require(args.luau_source and args.build_dir, "FRESH_SOURCE_BUILD_REQUIRED")
    capsule = lock["unchanged_H72_build_helper"]
    raw = capsule["utf8"].encode("utf-8")
    require(identity(raw) == capsule["identity"], "CAPSULE_IDENTITY")
    helper_path = output / "unchanged_H72_build_helper.py"
    helper_path.write_bytes(raw)
    module = types.ModuleType("p0d033_pinned_H72_build_helper")
    module.__file__ = str(helper_path)
    exec(compile(raw, str(helper_path), "exec"), module.__dict__)
    build_output = output / "fresh_build"
    build_output.mkdir()
    runtime, receipt, tree_before = module.build_repl(
        Path(args.luau_source), Path(args.build_dir), build_output, {"toolchain": lock["toolchain"]},
        args.cmake, args.ninja, args.git, args.cc, args.cxx)
    # Save real fresh-build evidence immediately, even if a later check fails.
    write_json(build_output / "build_receipt.json", receipt)
    cache_before = read(Path(args.build_dir) / "CMakeCache.txt")
    compiler = Path(args.build_dir) / "luau-compile"
    require(not compiler.exists(), "COMPILER_MUST_NOT_PREEXIST")
    import time
    started = time.time_ns()
    command_log([Path(args.cmake).resolve(), "--build", Path(args.build_dir), "--target", "Luau.Compile.CLI",
                 "--parallel", "2"], build_output, "compile_build", 900)
    require(compiler.is_file() and compiler.stat().st_mtime_ns >= started and os.access(compiler, os.X_OK),
            "FRESH_COMPILER_REQUIRED")
    require(read(Path(args.build_dir) / "CMakeCache.txt") == cache_before, "CACHE_CHANGED")
    require(module.verify_clean_source(Path(args.luau_source), Path(args.git), lock["toolchain"]) == tree_before,
            "TOOLCHAIN_SOURCE_CHANGED")
    compile_receipt = {"mode": "FRESH_COMPILER_SAME_SOURCE_AND_CACHE", "build_started_ns": started,
                       "binary": identity(read(compiler)), "runtime_unchanged":
                       identity(read(runtime)) == receipt["binary_before_suites"]}
    require(compile_receipt["runtime_unchanged"], "REPL_CHANGED_DURING_COMPILER_BUILD")
    write_json(build_output / "compile_build_receipt.json", compile_receipt)
    return runtime, compiler, {"mode": "FRESH_F46_SOURCE_BUILD", "repl": receipt, "compiler": compile_receipt}, module


def run(args):
    raw_lock = read(HERE / "INPUT_LOCK.json")
    require(identity(raw_lock)["sha256"] == LOCK_SHA256, "INPUT_LOCK_CHANGED")
    lock = strict_json(raw_lock)
    require(lock["schema"] == "P0D033_SEVEN_BODY_NATIVE_GATE_V1", "LOCK_SCHEMA")
    before = verify_head(args.git, args.expected_head, lock)
    spec = importlib.util.spec_from_file_location("p0d033_exact_prepare", PACKAGE / "prepare_bridge.py")
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    output = prep.safe_path(args.output)
    require(not output.exists() and output.parent.is_dir(), "NEW_OUTPUT_REQUIRED")
    source_lock, input_paths, original_inputs, _ = prep.verify_inputs(args.official_zip, args.donor_zip)
    require(not any(p.is_relative_to(output) for p in input_paths) and not ROOT.is_relative_to(output)
            and not output.is_relative_to(ROOT), "OUTPUT_OVERLAP")
    output.mkdir()
    write_json(output / "HEAD_BINDING.json", before)
    prepared = output / "prepared"
    preparation = prep.prepare(args.official_zip, args.donor_zip, prepared)
    runtime, compiler, build_receipt, build_module = build_tools(args, lock, output, prep)
    tool_before = {"runtime": identity(read(runtime)), "compiler": identity(read(compiler))}
    module_root = prepared / prep.NAMESPACE
    cases = read(HERE / "bridge_cases.luau")
    program, ranges = assemble(module_root, cases, lock)
    program_path = output / "bridge_program.luau"
    program_path.write_bytes(program)
    write_json(output / "FULL_BODY_RANGES.json", ranges)
    compile_dir = output / "compile"
    compile_dir.mkdir()
    compiled = []
    for path in [*sorted(module_root.glob("*.luau")), program_path]:
        command_log([compiler, "--null", path], compile_dir, path.stem, 60)
        compiled.append({"file": str(path.relative_to(output)), **identity(read(path))})
    require(len(compiled) == 8, "COMPILE_COUNT")
    result = command_log([runtime, program_path], output, "native", 60)
    require(not result.stderr, "NATIVE_STDERR")
    vector = check_vector(result.stdout, lock)
    require(tool_before == {"runtime": identity(read(runtime)), "compiler": identity(read(compiler))},
            "TOOL_BINARY_CHANGED")
    require(before == verify_head(args.git, args.expected_head, lock), "REPOSITORY_CHANGED_DURING_RUN")
    require(all(read(path) == raw for path, raw in zip(input_paths, original_inputs)), "INPUT_CHANGED")
    if build_module is not None:
        final_tree = build_module.verify_clean_source(Path(args.luau_source), Path(args.git), lock["toolchain"])
        manifest = strict_json(read(output / "fresh_build/source_tree_manifest.json"))
        require(final_tree == manifest["files"], "TOOLCHAIN_CHANGED_DURING_RUN")
    files = {p.relative_to(output).as_posix(): identity(read(p)) for p in sorted(output.rglob("*")) if p.is_file()}
    receipt = {"schema": "P0D033_SEVEN_BODY_NATIVE_RECEIPT_V1", "at_utc": datetime.now(timezone.utc).isoformat(),
               "status": "PASS_AUTHOR_DEBUG" if build_module is None else "PASS_FIXED_HEAD_NATIVE_SOURCE_GATE",
               "head_binding": before, "input_lock": identity(raw_lock), "preparation": preparation,
               "full_body_ranges": ranges, "program": identity(program), "compile_count": len(compiled),
               "compiled": compiled, "native": vector, "build": build_receipt, "binaries_unchanged": True,
               "input_zip_bytes_unchanged": True, "evidence_files": files, "manifest_self_excluded": True,
               "source_acceptance_requires_registered_nonauthor_review": True,
               "DEPENDENCY_SOURCE_READY": False, "PREP_READY": False, "RC_adopted": False,
               "genuine_studio_or_actual_datastore": False, "runtime_installed": False}
    write_json(output / "RECEIPT.json", receipt)
    print(json.dumps({"status": receipt["status"], "head": args.expected_head, "native": vector,
                      "compile_count": len(compiled), "output": str(output)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("official-zip", "donor-zip", "output", "expected-head"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--luau-source")
    parser.add_argument("--build-dir")
    parser.add_argument("--debug-runtime")
    parser.add_argument("--debug-compiler")
    for key, default in (("cmake", "/usr/bin/cmake"), ("ninja", "/usr/bin/ninja"),
                         ("git", "/usr/bin/git"), ("cc", "/usr/bin/cc"), ("cxx", "/usr/bin/c++")):
        parser.add_argument("--" + key, default=default)
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
