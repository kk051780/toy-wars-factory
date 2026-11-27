#!/usr/bin/env python3
"""Build and exercise the bounded GQ618 current69 candidate, never an RC admission.

Reuse the immutable formal producer's route/class verifier, native fixtures and
clean Luau source builder. Keep the original21/current31 contracts untouched.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import patch_current69 as patch

LOCK_SHA256 = "e84135044d6e59c608c11ce85203357040f813857e89599cf13637e147a1908c"
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
BASE = "quality_gameplay/gq470_union22_real69_20261122"
SOURCE_PATHS = (
    "patch_current69.py", "test_patch_current69.py", "README.md",
    "native/run_current69.py", "native/INPUT_LOCK.json",
    "native/beast_fixture.luau", "native/beast_cases.luau",
)
WORKFLOW = ".github/workflows/p0d-gq-beast-escort-20261117.yml"
require, identity, read = patch.require, patch.identity, patch.read_regular


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_lock():
    raw = read(HERE / "INPUT_LOCK.json")
    require(identity(raw)["sha256"] == LOCK_SHA256, "INPUT_LOCK_IDENTITY")
    lock = strict_json(raw)
    require(lock["schema"] == "GQ618_CURRENT69_TARGET_SELECTION_SOURCE_GATE_V1"
            and len(lock["sources"]) == 69, "INPUT_LOCK_SCHEMA")
    require(lock["sources"][patch.COMBAT_PATH]["identity"] == patch.BEFORE
            and lock["combat_after"] == patch.AFTER, "PATCH_LOCK_AGREEMENT")
    return lock


def import_pinned(name, path, expected):
    require(identity(read(path)) == expected, "PINNED_HELPER:" + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_helpers(repo, lock):
    helpers = lock["helpers"]
    compose = import_pinned("gq618_frozen_compose", repo / BASE / "compose_union22.py", helpers["compose"])
    native = import_pinned("gq618_frozen_native", repo / BASE / "native/run_profile.py", helpers["native"])
    native_lock = native.load_lock()
    require(identity(read(repo / BASE / "native/INPUT_LOCK.json")) == helpers["native_lock"], "BASE_NATIVE_LOCK")
    native.fixture_snapshot(native_lock)
    require(native_lock["sources"] == {p: r["identity"] for p, r in lock["sources"].items()},
            "BASE_NATIVE_SOURCE_PROFILE")
    return compose, native, native_lock


def source_snapshot(root):
    require(root.is_dir(), "SOURCE_DIRECTORY")
    sources = {}
    for file in sorted(root.rglob("*")):
        require(not file.is_symlink(), "SOURCE_SYMLINK")
        if file.is_dir():
            continue
        require(file.suffix == ".luau", "EXTRA_SOURCE_FILE")
        sources[file.relative_to(root).as_posix()] = read(file)
    return sources


def validate_payload(folder, lock, compose):
    sources = source_snapshot(folder / "sources")
    require({p: identity(raw) for p, raw in sources.items()} ==
            {p: r["identity"] for p, r in lock["sources"].items()}, "EXACT_69_SOURCE_PROFILE")
    project, place = read(folder / PROJECT), read(folder / PLACE)
    require(identity(project) == lock["project"] and identity(place) == lock["place_before"],
            "BASE_PROJECT_OR_PLACE_IDENTITY")
    inventory = compose.project_inventory(project)
    require(inventory == {p: {"route": r["route"], "class": r["class"]}
                          for p, r in lock["sources"].items()}, "PROJECT_ROUTE_CLASS")
    embedded, non_source = compose.place_inventory(place)
    require(embedded == {r["route"]: {"class": r["class"], "raw": sources[p]}
                         for p, r in lock["sources"].items()}, "BASE_EMBEDDED_69_EXACT")
    return sources, project, place, non_source


def validate_outputs(artifact, luau_source, build, output, baseline_repo=None):
    roots = [p.absolute() for p in (artifact, luau_source, build, output)]
    if baseline_repo is not None:
        roots.append(baseline_repo.absolute())
    require(all(not any(q.is_symlink() for q in (p, *p.parents)) for p in roots), "DIRECTORY_SYMLINK")
    # Normalize '..' only after inspecting the original path for symlinks.
    # Lexical absolute paths alone can alias an immutable input directory.
    roots = [p.resolve(strict=False) for p in roots]
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for i, a in enumerate(roots) for b in roots[i + 1:]), "INPUT_OUTPUT_OVERLAP")
    require(not build.exists() and not output.exists(), "BUILD_AND_OUTPUT_MUST_BE_NEW")


def source_context(expected_head, ci):
    repo = HERE.parents[2]
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, check=True)
    head = result.stdout.decode().strip()
    require(re.fullmatch(r"[0-9a-f]{40}", head), "GIT_HEAD")
    paths = [HERE.parent / p for p in SOURCE_PATHS] + [repo / WORKFLOW]
    files = {p.relative_to(repo).as_posix(): identity(read(p)) for p in paths}
    context = {"kind": "LOCAL_SOURCE_ONLY", "checkout_head": head, "files": files,
               "official_rc_adopted": False, "observed_at_utc": datetime.now(timezone.utc).isoformat()}
    if ci:
        require(os.environ.get("GITHUB_ACTIONS") == "true" and head == expected_head,
                "CI_CHECKOUT_HEAD")
        event_name = os.environ.get("GITHUB_EVENT_NAME")
        event = strict_json(read(Path(os.environ["GITHUB_EVENT_PATH"])))
        event_head = event["pull_request"]["head"]["sha"] if event_name == "pull_request" else os.environ.get("GITHUB_SHA")
        require(event_name in ("pull_request", "workflow_dispatch") and event_head == head,
                "CI_EVENT_HEAD")
        for name, pin in files.items():
            blob = subprocess.run(["git", "-C", str(repo), "show", head + ":" + name],
                                  capture_output=True, check=True).stdout
            require(identity(blob) == pin, "CI_UNCOMMITTED_SOURCE:" + name)
        run_id, attempt = os.environ.get("GITHUB_RUN_ID", ""), os.environ.get("GITHUB_RUN_ATTEMPT", "")
        require(run_id.isdigit() and attempt.isdigit(), "CI_PROVIDER_IDENTITY")
        context.update(kind="SAME_PR_HEAD_SOURCE_GATE", event=event_name, run_id=run_id, run_attempt=attempt)
    return context


def exact_cases(stdout, expected_names, failures):
    rows = [line.split("\t", 3) for line in stdout.decode("utf-8").splitlines() if line.startswith("CASE\t")]
    require(len(rows) == len(expected_names) and all(len(row) == 4 for row in rows)
            and [row[1] for row in rows] == expected_names, "EXACT_CASE_VECTOR")
    require(all(row[2] == ("FAIL" if row[1] in failures else "PASS") for row in rows), "CASE_OUTCOME_VECTOR")
    return rows


def verify_body_bindings(program, ranges, sources):
    require(len(ranges) == 28, "FULL_28_BODY_COUNT")
    for name, row in ranges.items():
        require(name in sources and {k: row[k] for k in ("bytes", "sha256")} == identity(sources[name])
                and program[row["start"]:row["end"]] == sources[name],
                "EXECUTED_BODY_DIFFERS_FROM_COMPILED_SOURCE:" + name)


def verify_built_profiles(output, selected, project, profiles):
    for label, sources in selected.items():
        folder = output / label
        require(source_snapshot(folder / "sources") == sources, "FINAL_SOURCE_PROFILE_CHANGED:" + label)
        require(read(folder / PROJECT) == project, "FINAL_PROJECT_CHANGED:" + label)
        require(identity(read(folder / PLACE)) == profiles[label]["place"], "FINAL_PLACE_CHANGED:" + label)


def assemble_beast(sources, native, native_lock, lock):
    code = "".join(read(native.HERE / "fixtures" / name).decode() + "\n"
                   for name in native_lock["fixture_order"])
    for name in ("beast_fixture.luau", "beast_cases.luau"):
        require(identity(read(HERE / name)) == lock["new_fixtures"][name], "BEAST_FIXTURE_IDENTITY:" + name)
    code += read(HERE / "beast_fixture.luau").decode() + "\n"
    ranges = {}
    for name in native_lock["modules_in_load_order"] + ["LobbyCastleModesPreview.server"]:
        rel = "ServerScriptService/EGGRUMBLE_" + name + ".luau"
        raw = sources[rel]
        if name == "LobbyCastleModesPreview.server":
            code += "\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n"
        else:
            code += "\nloadingModule='" + name + "'\n"
            first = code.count("\n") + 3
            code += f"fullSourceRanges.{name}={{first={first},last={first + raw.count(bytes([10]))}}}\n"
            code += "dependencies.EGGRUMBLE_" + name + "=(function()\n"
        first_byte = len(code.encode())
        code += raw.decode()
        ranges[rel] = {"start": first_byte, "end": len(code.encode()), **identity(raw)}
        code += "\nend)()end\n" if name == "LobbyCastleModesPreview.server" else "\nend)()\n"
    code += "\n" + read(HERE / "beast_cases.luau").decode()
    generated = code.encode()
    verify_body_bindings(generated, ranges, sources)
    return generated, ranges


def execute(binary, program, ranges, out, expected_names, failures, native):
    out.mkdir(exist_ok=False)
    generated = out / "generated.luau"
    generated.write_bytes(program)
    result = subprocess.run([str(binary), str(generated)], env=native.clean_environment(),
                            capture_output=True, timeout=60)
    (out / "stdout.log").write_bytes(result.stdout)
    (out / "stderr.log").write_bytes(result.stderr)
    expected_exit = 1 if failures else 0
    require(result.returncode == expected_exit, "NATIVE_EXIT:" + out.name)
    rows = exact_cases(result.stdout, expected_names, failures)
    if failures:
        require(b"RED_BEAST_FULL_SOURCE_TARGET_SELECTION" in result.stderr, "EXPECTED_REPRODUCTION_ASSERTION")
    require(read(generated) == program, "GENERATED_PROGRAM_MUTATED")
    receipt = {"status": "EXPECTED_BASELINE_REPRODUCTION" if failures else "PASS_SOURCE_FIXTURE_ONLY",
               "exit_code": result.returncode, "cases": rows, "expected_failures": sorted(failures),
               "generated": identity(program), "stdout": identity(result.stdout), "stderr": identity(result.stderr),
               "full_body_count": len(ranges), "full_body_byte_ranges": ranges,
               "studio_tested": False, "humanoid_move_to": "RECORD_ONLY_NOT_PHYSICS"}
    write_json(out / "receipt.json", receipt)
    print(out.name + ": " + str(len(rows)) + " exact cases; expected failures=" + str(len(failures)), flush=True)
    return receipt


def run(args):
    lock = load_lock()
    artifact, baseline_repo, luau_source, build, output = [p.absolute() for p in
        (args.artifact_dir, args.baseline_repo, args.luau_source, args.build_dir, args.out)]
    validate_outputs(artifact, luau_source, build, output, baseline_repo)
    context = source_context(args.expected_head, args.ci)
    compose, native, native_lock = load_helpers(baseline_repo, lock)
    original, project, old_place, non_source = validate_payload(artifact, lock, compose)
    history = {p: identity(read(HERE.parent / p)) for p in lock["historical_files"]}
    require(history == lock["historical_files"], "HISTORICAL_21_31_CONTRACT_CHANGED")
    rojo = args.rojo.absolute()
    require(identity(read(rojo)) == lock["rojo"] and os.access(rojo, os.X_OK), "PINNED_ROJO")
    on = dict(original)
    on[patch.COMBAT_PATH] = patch.transform(original[patch.COMBAT_PATH])
    off = dict(on)
    off[patch.COMBAT_PATH] = patch.transform(on[patch.COMBAT_PATH], "off")
    require(off == original and [p for p in original if original[p] != on[p]] == [patch.COMBAT_PATH],
            "ONE_CHANGED_SOURCE_AND_EXACT_INVERSE")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "context.json", context)
    try:
        build_evidence = output / "toolchain"
        build_evidence.mkdir()
        tool_paths = [getattr(args, option) or Path(shutil.which(command) or "")
                      for option, command in (("cmake", "cmake"), ("ninja", "ninja"),
                                              ("git", "git"), ("cc", "cc"), ("cxx", "c++"))]
        binary, built, tree_before = native.build_repl(luau_source, build, build_evidence, native_lock, *tool_paths)
        binary_pin = identity(read(binary))
        compiler = build / "luau-compile"
        require(not compiler.exists(), "FRESH_COMPILER_REQUIRED")
        started = time.time_ns()
        compile_build = native.command_log([tool_paths[0], "--build", build, "--target", "Luau.Compile.CLI", "--parallel", "2"],
                                          build_evidence, "compiler_build", 900)
        require(compiler.is_file() and compiler.stat().st_mtime_ns >= started
                and b"Linking CXX executable luau-compile" in read(build_evidence / "compiler_build.stdout.log"),
                "FRESH_COMPILER_BUILD")
        compiler_pin = identity(read(compiler))
        profiles = {}
        for label, sources in (("on", on), ("off", off)):
            folder = output / label
            folder.mkdir()
            (folder / PROJECT).write_bytes(project)
            for name, raw in sources.items():
                file = folder / "sources" / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(raw)
                result = subprocess.run([str(compiler), "--text", str(file)], env=native.clean_environment(),
                                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
                require(result.returncode == 0, "NATIVE_COMPILE:" + name)
            command = native.command_log([rojo, "build", folder / PROJECT, "-o", folder / PLACE], folder, "rojo", 60)
            actual = read(folder / PLACE)
            embedded, properties = compose.place_inventory(actual)
            require(properties == non_source, "NON_SOURCE_PROPERTIES_CHANGED")
            require(embedded == {r["route"]: {"class": r["class"], "raw": sources[p]}
                                 for p, r in lock["sources"].items()}, "BUILT_ROUTE_CLASS_SOURCE_69")
            require(source_snapshot(folder / "sources") == sources, "BUILD_SOURCE_MUTATION")
            if label == "off":
                require(actual == old_place, "OFF_PLACE_NOT_BYTE_EXACT")
            profiles[label] = {"source_count": 69, "compiled": 69, "embedded_exact": 69,
                               "place": identity(actual), "rojo_command": command,
                               "sources": {p: identity(raw) for p, raw in sources.items()}}
        suites = {}
        baseline_program = None
        for label, sources in (("baseline", original), ("on", on), ("off", off)):
            program, ranges = assemble_beast(sources, native, native_lock, lock)
            if label == "baseline":
                baseline_program = program
            if label == "off":
                require(program == baseline_program, "OFF_FULL_PROGRAM_NOT_EXACT_BASELINE")
            failures = set() if label == "on" else set(lock["baseline_failures"])
            suites["beast_" + label] = execute(binary, program, ranges, output / ("beast_" + label),
                lock["expected_cases"], failures, native)
        for name in ("combined_clear_los", "objective_full_clear_los"):
            program, line_ranges, byte_ranges = native.assemble(output / "on/sources", native_lock, name)
            verify_body_bindings(program, byte_ranges, on)
            suites[name] = execute(binary, program, byte_ranges, output / name,
                native_lock["suites"][name]["expected_case_names"], set(), native)
        verify_built_profiles(output, {"on": on, "off": off}, project, profiles)
        require(source_snapshot(artifact / "sources") == original, "BASE_SOURCE_MUTATED")
        require(read(artifact / PROJECT) == project and read(artifact / PLACE) == old_place, "BASE_PAYLOAD_MUTATED")
        require(identity(read(binary)) == binary_pin and identity(read(compiler)) == compiler_pin
                and identity(read(rojo)) == lock["rojo"], "TOOL_CHANGED")
        require(native.verify_clean_source(luau_source, tool_paths[2], native_lock["toolchain"]) == tree_before,
                "LUAU_SOURCE_CHANGED")
        for tool in built["tools"].values():
            require(identity(read(Path(tool["path"]))) == {k: tool[k] for k in ("bytes", "sha256")},
                    "BUILD_TOOL_CHANGED")
        for name in ("CMakeCache.txt", "build.ninja"):
            require(read(build / name) == read(build_evidence / name), "BUILD_RECIPE_CHANGED:" + name)
        load_helpers(baseline_repo, lock)
        require(source_context(args.expected_head, args.ci)["files"] == context["files"], "GATE_SOURCE_CHANGED")
        require({p: identity(read(HERE.parent / p)) for p in history} == history, "HISTORICAL_SOURCE_MUTATED")
        built.update(binary_after_suites=binary_pin, compiler=compiler_pin, compiler_build=compile_build)
        write_json(build_evidence / "build_receipt.json", built)
        receipt = {"schema": "GQ618_CURRENT69_BUILD_AND_BEHAVIOR_V1", "status": "PASS_SOURCE_CANDIDATE_ONLY",
                   "execution_context": context, "base": lock["formal_base"], "feature_id": patch.FEATURE_ID,
                   "input_lock": identity(read(HERE / "INPUT_LOCK.json")), "changed_sources": [patch.COMBAT_PATH],
                   "unchanged_source_count": 68, "profiles": profiles, "actual_inverse_sources_and_place_exact": True,
                   "native_suites": suites, "native_full_body_count_per_suite": 28,
                   "compile_count": 138, "rojo_build_count": 2,
                   "toolchain_receipt": identity(read(build_evidence / "build_receipt.json")),
                   "historical_contracts_preserved": history, "official_rc_adopted": False,
                   "limitations": lock["limitations"]}
        write_json(output / "receipt.json", receipt)
        print("GQ618_CURRENT69_SOURCE_GATE_PASS_NOT_OFFICIAL_ADOPTION", flush=True)
        return receipt
    except Exception as error:
        write_json(output / "FAILED.json", {"status": "FAIL_NO_ADMISSION", "error": str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("artifact-dir", "baseline-repo", "luau-source", "build-dir", "out", "rojo"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("cmake", "ninja", "git", "cc", "cxx"):
        parser.add_argument("--" + name, type=Path,
                            help="Actual tool executable; otherwise locate it on PATH")
    parser.add_argument("--expected-head")
    parser.add_argument("--ci", action="store_true")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
