"""Exercise the author SkillFX bodies and preserve the shared part budget."""

import json
from pathlib import Path
import subprocess


ROUTE = "ServerScriptService/EGGRUMBLE_SkillFX.luau"
FIXTURE = Path(__file__).with_name("art_polish_skillfx_cases.luau")
FILES = {"receipt.json", "generated.luau", "stdout.log", "stderr.log"}
ROLES = ("WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE")
ROWS = [f"PASS\t{role}\t{slot}\t{6 if slot == 'C' else 5}" for role in ROLES for slot in "ABC"]
ROWS += ["PASS\tCAP_AND_CLEANUP\t72"]


def quote(raw):
    separator = b"="
    while b"]" + separator + b"]" in raw:
        separator += b"="
    return b"[" + separator + b"[" + raw + b"]" + separator + b"]"


def program_and_pins(root, lock, compose):
    group = lock["art_polish_followup"]
    before = compose.read_file(root.parent / compose.ART_POLISH_OFF / "sources" / ROUTE)
    after = compose.read_file(root / ROUTE)
    fixture = compose.read_file(FIXTURE)
    pin = compose.identity
    compose.need(pin(before) == group["rows"][ROUTE]["parent"]["after"]
                 and pin(after) == lock["sources"][ROUTE]["after"]
                 and pin(fixture) == group["skillfx_fixture"], "ART_POLISH_SKILLFX_INPUT_PINS")
    program = fixture + b"\nrun(" + quote(before) + b"," + quote(after) + b")\n"
    return program, {"before": pin(before), "after": pin(after), "fixture": pin(fixture)}


def observed(root, folder, binary_pin, context, lock, compose):
    program, inputs = program_and_pins(root, lock, compose)
    stdout = compose.read_file(folder / "stdout.log")
    compose.need(compose.read_file(folder / "generated.luau") == program
                 and stdout.decode().splitlines() == ROWS and compose.read_file(folder / "stderr.log") == b"",
                 "ART_POLISH_SKILLFX_VECTOR")
    return {"status": "PASS", "binary": binary_pin, "context": context, "inputs": inputs,
            "program": compose.identity(program), "stdout": compose.identity(stdout), "cases": ROWS}


def run(root, folder, binary, binary_pin, context, lock, compose):
    program, _ = program_and_pins(root, lock, compose)
    folder.mkdir()
    script = folder / "generated.luau"
    script.write_bytes(program)
    result = subprocess.run([str(binary), str(script)], capture_output=True, timeout=30)
    (folder / "stdout.log").write_bytes(result.stdout)
    (folder / "stderr.log").write_bytes(result.stderr)
    compose.need(result.returncode == 0 and compose.identity(compose.read_file(binary)) == binary_pin,
                 "ART_POLISH_SKILLFX_NATIVE_PROCESS")
    checked = observed(root, folder, binary_pin, context, lock, compose)
    (folder / "receipt.json").write_text(json.dumps(checked, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    print("art_polish_skillfx: 21 role/slot cases and shared 72-part cap and cleanup PASS", flush=True)
