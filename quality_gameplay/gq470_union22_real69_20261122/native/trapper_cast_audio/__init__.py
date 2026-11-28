"""Exercise the real Trapper field Tools on exact PRIVATE ON and OFF sources."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "trapper_cast_audio"
FOLLOWUP = "trapper_cast_audio_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
COMBAT_FEEL = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
CASE_PINS = {
    "trapper_cases.luau": "7cb0029883cae471558f136b6362e557011cc4795743bb9a23f3dc9022ed57cd",
}
EXPECTED = {
    "trapper_field_push": "real one-stud neutral push, no HP, circle or heavy-target effect",
    "trapper_field_flight": "swept pebble deals one real neutral HP write, S0 cap one",
    "trapper_field_flight_late_wall": "a real late wall prevents the in-flight neutral hit",
    "trapper_field_stop": "bounded stop pauses and releases the same living neutral",
    "trapper_field_ward": "real front guardian bolt deals 5.52HP; melee leaves the shield available",
    "trapper_field_pair": "two distinct directions share cap two without center or rear effects",
    "trapper_field_ground": "real one-second ground warning, two bounded neutral displacements, no HP",
    "trapper_field_live_off": "live OFF cancels queued move and leaves original Trapper kit",
    "trapper_field_physical_off": "physical OFF sources keep the original Trapper toolkit",
}
OFF_CASES = {"trapper_field_physical_off"}
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


cast_cues = _module(HERE / "cast_cues.py", "union22_trapper_cast_audio_cues")
PROCESS_COUNT = len(EXPECTED) + cast_cues.PROCESS_COUNT
FILES |= cast_cues.FILES


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "TRAPPER_CAST_AUDIO_MANIFEST")
    upstream = compose.strict_json(manifest)
    routes = upstream["runtime_routes"]
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "TRAPPER_CAST_AUDIO_ENGINE")
    helpers = {}
    for label, want in TEMPLATE_PINS.items():
        helper = _module(native / label / "__init__.py", "union22_trapper_cast_audio_" + label)
        source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[label + "_template"] = compose.identity(source)
        compose.need(fixtures[label + "_template"]["sha256"] == want, "TRAPPER_CAST_AUDIO_TEMPLATE_PIN:" + label)
        helpers[label] = helper
    template = helpers["footing_wards"]._template(fixture, helpers, compose)
    engine = native / "mage_water_chain"
    common = _module(engine / "__init__.py", "union22_trapper_cast_audio_shared_cases")
    shared_cases = compose.read_file(engine / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "TRAPPER_CAST_AUDIO_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        raw = compose.read_file(HERE / label)
        fixtures[label] = compose.identity(raw)
        compose.need(fixtures[label]["sha256"] == want, "TRAPPER_CAST_AUDIO_CASE_PIN:" + label)
        cases.append(raw.decode("utf-8"))
    corpus = "\n".join(cases)

    sources = profile["sources"]
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "TRAPPER_CAST_AUDIO_PROFILE_STAGE")
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in sources.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    changed = profile[FOLLOWUP]["rows"]
    scope = {COMBAT_FEEL, *(routes[name] for name in (
        "Host", "SevenRoleCombat", "SwarmCombat", "InvulRuntime", "InteractionGuard"))}
    compose.need(set(changed) == scope
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] == before[name] for name, row in changed.items())
                 and {name for name in after if after[name] != before[name]} == scope, "TRAPPER_CAST_AUDIO_PROFILE_SCOPE")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    on_root = source_root.parent / compose.ZOMBIE_FORMATION_CAMERA_OFF / "sources" if index else source_root
    off_root = source_root.parent / compose.TRAPPER_CAST_AUDIO_OFF / "sources"

    generated = {name: common._program(common._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, on_root), (OFF_PROGRAM, off_root))}
    for mode, case in cast_cues.CASES.items():
        root = on_root if mode == "ON" else off_root
        generated[case + ".luau"] = cast_cues.program(root, mode, native / "fixed_cues")
    fixtures["cast_cues"] = cast_cues.FIXTURE_PINS
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "TRAPPER_CAST_AUDIO_BINARY")


def _result_line(case, stdout, compose):
    marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{EXPECTED[case]}".encode("utf-8")
    compose.need(stdout.replace(b"\r\n", b"\n") == marker+b"\n", "TRAPPER_CAST_AUDIO_RESULT:" + case)
    return marker.decode("utf-8")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "TRAPPER_CAST_AUDIO_GENERATED:" + name)
    results = {}
    for case in EXPECTED:
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        compose.need(stderr == b"" and status == b"0\n", "TRAPPER_CAST_AUDIO_RESULT:" + case)
        marker = _result_line(case, stdout, compose)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    for mode, case in cast_cues.CASES.items():
        streams = {suffix: compose.read_file(output / f"{case}.{suffix}")
                   for suffix in ("stdout.log", "stderr.log", "status.txt")}
        compose.need(streams["status.txt"] == b"0\n", "TRAPPER_CAST_AUDIO_CUE_STATUS:" + case)
        markers = cast_cues.assert_result(mode, streams["stdout.log"], streams["stderr.log"], 0)
        results[case] = {"argv": [binary.name, f"{OUTPUT_NAME}/{case}.luau"],
                         "markers": list(markers),
                         **{label.split(".")[0]: compose.identity(data) for label, data in streams.items()}}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "TRAPPER_CAST_AUDIO_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "TRAPPER_CAST_AUDIO_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "TRAPPER_CAST_AUDIO_OUTPUT")
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
        compose.need(result.returncode == 0, "TRAPPER_CAST_AUDIO_EXIT:" + case)
    run_cases(EXPECTED, run_case)
    for mode, case in cast_cues.CASES.items():
        _binary(binary, binary_pin, compose)
        result = subprocess.run([str(binary.resolve()), f"{OUTPUT_NAME}/{case}.luau"], cwd=output.parent,
                                capture_output=True, env=environment, timeout=110)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        cast_cues.assert_result(mode, result.stdout, result.stderr, result.returncode)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
