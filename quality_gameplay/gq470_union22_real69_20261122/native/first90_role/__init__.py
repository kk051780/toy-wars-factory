"""Check the selected First90 role and controls copy without mounting extra GUI."""
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT = "first90_role"
PROGRAM_ARG = f"{OUTPUT}/generated.luau"
FILES = {"generated.luau", "stdout.log", "stderr.log", "status.txt", "receipt.json"}
PROCESS_COUNT = 1
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
CASE_PIN = "d59eddc28d666c91594028da3b434d32bbae9127fdbcc76d452518190306747f"
START = b"local roleIntroduction=table.freeze"
END = b"task.spawn(function()\n while alive and player.Parent==Players do"
BOUNDARY = b'''local player={attrs={}}
local workspace={attrs={}}
function player:GetAttribute(key) return self.attrs[key] end
function workspace:GetAttribute(key) return self.attrs[key] end
local deployedAt=nil
local STEP1,STEP2=22,48
'''
MARKERS = (
    b"FB004_EACH_REAL_ROLE_HAS_OWN_FIRST_ACTION_PASS",
    b"FB004_KIT_SELECTION_SAFE_ROLLBACK_AND_NARROW_FALLBACK_PASS",
    b"FB004_READY_COMBAT_BUTTONS_OBJECTIVE_AND_ELIMINATION_PASS",
    b"FB004_ECLIPSE_WARRIOR_CUES_AND_UTF8_KIT_TITLE_PASS",
)


def prepare(root, profile, compose):
    late_stage = profile.get("navigation_entry_sky_followup")
    # Replay the original guide after its last historical change, with its original loop.
    selected = root.parent / compose.NAVIGATION_ENTRY_SKY_OFF / "sources" if late_stage else root
    expected = late_stage["rows"][ROUTE]["parent"]["after"] if late_stage else profile["sources"][ROUTE]["after"]
    new = compose.read_file(selected / ROUTE)
    previous = compose.read_file(root.parent / compose.FIELD_LOADOUTS_OFF / "sources" / ROUTE)
    cases = compose.read_file(HERE / "cases.luau")
    pins = {name: compose.identity(raw) for name, raw in
            (("selected", new), ("previous", previous), ("case", cases))}
    compose.need(pins["selected"] == expected
                 and pins["previous"] == profile["field_loadouts_followup"]["rows"][ROUTE]["parent"]["after"]
                 and pins["case"]["sha256"] == CASE_PIN, "FIRST90_ROLE_SOURCE_PINS")
    compose.need(new.count(END) == previous.count(END) == new.count(START) == 1
                 and new.index(START) < new.index(END)
                 and new.split(END, 1)[1] == previous.split(END, 1)[1], "FIRST90_ROLE_GUIDE_LIFECYCLE")
    return BOUNDARY + new[new.index(START):new.index(END)] + cases, pins


def _record(root, output, binary, binary_pin, context, profile, compose):
    data, pins = prepare(root, profile, compose)
    read = compose.read_file
    compose.need(compose.identity(read(binary)) == binary_pin and read(output/"generated.luau") == data,
                 "FIRST90_ROLE_BINARY_AND_GENERATED")
    compose.need(read(output/"status.txt") == b"0\n" and read(output/"stderr.log") == b""
                 and tuple(read(output/"stdout.log").splitlines()) == MARKERS, "FIRST90_ROLE_NATIVE_EVIDENCE")
    return {"schema": "UNION22_FIRST90_ROLE_CUE_NATIVE_V1", "context": context,
            "binary": binary_pin, "pins": pins, "argv": [binary.name, PROGRAM_ARG],
            "files": {name: compose.identity(read(output/name)) for name in FILES-{"receipt.json"}},
            "studio": "NOT_TESTED"}


def observe(root, output, binary, binary_pin, context, profile, compose):
    root, output, binary = Path(root), Path(output), Path(binary)
    compose.need(output.name == OUTPUT and not output.is_symlink() and output.is_dir()
                 and {entry.name for entry in output.iterdir()} == FILES, "FIRST90_ROLE_FILES")
    value = _record(root, output, binary, binary_pin, context, profile, compose)
    compose.need(compose.strict_json(compose.read_file(output/"receipt.json")) == value,
                 "FIRST90_ROLE_RECEIPT")
    return value


def run(root, output, binary, binary_pin, context, profile, compose, environment):
    root, output, binary = Path(root), Path(output), Path(binary)
    compose.need(output.name == OUTPUT and compose.identity(compose.read_file(binary)) == binary_pin,
                 "FIRST90_ROLE_INPUT")
    generated, _ = prepare(root, profile, compose)
    output.mkdir()
    (output/"generated.luau").write_bytes(generated)
    result = subprocess.run([str(binary.resolve()), PROGRAM_ARG], cwd=output.parent, env=environment,
                            capture_output=True, timeout=60)
    (output/"stdout.log").write_bytes(result.stdout)
    (output/"stderr.log").write_bytes(result.stderr)
    (output/"status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
    compose.write_json(output/"receipt.json", _record(root, output, binary, binary_pin, context, profile, compose))
    return observe(root, output, binary, binary_pin, context, profile, compose)
