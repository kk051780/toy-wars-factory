"""Re-run the two original role-readability contracts on the composed source."""

from __future__ import annotations

import ast
import json
import subprocess
import sys


MOTION_RUNNER = "quality_gameplay/gq470_role_motion_real69_20261121/test_native_cast_wiring.py"
MOTION_FILES = {"REPORT.json", "contract.luau", "compile.stdout.log", "compile.stderr.log",
                "native.stdout.log", "native.stderr.log"}
WEAPON_FILES = {"generated.luau", "parts.tsv", "stderr.log"}
FILE_NAMES = {"receipt.json", "reference.client.luau"} | {
    f"motion/{name}" for name in MOTION_FILES
} | {f"weapon/{name}" for name in WEAPON_FILES}


def inputs(root, profile, compose):
    lock = profile["role_readability_followup"]
    previous = root.parent / compose.ROLE_READABILITY_OFF / "sources"
    for path, pin in lock["original_motion_files"].items():
        compose.need(compose.identity(compose.read_file(compose.REPO / path)) == pin, "ROLE_AUTHOR_FILE:" + path)
    current = {name: compose.read_file(root / name) for name in compose.ROLE_READABILITY_SOURCES}
    old = {name: compose.read_file(previous / name) for name in compose.ROLE_READABILITY_SOURCES}
    for name, body in current.items():
        compose.need(compose.identity(body) == profile["sources"][name]["after"]
                     and compose.identity(old[name]) == lock["rows"][name]["parent"]["after"],
                     "ROLE_SELECTED_SOURCE:" + name)
    original_motion = compose.apply_hunks(old[compose.ROLE_MOTION_SOURCE], lock["motion_reference_hunks"])
    fixture = lock["weapon_fixture"].encode()
    old_weapon = lock["weapon_previous"].encode()
    compose.need(compose.identity(original_motion) == lock["motion_reference"]
                 and compose.identity(fixture) == lock["weapon_fixture_pin"]
                 and compose.identity(old_weapon) == lock["weapon_previous_pin"], "ROLE_CONTROL_FIXTURES")
    for label, source in (("RC", old[compose.ROLE_WEAPON_SOURCE]), ("V2", old_weapon),
                          ("FACETS", current[compose.ROLE_WEAPON_SOURCE])):
        compose.need(b"]===]" not in source, "ROLE_WEAPON_LITERAL")
        fixture += b'\nscan("' + label.encode() + b'",[===[' + source + b']===])\n'
    return lock, current, original_motion, fixture


def motion_input(root, profile, compose):
    path = compose.ROLE_MOTION_SOURCE
    camera = profile.get("zombie_formation_camera_followup")
    if not camera:
        return root, compose.read_file(root / path)
    # The immutable #943 fixture models pose callbacks. The current camera
    # API and current full client are verified in zombie_formation_camera.
    old = root.parent / compose.ZOMBIE_FORMATION_CAMERA_OFF / "sources"
    body = compose.read_file(old / path)
    compose.need(compose.identity(body) == camera["rows"][path]["parent"]["after"],
                 "ROLE_HISTORICAL_PRE_CAMERA_SOURCE")
    return old, body


