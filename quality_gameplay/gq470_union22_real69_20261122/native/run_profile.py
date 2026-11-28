#!/usr/bin/env python3
"""Execute separately named combined and objective clear-LOS inputs with 28 bodies.

This is a new, separate source-build contract. It does not relax or edit the
historical adapter's exact 9c68 binary pin. No supplied/prebuilt Repl is accepted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
INPUT_LOCK_SHA256 = "ab34679bcc911208a215cc72e27fb5b1c7eee9ba83676d836ba4fe937912e732"
CASE_FILES = {"combined_clear_los": "combined_cases_clear_los.luau",
              "objective_full_clear_los": "objective_full_cases_clear_los.luau",
              "beast_target_selection": "beast_cases.luau"}
BOT_INPUTS = {
    "bot_vault_base.template.luau": {"bytes": 39006, "sha256": "ba71e926da72b3c60118751d4c89ba4086dfec24a9d67b0d2ee9a04877f81ad7"},
    "bot_vault_cases.json": {"bytes": 71446, "sha256": "dc1434c328ab30853a75993d2f6042b01e1d0bdc8733c528d4a9b39b7557289c"},
    "bot_vault_suite.py": {"bytes": 20273, "sha256": "e0f72127a01f9a6af8422a5d35d6f515f9a3f00eb75f43a2ef8624df1fb46c09"},
}


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
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


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
    require(identity(read(HERE / "beast_fixture.luau"))
            == lock["suites"]["beast_target_selection"]["fixture"], "BEAST_FIXTURE_CHANGED")
    return result


def bot_input_snapshot(lock):
    require(lock.get("bot_vault_supplement", {}).get("input_files") == BOT_INPUTS,
            "BOT_FIXED_INPUT_CONTRACT")
    observed = {name: identity(read(HERE / name)) for name in BOT_INPUTS}
    require(observed == BOT_INPUTS, "BOT_FIXED_INPUT_CHANGED")
    return observed


def load_bot_vault_supplement(lock):
    before = bot_input_snapshot(lock)
    spec = importlib.util.spec_from_file_location("union22_fixed_bot_vault_supplement", HERE / "bot_vault_suite.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    cases = adapter.load_contract()
    modules = cases["modules_in_load_order"]
    scenarios = cases["scenarios"]
    selected = {m["relative_source_path"]: lock["sources"][m["relative_source_path"]] for m in modules}
    original_names = set(lock["modules_in_load_order"]) | {"Host"}
    bot_names = {m["module"] for m in modules}
    require(len(original_names) == 28 and len(bot_names) == 16 and len(original_names | bot_names) == 30
            and bot_names - original_names == {"BotPathRouter", "BotActors"}, "BOT_DISTINCT_BODY_ACCOUNTING")
    expected = {
        "schema": "UNION22_BOT_VAULT_SUPPLEMENT_LOCK_V1", "input_files": BOT_INPUTS,
        "output_directory": "bot_vault", "module_order": [m["module"] for m in modules],
        "selected_sources": selected, "scenario_order": [s["scenario_id"] for s in scenarios],
        "scenarios": {s["scenario_id"]: {
            "configuration_substitutions": s["configuration_substitutions"],
            "case_assembly": s["case_assembly_identity"],
            "expected_case_names": s["expected_ordered_CASE_names"],
            "expected_check_names": s["expected_ordered_CHECK_names"]} for s in scenarios},
        "expected_totals": {"scenarios": 9, "CASE_rows": 13, "CHECK_rows": 43, "warning_rows": 0,
                            "stderr_bytes": 0, "each_exit_code": 0, "evidence_files": 37},
        "full_bodies_each_scenario": 16, "original_dual28_full_bodies": 28,
        "distinct_server_full_bodies": 30, "hud_policy_separate_from_server_body_count": True,
        "preserve_original_dual28_generated_programs": True,
        "same_fresh_F46_binary_required": True, "source_only": True,
    }
    require(lock["bot_vault_supplement"] == expected, "BOT_SCENARIO_OR_PROFILE_BINDING")
    for module in modules:
        pinned = selected[module["relative_source_path"]]
        if module["module"] == "BotActors":
            require(pinned == adapter.BOT_OBJECTIVE_TAG_PIN, "BOT_EXACT_DISPLAY_SOURCE")
        if module["module"] == "BotPathRouter":
            require(pinned == module["historical_candidate"], "BOT_ORIGINAL_ROUTER")
    require(adapter.package_pins() == before and bot_input_snapshot(lock) == before,
            "BOT_HELPER_OR_INPUT_CHANGED_DURING_LOAD")
    return adapter, before


def evidence_snapshot(root):
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "EVIDENCE_SYMLINK")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = identity(read(path))
        else:
            require(path.is_dir(), "EVIDENCE_SPECIAL_FILE")
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


def prepare_selected_hud_layout(root, output, lock):
    """Run the unchanged REAL63 generator main on the actual final two sources."""
    contract = lock["selected_hud_layout"]
    relative = "quality_gameplay/gq8_real63_ui_occlusion_20261119/native_layout.py"
    generator = HERE.parents[2] / relative
    generator_pin = {"bytes": 3097, "sha256": "1323e10a2d66ca5c986f9a75049df5b4e7fbd016c22583f9d9790d7d1d3e164d"}
    flat = {
        "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau":
            "EGGRUMBLE_HudIntelRuntime.client.luau",
        "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy.luau":
            "EGGRUMBLE_HudPresentationPolicy.luau",
    }
    require(contract["schema"] == "GQ828_SELECTED_HUD_LAYOUT_GATE_V1"
            and contract["generator"] == {"path": relative, **generator_pin}
            and identity(read(generator)) == generator_pin
            and contract["flat_sources"] == flat
            and contract["viewport_shapes"] == [[320, 260], [393, 851], [375, 667],
                                               [600, 300], [851, 393], [1280, 720], [1024, 768]]
            and contract["hands"] == ["RIGHT", "LEFT"] and contract["condition_count"] == 14
            and contract["expected_generator_stdout"] == "GQ8_REAL63_SELECTED_SOURCE_MODAL_LAYOUT_PROOFS_PASS\n"
            and contract["expected_native_stdout"] == "GQ8_REAL63_UI_SQUARE_COLLISIONS_14_CASES_PASS\n"
            and contract["generator_python_optimization"] == 0
            and contract["hud_runtime_executed"] is False
            and contract["policy_full_body_executed"] is True, "SELECTED_LAYOUT_CONTRACT")
    output.mkdir(exist_ok=False)
    (output / "sources").mkdir()
    (output / "native_layout.py").write_bytes(read(generator))
    selected = {}
    for relative_source, name in flat.items():
        raw = read(root / relative_source)
        require(identity(raw) == lock["sources"][relative_source], "SELECTED_LAYOUT_SOURCE_PIN")
        (output / "sources" / name).write_bytes(raw)
        selected[relative_source] = identity(raw)
    python, python_pin = executable(sys.executable)
    # clean_environment excludes PYTHONOPTIMIZE; the child argv deliberately
    # does not inherit a parent's -O. The original generator uses assertions.
    command = command_log([python, "-B", output / "native_layout.py", "--sources",
                           output / "sources", "--out", output / "generated.luau"],
                          output, "generator", 60)
    require(read(output / "generator.stdout.log").decode("utf-8") == contract["expected_generator_stdout"]
            and read(output / "generator.stderr.log") == b"", "SELECTED_LAYOUT_GENERATOR_LOG")
    require(read(output / "native_layout.py") == read(generator)
            and all(read(output / "sources" / name) == read(root / path)
                    for path, name in flat.items()), "SELECTED_LAYOUT_INPUT_CHANGED")
    return {"contract": contract, "selected_sources": selected, "generator_command": command,
            "python": {"path": str(python), **python_pin}}


def run_selected_hud_layout(root, output, binary, lock, binary_pin, context, source_receipt, runner_pin):
    prepared = prepare_selected_hud_layout(root, output, lock)
    generated = read(output / "generated.luau")
    require(identity(read(binary)) == binary_pin, "SELECTED_LAYOUT_BINARY_BEFORE")
    native_command = command_log([binary, output / "generated.luau"], output, "native", 60)
    require(read(output / "native.stdout.log").decode("utf-8") == prepared["contract"]["expected_native_stdout"]
            and read(output / "native.stderr.log") == b"", "SELECTED_LAYOUT_NATIVE_LOG")
    require(read(output / "generated.luau") == generated and identity(read(binary)) == binary_pin,
            "SELECTED_LAYOUT_PROGRAM_OR_BINARY_CHANGED")
    for path, name in prepared["contract"]["flat_sources"].items():
        require(identity(read(root / path)) == prepared["selected_sources"][path]
                and read(root / path) == read(output / "sources" / name), "SELECTED_LAYOUT_FINAL_INPUT_CHANGED")
    receipt = {
        "schema": "UNION22_SELECTED_HUD_LAYOUT_EXECUTION_V1", "status": "PASS_SOURCE_LAYOUT_ONLY",
        "execution_context": context, "source_receipt": source_receipt,
        "input_lock": identity(read(HERE / "INPUT_LOCK.json")), "runner": runner_pin,
        "contract": prepared["contract"], "selected_sources": prepared["selected_sources"],
        "source_root": str(root), "execution_directory": str(output),
        "generator": identity(read(output / "native_layout.py")),
        "generated": identity(generated), "python": prepared["python"], "native": binary_pin,
        "commands": {"generator": prepared["generator_command"], "native": native_command},
        "condition_count": 14, "completion_marker_count": 1,
        "hud_runtime_executed": False, "policy_full_body_executed": True,
        "separate_from_server28_suites": True, "source_inputs_unchanged": True,
    }
    write_json(output / "receipt.json", receipt)
    print("selected_hud_layout: original main and 14 fixed Policy conditions PASS; HUD runtime not executed", flush=True)
    return receipt


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


def assemble(root, lock, suite_name):
    require(suite_name in CASE_FILES and lock["case_files"] == CASE_FILES, "UNKNOWN_CASE_VARIANT")
    case = HERE / CASE_FILES[suite_name]
    require(identity(read(case)) == lock["suites"][suite_name]["case"], "EXACT_CASE_FILE")
    code = "".join(read(HERE / "fixtures" / name).decode("utf-8") + "\n" for name in lock["fixture_order"])
    if suite_name == "combined_clear_los":
        # Only this suite drives the new guard movement through the Roblox physics fixture.
        name = "guardian_wall_geometry.luau"
        adapter = read(HERE / "fixtures" / name)
        require(identity(adapter) == lock["fixtures"][name], "GUARDIAN_WALL_GEOMETRY_FIXTURE")
        code += adapter.decode("utf-8") + "\n"
    if suite_name == "beast_target_selection":
        fixture = read(HERE / "beast_fixture.luau")
        require(identity(fixture) == lock["suites"][suite_name]["fixture"], "BEAST_FIXTURE_IDENTITY")
        code += fixture.decode("utf-8") + "\n"
    ranges, byte_ranges = {}, {}
    order = lock["modules_in_load_order"] + ["LobbyCastleModesPreview.server"]
    for name in order:
        rel = "ServerScriptService/EGGRUMBLE_" + name + ".luau"
        raw = read(root / rel)
        if name == "LobbyCastleModesPreview.server":
            code += "\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n"
            label, start = "Host", code.count("\n") + 1
        else:
            label = name
            code += "\nloadingModule='" + name + "'\n"
            start = code.count("\n") + 3
            code += f"fullSourceRanges.{name}={{first={start},last={start+raw.count(bytes([10]))}}}\n"
            code += "dependencies.EGGRUMBLE_" + name + "=(function()\n"
            require(code.count("\n") + 1 == start, "WRAPPER_SOURCE_LINE_RANGE")
        first_byte = len(code.encode("utf-8"))
        code += raw.decode("utf-8")
        last_byte = len(code.encode("utf-8"))
        byte_ranges[rel] = {"start": first_byte, "end": last_byte, **identity(raw)}
        code += "\nend)()end\n" if label == "Host" else "\nend)()\n"
        ranges[label] = {"first": start, "last": start + raw.count(b"\n")}
    code += "\n" + read(case).decode("utf-8")
    generated = code.encode("utf-8")
    for rel, row in byte_ranges.items():
        require(generated[row["start"]:row["end"]] == read(root / rel), "FULL_BODY_CHANGED")
    require(len(byte_ranges) == 28, "FULL_BODY_COUNT")
    return generated, ranges, byte_ranges


def exact_vector(stdout, expected):
    lines = [line for line in stdout.splitlines() if line.startswith("CASE\t")]
    parts = [line.split("\t", 3) for line in lines]
    okay = (len(parts) == len(expected) and [p[1] for p in parts if len(p) == 4] == expected
            and all(len(p) == 4 and p[2] == "PASS" for p in parts))
    return okay, lines


def vector_parse_reason(lines, expected):
    """Describe the existing vector predicate without changing its acceptance."""
    parts = [line.split("\t", 3) for line in lines]
    reasons = []
    if len(parts) != len(expected):
        reasons.append("CASE_COUNT_MISMATCH")
    if any(len(row) != 4 for row in parts):
        reasons.append("MALFORMED_CASE_ROW")
    if [row[1] for row in parts if len(row) == 4] != expected:
        reasons.append("CASE_NAME_OR_ORDER_MISMATCH")
    if any(len(row) == 4 and row[2] != "PASS" for row in parts):
        reasons.append("NON_PASS_CASE")
    return "+".join(reasons) if reasons else "EXACT_PASS_VECTOR"


def emit_suite_failure(output, diagnostic, stdout, stderr, error):
    """Failure evidence only; callers always re-raise the original exception."""
    diagnostic.update(exception_type=type(error).__name__, exception=str(error),
                      stdout=identity(stdout), stderr=identity(stderr))
    try:
        (output / "stdout.log").write_bytes(stdout)
        (output / "stderr.log").write_bytes(stderr)
        write_json(output / "FAILED.json", diagnostic)
    finally:
        # JSON escaping keeps complete output on inert log lines, including
        # invalid UTF-8 display escapes, even if diagnostic disk writes failed.
        print("UNION22_NATIVE_FAILURE " + json.dumps(diagnostic, ensure_ascii=True, sort_keys=True), flush=True)
        print("UNION22_NATIVE_FAILURE_STDOUT " + json.dumps(stdout.decode("utf-8", errors="backslashreplace")), flush=True)
        print("UNION22_NATIVE_FAILURE_STDERR " + json.dumps(stderr.decode("utf-8", errors="backslashreplace")), flush=True)


def run_suite(root, output, binary, lock, suite_name, source_before, binary_pin, context, source_receipt, runner_pin):
    output.mkdir(exist_ok=False)
    generated, line_ranges, byte_ranges = assemble(root, lock, suite_name)
    (output / "generated.luau").write_bytes(generated)
    require(identity(read(binary)) == binary_pin, "BINARY_CHANGED_BEFORE_SUITE")
    expected = lock["suites"][suite_name]["expected_case_names"]
    stdout, stderr = b"", b""
    diagnostic = {"schema": "UNION22_NATIVE_SUITE_FAILURE_DIAGNOSTIC_V1", "status": "FAIL_DIAGNOSTIC_ONLY",
                  "suite": suite_name, "execution_context": context, "source_receipt": source_receipt,
                  "input_lock": identity(read(HERE / "INPUT_LOCK.json")), "runner": runner_pin,
                  "native": binary_pin, "generated": identity(generated), "case_file": lock["suites"][suite_name]["case"],
                  "expected_case_names": expected, "cases": [], "native_exit": None, "timed_out": False,
                  "exact_complete_pass_vector": None, "source_inputs_unchanged": None,
                  "phase": "NATIVE_PROCESS", "parse_reason": "NOT_PARSED", "native_admission": False}
    try:
        result = subprocess.run([str(binary), str(output / "generated.luau")], env=clean_environment(),
                                capture_output=True, timeout=60)
        stdout, stderr = result.stdout, result.stderr
        diagnostic.update(native_exit=result.returncode, phase="STDOUT_UTF8_PARSE")
        (output / "stdout.log").write_bytes(stdout)
        (output / "stderr.log").write_bytes(stderr)
        vector, lines = exact_vector(result.stdout.decode("utf-8"), expected)
        diagnostic.update(cases=lines, exact_complete_pass_vector=vector,
                          parse_reason=vector_parse_reason(lines, expected), phase="SOURCE_SNAPSHOT")
        unchanged = source_snapshot(root) == source_before
        diagnostic.update(source_inputs_unchanged=unchanged, phase="SUITE_ACCEPTANCE_PREDICATE")
        require(result.returncode == 0 and vector and unchanged, "SUITE_FAILED_OR_SOURCE_MUTATED:" + suite_name)
        diagnostic["phase"] = "GENERATED_AND_BINARY_RECHECK"
        require(read(output / "generated.luau") == generated and identity(read(binary)) == binary_pin,
                "GENERATED_OR_NATIVE_CHANGED_DURING_SUITE")
        diagnostic["phase"] = "FIXTURE_RECHECK"
        fixture_snapshot(lock)
    except Exception as error:
        if isinstance(error, subprocess.TimeoutExpired):
            stdout, stderr = error.stdout or b"", error.stderr or b""
            diagnostic.update(timed_out=True, parse_reason="NOT_PARSED_TIMEOUT")
        elif isinstance(error, UnicodeDecodeError):
            diagnostic["parse_reason"] = "INVALID_UTF8"
        try:
            emit_suite_failure(output, diagnostic, stdout, stderr, error)
        except Exception as diagnostic_error:
            # A diagnostic I/O error must not replace the original failing gate.
            try:
                print("UNION22_NATIVE_DIAGNOSTIC_OUTPUT_ERROR " + repr(diagnostic_error), file=sys.stderr, flush=True)
            except Exception:
                pass
        raise
    fixture_pins = lock["fixtures"]
    if suite_name == "beast_target_selection":
        fixture_pins = fixture_pins | {"beast_fixture.luau": lock["suites"][suite_name]["fixture"]}
    receipt = {"schema": "UNION22_FULL_RUNTIME_SUITE_V2", "status": "PASS", "profile": "union22", "suite": suite_name,
        "input_variant": lock["suites"][suite_name]["input_variant"], "case_path": CASE_FILES[suite_name],
        "execution_context": context, "source_receipt": source_receipt,
        "source_count_pinned": 69, "source_count_executed_full_body": 28, "source_profile": source_before,
        "source_root": str(root), "full_body_byte_ranges": byte_ranges, "source_line_ranges": line_ranges,
        "fixture_pins": fixture_pins, "runner": runner_pin,
        "input_lock": identity(read(HERE / "INPUT_LOCK.json")), "case_file": lock["suites"][suite_name]["case"],
        "generated": identity(generated), "stdout": identity(result.stdout), "stderr": identity(result.stderr),
        "native": binary_pin, "exit_code": result.returncode, "cases": lines,
        "expected_case_names": expected, "exact_complete_pass_vector": True, "source_inputs_unchanged": True,
        "traces": [line for line in result.stdout.decode().splitlines() if line.startswith(("TRACE\t", "METRIC\t"))],
        "limitations": lock["limitations"]}
    write_json(output / "receipt.json", receipt)
    print(suite_name + ": " + str(len(lines)) + "/" + str(len(expected)) + " exact PASS cases", flush=True)
    return receipt


def run_relay_presentation(root, output, binary, binary_pin, context, profile, compose):
    lock = profile["relay_presentation_followup"]
    client = read(root / compose.HUD_SOURCE)
    require(identity(client) == profile["relay_eligibility_followup"]["rows"][compose.HUD_SOURCE]["parent"]["after"],
            "RELAY_PRESENTATION_SOURCE_PIN")
    mounted = client[lock["client_start"]:lock["client_end"]]
    require(identity(mounted) == lock["client_wrapper"], "RELAY_PRESENTATION_MOUNTED_PIN")
    template_path = HERE / "relay_presentation_cases.luau"
    template = read(template_path)
    placeholder = b"-- @RELAY_PRESENTATION_MOUNTED@\n"
    require(identity(template) == lock["native_case"] and template.count(placeholder) == 1,
            "RELAY_PRESENTATION_CASE_PIN")
    program = template.replace(placeholder, mounted, 1)
    require(identity(program) == lock["native_program"], "RELAY_PRESENTATION_PROGRAM_PIN")
    output.mkdir()
    program_path = output / "generated.luau"
    program_path.write_bytes(program)
    result = subprocess.run([str(binary),str(program_path)], env=clean_environment(), capture_output=True, timeout=30)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    require(result.returncode == 0 and not result.stderr
            and identity(result.stdout.replace(b"\r\n",b"\n")) == {
                "bytes": 1567, "sha256": "07337ca815254902b5b8e9b4359787ffe175bdae73cc59d1487c07aff4cd0473"},
            "RELAY_PRESENTATION_EXACT_VECTOR")
    require(identity(read(binary)) == binary_pin and read(program_path) == program
            and read(template_path) == template and read(root / compose.HUD_SOURCE) == client,
            "RELAY_PRESENTATION_INPUT_DRIFT")
    write_json(output / "receipt.json", {"source": identity(client), "native": binary_pin,
               "execution_context": context, "generated": identity(program), "stdout": identity(result.stdout),
               "stderr": identity(result.stderr), "exit": result.returncode, "cases": 22})
    print("relay_presentation: 22 Native cases PASS; physical Studio overlap remains separate", flush=True)


BR_CANYON_STDOUT = (
    b"PASS TEAM CENTER_AND_FOUR_LANES\n"
    b"PASS TEAM 16_CASTLE_FRONT_APPROACHES\n"
    b"PASS BATTLE_ROYALE CENTER_AND_FOUR_LANES\n"
    b"PASS BATTLE_ROYALE 16_CASTLE_FRONT_APPROACHES\n"
)


def br_canyon_program(root, profile, compose):
    canyon_path, realm_path = compose.BR_CANYON_SOURCES
    bodies = {name: read(root / name) for name in (canyon_path, realm_path, compose.VAULT_SOURCE)}
    pins = {name: identity(raw) for name, raw in bodies.items()}
    require(all(pin == profile["sources"][name]["after"] for name, pin in pins.items()),
            "BR_CANYON_SOURCE_PINS")
    canyon, realm, host = (bodies[path] for path in (canyon_path, realm_path, compose.VAULT_SOURCE))

    def between(raw, first, last):
        require(raw.count(first) == 1, "BR_CANYON_FRAGMENT_START")
        start = raw.index(first)
        return raw[start:raw.index(last, start)]

    def center_before(end):
        tail = realm.index(end)
        start = realm.rindex(b"  local center=", 0, tail)
        return realm[start:tail].rstrip()

    template = read(HERE / "br_canyon_cases.luau")
    require(identity(template) == profile["br_canyon_followup"]["native_case"], "BR_CANYON_FIXTURE_PIN")
    fragments = {
        "CASTLE_POINTS": between(host, b"local function getCastlePoint(", b"-- GQ8_HUMAN_SIEGE_PACING_BEGIN"),
        "BATTLEFIELD": between(host,
                               b' local worldX=mode=="TEAM" and -620 or 620\n local floor=block(session.world,"TacticalBattlefield",',
                               b" floor.Material=Enum.Material.Grass"),
        "REALM_OFFSET": between(realm, b" core.Name=CORE_NAME", b" local state={mode=mode"),
        "STARFALL_CENTER": center_before(b"  local bridge={}"),
        "METEOR_CENTER": center_before(b"  local segments={}"),
        "CANYON_OFFSET": between(canyon, b' if arena:FindFirstChild("GQ8_RC85_WCS_Canyon")',
                                 b" installed[arena]=true").split(b"\n", 1)[1],
        "CANYON_ORIGIN": between(canyon, b" local origin=floor.CFrame", b" local grass="),
        "CANYON_PARTS": between(canyon, b' local west=block("WestBank"', b' block("CrystalCanyonBottom"')
                         + between(canyon, b' local shortcut=block("ShortcutBridge"', b" local gate="),
    }
    for name, raw in fragments.items():
        placeholder = b"-- @" + name.encode() + b"@"
        require(template.count(placeholder) == 1, "BR_CANYON_FIXTURE_BOUNDARY:" + name)
        template = template.replace(placeholder, raw.rstrip(), 1)
    return template, pins


def run_br_canyon(root, output, binary, binary_pin, context, profile, compose):
    program, pins = br_canyon_program(root, profile, compose)
    output.mkdir()
    program_path = output / "generated.luau"
    program_path.write_bytes(program)
    result = subprocess.run([str(binary), str(program_path)], env=clean_environment(), capture_output=True, timeout=30)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    require(result.returncode == 0 and not result.stderr
            and result.stdout.replace(b"\r\n", b"\n") == BR_CANYON_STDOUT, "BR_CANYON_EXACT_VECTOR")
    require(identity(read(binary)) == binary_pin and read(program_path) == program
            and br_canyon_program(root, profile, compose) == (program, pins), "BR_CANYON_INPUT_DRIFT")
    write_json(output / "receipt.json", {"sources": pins, "native": binary_pin,
               "execution_context": context, "generated": identity(program), "stdout": identity(result.stdout),
               "stderr": identity(result.stderr), "exit": result.returncode, "cases": 4})
    print("br_canyon: TEAM and BR lane placements and 32 straight castle approaches PASS", flush=True)


def run_score_regressions(root, output, binary, binary_pin, context, profile, compose):
    source = read(root / compose.SCORE_SOURCE)
    require(identity(source) == profile["sources"][compose.SCORE_SOURCE]["after"],
            "SCORE_REGRESSION_SOURCE")
    repair = profile["score_relay_followup"]
    required = {
        "EGGRUMBLE_ScoreBalance.spec.luau": b"EGGRUMBLE_V3_MATCH_RESULTS_NATIVE_PASS assertions=107\n",
        "EGGRUMBLE_RelayScoreRegression.spec.luau": b"EGGRUMBLE_RELAY_SCORE_NATIVE_REGRESSION_PASS assertions=16\n",
    }
    require(set(repair["regression_specs"]) == {"native/" + name for name in required},
            "SCORE_REGRESSION_SPEC_SET")
    donor = HERE.parents[2] / compose.SCORE_REGRESSION_DONOR / "native"
    output.mkdir()
    results = {}
    for name, expected in required.items():
        spec = read(donor / name)
        require(identity(spec) == repair["regression_specs"]["native/" + name],
                "SCORE_REGRESSION_SPEC_IDENTITY")
        prefix = name.split(".")[0]
        program_path = output / (prefix + ".luau")
        program = b"local score=(function()\n" + source + b"\nend)()\nlocal spec=(function()\n" + spec
        program += b"\nend)()\nassert(spec(score))\n"
        program_path.write_bytes(program)
        run = subprocess.run([str(binary), str(program_path)], env=clean_environment(),
                             capture_output=True, timeout=30)
        (output / (prefix + ".stdout.log")).write_bytes(run.stdout)
        (output / (prefix + ".stderr.log")).write_bytes(run.stderr)
        require(run.returncode == 0 and run.stdout == expected.replace(b"\n", os.linesep.encode()) and not run.stderr,
                "SCORE_REGRESSION_EXACT_VECTOR:" + name)
        require(identity(read(binary)) == binary_pin and read(program_path) == program
                and read(donor / name) == spec and read(root / compose.SCORE_SOURCE) == source,
                "SCORE_REGRESSION_INPUT_DRIFT")
        results[name] = {"spec": identity(spec), "program": identity(program), "stdout": identity(run.stdout),
                         "stderr": identity(run.stderr), "exit": run.returncode}
    write_json(output / "receipt.json", {"source": identity(source), "native": binary_pin,
                                       "execution_context": context, "results": results})
    print("score_relay: original 107 + 16 checks PASS in two fresh processes", flush=True)


def run_profile(source_root, luau_source, build_dir, output, cmake, ninja, git, cc, cxx, context):
    lock = load_lock()
    runner_before = read(Path(__file__))
    lock_before = read(HERE / "INPUT_LOCK.json")
    root, source, build, output = [safe_root(p) for p in (source_root, luau_source, build_dir, output)]
    require(not output.exists() and not build.exists(), "OUTPUT_AND_BUILD_MUST_BE_NEW")
    roots = [root, source, build, output]
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for i, a in enumerate(roots) for b in roots[i+1:]), "DIRECTORY_OVERLAP")
    sys.path.insert(0, str(HERE.parent))
    import compose_union22 as compose
    source_receipt_raw = read(root.parent / compose.RECEIPT)
    source_receipt = strict_json(source_receipt_raw)
    core = strict_json(read(root.parent / "CORE_BUILD_REPORT.json"))
    compose.validate_context(context, source_receipt)
    require(core.get("context") == context and source_receipt.get("execution_context") == context
            and core.get("status") == "PASS_SOURCE_BUILD_ONLY", "CURRENT_SOURCE_EXECUTION_CONTEXT")
    before = source_snapshot(root)
    require(before == lock["sources"] and len(before) == 69, "SOURCE_PROFILE_MISMATCH")
    fixture_snapshot(lock)
    bot_adapter, bot_before = load_bot_vault_supplement(lock)
    output.mkdir(parents=True, exist_ok=False)
    try:
        binary, built, tree_before = build_repl(source, build, output, lock, cmake, ninja, git, cc, cxx)
        built["execution_context"] = context
        built["source_receipt"] = identity(source_receipt_raw)
        built["input_lock"] = identity(lock_before)
        built["runner"] = identity(runner_before)
        pin = built["binary_before_suites"]
        for suite in CASE_FILES:
            run_suite(root, output / suite, binary, lock, suite, before, pin, context,
                      identity(source_receipt_raw), identity(runner_before))
        profile = compose.load_lock()
        layout_parent = profile["portrait_followup"]["rows"][compose.PORTRAIT_SOURCE]["parent"]["after"]
        traversal_parent = profile["shorefoam_followup"]["rows"][compose.SHOREFOAM_SOURCE]["parent"]["after"]
        host_parent = profile["team_win_rule_followup"]["rows"][compose.VAULT_SOURCE]["parent"]["after"]
        hud_parent = profile["fractional_hp_followup"]["rows"][compose.HUD_SOURCE]["parent"]["after"]
        water_chain_parent_pins = lock["sources"] | {
            name: row["parent"]["after"] for name, row in profile["cover_orders_followup"]["rows"].items()
        } | {
            name: row["parent"]["after"] for name, row in profile["ground_night_followup"]["rows"].items()
        } | {
            name: row["parent"]["after"] for name, row in profile["return_convert_followup"]["rows"].items()
        } | {
            name: row["parent"]["after"] for name, row in profile["field_loadouts_followup"]["rows"].items()
        } | {
            name: row["parent"]["after"] for name, row in profile["wing_warrior_followup"]["rows"].items()
        } | {
            name: row["parent"]["after"] for name, row in profile["ninja_s4_followup"]["rows"].items()
        } | {
            name: row["parent"]["after"] for name, row in profile["mage_water_chain_followup"]["rows"].items()
        }
        projectile_parent_pins = water_chain_parent_pins | {
            name: row["parent"]["after"] for name, row in profile["mage_projectile_followup"]["rows"].items()
        }
        layout_pins = lock | {"sources": projectile_parent_pins | {compose.PORTRAIT_SOURCE: layout_parent,
                                                         compose.SHOREFOAM_SOURCE: traversal_parent,
                                                         compose.VAULT_SOURCE: host_parent,
                                                         compose.HUD_SOURCE: hud_parent}}
        run_selected_hud_layout(root.parent / compose.PORTRAIT_OFF / "sources",
                                output / "selected_hud_layout", binary, layout_pins, pin, context,
                                identity(source_receipt_raw), identity(runner_before))
        original_outputs = {name: evidence_snapshot(output / name)
                            for name in (*CASE_FILES, "selected_hud_layout")}
        require({name: len(rows) for name, rows in original_outputs.items()} == {
            "combined_clear_los": 4, "objective_full_clear_los": 4, "beast_target_selection": 4, "selected_hud_layout": 9},
            "ORIGINAL_DUAL28_AND_HUD_FILE_COUNTS")
        bot_result = bot_adapter.run_supplement(
            source_root=root, expected_profile=lock["sources"], binary=binary,
            build_receipt=built, execution_context=context, source_receipt=identity(source_receipt_raw),
            output=output / "bot_vault")
        require(bot_result["status"] == "PASS" and bot_result["execution_context"] == context
                and bot_result["source_profile"] == before and bot_result["native"] == pin
                and bot_result["totals"] == {"scenarios": 9, "CASE_rows": 13, "CHECK_rows": 43,
                    "warning_rows": 0, "full_bodies_per_scenario": 16,
                    "distinct_full_bodies_with_existing_dual28": 30}
                and len(evidence_snapshot(output / "bot_vault")) == 37, "BOT_COMPLETE_SUPPLEMENT")
        print("bot_vault: 9 scenarios, 13 CASE, 43 CHECK PASS; same fresh F46; 30 distinct server bodies with dual28", flush=True)
        run_score_regressions(root, output / "score_relay", binary, pin, context, compose.load_lock(), compose)
        run_relay_presentation(root.parent / compose.RELAY_ELIGIBILITY_OFF / "sources", output / "relay_presentation",
                               binary, pin, context, compose.load_lock(), compose)
        run_br_canyon(root, output / "br_canyon", binary, pin, context, compose.load_lock(), compose)
        from role_readability_native import run as run_role_readability
        role_compiler = Path(core["commands"][0]["command"][0])
        require(identity(read(role_compiler)) == core["compiler"], "ROLE_READABILITY_COMPILER")
        run_role_readability(root, output / "role_readability", binary, role_compiler, source,
                             pin, context, compose.load_lock(), compose)
        from field_prompt_native import run as run_field_prompt
        run_field_prompt(root, output / "field_prompt", binary, pin, context, compose.load_lock(), compose)
        from foliage_readability import run as run_foliage
        run_foliage(root, output / "foliage_readability", binary, pin, context, compose.load_lock(), compose)
        from guardian_wall import run as run_guardian_wall
        run_guardian_wall(root, output / "guardian_wall", binary, pin, context, compose.load_lock(), compose)
        from combat_visual_native import run as run_combat_visual
        run_combat_visual(root, output / "combat_visual", binary, pin, context, compose.load_lock(), compose)
        from growth_musou import run as run_growth_musou
        run_growth_musou(root.parent, output / "growth_musou", binary, pin, context, compose.load_lock(), compose)
        from art_polish_skillfx import run as run_art_polish_skillfx
        run_art_polish_skillfx(root, output / "art_polish_skillfx", binary, pin, context, compose.load_lock(), compose)
        from mage_contact_native import run as run_mage_contact
        run_mage_contact(root.parent, output / "mage_contact", binary, pin, context, compose.load_lock(), compose)
        from relay_eligibility_native import run as run_relay_eligibility
        run_relay_eligibility(root.parent, output / "relay_eligibility", binary, pin, context, compose.load_lock(), compose)
        from private_touch_native import run as run_private_touch
        run_private_touch(root, output / "private_touch", binary, pin, context, compose.load_lock(), compose,
                          clean_environment())
        from portrait_native import run as run_portrait
        run_portrait(root, output / "portrait", binary, pin, context, profile, compose, clean_environment())
        from team_win_rule_native import run as run_team_win_rule
        run_team_win_rule(root, output / "team_win_rule", binary, pin, context, profile, compose, clean_environment())
        from fractional_hp_native import run as run_fractional_hp
        run_fractional_hp(root, output / "fractional_hp", binary, pin, context, profile, compose, clean_environment())
        from mage_projectiles import FILES as projectile_files, PROCESS_COUNT as projectile_runs
        from mage_projectiles import run as run_mage_projectiles
        run_mage_projectiles(root, output / "mage_projectiles", binary, pin, context, profile,
                             compose, clean_environment())
        from mage_water_chain import FILES as water_chain_files, PROCESS_COUNT as water_chain_runs
        from mage_water_chain import run as run_mage_water_chain
        run_mage_water_chain(root, output / "mage_water_chain", binary, pin, context, profile,
                              compose, clean_environment())
        from ninja_s4 import FILES as ninja_s4_files, PROCESS_COUNT as ninja_s4_runs
        from ninja_s4 import run as run_ninja_s4
        run_ninja_s4(root, output / "ninja_s4", binary, pin, context, profile,
                      compose, clean_environment())
        from wing_warrior import FILES as wing_warrior_files, PROCESS_COUNT as wing_warrior_runs
        from wing_warrior import run as run_wing_warrior
        run_wing_warrior(root, output / "wing_warrior", binary, pin, context, profile,
                         compose, clean_environment())
        from fixed_cues import FILES as fixed_cue_files, PROCESS_COUNT as fixed_cue_runs
        from fixed_cues import run as run_fixed_cues
        run_fixed_cues(root, output / "fixed_cues", binary, pin, context, profile,
                       compose, clean_environment())
        from field_loadouts import FILES as field_loadout_files, PROCESS_COUNT as field_loadout_runs
        from field_loadouts import run as run_field_loadouts
        run_field_loadouts(root, output / "field_loadouts", binary, pin, context, profile,
                           compose, clean_environment())
        from first90_role import FILES as first90_role_files, PROCESS_COUNT as first90_role_runs
        from first90_role import run as run_first90_roles
        run_first90_roles(root, output / "first90_role", binary, pin, context, profile,
                          compose, clean_environment())
        from return_convert import FILES as return_convert_files, PROCESS_COUNT as return_convert_runs
        from return_convert import run as run_return_convert
        run_return_convert(root, output / "return_convert", binary, pin, context, profile,
                           compose, clean_environment())
        from ground_night import FILES as ground_night_files, PROCESS_COUNT as ground_night_runs
        from ground_night import run as run_ground_night
        run_ground_night(root, output / "ground_night", binary, pin, context, profile,
                         compose, clean_environment())
        from cover_orders import FILES as cover_orders_files, PROCESS_COUNT as cover_orders_runs
        from cover_orders import run as run_cover_orders
        run_cover_orders(root, output / "cover_orders", binary, pin, context, profile,
                         compose, clean_environment())
        require(source_snapshot(root) == before, "SOURCE_CHANGED_AFTER_BOTH_SUITES")
        require(read(root.parent / compose.RECEIPT) == source_receipt_raw
                and strict_json(read(root.parent / "CORE_BUILD_REPORT.json")) == core,
                "SOURCE_RECEIPT_OR_CONTEXT_CHANGED_DURING_NATIVE")
        require(read(Path(__file__)) == runner_before and read(HERE / "INPUT_LOCK.json") == lock_before,
                "RUNNER_OR_LOCK_CHANGED_DURING_NATIVE")
        fixture_snapshot(lock)
        require(bot_input_snapshot(lock) == bot_before, "BOT_INPUTS_CHANGED_AFTER_ALL_RUNS")
        require({name: evidence_snapshot(output / name) for name in original_outputs} == original_outputs,
                "ORIGINAL_DUAL28_OR_HUD_OUTPUT_CHANGED")
        require(verify_clean_source(source, Path(built["tools"]["git"]["path"]), lock["toolchain"]) == tree_before,
                "TOOLCHAIN_SOURCE_CHANGED_AFTER_SUITES")
        for tool in built["tools"].values():
            require(identity(read(Path(tool["path"]))) == {k: tool[k] for k in ("bytes", "sha256")}, "BUILD_TOOL_CHANGED")
        built["binary_after_suites"] = identity(read(binary))
        require(built["binary_after_suites"] == pin, "BINARY_CHANGED_AFTER_SUITES")
        built["bot_vault_input_files"] = bot_before
        write_json(output / "build_receipt.json", built)
        evidence = evidence_snapshot(output)
        growth_files = sum(name.startswith("growth_musou/") for name in evidence)
        art_files = sum(name.startswith("art_polish_skillfx/") for name in evidence)
        mage_files = sum(name.startswith("mage_contact/") for name in evidence)
        eligibility_files = sum(name.startswith("relay_eligibility/") for name in evidence)
        touch_files = sum(name.startswith("private_touch/") for name in evidence)
        portrait_files = sum(name.startswith("portrait/") for name in evidence)
        team_win_rule_files = sum(name.startswith("team_win_rule/") for name in evidence)
        hp_files = sum(name.startswith("fractional_hp/") for name in evidence)
        current_stage_files = (len(wing_warrior_files) + len(fixed_cue_files)
                               + len(field_loadout_files) + len(first90_role_files) + len(return_convert_files)
                               + len(ground_night_files) + len(cover_orders_files))
        require(len(evidence) == 315 + len(projectile_files) + len(water_chain_files) + len(ninja_s4_files)
                + current_stage_files
                and {name.removeprefix("wing_warrior/") for name in evidence
                     if name.startswith("wing_warrior/")} == wing_warrior_files
                and {name.removeprefix("fixed_cues/") for name in evidence
                     if name.startswith("fixed_cues/")} == fixed_cue_files
                and {name.removeprefix("field_loadouts/") for name in evidence
                     if name.startswith("field_loadouts/")} == field_loadout_files
                and {name.removeprefix("first90_role/") for name in evidence
                     if name.startswith("first90_role/")} == first90_role_files
                and {name.removeprefix("return_convert/") for name in evidence
                     if name.startswith("return_convert/")} == return_convert_files
                and {name.removeprefix("ground_night/") for name in evidence
                     if name.startswith("ground_night/")} == ground_night_files
                and {name.removeprefix("cover_orders/") for name in evidence
                     if name.startswith("cover_orders/")} == cover_orders_files
                and {name.removeprefix("ninja_s4/") for name in evidence
                     if name.startswith("ninja_s4/")} == ninja_s4_files
                and {name.removeprefix("mage_water_chain/") for name in evidence
                     if name.startswith("mage_water_chain/")} == water_chain_files
                and {name.removeprefix("mage_projectiles/") for name in evidence
                     if name.startswith("mage_projectiles/")} == projectile_files
                and growth_files == 103 and art_files == 4 and mage_files == 77
                and eligibility_files == 10 and touch_files == 4 and portrait_files == 4
                and team_win_rule_files == 4 and hp_files == 4,
                "NATIVE_OUTPUT_COUNT_BEFORE_AGGREGATE")
        receipt = {"schema": "UNION22_NATIVE_BOTH_SUITES_V3", "status": "PASS", "profile": "union22",
                   "suite_input_variants": {name: row["input_variant"] for name, row in lock["suites"].items()},
                   "original_combined_case_preserved_not_claimed_as_unchanged_pass": True,
                   "original_objective_case_preserved_not_claimed_as_unchanged_pass": True,
                   "execution_context": context, "source_receipt": identity(source_receipt_raw),
                   "source_inputs_unchanged": True, "source_profile": before,
                   "source_count_pinned": 69, "source_count_executed_full_body": 28,
                   "source_count_executed_full_body_basis": "original_dual28_suites_and_beast_target_selection",
                   "input_lock": identity(lock_before), "runner": identity(runner_before),
                   "build_receipt": identity(read(output / "build_receipt.json")),
                   "suites": {name: identity(read(output / name / "receipt.json")) for name in lock["suites"]},
                   "selected_hud_layout": identity(read(output / "selected_hud_layout/receipt.json")),
                   "bot_vault_supplement": identity(read(output / "bot_vault/receipt.json")),
                   "score_relay_regressions": identity(read(output / "score_relay/receipt.json")),
                   "relay_presentation": identity(read(output / "relay_presentation/receipt.json")),
                   "br_canyon": identity(read(output / "br_canyon/receipt.json")),
                   "role_readability": identity(read(output / "role_readability/receipt.json")),
                   "field_prompt": identity(read(output / "field_prompt/receipt.json")),
                   "foliage_readability": identity(read(output / "foliage_readability/receipt.json")),
                   "guardian_wall": identity(read(output / "guardian_wall/receipt.json")),
                   "combat_visual": identity(read(output / "combat_visual/receipt.json")),
                   "growth_musou": identity(read(output / "growth_musou/receipt.json")),
                   "art_polish_skillfx": identity(read(output / "art_polish_skillfx/receipt.json")),
                   "mage_contact": identity(read(output / "mage_contact/receipt.json")),
                   "relay_eligibility": identity(read(output / "relay_eligibility/receipt.json")),
                   "private_touch": identity(read(output / "private_touch/receipt.json")),
                   "portrait": identity(read(output / "portrait/receipt.json")),
                   "team_win_rule": identity(read(output / "team_win_rule/receipt.json")),
                   "fractional_hp": identity(read(output / "fractional_hp/receipt.json")),
                   "mage_projectiles": identity(read(output / "mage_projectiles/receipt.json")),
                   "mage_water_chain": identity(read(output / "mage_water_chain/receipt.json")),
                   "ninja_s4": identity(read(output / "ninja_s4/receipt.json")),
                   "wing_warrior": identity(read(output / "wing_warrior/receipt.json")),
                   "fixed_cues": identity(read(output / "fixed_cues/receipt.json")),
                   "field_loadouts": identity(read(output / "field_loadouts/receipt.json")),
                   "first90_role": identity(read(output / "first90_role/receipt.json")),
                   "return_convert": identity(read(output / "return_convert/receipt.json")),
                   "ground_night": identity(read(output / "ground_night/receipt.json")),
                   "cover_orders": identity(read(output / "cover_orders/receipt.json")),
                   "bot_vault_input_files": bot_before,
                   "full_body_coverage": {"original_dual28": 28, "beast_target_selection": 28, "bot_vault_each": 16,
                                          "distinct_server_union": 30, "selected_hud_policy": 1,
                                          "hud_policy_separate": True, "distinct_all_full_bodies": 31,
                                          "hud_client_runtime_executed_in_original_suites": False,
                                          "growth_ui_full_bodies_each": 31,
                                          "hud_client_runtime_executed_in_growth": True},
                   "native_process_count": 99 + projectile_runs + water_chain_runs + ninja_s4_runs
                   + wing_warrior_runs + fixed_cue_runs + field_loadout_runs
                   + first90_role_runs + return_convert_runs + ground_night_runs + cover_orders_runs,
                   "native_evidence_file_count": 316 + len(projectile_files) + len(water_chain_files)
                   + len(ninja_s4_files) + current_stage_files,
                   "source_only": True, "formal_rc_adoption_proven": False, "limitations": lock["limitations"]}
        write_json(output / "receipt.json", receipt)
        from run_guardian_diagnostic import run_from_profile
        guardian_result = run_from_profile(root.parent, output, context)
        if guardian_result is not None:
            receipt["guardian_target_diagnostic"] = guardian_result
            write_json(output / "receipt.json", receipt)
        return receipt
    except Exception as error:
        write_json(output / "FAILED.json", {"status": "FAIL_NO_NATIVE_ADMISSION", "reason": str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-root", "luau-source", "build-dir", "out", "cmake", "ninja", "git", "cc", "cxx"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(HERE.parent))
    import compose_union22 as compose
    source_receipt = strict_json(read(args.source_root.parent / compose.RECEIPT))
    context = compose.live_context(source_receipt, args.head)
    run_profile(args.source_root, args.luau_source, args.build_dir, args.out,
                args.cmake, args.ninja, args.git, args.cc, args.cxx, context)
    print("UNION22_NATIVE_FULL_28_BODIES_DUAL_CLEAR_LOS_INPUTS_PASS_SOURCE_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
