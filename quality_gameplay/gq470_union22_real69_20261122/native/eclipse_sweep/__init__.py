"""Prove the exact Eclipse, Warrior and Trapper stage through existing game owners."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "eclipse_sweep"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
COVER_TEMPLATE_SHA = "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089"
CASE_PINS = {
    "eclipse_cases.luau": "b4bb75083cb667a0609754209553f08bb1a64b973fab96586763d5578d7a04ab",
    "warrior_cases.luau": "8ba2ba915f2ae4df77471ba2c9fbf63f1276b28a9cc8fa79794c8391232657b9",
    "swap_hover_cases.luau": "e507745cbdb17a3086f34fdc5b8c837b3dd404083f3f783f5d458bda5f47bfd9",
}
EXPECTED = {
    "eclipse020_standalone": "B real 1.5s server stealth, restored concrete avatar, and full 0.45s reappearance without damage",
    "eclipse028_single": "C uses two harmless visuals, one five-stud scan, one real S0 neutral, and one existing damage budget",
    "eclipse007_combo": "D ends real stealth, warns visibly for 0.45s, then deals one authorized S0 hit and one original KO",
    "eclipse028_range": "the real 5-stud bound and forward preview reject a target just outside each condition",
    "eclipse_actual_defense": "actual old enemy turret denies target acquisition while concealed and resumes after visibility returns",
    "eclipse_egg": "the real Host vault transfer reveals immediately and cancels the queued strike",
    "eclipse_attack": "the real basic and legacy A cannot attack from hidden or during reveal; old A works afterward",
    "eclipse_siege": "existing physical castle attack reveals without hidden damage, then normal siege works",
    "eclipse_late_wall": "a solid late wall blocks the once-only visible strike",
    "eclipse_cancel_avatar": "actual Eclipse effect and avatar appearance retire on avatar",
    "eclipse_cancel_off": "actual Eclipse effect and avatar appearance retire on off",
    "eclipse_physical_off": "exact physical parent keeps original wind stealth and original Ninja Tools",
    "wtech_half": "WARRIOR-001 actual Tool completes its own warning, geometry and bounded neutral HP",
    "wtech_split": "WARRIOR-003 actual Tool completes its own warning, geometry and bounded neutral HP",
    "wtech_twin": "WARRIOR-005 actual Tool completes its own warning, geometry and bounded neutral HP",
    "wtech_spin": "WARRIOR-008 actual Tool completes its own warning, geometry and bounded neutral HP",
    "wtech_spear": "WARRIOR-015 actual Tool completes its own warning, geometry and bounded neutral HP",
    "wtech_charge": "WARRIOR-091 actual Tool completes its own warning, geometry and bounded neutral HP",
    "wtech_diamond": "WARRIOR-018 actual Swarm melee uses precise finite guard, original HP and direction, no immunity",
    "wtech_parry": "WARRIOR-021 actual Swarm melee uses precise finite guard, original HP and direction, no immunity",
    "wtech_side": "WARRIOR-027 actual Swarm melee uses precise finite guard, original HP and direction, no immunity",
    "wtech_guard_back": "WARRIOR-018 actual Swarm melee uses precise finite guard, original HP and direction, no immunity",
    "wtech_guard_wrong_side": "WARRIOR-027 actual Swarm melee uses precise finite guard, original HP and direction, no immunity",
    "wtech_guard_live_pvp": "existing separate PvP hit travels through the same guard pre-hit factor",
    "wtech_guard_round": "actual phase end removes that active finite guard immediately",
    "wtech_deny_wall": "real warning, guard or damage cancels on wall",
    "wtech_deny_off": "real warning, guard or damage cancels on off",
    "wtech_deny_guard_off": "real warning, guard or damage cancels on guard_off",
    "wtech_switch_kits": "same physical stand keeps J, F and G independent and reaches real legacy G Tools",
    "wtech_physical_off": "physical parent retains real old Warrior selection and default A/B/C",
    "swap_pair": "B exact two confirmations and a safe atomic position exchange",
    "swap_hover": "C rises by real bounded height and releases its caster",
    "swap_combo": "D performs exchange, hover and landing after one paid opportunity",
    "swap_late_wall": "late corridor obstruction cancels the pair without partial exchange",
    "swap_ceiling": "real overhead geometry blocks unpayable hover",
    "swap_egg": "real held egg cancels movement rather than changing custody",
    "swap_live_off": "real OFF stops pending movement and restores A/B/C",
    "swap_physical_off": "physical OFF keeps the original role and no exchange prompt",
}
OFF_CASES = {"eclipse_physical_off", "wtech_physical_off", "swap_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _load(alias, path):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _template(raw, compose, cover):
    template = cover._template(raw, compose)
    boundary = "local CFrame={}\n"
    entry = "-- MAGE_RUNTIME_CASES\n"
    props = "  CanCollide=false,CanQuery=true,Anchored=false,Health=100,MaxHealth=100,FloorMaterial=Enum.Material.Concrete,"
    edits = (
        (boundary, "local builtInTypeof=typeof\nlocal function typeof(value)\n"
         " if getmetatable(value)==vectorMeta then return 'Vector3' end\n"
         " return builtInTypeof(value)\nend\n" + boundary),
        (entry, "vectorMeta.__unm=function(value) return Vector3.new(-value.X,-value.Y,-value.Z) end\n"
         "frameMeta.__add=function(frame,delta) return setmetatable({Position=frame.Position+delta,"
         "LookVector=frame.LookVector,RightVector=frame.RightVector},frameMeta) end\n" + entry),
        (props, "  DescendantAdded=signal(),DisplayDistanceType=Enum.HumanoidDisplayDistanceType.Viewer,Transparency=0,"
         + props.lstrip()),
    )
    for old, new in edits:
        compose.need(template.count(old) == 1, "ECLIPSE_SWEEP_FIXTURE_BOUNDARY")
        template = template.replace(old, new, 1)
    return template


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    mage = native / "mage_water_chain"
    cover_entry = native / "cover_orders" / "__init__.py"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "ECLIPSE_SWEEP_SHARED_PINS")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "ECLIPSE_SWEEP_ENGINE")
    cover = _load("union22_eclipse_cover_base", cover_entry)
    template_bytes = inspect.getsource(cover._template).replace("\r\n", "\n").encode("utf-8")
    fixtures["cover_template"] = compose.identity(template_bytes)
    compose.need(fixtures["cover_template"]["sha256"] == COVER_TEMPLATE_SHA, "ECLIPSE_SWEEP_COVER_TEMPLATE")
    template = _template(fixture, compose, cover)
    common = _load("union22_eclipse_shared_cases", mage / "__init__.py")
    root_cases = compose.read_file(mage / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(root_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "ECLIPSE_SWEEP_SHARED_CASES")
    cases = [root_cases.decode("utf-8")]
    for label, expected in CASE_PINS.items():
        raw = compose.read_file(HERE / label)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == expected, "ECLIPSE_SWEEP_CASE_PIN:" + label)
        fixtures[label] = pin
        cases.append(raw.decode("utf-8"))

    routes = upstream["runtime_routes"]
    sources = profile["sources"]
    after = {name: row["after"] for name, row in sources.items()}
    changed = profile["eclipse_sweep_followup"]["rows"]
    scope = {"Host", "SevenRoleCombat", "SwarmCombat", "InvulRuntime", "InteractionGuard"}
    must_change = {FIRST90, *(routes[name] for name in scope)}
    compose.need(set(changed) == must_change
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "ECLIPSE_SWEEP_PROFILE_SCOPE")
    before = after | {name: row["parent"]["after"] for name, row in changed.items()}
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.ECLIPSE_SWEEP_OFF / "sources"
    corpus = "\n".join(cases)
    generated = {name: common._program(common._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "ECLIPSE_SWEEP_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "ECLIPSE_SWEEP_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "ECLIPSE_SWEEP_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "ECLIPSE_SWEEP_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "ECLIPSE_SWEEP_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "ECLIPSE_SWEEP_OUTPUT")
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
        compose.need(result.returncode == 0, "ECLIPSE_SWEEP_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