def check_runs(root, path, profile, compose, binary_pin, context):
    lock, current, reference, weapon_program = inputs(root, profile, compose)
    read, pin = compose.read_file, compose.identity
    require = compose.need
    expected = compose.REPO / MOTION_RUNNER
    source = read(expected)
    strings = {name.id: ast.literal_eval(statement.value)
               for statement in ast.parse(source).body if isinstance(statement, ast.Assign)
               for name in statement.targets if isinstance(name, ast.Name)
               and name.id in {"FIXTURE_TEXT", "CASES_TEXT", "CASES"}}
    _, motion_body = motion_input(root, profile, compose)
    expected_parts = [strings["FIXTURE_TEXT"].encode()]
    for name, body in (("candidateBody", motion_body), ("referenceBody", reference)):
        expected_parts.append(("\nlocal function " + name + "(env)\n"
                               " local game=env.game\n local workspace=env.workspace\n"
                               " local os={clock=function() return env.now end}\n"
                               " -- BEGIN BYTE-EXACT PRODUCT SOURCE\n").encode())
        expected_parts.extend((body, b"\n -- END BYTE-EXACT PRODUCT SOURCE\nend\n"))
    expected_parts.append(b"\n" + strings["CASES_TEXT"].encode())
    motion_program = b"".join(expected_parts)
    motion = path / "motion"
    report = compose.strict_json(read(motion / "REPORT.json"))
    names = strings["CASES"]
    stdout = read(motion / "native.stdout.log")
    rows = [line.split("\t") for line in stdout.decode().splitlines() if line.startswith("CASE\t")]
    require(read(path / "reference.client.luau") == reference
            and read(motion / "contract.luau") == motion_program and report["generated"] == pin(motion_program)
            and {key: report["source"][key] for key in ("bytes", "sha256")} == pin(motion_body)
            and report["runner"] == pin(source) == lock["original_motion_files"][MOTION_RUNNER]
            and report["all_inputs_unchanged"] and report["expectation_observed"]
            and report["expected_result"] == "green"
            and report["case_names"] == names and len(names) == 20
            and len(rows) == 20 and all(len(row) == 4 and row[2] == "PASS" for row in rows)
            and [row[1] for row in rows] == names
            and report["summary"] == {"total": 20, "passed": 20, "failed": 0}
            and report["native"]["exit_code"] == report["compile"]["exit_code"] == 0
            and {key: report["cached_native_binary"][key] for key in ("bytes", "sha256")} == binary_pin
            and not read(motion / "native.stderr.log"), "ROLE_MOTION_ORIGINAL_CONTRACT")
    weapon = path / "weapon"
    outputs = read(weapon / "parts.tsv").replace(b"\r\n", b"\n")
    require(read(weapon / "generated.luau") == weapon_program and not read(weapon / "stderr.log")
            and pin(outputs) == lock["weapon_native_output"] and len(outputs.splitlines()) == 96,
            "ROLE_WEAPON_ORIGINAL_96_ROWS")
    actual = {item.relative_to(path).as_posix(): pin(read(item))
              for item in path.rglob("*") if item.is_file() and item.name != "receipt.json"}
    require(set(actual) == FILE_NAMES - {"receipt.json"}, "ROLE_NATIVE_FILE_SET")
    return {"execution_context": context, "native": binary_pin,
            "selected_sources": {name: pin(body) for name, body in current.items()},
            "motion_source": pin(motion_body),
            "motion_cases": 20, "weapon_rows": 96,
            "official_or_engine_status_inferred": False, "files": actual}


def run(root, path, binary, compiler, luau_source, binary_pin, context, profile, compose):
    _, _, reference, weapon_program = inputs(root, profile, compose)
    path.mkdir()
    reference_path = path / "reference.client.luau"
    reference_path.write_bytes(reference)
    motion_runner = compose.REPO / MOTION_RUNNER
    motion_root, _ = motion_input(root, profile, compose)
    subprocess.run([sys.executable, "-B", str(motion_runner), "--source-root", str(motion_root),
                    "--reference", str(reference_path), "--luau", str(binary), "--compiler", str(compiler),
                    "--luau-source", str(luau_source), "--out", str(path / "motion"),
                    "--expect", "green", "--label", "canonical-943-selected-motion"],
                   check=True, timeout=90)
    weapon = path / "weapon"
    weapon.mkdir()
    generated = weapon / "generated.luau"
    generated.write_bytes(weapon_program)
    result = subprocess.run([str(binary), str(generated)], capture_output=True, timeout=30, check=True)
    (weapon / "parts.tsv").write_bytes(result.stdout)
    (weapon / "stderr.log").write_bytes(result.stderr)
    report = check_runs(root, path, profile, compose, binary_pin, context)
    (path / "receipt.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    print("role_readability: original #943 20 cases and original #929 96 native parts rows PASS", flush=True)
