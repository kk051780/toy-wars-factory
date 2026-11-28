"""Verify real Warrior abilities and the same neutral rigs on both PRIVATE versions."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "warrior_field_horde"
FOLLOWUP = "warrior_field_horde_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
CASE_PINS = {
    "warrior_cases.luau": "cfbb58c3d494783db86591a4d8839939a2413a3431f53d3c8ae5a5dfc3e23cdc",
    "horde_cases.luau": "dbe61ceaaf31b6c2dc13251200241c92ade78856b33a6c308946405ae2c10a02",
}
EXPECTED = {
    "warrior_field_hilt": "one short hilt strike and one actual neutral displacement",
    "warrior_field_push": "one swept shove with no damage, KO or score side effect",
    "warrior_field_push_weight": "the checked movement owner rejects a heavy neutral before applying the shove",
    "warrior_field_blade": "a blade follows valid floor and touches just the admitted lane once",
    "warrior_field_blade_wall": "the late solid wall intercepts the actual advancing blade",
    "warrior_field_cross": "actual crossing lines share the target cap and never double hit at the center",
    "warrior_field_mark": "real impact marker is local, noninteractive and lasts its fixed stage window",
    "warrior_field_drop": "two legitimate targets inside the warned circle",
    "warrior_field_drop_wall": "late wall revokes the authored ground attack",
    "warrior_field_live_off": "changing newer field weapons OFF cancels pending hits and restores the original deck",
    "warrior_field_physical_off": "the exact prior build retains the original three optional kits and standard gear",
    "horde951_shapes": "rig=",
    "horde951_physical_off": "rig=",
    "horde951_reaction": "solid wall gives no HP/cue; real accepted strike 32→27 HP + existing accent pulse, one credited KO + rejected duplicate",
    "horde951_guardian_regression": "real siege prompts start WARRIOR guard; MAGE Tool A changes actual guardian 110→80 HP",
}
OFF_CASES = {"warrior_field_physical_off", "horde951_physical_off"}
RIG_CASES = {"horde951_shapes", "horde951_physical_off"}
RIG_PIN = {"bytes": 1130, "sha256": "f46ed1fa5c22ec8035053d643a1bd4e839af90bd70a1b77620cfd2ef4f1134b9"}
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
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "WARRIOR_FIELD_HORDE_MANIFEST")
    upstream = compose.strict_json(manifest)
    routes = upstream["runtime_routes"]
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "WARRIOR_FIELD_HORDE_ENGINE")
    helpers = {}
    for label, want in TEMPLATE_PINS.items():
        helper = _module(native / label / "__init__.py", "union22_warrior_field_horde_" + label)
        source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[label + "_template"] = compose.identity(source)
        compose.need(fixtures[label + "_template"]["sha256"] == want, "WARRIOR_FIELD_HORDE_TEMPLATE_PIN:" + label)
        helpers[label] = helper
    template = helpers["footing_wards"]._template(fixture, helpers, compose)
    engine = native / "mage_water_chain"
    common = _module(engine / "__init__.py", "union22_warrior_field_horde_shared_cases")
    shared_cases = compose.read_file(engine / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "WARRIOR_FIELD_HORDE_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        raw = compose.read_file(HERE / label)
        fixtures[label] = compose.identity(raw)
        compose.need(fixtures[label]["sha256"] == want, "WARRIOR_FIELD_HORDE_CASE_PIN:" + label)
        cases.append(raw.decode("utf-8"))
    corpus = "\n".join(cases)

    sources = profile["sources"]
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "WARRIOR_FIELD_HORDE_PROFILE_STAGE")
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in sources.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    changed = profile[FOLLOWUP]["rows"]
    scope = {routes[name] for name in ("Host", "SevenRoleCombat", "SwarmCombat")}
    compose.need(set(changed) == scope
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] == before[name] for name, row in changed.items())
                 and {name for name in after if after[name] != before[name]} == scope, "WARRIOR_FIELD_HORDE_PROFILE_SCOPE")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    on_root = source_root.parent / compose.TRAPPER_CAST_AUDIO_OFF / "sources" if index else source_root
    off_root = source_root.parent / compose.WARRIOR_FIELD_HORDE_OFF / "sources"

    generated = {name: common._program(common._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, on_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "WARRIOR_FIELD_HORDE_BINARY")


def _result_line(case, stdout, compose):
    marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{EXPECTED[case]}".encode("utf-8")
    lines = stdout.replace(b"\r\n", b"\n").split(b"\n")
    evidence = {}
    if case in RIG_CASES:
        compose.need(len(lines) == 2 and lines[1] == b"" and lines[0].startswith(marker),
                     "WARRIOR_FIELD_HORDE_RIG_LINE:" + case)
        rig = compose.identity(lines[0][len(marker):])
        compose.need(rig == RIG_PIN, "WARRIOR_FIELD_HORDE_RIG_IDENTITY:" + case)
        evidence["rig"] = rig
    else:
        compose.need(lines == [marker, b""], "WARRIOR_FIELD_HORDE_RESULT:" + case)
    return lines[0].decode("utf-8"), evidence


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "WARRIOR_FIELD_HORDE_GENERATED:" + name)
    results = {}
    for case in EXPECTED:
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        compose.need(stderr == b"" and status == b"0\n", "WARRIOR_FIELD_HORDE_RESULT:" + case)
        marker, evidence = _result_line(case, stdout, compose)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status), **evidence}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED",
            "art": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "WARRIOR_FIELD_HORDE_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "WARRIOR_FIELD_HORDE_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "WARRIOR_FIELD_HORDE_OUTPUT")
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
        compose.need(result.returncode == 0, "WARRIOR_FIELD_HORDE_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
