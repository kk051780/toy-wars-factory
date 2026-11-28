"""Prepare the exact Return and Convert Native evidence against its physical parent."""
from pathlib import Path
import importlib.util
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "return_convert"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
CASE_PINS = {
    "trapper_return_cases.luau": "a1080361b918bd8c939d6a21b5ebfd1374244fb5aaa3afe8aa8d3d820faa6cf9",
    "zombie_convert_cases.luau": "35f6c8dc66bea6f0ff38a0a5e7222b17cc496daa3432e0167c1b15cb6508465d",
    "mage_tooltip_cases.luau": "7adefec95da1ed05d81aeda1a4ef68adf4fe7333e6649f298f7706795b1b4f74",
    "original_gravity_cases": "b3fb6d701ebce62cae2c9e1753894e59a9067e85ab68a1a6dfa18b7739a4063c",
}
MAGE_TOOLTIP = "actual equipped Tool tooltip matches the same recipe limits and energy"
EXPECTED = {
    "return_player_only": "actual C warns, translates only the same live body and preserves combat and clock state",
    "return_combo": "real D uses confirmed pull/release before one shared-cost, real self-position return",
    "return_negative_range": "outside fixed six-stud range cannot return",
    "return_negative_release_wall": "late solid release fails compound without a return cue or success",
    "return_negative_carry": "carrying egg never authorizes either self return",
    "return_negative_avatar": "safe return rechecks current identity, support and sweep: avatar",
    "z19_mark": "B actual Host/Tool -> candidate only, S0 distance 6, E30, CD20, expiry",
    "z19_real_mark_confirmed": "035 acknowledgement follows the genuine old A conversion and creates no order nor soldier",
    "z19_no_member": "C denies unconverted model without energy or extra unit",
    "z19_real_order": "C actual S0 order E45, existing Model moves, order expires before original charm",
    "z19_combo": "D E80 once, A retains HP authority, original CHARM -> owned order",
    "z19_wrong_target": "bound Model and caster cannot be exchanged",
    "z19_combo_timeout": "019 pending timeout cleanup and no extra command",
    "z19_combo_carry": "019 pending carry cleanup and no extra command",
    "z19_combo_old_avatar": "019 pending replacement cleanup and no extra command",
    "z19_wall_and_immune": "blocked normal and unsupported species fail; real unblocked candidate succeeds",
    "z19_runtime_off": "runtime OFF retires new loadout and leaves actual original same-round conversion",
    "return_physical_parent_off": "real S0 Tool charges E40, 0.30 tell then two neutral pulls and .32 release; no HP/KO/players",
    "z19_physical_off": "physical parent 69 sources, original A/B/C and original real two-attack charm",
    **{f"element_tooltip_{i}": MAGE_TOOLTIP for i in range(1, 5)},
}
OFF_CASES = {"return_physical_parent_off", "z19_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _template(raw, compose):
    # These two mock values and CFrame translation support are the same as the authored return suite.
    prelude = (
        "Vector3.zero=Vector3.new(0,0,0)\n"
        "humanoid.Sit=false\nhumanoid.PlatformStand=false\n"
        "frameMeta.__add=function(frame,delta) return setmetatable({Position=frame.Position+delta,"
        "LookVector=frame.LookVector,RightVector=frame.RightVector},frameMeta) end\n"
    )
    edits = (
        ("local fixturePrint=print", "local fixturePrint=print;math.randomseed(12345)"),
        ("-- MAGE_RUNTIME_CASES\n", prelude + "-- MAGE_RUNTIME_CASES\n"),
        ("local function ready(label)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')\n",
         "local function ready(label,role)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_'..(role or 'MAGE')),'職業選択')\n"),
    )
    text = raw.decode("utf-8")
    for old, new in edits:
        compose.need(text.count(old) == 1, "RETURN_CONVERT_FIXTURE_BOUNDARY")
        text = text.replace(old, new, 1)
    return text


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    mage = native / "mage_water_chain"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "RETURN_CONVERT_MANIFEST")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "RETURN_CONVERT_ENGINE")
    template = _template(fixture, compose)

    spec = importlib.util.spec_from_file_location("union22_shared_return_convert", mage / "__init__.py")
    shared_mage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared_mage)
    shared_cases = compose.read_file(mage / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == shared_mage.CASES_SHA, "RETURN_CONVERT_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        path = native / "field_loadouts" / "trapper_cases.luau" if label == "original_gravity_cases" else HERE / label
        raw = compose.read_file(path)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == want, "RETURN_CONVERT_CASE_PIN:" + label)
        fixtures[label] = pin
        # The authored Return tests reference Gravity by name when their block is evaluated.
        cases.insert(1, raw.decode("utf-8")) if label == "original_gravity_cases" else cases.append(raw.decode("utf-8"))

    routes = upstream["runtime_routes"]
    sources = profile["sources"]
    after = {name: row["after"] for name, row in sources.items()}
    changed = profile["return_convert_followup"]["rows"]
    must_change = {FIRST90, *(routes[name] for name in ("Host", "SwarmCombat", "SevenRoleCombat", "CurseConversionPolicy"))}
    compose.need(set(changed) == must_change
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "RETURN_CONVERT_PROFILE_SCOPE")
    before = after | {name: row["parent"]["after"] for name, row in changed.items()}
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.RETURN_CONVERT_OFF / "sources"
    corpus = "\n".join(cases)
    generated = {name: shared_mage._program(shared_mage._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "RETURN_CONVERT_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "RETURN_CONVERT_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "RETURN_CONVERT_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "RETURN_CONVERT_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "RETURN_CONVERT_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "RETURN_CONVERT_OUTPUT")
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
        compose.need(result.returncode == 0, "RETURN_CONVERT_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
