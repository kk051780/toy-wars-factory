#!/usr/bin/env python3
"""Fresh current69 Native comparison of two existing Guardian repairs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from apply_existing_repairs import HERE, ROLE, VARIANTS, identity, load_lock, load_frozen_role, transform

PACKAGE = ("apply_existing_repairs.py", "INPUT_LOCK.json", "run.py", "README.md",
           "case.luau", "fixture_boundary.luau")


def require(ok, reason):
    if not ok:
        raise ValueError("GQ815_COMBINED_" + reason)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_role_runner(lock):
    adapter = load_frozen_role(lock)
    require("apply_role_snapshot" not in sys.modules, "AMBIGUOUS_ROLE_IMPORT")
    sys.modules["apply_role_snapshot"] = adapter
    spec = importlib.util.spec_from_file_location("gq815_frozen_role_runner", ROLE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner, json.loads((ROLE / "INPUT_LOCK.json").read_text())


def case_inputs(lock, native):
    los = lock["los_test_inputs"]
    container = (HERE / "case.luau").read_bytes()
    require(identity(container) == los["case_container"], "REUSED_CASE_CONTAINER_DRIFT")
    require(identity((HERE / "fixture_boundary.luau").read_bytes()) == los["fixture_boundary"],
            "REUSED_LOS_FIXTURE_DRIFT")
    for name, expected in los["first_three_fixture_pins"].items():
        require(identity((native / "fixtures" / name).read_bytes()) == expected, "ORIGINAL_FIXTURE_DRIFT:" + name)
    extracted = {}
    for name, row in los["embedded_case_ranges"].items():
        raw = container[row["start"]:row["end"]]
        require(identity(raw) == {key: row[key] for key in ("bytes", "sha256")}, "ORIGINAL_CASE_RANGE_DRIFT:" + name)
        extracted[name] = raw
    return extracted


def assemble_los(root, native, lock, scenario):
    los = lock["los_test_inputs"]
    extracted = case_inputs(lock, native)
    code = b"".join((native / "fixtures" / name).read_bytes() + b"\n"
                    for name in los["fixture_order"][:3])
    code += (HERE / "fixture_boundary.luau").read_bytes() + b"\n"
    ranges = {}
    for name in los["modules_in_load_order"] + [los["host_loaded_last"]]:
        rel = "ServerScriptService/EGGRUMBLE_" + name + ".luau"
        raw = (root / rel).read_bytes()
        if name == los["host_loaded_last"]:
            code += b"\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n"
        else:
            code += f"\nloadingModule='{name}'\n".encode()
            line = code.count(b"\n") + 3
            code += f"fullSourceRanges.{name}={{first={line},last={line+raw.count(bytes([10]))}}}\n".encode()
            code += f"dependencies.EGGRUMBLE_{name}=(function()\n".encode()
            require(code.count(b"\n") + 1 == line, "LOS_SOURCE_LINE_RANGE")
        start = len(code)
        code += raw
        ranges[rel] = {"start": start, "end": len(code), **identity(raw)}
        code += b"\nend)()end\n" if name == los["host_loaded_last"] else b"\nend)()\n"
    code += b"\n" + extracted["common_setup.luau"] + b"\n" + extracted[scenario + "_case.luau"]
    require(len(ranges) == los["full_body_count"] == 28, "LOS_FULL_BODY_COUNT")
    for rel, row in ranges.items():
        require(code[row["start"]:row["end"]] == (root / rel).read_bytes(), "LOS_FULL_BODY_CHANGED")
    return code, ranges


def los_protocol(stdout, stderr, exit_code, has_los, scenario, program, contract):
    # Preserve the original reviewer's IDs/status/order, exact known-negative
    # stderr and trace predicates; four-state selection replaces its two labels.
    rows = [line.split("\t") for line in stdout.splitlines() if line.startswith("CASE\t")]
    require(all(len(row) == 4 and row[3].strip() for row in rows), "LOS_CASE_SHAPE")
    negative = not has_los and scenario == "gate"
    key = "gate_without_los" if negative else ("gate_positive" if scenario == "gate" else "wall_all_variants")
    require([[row[1], row[2]] for row in rows] == contract["expected_cases"][key], "LOS_EXACT_CASE_VECTOR")
    require(exit_code == (1 if negative else 0), "LOS_PROCESS_EXIT")
    if negative:
        code = program.read_text()
        anchor, footer = contract["assertion_line_anchor"], contract["error_footer_anchor"]
        require(code.count(anchor) == code.count(footer) == 1, "LOS_KNOWN_ERROR_ANCHORS")
        assertion_line = code[:code.index(anchor)].count("\n") + 1
        footer_line = code[:code.index(footer)].count("\n") + 1
        error = str(program.resolve()) + ":" + str(assertion_line) + ": " + contract["known_gate_failure"]
        require(rows[-1][3] == error, "LOS_KNOWN_NUMERIC_FAILURE")
        expected_stderr = contract["strict_negative_stderr_template"].format(
            absolute_generated_path=str(program.resolve()), assertion_line=assertion_line, footer_line=footer_line)
        require(stderr == expected_stderr, "LOS_EXACT_NEGATIVE_STDERR")
    else:
        require(not stderr, "LOS_POSITIVE_STDERR")
    traces = [line.split("\t") for line in stdout.splitlines() if line.startswith("TRACE\t")]
    ids = [row[1] for row in traces]
    if scenario == "gate":
        require(ids == ["SPAWN", "GATE", "GATE_OUTGOING"] + ([] if negative else ["GATE_INCOMING"]), "LOS_GATE_TRACE_IDS")
        require(traces[2][6:] == (["nil", "SiegeGate", "HP100"] if negative else ["true", "CLEAR", "HP94"]), "LOS_GATE_TRACE_OUTCOME")
    else:
        require(ids == ["SPAWN", "GATE", "REAL_WALL"] + ["WALL_OUTGOING"] * 10 + ["WALL_INCOMING"], "LOS_WALL_TRACE_IDS")
        require(all(row[6:] == (["true", "CastleFrontRight"] if has_los else ["nil", "CastleFrontRight"])
                    for row in traces if row[1] == "WALL_OUTGOING"), "LOS_WALL_TRACE_OUTCOME")
    return rows, traces


def execute_los(binary, code, ranges, output, has_los, scenario, lock):
    output.mkdir()
    program = output / "generated.luau"
    program.write_bytes(code)
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(binary), str(program)], capture_output=True, timeout=90)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    stdout, stderr = result.stdout.decode(), result.stderr.decode()
    rows, traces = los_protocol(stdout, stderr, result.returncode, has_los, scenario, program, lock["los_test_inputs"])
    receipt = {"started_at_utc": started, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
               "exit": result.returncode, "has_outgoing_los_repair": has_los,
               "exact_expected_vector": True, "expected_process_result": True,
               "expected_known_negative": not has_los and scenario == "gate",
               "cases": ["\t".join(row) for row in rows], "traces": traces,
               "generated": identity(code), "full_body_count": len(ranges), "full_body_ranges": ranges,
               "stdout": identity(result.stdout), "stderr": identity(result.stderr)}
    write_json(output / "receipt.json", receipt)
    require(program.read_bytes() == code, "LOS_GENERATED_MUTATED")
    print(output.name + ": " + ("EXPECTED_BASELINE_RED" if receipt["expected_known_negative"] else "PASS"), flush=True)
    return {"receipt": identity((output / "receipt.json").read_bytes()), "case_count": len(rows),
            "expected_failure_count": int(receipt["expected_known_negative"]), "exit": result.returncode}, traces


def plane_crossing(row, z_plane, x_bounds, y_bounds):
    # Original independent analytic plane check, separate from fixture slab ray.
    origin = [float(x) for x in row[3].split(",")]
    target = [float(x) for x in row[4].split(",")]
    require(len(origin) == len(target) == 3 and all(math.isfinite(x) for x in origin + target), "LOS_FINITE_THREE_VECTOR_COMPONENTS")
    t = (z_plane - origin[2]) / (target[2] - origin[2])
    x = origin[0] + t * (target[0] - origin[0])
    y = origin[1] + t * (target[1] - origin[1])
    require(0 < t < 1 and x_bounds[0] < x < x_bounds[1] and y_bounds[0] < y < y_bounds[1], "LOS_PLANE_CROSSING")
    if row[1].endswith("OUTGOING"):
        distance = math.dist(origin, target)
        require(distance < 17 and abs(distance - float(row[5])) < 2e-8, "LOS_RAY_RANGE")
    return {"trace": row[1], "at": float(row[2]), "t": t, "point": [x, y, z_plane]}


def run(args, role_runner, role_lock, lock):
    require(not args.output.is_symlink() and not args.build_dir.is_symlink(), "OUTPUT_SYMLINK")
    root, rc, output, build, luau_source = [p.resolve() for p in
        (args.sources, args.rc_root, args.output, args.build_dir, args.luau_source)]
    require(not output.exists() and not build.exists(), "NEW_OUTPUT_AND_BUILD_REQUIRED")
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for a in (output, build) for b in (root, rc, luau_source, HERE.parent)), "DIRECTORY_OVERLAP")
    require(not output.is_relative_to(build) and not build.is_relative_to(output), "OUTPUT_BUILD_OVERLAP")
    before = role_runner.snapshot(root)
    require(before == role_lock["sources"] and len(before) == 69, "OFFICIAL69_IDENTITY")
    require(lock["official_rc"] == role_lock["official_rc"], "RC_INPUT_BINDING")
    package = {name: identity((HERE / name).read_bytes()) for name in PACKAGE}
    native = rc / role_lock["native_relative_path"]
    module, native_lock = role_runner.load_native(native, role_lock)
    case_inputs(lock, native)
    output.mkdir(parents=True)
    st = output.stat()
    args.owned_output = (output, st.st_dev, st.st_ino)
    for name in PACKAGE:
        shutil.copyfile(HERE / name, output / name)
    shutil.copytree(ROLE, output / "frozen_role_package", ignore=shutil.ignore_patterns("__pycache__"))
    tool_output = output / "toolchain"
    tool_output.mkdir()
    binary, built, tree_before = module.build_repl(luau_source, build, tool_output, native_lock,
        args.cmake, args.ninja, args.git, args.cc, args.cxx)
    module.command_log([args.cmake, "--build", build, "--target", "Luau.Compile.CLI", "--parallel", "2"],
                       tool_output, "compile_target", 900)
    compiler = build / "luau-compile"
    original = (root / lock["guardian"]["path"]).read_bytes()
    variants = {name: original if name == "baseline" else transform(original, "baseline", name) for name in VARIANTS}
    transitions = []
    for source in VARIANTS:
        for target in VARIANTS:
            if source != target:
                require(transform(variants[source], source, target) == variants[target], "PARTIAL_OR_FULL_INVERSE")
                transitions.append({"from": source, "to": target})
    rejected = []
    for name, raw, source, target in (("already_applied", variants["combined"], "baseline", "combined"),
            ("truncated", original[:-1], "baseline", "combined"),
            ("unrelated_append", original + b"\n", "baseline", "combined"),
            ("wrong_partial_origin", variants["role_only"], "los_only", "combined"),
            ("identity_transition", original, "baseline", "baseline")):
        try:
            transform(raw, source, target)
        except ValueError:
            rejected.append(name)
    require(len(rejected) == 5, "PATCH_FAIL_CLOSED")
    for name, raw in variants.items():
        (output / (name + "_guardian.luau")).write_bytes(raw)
    (output / "inverse_guardian.luau").write_bytes(transform(variants["combined"], "combined", "baseline"))
    results, traces = {}, {}
    with tempfile.TemporaryDirectory(prefix="gq815-role-los-") as tmp:
        selected = Path(tmp) / "sources"
        shutil.copytree(root, selected)
        for variant, raw in variants.items():
            has_role, has_los = VARIANTS[variant]
            (selected / lock["guardian"]["path"]).write_bytes(raw)
            expected = dict(before)
            expected[lock["guardian"]["path"]] = identity(raw)
            require(role_runner.snapshot(selected) == expected, "OTHER68_SOURCE_CHANGED")
            if variant in ("baseline", "combined"):
                role_runner.compile_sources(compiler, selected, output / (variant + "_compile69.json"), module)
            for scenario, contract in role_lock["role_cases"].items():
                code, ranges = role_runner.assemble_role(selected, native, role_lock, scenario)
                key = variant + "_role_" + scenario
                results[key] = role_runner.execute(binary, code, ranges, output / key, contract["expected_names"],
                    [] if has_role else contract["baseline_fail_names"], contract["baseline_error"])
            for scenario in ("gate", "wall"):
                code, ranges = assemble_los(selected, native, lock, scenario)
                key = variant + "_los_" + scenario
                results[key], traces[key] = execute_los(binary, code, ranges, output / key, has_los, scenario, lock)
            for scenario in role_lock["official_regressions"]:
                code, _, ranges = module.assemble(selected, native_lock, scenario)
                key = variant + "_" + scenario
                results[key] = role_runner.execute(binary, code, ranges, output / key,
                    native_lock["suites"][scenario]["expected_case_names"], [])
            require(role_runner.snapshot(selected) == expected, "SELECTED_SOURCES_MUTATED")
    gate = traces["combined_los_gate"][2]
    walls = [row for row in traces["combined_los_wall"] if row[1] == "WALL_OUTGOING"]
    require(len(walls) == 10 and float(walls[-1][2]) - float(walls[0][2]) > 2.7, "TEN_WALL_RAYS")
    for variant in VARIANTS:
        require(traces[variant + "_los_gate"][2][:6] == gate[:6], "SAME_FIRST_GATE_QUERY")
        other = [row for row in traces[variant + "_los_wall"] if row[1] == "WALL_OUTGOING"]
        require([row[:6] for row in other] == [row[:6] for row in walls], "SAME_TEN_WALL_QUERIES")
    geometry = [plane_crossing(gate, 247, (-479.5, -470.5), (6, 14))]
    geometry += [plane_crossing(row, 248, (-470, -460), (6, 18)) for row in walls]
    geometry += [plane_crossing(traces["combined_los_gate"][-1], 247, (-479.5, -470.5), (6, 14)),
                 plane_crossing(traces["combined_los_wall"][-1], 246, (-470, -460), (6, 18))]
    require(len(results) == 24, "EXPECTED_TWENTY_FOUR_SUITES")
    require(role_runner.snapshot(root) == before, "ORIGINAL69_MUTATED")
    require({name: identity((HERE / name).read_bytes()) for name in PACKAGE} == package, "PACKAGE_MUTATED")
    load_frozen_role(lock)
    module.fixture_snapshot(native_lock)
    require(identity(binary.read_bytes()) == built["binary_before_suites"], "NATIVE_BINARY_CHANGED")
    require(module.verify_clean_source(luau_source, Path(built["tools"]["git"]["path"]), native_lock["toolchain"]) == tree_before,
            "LUAU_SOURCE_CHANGED")
    built["binary_after_suites"] = identity(binary.read_bytes())
    built["compile_binary"] = identity(compiler.read_bytes())
    write_json(tool_output / "receipt.json", built)
    receipt = {"schema": "GQ815_ROLE170_LOS30_COMBINED_NATIVE_RESULT_V1", "status": "PASS_EXISTING_REPAIRS_COMBINED_NATIVE",
               "official_rc_input": lock["official_rc"], "official_rc_adopted": False, "PREP_READY": False,
               "guardian": lock["guardian"], "other68_byte_exact": True, "source69_unchanged": True,
               "package": package, "frozen_role_package": lock["frozen_role_package"],
               "exact_transitions": transitions, "negative_patch_inputs_rejected": rejected,
               "results": results, "independent_analytic_geometry": geometry,
               "same_four_state_first_gate_and_ten_wall_queries": True,
               "toolchain": identity((tool_output / "receipt.json").read_bytes()),
               "studio": "NOT_TESTED", "android": "NOT_TESTED", "fun": "NOT_TESTED", "art": "ART_NO_GO",
               "limitations": lock["limitations"]}
    write_json(output / "RESULT.json", receipt)
    print(json.dumps({"status": receipt["status"], "suites": len(results), "guardian": lock["guardian"],
                      "official_rc_adopted": False}, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sources", "rc-root", "output", "build-dir", "luau-source"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name, default in (("cmake", "cmake"), ("ninja", "ninja"), ("git", "git"), ("cc", "cc"), ("cxx", "c++")):
        parser.add_argument("--" + name, default=shutil.which(default), type=Path)
    args = parser.parse_args()
    args.owned_output = None
    lock = load_lock()
    role_runner, role_lock = load_role_runner(lock)
    try:
        run(args, role_runner, role_lock, lock)
    except Exception as exc:
        role_runner.record_failure(args.owned_output, exc)
        raise


if __name__ == "__main__":
    main()
