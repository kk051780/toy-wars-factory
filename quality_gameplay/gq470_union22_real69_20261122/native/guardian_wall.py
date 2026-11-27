"""Replay the original seven wall movement cases on the selected Guardian body."""

import json
from pathlib import Path
import subprocess


FIXTURE = Path(__file__).with_name("guardian_wall_cases.luau")
FILE_NAMES = {"generated.luau", "stdout.log", "stderr.log", "receipt.json"}
CASES = ("clear", "straight_wall", "oblique_tangent", "vertical_normal",
         "initial_and_end_overlap", "shallow_overlap_exit", "tangent_blocked_by_second_wall")
OFF = {"bytes": 14201, "sha256": "a6a4433966ba52212d42e12dc69e8bca7a63424fe31c25ade89724928d417ef2"}
ON = {"bytes": 15746, "sha256": "073c88a02e84d27c4f2cddd8ebd701c36e389f7050876b0551b4aa872301746c"}
TEMPLATE = {"bytes": 5321, "sha256": "b41993d6d972a9e9b50bd6fe43ede1a4f120b73ee8bba2fe2314cb2f7e1fd826"}
PROGRAM = {"bytes": 6698, "sha256": "f7ee3db35e5756d778a567119cb62b13b5c68967100ef54154944005be6b4085"}


def assemble(root, lock, compose):
    route = compose.GUARDIAN_SOURCE
    record = lock["guardian_wall_followup"]
    candidate = compose.read_file(root / route)
    original = compose.read_file(root.parent / compose.GUARDIAN_WALL_OFF / "sources" / route)
    before_art = compose.read_file(root.parent / compose.ART_POLISH_OFF / "sources" / route)
    compose.need(compose.identity(original) == record["rows"][route]["parent"]["after"] == OFF
                 and compose.identity(before_art) == lock["art_polish_followup"]["rows"][route]["parent"]["after"] == ON
                 and compose.identity(candidate) == lock["sources"][route]["after"],
                 "WALL_NATIVE_EXACT_PAIR")
    program = compose.read_file(FIXTURE)
    compose.need(compose.identity(program) == record["native_case"] == TEMPLATE, "WALL_NATIVE_ORIGINAL_FIXTURE")
    for marker, start, stop in (
        (b"-- @movement-source", b"-- The guardian's body sets the movement volume.", b"local function impact("),
        (b"-- @movement-settings", b"  local movementRay=RaycastParams.new()",
         b"  local d={owner=owner,role=proposal.role,model=model,siege=siege,"),
    ):
        compose.need(candidate.count(start) == candidate.count(stop) == program.count(marker) == 1
                     and candidate.index(start) < candidate.index(stop), "WALL_NATIVE_SECTION")
        program = program.replace(marker, candidate[candidate.index(start):candidate.index(stop)], 1)
    compose.need(compose.identity(program) == PROGRAM, "WALL_NATIVE_ORIGINAL_PROGRAM")
    return program


def observed(root, folder, native, context, lock, compose):
    program = assemble(root, lock, compose)
    stdout = compose.read_file(folder / "stdout.log")
    rows = [f"PASS {case}" for case in CASES]
    expected = ("\n".join(rows) + "\n").encode()
    compose.need(compose.read_file(folder / "generated.luau") == program
                 and stdout in (expected, expected.replace(b"\n", b"\r\n"))
                 and compose.read_file(folder / "stderr.log") == b"", "WALL_NATIVE_EXACT_VECTOR")
    return {"status": "PASS", "native": native, "context": context,
            "source": compose.identity(compose.read_file(root / compose.GUARDIAN_SOURCE)), "control_source": OFF,
            "fixture": TEMPLATE, "program": PROGRAM, "stdout": compose.identity(stdout), "exit": 0,
            "cases": rows, "scope": "Guardian movement and query settings with deterministic spatial mocks"}


def check(root, folder, native, context, lock, compose):
    report = observed(root, folder, native, context, lock, compose)
    compose.need({entry.name for entry in folder.iterdir()} == FILE_NAMES
                 and compose.strict_json(compose.read_file(folder / "receipt.json")) == report,
                 "WALL_NATIVE_EXACT_RECEIPT")
    return report


def run(root, folder, binary, native, context, lock, compose):
    program = assemble(root, lock, compose)
    compose.need(compose.identity(compose.read_file(binary)) == native, "WALL_NATIVE_EXECUTABLE")
    folder.mkdir()
    path = folder / "generated.luau"
    path.write_bytes(program)
    result = subprocess.run([str(binary), str(path)], capture_output=True, timeout=30)
    (folder / "stdout.log").write_bytes(result.stdout)
    (folder / "stderr.log").write_bytes(result.stderr)
    compose.need(result.returncode == 0 and compose.identity(compose.read_file(binary)) == native,
                 "WALL_NATIVE_EXECUTION")
    report = observed(root, folder, native, context, lock, compose)
    (folder / "receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    check(root, folder, native, context, lock, compose)
    print("guardian_wall: 7 original movement and query cases PASS", flush=True)
