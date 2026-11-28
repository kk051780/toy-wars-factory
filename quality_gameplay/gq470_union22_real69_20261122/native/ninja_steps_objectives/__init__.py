"""Exercise exact Ninja direction Tools and the original objective map route."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "ninja_steps_objectives"
FOLLOWUP = "ninja_steps_objectives_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
MAP_ON_PROGRAM, MAP_OFF_PROGRAM = "generated_map_on.luau", "generated_map_off.luau"
HUD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau"
MAP_BRIDGE = "ServerScriptService/EGGRUMBLE_MapIntelBridge.server.luau"
MAP_POLICY = "ServerScriptService/EGGRUMBLE_MapVisibilityPolicy.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
CASE_PINS = {
    "steps_cases.luau": "cb4bb7447452cc0d9a843fe26df59298dc5fa61a6f7a30ef72e85c663e5d5e95",
    "map_cases.luau": "535d37adecf98beb53a3fa958097edbeba436f7856b453b968607df6beaf17ce",
    "round_case.luau": "d3072a5d33c5cbcdfe81cca4f11517ae6e2a23eb0bbcc29ce084ea427d877c47",
}
EXPECTED = {
    "ninja_step_back": "actual three-stud backward step without turning or immunity",
    "ninja_step_side": "captured lateral movement selects the indicated side",
    "ninja_step_land": "visible destination remains the same safe ground for 0.45 seconds before arrival",
    "ninja_step_diagonal": "four-stud selected diagonal uses the same checked pivot and no damage",
    "ninja_step_late_wall": "the newly blocked arrival is rechecked before any movement",
    "ninja_step_castle_floor": "an actual other castle's floor may not become this ability's destination",
    "ninja_step_egg_and_speed": "egg custody and actor speed are checked before any preview",
    "ninja_step_live_off": "live flag rollback keeps current position and restores old gear",
    "ninja_step_old_kit": "old movement kit remains individually available after using the new option",
    "ninja_step_physical_off": "actual complete older profile still owns prior cut and default kits without directional skill",
    "minimap_team": "actual TEAM per-recipient map sends each own deposit coordinates and no other deposit; same client pin rendered",
    "minimap_missing": "disabled real destination remains ordinary castle and elimination cleared all stale markers",
    "minimap_egg_visibility": "current Host remote filters a real unexplored egg, then publishes gold only after real explored positions",
    "minimap_br": "same authenticated current solo BR owned deposit and no client payload to nonmember",
    "minimap_physical_off": "physical parent preserved same public castle format, old color, and no deposit marker",
    "private_round_custody": "actual PRIVATE selection→TEAM READY with AI roster→enemy egg→human deposit/score→results/lobby→voluntary replay",
}
OFF_CASES = {"ninja_step_physical_off", "minimap_physical_off"}
MAP_CASES = {case for case in EXPECTED if case.startswith("minimap_")} | {"private_round_custody"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, MAP_ON_PROGRAM, MAP_OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def _section(text, start, end, compose):
    compose.need(text.count(start) == text.count(end) == 1 and text.index(start) < text.index(end),
                 "NINJA_STEPS_OBJECTIVES_HUD_SECTION")
    return text[text.index(start):text.index(end)]


def _map_program_cases(cases, bodies, compose):
    hud = bodies[HUD]
    inserts = {
        "-- INSERT_MAP_POLICY": bodies[MAP_POLICY],
        "-- INSERT_MAP_BRIDGE": bodies[MAP_BRIDGE],
        "-- INSERT_MAP_REDRAW": _section(hud, 'local activeLayer="LAND"', 'local statusBox=frame("CompactStatus"', compose),
        "-- INSERT_MAP_EVENT": _section(hud, "remote.OnClientEvent:Connect(function(s)",
                                       "local function touchJumpGeometry()", compose),
    }
    for marker, body in inserts.items():
        compose.need(cases.count(marker) == 1, "NINJA_STEPS_OBJECTIVES_MAP_INSERT:" + marker)
        cases = cases.replace(marker, body, 1)
    return cases


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "NINJA_STEPS_OBJECTIVES_MANIFEST")
    upstream = compose.strict_json(manifest)
    routes = upstream["runtime_routes"]
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "NINJA_STEPS_OBJECTIVES_ENGINE")
    helpers = {}
    for label, want in TEMPLATE_PINS.items():
        helper = _module(native / label / "__init__.py", "union22_ninja_steps_objectives_" + label)
        source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[label + "_template"] = compose.identity(source)
        compose.need(fixtures[label + "_template"]["sha256"] == want, "NINJA_STEPS_OBJECTIVES_TEMPLATE_PIN:" + label)
        helpers[label] = helper
    template = helpers["footing_wards"]._template(fixture, helpers, compose)
    engine = native / "mage_water_chain"
    common = _module(engine / "__init__.py", "union22_ninja_steps_objectives_shared_cases")
    shared_cases = compose.read_file(engine / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "NINJA_STEPS_OBJECTIVES_SHARED_CASES")
    cases = {}
    for label, want in CASE_PINS.items():
        raw = compose.read_file(HERE / label)
        fixtures[label] = compose.identity(raw)
        compose.need(fixtures[label]["sha256"] == want, "NINJA_STEPS_OBJECTIVES_CASE_PIN:" + label)
        cases[label] = raw.decode("utf-8")
    shared_cases = shared_cases.decode("utf-8")
    step_cases = shared_cases + "\n" + cases["steps_cases.luau"]
    map_cases = cases["map_cases.luau"]
    round_case = cases["round_case.luau"]

    sources = profile["sources"]
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "NINJA_STEPS_OBJECTIVES_PROFILE_STAGE")
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in sources.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    changed = profile[FOLLOWUP]["rows"]
    scope = {HUD, MAP_BRIDGE, *(routes[name] for name in ("Host", "SevenRoleCombat", "InteractionGuard"))}
    compose.need(set(changed) == scope
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] == before[name] for name, row in changed.items())
                 and {name for name in after if after[name] != before[name]} == scope, "NINJA_STEPS_OBJECTIVES_PROFILE_SCOPE")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    on_root = source_root.parent / compose.WARRIOR_FIELD_HORDE_OFF / "sources" if index else source_root
    off_root = source_root.parent / compose.NINJA_STEPS_OBJECTIVES_OFF / "sources"

    generated = {}
    for name, map_name, root in ((ON_PROGRAM, MAP_ON_PROGRAM, on_root),
                                 (OFF_PROGRAM, MAP_OFF_PROGRAM, off_root)):
        bodies = common._sources(root, pins[name], compose)
        generated[name] = common._program(bodies, routes, template, step_cases, compose)
        # The author map fixture wraps an actual bridge and client callback.
        # Keep it outside the role-only program; both use the same real pair.
        map_case = _map_program_cases(map_cases, bodies, compose)
        generated[map_name] = common._program(bodies, routes, template,
                                              "\n".join((shared_cases, map_case, round_case)), compose)
    return generated, pins, fixtures


def _args(case, binary):
    if case in MAP_CASES:
        name = MAP_OFF_PROGRAM if case in OFF_CASES else MAP_ON_PROGRAM
    else:
        name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "NINJA_STEPS_OBJECTIVES_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "NINJA_STEPS_OBJECTIVES_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "NINJA_STEPS_OBJECTIVES_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "NINJA_STEPS_OBJECTIVES_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "NINJA_STEPS_OBJECTIVES_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "NINJA_STEPS_OBJECTIVES_OUTPUT")
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, raw in prepared[0].items():
        (output / name).write_bytes(raw)
    from case_batch import run_cases

    def run_case(case):
        _binary(binary, binary_pin, compose)
        result = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                                capture_output=True, env=environment, timeout=110)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        compose.need(result.returncode == 0, "NINJA_STEPS_OBJECTIVES_EXIT:" + case)
    run_cases(EXPECTED, run_case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
