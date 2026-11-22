#!/usr/bin/env python3
"""Execute separately named combined and objective clear-LOS inputs with 28 bodies.

This is a new, separate source-build contract. It does not relax or edit the
historical adapter's exact 9c68 binary pin. No supplied/prebuilt Repl is accepted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
INPUT_LOCK_SHA256 = "999ef08d3c0215bd33066f47ab482e0cec1c9624b270294282c0ecda47a30787"
CASE_FILES = {"combined_clear_los": "combined_cases_clear_los.luau",
              "objective_full_clear_los": "objective_full_cases_clear_los.luau"}


def require(value, reason):
    if not value:
        raise ValueError("RED_UNION22_NATIVE_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file() and stat.S_ISREG(path.stat().st_mode),
            "REGULAR_FILE_REQUIRED:" + str(path))
    return path.read_bytes()


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def load_lock():
    raw = read(HERE / "INPUT_LOCK.json")
    require(identity(raw)["sha256"] == INPUT_LOCK_SHA256, "INPUT_LOCK_MISMATCH")
    lock = strict_json(raw)
    require(lock["schema"] == "UNION22_NATIVE_DUAL_CLEAR_LOS_SOURCE_BUILD_INPUTS_V3"
            and len(lock["sources"]) == 69 and len(lock["modules_in_load_order"]) == 27
            and len(set(lock["modules_in_load_order"])) == 27
            and set(lock["suites"]) == set(CASE_FILES) and lock["case_files"] == CASE_FILES,
            "LOCK_CONTRACT")
    return lock


def safe_root(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in [path, *path.parents]), "SYMLINK_ROOT")
    return path.resolve()


def source_snapshot(root):
    require(root.is_dir(), "SOURCE_DIRECTORY")
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "SOURCE_SYMLINK")
        if path.is_file():
            require(path.suffix == ".luau", "EXTRA_SOURCE_FILE")
            result[path.relative_to(root).as_posix()] = identity(read(path))
        else:
            require(path.is_dir(), "SPECIAL_SOURCE_FILE")
    return result


def fixture_snapshot(lock):
    require({p.name for p in (HERE / "fixtures").iterdir()} == set(lock["fixtures"]), "FIXTURE_FILE_SET")
    result = {name: identity(read(HERE / "fixtures" / name)) for name in lock["fixtures"]}
    require(result == lock["fixtures"], "EXACT_FROZEN_FIXTURE_MISMATCH")
    for suite, filename in CASE_FILES.items():
        require(identity(read(HERE / filename)) == lock["suites"][suite]["case"], "CASE_MISMATCH:" + suite)
    original = lock["case_amendment"]["original_case"]
    require(original["path"] == "fixtures/combined_cases.luau"
            and identity(read(HERE / original["path"])) == {k: original[k] for k in ("bytes", "sha256")},
            "ORIGINAL_COMBINED_CASE_NOT_PRESERVED")
    objective = lock["objective_case_amendment"]["original_case"]
    require(objective == {"path": "objective_full_cases.luau", "bytes": 7882,
                          "sha256": "27d69b1cdf78c0936ab821d2ed0b945364839e62470a19d16fa6be084f8f9b1a"}
            and identity(read(HERE / objective["path"])) == {k: objective[k] for k in ("bytes", "sha256")},
            "ORIGINAL_OBJECTIVE_CASE_NOT_PRESERVED")
    return result


def clean_environment():
    # CMake receives explicit compiler/Ninja paths. Strip recipe injection and
    # build launchers while keeping the platform runtime search path available.
    keep = ("PATH", "HOME", "TMPDIR", "SYSTEMROOT", "LD_LIBRARY_PATH")
    env = {name: os.environ[name] for name in keep if name in os.environ}
    env.update({"LC_ALL": "C", "LANG": "C", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"})
    return env


def executable(path):
    path = Path(path).resolve()
    raw = read(path)
    require(os.access(path, os.X_OK), "TOOL_NOT_EXECUTABLE")
    return path, identity(raw)


def git_output(git, source, *args):
    command = [str(git), "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-C", str(source), *args]
    result = subprocess.run(command, env=clean_environment(), capture_output=True, timeout=60)
    require(result.returncode == 0, "GIT_COMMAND_FAILED:" + " ".join(args))
    return result.stdout


def verify_clean_source(source, git, toolchain):
    require(source.is_dir() and (source / ".git").exists(), "ACTUAL_GIT_SOURCE_REQUIRED")
    head = git_output(git, source, "rev-parse", "HEAD").decode().strip()
    tree = git_output(git, source, "rev-parse", "HEAD^{tree}").decode().strip()
    require(head == toolchain["source_commit"] and tree == toolchain["source_tree"], "SOURCE_COMMIT_OR_TREE")
    require(not git_output(git, source, "status", "--porcelain=v1", "--untracked-files=all", "--ignored"),
            "SOURCE_NOT_CLEAN")
    rows = git_output(git, source, "ls-tree", "-r", "-z", "HEAD").split(b"\0")
    manifest = {}
    for row in rows:
        if not row:
            continue
        metadata, raw_path = row.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        name = raw_path.decode("utf-8")
        path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts and "\\" not in name
                and name not in manifest and kind == "blob" and mode in ("100644", "100755"), "SOURCE_TREE_ENTRY")
        raw = read(source / name)
        actual_oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        actual_mode = "100755" if (source / name).stat().st_mode & 0o111 else "100644"
        require(actual_oid == oid and actual_mode == mode, "PHYSICAL_SOURCE_BLOB_OR_MODE:" + name)
        manifest[name] = {"git_blob": oid, "mode": mode, **identity(raw)}
    require(len(manifest) == toolchain["tracked_file_count"] == 2336, "SOURCE_TREE_FILE_COUNT")
    return manifest


def cache_values(raw):
    result = {}
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith(("#", "//")):
            continue
        key_type, value = line.split("=", 1)
        key, kind = key_type.rsplit(":", 1)
        require(key not in result, "CMAKE_CACHE_DUPLICATE")
        result[key] = {"type": kind, "value": value}
    return result


def validate_cache(raw, source, build, cmake, ninja, cc, cxx, recipe):
    cache = cache_values(raw)
    expected = {"CMAKE_HOME_DIRECTORY": str(source), "CMAKE_CACHEFILE_DIR": str(build),
                "CMAKE_GENERATOR": recipe["generator"], "CMAKE_BUILD_TYPE": recipe["CMAKE_BUILD_TYPE"],
                "LUAU_BUILD_TESTS": recipe["LUAU_BUILD_TESTS"], "LUAU_BUILD_CLI": recipe["LUAU_BUILD_CLI"],
                "CMAKE_MAKE_PROGRAM": str(ninja), "CMAKE_C_COMPILER": str(cc), "CMAKE_CXX_COMPILER": str(cxx),
                "CMAKE_COMMAND": str(cmake), "CMAKE_PROJECT_NAME": "Luau"}
    require(all(cache.get(k, {}).get("value") == v for k, v in expected.items()), "CMAKE_SOURCE_RECIPE_OR_COMPILER")
    forbidden = ("CMAKE_TOOLCHAIN_FILE", "CMAKE_C_COMPILER_LAUNCHER", "CMAKE_CXX_COMPILER_LAUNCHER",
                 "CMAKE_PROJECT_INCLUDE", "CMAKE_PROJECT_INCLUDE_BEFORE", "CMAKE_PROJECT_TOP_LEVEL_INCLUDES")
    require(all(not cache.get(k, {}).get("value") for k in forbidden), "CMAKE_EXTERNAL_RECIPE_INJECTION")
    require(cache.get("LUAU_BUILD_SHARED", {}).get("value") == "OFF"
            and cache.get("LUAU_BUILD_WEB", {}).get("value") == "OFF"
            and cache.get("CMAKE_C_FLAGS", {}).get("value") == ""
            and cache.get("CMAKE_CXX_FLAGS", {}).get("value") == "", "CMAKE_UNEXPECTED_BUILD_OPTIONS")
    return expected


def command_log(command, output, prefix, timeout):
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(x) for x in command], env=clean_environment(), capture_output=True, timeout=timeout)
    (output / (prefix + ".stdout.log")).write_bytes(result.stdout)
    (output / (prefix + ".stderr.log")).write_bytes(result.stderr)
    require(result.returncode == 0, prefix.upper() + "_FAILED:" + result.stderr.decode(errors="replace")[-1000:])
    return {"argv": [str(x) for x in command], "started_at_utc": started, "exit_code": result.returncode,
            "stdout": identity(result.stdout), "stderr": identity(result.stderr)}


def build_repl(source, build, output, lock, cmake, ninja, git, cc, cxx):
    source, build = safe_root(source), safe_root(build)
    require(not build.exists(), "BUILD_DIRECTORY_MUST_BE_NEW")
    require(not build.is_relative_to(source) and not source.is_relative_to(build), "BUILD_OVERLAPS_SOURCE")
    tools = {}
    for name, path in (("cmake", cmake), ("ninja", ninja), ("git", git), ("cc", cc), ("cxx", cxx)):
        actual, pin = executable(path)
        tools[name] = {"path": str(actual), **pin}
    cmake, ninja, git, cc, cxx = [Path(tools[name]["path"]) for name in ("cmake", "ninja", "git", "cc", "cxx")]
    tree_before = verify_clean_source(source, git, lock["toolchain"])
    recipe = lock["toolchain"]["recipe"]
    binary = build / recipe["binary_relative_path"]
    require(not binary.exists(), "PREBUILT_BINARY_FORBIDDEN")
    configure = command_log([cmake, "-S", source, "-B", build, "-G", recipe["generator"],
        "-DCMAKE_BUILD_TYPE=" + recipe["CMAKE_BUILD_TYPE"], "-DLUAU_BUILD_TESTS=" + recipe["LUAU_BUILD_TESTS"],
        "-DLUAU_BUILD_CLI=" + recipe["LUAU_BUILD_CLI"], "-DCMAKE_MAKE_PROGRAM=" + str(ninja),
        "-DCMAKE_C_COMPILER=" + str(cc), "-DCMAKE_CXX_COMPILER=" + str(cxx)], output, "configure", 180)
    cache = read(build / "CMakeCache.txt")
    cache_contract = validate_cache(cache, source, build, cmake, ninja, cc, cxx, recipe)
    require(not binary.exists(), "BINARY_CREATED_BEFORE_TARGET_BUILD")
    build_started_ns = time.time_ns()
    built = command_log([cmake, "--build", build, "--target", recipe["target"], "--parallel", str(recipe["build_parallel"])],
                        output, "build", 900)
    raw = read(binary)
    require(os.access(binary, os.X_OK) and binary.stat().st_mtime_ns >= build_started_ns
            and b"Linking CXX executable luau" in read(output / "build.stdout.log"), "FRESH_TARGET_BINARY_NOT_PROVEN")
    require(read(build / "CMakeCache.txt") == cache, "CMAKE_CACHE_CHANGED_DURING_BUILD")
    tree_after = verify_clean_source(source, git, lock["toolchain"])
    require(tree_before == tree_after, "SOURCE_CHANGED_DURING_BUILD")
    (output / "CMakeCache.txt").write_bytes(cache)
    (output / "build.ninja").write_bytes(read(build / "build.ninja"))
    write_json(output / "source_tree_manifest.json", {"source_commit": lock["toolchain"]["source_commit"],
        "source_tree": lock["toolchain"]["source_tree"], "files": tree_before})
    evidence_names = ("configure.stdout.log", "configure.stderr.log", "build.stdout.log", "build.stderr.log",
                      "CMakeCache.txt", "build.ninja", "source_tree_manifest.json")
    receipt = {"schema": "UNION22_F46_REPL_BUILD_V1", "status": "PASS_NEW_BUILD",
        "contract": "NEW_SOURCE_BUILD_CONTRACT_OLD_9C_BINARY_CONTRACT_UNCHANGED",
        "source_path": str(source), "source_commit": lock["toolchain"]["source_commit"],
        "source_tree": lock["toolchain"]["source_tree"], "tracked_file_count": len(tree_before),
        "source_tree_clean_before_after": True, "build_directory": str(build),
        "build_directory_absent_initially": True, "binary_absent_before_build": True,
        "binary_path": str(binary), "binary_mtime_ns": binary.stat().st_mtime_ns,
        "target_build_started_ns": build_started_ns, "recipe": recipe, "cache_contract": cache_contract,
        "configure_exit": 0, "build_exit": 0, "commands": {"configure": configure, "build": built},
        "tools": tools, "binary_before_suites": identity(raw), "binary_after_suites": None,
        "evidence_files": {name: identity(read(output / name)) for name in evidence_names}}
    return binary, receipt, tree_before

