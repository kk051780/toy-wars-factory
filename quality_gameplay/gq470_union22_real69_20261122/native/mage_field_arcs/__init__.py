"""Replay eight fixed Mage spells and Moon Beast using the exact PRIVATE sources."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "mage_field_arcs"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
COVER_TEMPLATE_SHA = "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089"
CASE_PINS = {
    "mage_field_cases.luau": "1dc83216ae63f48432a5e953ece901bad5505637b9c3f1c47f8514f011114f5b",
    "moon_cases.luau": "8f19d19988ffa7da9566aa6ffb3dc0b9add1ded4b65de7dc9913f713e9c4255c",
    "ground_night/mage_ground_cases.luau": "dc4b9bb784a1dad14322bde5f4c2add1af9acb2b0763dddc76080a0e84deecbb",
    "wing_warrior/element_cases.luau": "88b1a1366c4a0bb89c7525d0a4c3fcea541c79168c5e6af006068c1e0af456c8",
}
EXPECTED = {
    "field_pursuit": "MAGE-005 actual track route to one current neutral",
    "field_firebird": "MAGE-009 actual vertical route to one current neutral",
    "field_comet": "MAGE-079 actual lateral route to one current neutral",
    "field_rain": "MAGE-078 genuine settled neutral HP; one timed ground effect with exact S0 cap",
    "field_ice": "MAGE-015 genuine settled neutral HP; one timed ground effect with exact S0 cap",
    "field_water": "MAGE-047 genuine settled neutral HP; one timed ground effect with exact S0 cap",
    "field_ring": "MAGE-073 genuine settled neutral HP; one timed ground effect with exact S0 cap",
    "field_sand": "MAGE-083 genuine settled neutral HP; one timed ground effect with exact S0 cap",
    "field_ice_s4": "exact S4 by active-time movement gives one genuine pushed neutral",
    "field_denied_arc_wall": "live arc rechecks arc_wall before each real contact",
    "field_denied_carrier": "unqualified old actor/ground carries no cost",
    "field_denied_floor": "unqualified old actor/ground carries no cost",
    "field_denied_avatar": "live arc rechecks avatar before each real contact",
    "field_denied_off": "live arc rechecks off before each real contact",
    "field_physical_off": "parent standard Mage restored in physically independent OFF",
    "moon020_charge": "existing one escort moves six actual studs after warning and makes one admitted neutral-only hit",
    "moon095_guard": "actual C holds one radius-four circle with old contact cadence and timed return to normal behavior",
    "moon017_combo": "D pays E80 once, actual charge and stop then one ordered circle, one original KO and all deadlines",
    "moon_late_wall": "a new solid wall stops the original pet before contact, and cannot produce a step or guard",
    "moon_denials": "missing owned beast, allied neutral, pre-commit cover, and carrying fail closed",
    "moon_cancel_off": "the already moving COMBO-017 cannot finish on off",
    "moon_cancel_avatar": "the already moving COMBO-017 cannot finish on avatar",
    "moon_physical_off": "the exact physical predecessor keeps the standard original real companion",
    "ground_fire": "real Fire Pillar E40, whole 1s warn, exact r2 and actual elemental HP once",
    "element_icicle": "real icicle respects tell, captured direction, and S0 cap",
}
OFF_CASES = {"field_physical_off", "moon_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    template_path = native / "cover_orders" / "__init__.py"
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "MAGE_FIELD_ARCS_MANIFEST")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "MAGE_FIELD_ARCS_ENGINE")
    cover = _module(template_path, "union22_cover_orders_for_field_arcs")
    template_bytes = inspect.getsource(cover._template).replace("\r\n", "\n").encode("utf-8")
    fixtures["cover_orders_template"] = compose.identity(template_bytes)
    compose.need(fixtures["cover_orders_template"]["sha256"] == COVER_TEMPLATE_SHA, "MAGE_FIELD_ARCS_COVER_TEMPLATE")
    template = cover._template(fixture, compose)

    mage = native / "mage_water_chain"
    shared_mage = _module(mage / "__init__.py", "union22_shared_mage_field_arcs")
    shared_cases = compose.read_file(mage / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == shared_mage.CASES_SHA, "MAGE_FIELD_ARCS_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        path = (native if "/" in label else HERE) / label
        raw = compose.read_file(path)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == want, "MAGE_FIELD_ARCS_CASE_PIN:" + label)
        fixtures[label] = pin
        cases.append(raw.decode("utf-8"))

    routes = upstream["runtime_routes"]
    sources = profile["sources"]
    after = {name: row["after"] for name, row in sources.items()}
    changed = profile["mage_field_arcs_followup"]["rows"]
    must_change = {FIRST90, *(routes[name] for name in ("Host", "SwarmCombat", "SevenRoleCombat", "InteractionGuard"))}
    compose.need(set(changed) == must_change
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "MAGE_FIELD_ARCS_PROFILE_SCOPE")
    eclipse_sweep = profile["eclipse_sweep_followup"]["rows"]
    before = (after | {name: row["parent"]["after"] for name, row in eclipse_sweep.items()}
              | {name: row["parent"]["after"] for name, row in changed.items()})
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.MAGE_FIELD_ARCS_OFF / "sources"
    corpus = "\n".join(cases)
    generated = {name: shared_mage._program(shared_mage._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "MAGE_FIELD_ARCS_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "MAGE_FIELD_ARCS_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "MAGE_FIELD_ARCS_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "MAGE_FIELD_ARCS_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "MAGE_FIELD_ARCS_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "MAGE_FIELD_ARCS_OUTPUT")
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
        compose.need(result.returncode == 0, "MAGE_FIELD_ARCS_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
