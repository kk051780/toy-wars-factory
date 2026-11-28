"""Execute Builder transformations and Zombie runes on exact physical PRIVATE profiles."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "builder_forms"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
}
CASE_PINS = {
    "builder_transform_cases.luau": "a897d16f4c439d1d9319f3af45f217cc22857b1bc4fd6db52b3009ccffd8fd7d",
    "builder_switch_cases.luau": "15e4a97f9af4b4e2ce8f0ea4435eee13341cf261c09efbc4caf257b1f1414522",
    "cover_orders/builder_cover_cases.luau": "ba12dbb85b496671478c4d8f59ad2775111306dc5888e3d129d848d2c97a112a",
    "field_loadouts/builder_cases.luau": "13d7a716e527373c04fd425be58749273984e8b20abb08ced3e155e6689ac47c",
    "zombie_rune_cases.luau": "b6aeb896c23e1fed1c079f5fbc0c2f71c73792ecdcad22f1fef43278363aa600",
    "return_convert/zombie_convert_cases.luau": "35f6c8dc66bea6f0ff38a0a5e7222b17cc496daa3432e0167c1b15cb6508465d",
}
EXPECTED = {
    "transform_armor": "S0 one real armor form reduces known real damage by twelve per cent only for two seconds",
    "transform_drive": "S1 selecting driving changes only real WalkSpeed and retires the same lease",
    "transform_glide": "S3 current falling avatar gets actual VectorForce allocation below gravity and old motion returns",
    "transform_combo": "actual D activates one shape then original 048 geometry and commits one E80/Cooldown set",
    "transform_cover_only": "standalone C uses the same owned barrier without deploying or charging armor",
    "transform_deny_prewall": "illegal initial geometry rejects the real combo before E",
    "transform_deny_latewall": "live combo releases no residual form or wall after latewall",
    "transform_deny_avatar": "live combo releases no residual form or wall after avatar",
    "transform_deny_off": "live combo releases no residual form or wall after off",
    "transform_switch_kits": "new J, old G and old F switch cleanly, and real legacy F Tools survive the independent OFF",
    "transform_physical_off": "immediate physical predecessor keeps its original default, cannon and cover source",
    "builder_combo": "real air-to-ground D charges once and uses two bounded original-author timed neutral HP shots",
    "cover_neutral_break": "existing authoritative neutral swings physically break a covered player route before TTL",
    "rune001_mark": "001 real E30 single information mark, one existing target, exact expiry and zero HP/seal changes",
    "rune008_dual": "008 real E35 shows exactly two distinct targets, with independent valid visual removal",
    "rune009_ring": "009 actual 0.8s warning followed by two legal information marks inside radius 3",
    "rune072_bolt": "072 real moving projectile hits one target once, through existing Swarm HP and seal authority",
    "rune073_line": "073 actual 0.60s straight warning and one neutral-only hit inside its six-stud lane",
    "rune073_stage_budget": "073 actual S1 two neutral hits share one 10 HP base budget, with a third unit excluded",
    "rune097_pillar": "097 actual 1s floor warning, one original neutral KO and no second damage or scoring path",
    "rune_late_wall": "late solid terrain blocks the warned existing HP path",
    "rune_bolt_wall": "072 authoritative wall collision removes the real projectile and preserves blocked HP",
    "rune_retire_off": "pending rune cancels for off",
    "rune_switch": "physical G cycles MARK, BOLT and standard while the existing F conversion stays independent",
    "rune_physical_off": "exact physical #1059 parent retains existing ZOMBIE A/B/C and existing selection",
    "z19_combo": "D E80 once, A retains HP authority, original CHARM -> owned order",
}
OFF_CASES = {"transform_physical_off", "rune_physical_off"}
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
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "BUILDER_FORMS_MANIFEST")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "BUILDER_FORMS_ENGINE")
    helpers = {}
    for label, want in TEMPLATE_PINS.items():
        helper = _module(native / label / "__init__.py", "union22_builder_forms_" + label)
        source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[label + "_template"] = compose.identity(source)
        compose.need(fixtures[label + "_template"]["sha256"] == want, "BUILDER_FORMS_TEMPLATE_PIN:" + label)
        helpers[label] = helper
    template = helpers["eclipse_sweep"]._template(fixture, compose, helpers["cover_orders"])
    engine = native / "mage_water_chain"
    common = _module(engine / "__init__.py", "union22_builder_forms_shared_cases")
    shared_cases = compose.read_file(engine / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "BUILDER_FORMS_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        path = (native if "/" in label else HERE) / label
        raw = compose.read_file(path)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == want, "BUILDER_FORMS_CASE_PIN:" + label)
        fixtures[label] = pin
        cases.append(raw.decode("utf-8"))

    routes = upstream["runtime_routes"]
    sources = profile["sources"]
    after = {name: row["after"] for name, row in sources.items()}
    changed = profile["builder_forms_followup"]["rows"]
    scope = {FIRST90, *(routes[name] for name in ("Host", "SevenRoleCombat", "InvulRuntime", "InteractionGuard"))}
    compose.need(set(changed) == scope
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "BUILDER_FORMS_PROFILE_SCOPE")
    before = compose.trial_sources_before(profile, "builder_forms_followup")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.BUILDER_FORMS_OFF / "sources"
    corpus = "\n".join(cases)
    generated = {name: common._program(common._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "BUILDER_FORMS_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "BUILDER_FORMS_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "BUILDER_FORMS_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "BUILDER_FORMS_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "BUILDER_FORMS_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "BUILDER_FORMS_OUTPUT")
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
        compose.need(result.returncode == 0, "BUILDER_FORMS_EXIT:" + case)
    run_cases(EXPECTED, run_case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
