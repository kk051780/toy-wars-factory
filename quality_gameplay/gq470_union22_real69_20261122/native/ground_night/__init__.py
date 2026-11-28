"""Replay the Ground and Night abilities and their immediate physical predecessor."""
import importlib.util
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "ground_night"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
CAST_FEEL = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
CASE_PINS = {
    "mage_ground_cases.luau": "dc4b9bb784a1dad14322bde5f4c2add1af9acb2b0763dddc76080a0e84deecbb",
    "ninja_flight_cases.luau": "14cef76e93a543089225fc3c97effab575850a01f2dd902161f94872d9b76836",
    "prior_ninja_cases": "f557125f73f57ca628bcc89a6bb5552ea8285d45d8d70c516888e056ad2e31ef",
}
EXPECTED = {
    "ground_fire": "real Fire Pillar E40, whole 1s warn, exact r2 and actual elemental HP once",
    "ground_lightning": "real lightning at legal target after .8s, one resisted exact current Swarm hit",
    "ground_stone": "real stone arm uses existing safe neutral sweep, ignores heavy targets and keeps HP",
    "ground_holy": "real holy radial displacement, bounded heavy resistance and two-target cap",
    "ground_negative_illegal_floor": "decor and foreign placement never accept or charge",
    "ground_negative_caster_wall": "current-life/terrain recheck denies late ground release on caster_wall",
    "ground_negative_push_wall": "current-life/terrain recheck denies late ground release on push_wall",
    "ground_negative_off": "current-life/terrain recheck denies late ground release on off",
    "ground_ancestor_zombie_default": "Zombie remains grantable by the local player's explicit opt-in with nil attribute",
    "n09_run_shadow": "real B moves one noninteractive mirror up to four studs in one second; no player or neutral mutation",
    "n09_shadow_wall": "one straight illusion stops at a late solid wall and cannot resume",
    "n09_flight": "real C uses the bounded flight motor and lands at S0/E45 without a hit or decoy",
    "n09_combo": "real D E80 once, verified flight/landing, one moving decoy with inherited B/C/D clocks",
    "n09_denied": "blocked geometry and egg authority reject the real Tools without charging",
    "n09_interrupted_carry": "old cast cannot mint a visual after carry",
    "n09_interrupted_avatar": "old cast cannot mint a visual after avatar",
    "n09_interrupted_off": "old cast cannot mint a visual after off",
    "n09_switch_kit": "new G, old F, standard and independent toggles stay reversible in actual Host",
    "n09_prompt_guard": "the real new prompt enforces role choice, distance, and the shared guard cooldown",
    "n09_shadow_retired": "a live noninteractive visual cannot outlive its same-session caster eligibility",
    "ninja_components": "original A damages its neutral, real B moves, and C places smoke with separate Swarm clocks",
    "ground_parent_off": "existing Mage default and original physical rollback stay intact",
    "n09_physical_off": "physical 69 source parent honors old standard motion and stealth, with no 009 state",
}
OFF_CASES = {"ground_parent_off", "n09_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _template(raw, compose):
    edits = (
        ("local fixturePrint=print", "local fixturePrint=print;math.randomseed(12345)"),
        ("-- MAGE_RUNTIME_CASES\n", "Vector3.zero=Vector3.new(0,0,0)\n-- MAGE_RUNTIME_CASES\n"),
        ("local function ready(label)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')\n",
         "local function ready(label,role)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_'..(role or 'MAGE')),'職業選択')\n"),
    )
    text = raw.decode("utf-8")
    for old, new in edits:
        compose.need(text.count(old) == 1, "GROUND_NIGHT_FIXTURE_BOUNDARY")
        text = text.replace(old, new, 1)
    return text


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    mage = native / "mage_water_chain"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "GROUND_NIGHT_MANIFEST")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "GROUND_NIGHT_ENGINE")
    template = _template(fixture, compose)

    spec = importlib.util.spec_from_file_location("union22_shared_ground_night", mage / "__init__.py")
    shared_mage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared_mage)
    shared_cases = compose.read_file(mage / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == shared_mage.CASES_SHA, "GROUND_NIGHT_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        path = native / "ninja_s4" / "ninja_cases.luau" if label == "prior_ninja_cases" else HERE / label
        raw = compose.read_file(path)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == want, "GROUND_NIGHT_CASE_PIN:" + label)
        fixtures[label] = pin
        cases.append(raw.decode("utf-8"))

    routes = upstream["runtime_routes"]
    sources = profile["sources"]
    after = {name: row["after"] for name, row in sources.items()}
    changed = profile["ground_night_followup"]["rows"]
    must_change = {FIRST90, CAST_FEEL, *(routes[name] for name in ("Host", "SwarmCombat", "SevenRoleCombat", "InteractionGuard"))}
    compose.need(set(changed) == must_change
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "GROUND_NIGHT_PROFILE_SCOPE")
    cover_orders = profile["cover_orders_followup"]["rows"]
    before = (after | {name: row["parent"]["after"] for name, row in cover_orders.items()}
              | {name: row["parent"]["after"] for name, row in changed.items()})
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.GROUND_NIGHT_OFF / "sources"
    corpus = "\n".join(cases)
    generated = {name: shared_mage._program(shared_mage._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "GROUND_NIGHT_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "GROUND_NIGHT_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "GROUND_NIGHT_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "GROUND_NIGHT_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "GROUND_NIGHT_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "GROUND_NIGHT_OUTPUT")
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, raw in prepared[0].items():
        (output / name).write_bytes(raw)
    for case in EXPECTED:
        _binary(binary, binary_pin, compose)
        result = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                                capture_output=True, env=environment, timeout=110)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        compose.need(result.returncode == 0, "GROUND_NIGHT_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
