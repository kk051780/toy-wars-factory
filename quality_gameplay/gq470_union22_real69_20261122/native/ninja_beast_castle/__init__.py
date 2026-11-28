"""Execute actual role Tools and the selected CastleApproach client against PRIVATE."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "ninja_beast_castle"
FOLLOWUP = "ninja_beast_castle_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
ART_LOD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD.client.luau"
CLIENT_INSERT = "-- INSERT_PHYSICAL_ART_LOD"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
CASE_PINS = {
    "ninja_cases.luau": "9ed8ac8553dcf1a3bc969fbc728a13da4021827ecc3c12584054ee674523f261",
    "beast_cases.luau": "f4a10c4dd3a30463c68fae561e48e2a7d74f9c70dac1f384ec1a9d40827a8df8",
    "castle_cases.luau": "5ff9b42632571072f969a98eba70c9ac7fcd0317a5919d0482016562f8d085f7",
}
EXPECTED = {
    "ninja_cut_front": "a real front warning then one short legal strike",
    "ninja_cut_backstab": "rear orientation and its stage-zero bonus use one real hit",
    "ninja_cut_rear": "the held backward grip attacks behind the current avatar",
    "ninja_cut_echo": "initial and echo strikes share one budget and one actual target",
    "ninja_cut_echo_dodge": "delayed shadow hit is independently avoidable",
    "ninja_cut_pair": "two indicated angles with separate hit times and one total damage budget",
    "ninja_cut_flight": "flight has one confirmed thin-lane contact",
    "ninja_cut_flight_wall": "late wall stops the flying cut",
    "ninja_cut_hidden_egg": "old stealth and actual egg custody cannot start the optional damage path",
    "ninja_cut_off": "live OFF keeps HP unchanged and restores the base role",
    "ninja_cut_physical_off": "immediate exact parent has the original Ninja tool and no new plaque",
    "beast001_maneuver": "B original pet; fixed radius3 tail fan hits one eligible neutral for 16 HP after warning; extra/rear/far untouched",
    "beast007_maneuver": "same grounded beast hits one exact neutral in 5-stud lance; lateral near target and outside range safe",
    "beast028_maneuver": "Earth target takes authoritative resisted 10 HP after .42s; in-lane second and beyond 7stud remain safe",
    "beast028_maneuver_s4": "true active S4: five distinct old neutral HP writes inside 15 stud; sixth and farther excluded",
    "beast_maneuver_wall": "actual late world wall defeats unchanged canonical neutral HP",
    "beast_maneuver_denials": "no pet, air and egg leave energy unchanged; actual stale avatar after accepted warning produces no impact",
    "beast_maneuver_off": "rollback removes only new deck and its pending effect; old owned beast and original A/B/C retained",
    "beast_maneuver_switches": "live offer changes preserve older Moon and Orders and one authoritative frozen deck",
    "beast_maneuver_physical_off": "actual ancestor: no new prompt, standard tools and same original B physical pet",
    "approach_touch": "existing current Host CastleAccessRamp receives at most 16 touch matte marks; physical door, ramp and HP preserved",
    "approach_desktop": "actual opted-in desktop scene shows three nearest current castle ramp pairs, 24 max",
    "approach_clip_fade": "actual floor obstruction rejects one mark, restores on requery, and applies author 125–155 stud fade",
    "approach_wrong_arena": "wrong/past arena and non-active result phase cannot own visible decorations",
    "approach_live_off": "runtime OFF immediately clears and does not recreate wedges",
    "approach_physical_off": "physical ancestor untouched; no new wedge state",
}
OFF_CASES = {"ninja_cut_physical_off", "beast_maneuver_physical_off", "approach_physical_off"}
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
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "NINJA_BEAST_CASTLE_MANIFEST")
    upstream = compose.strict_json(manifest)
    routes = upstream["runtime_routes"]
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "NINJA_BEAST_CASTLE_ENGINE")
    helpers = {}
    for label, want in TEMPLATE_PINS.items():
        helper = _module(native / label / "__init__.py", "union22_ninja_beast_castle_" + label)
        source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[label + "_template"] = compose.identity(source)
        compose.need(fixtures[label + "_template"]["sha256"] == want, "NINJA_BEAST_CASTLE_TEMPLATE_PIN:" + label)
        helpers[label] = helper
    template = helpers["footing_wards"]._template(fixture, helpers, compose)
    engine = native / "mage_water_chain"
    common = _module(engine / "__init__.py", "union22_ninja_beast_castle_shared_cases")
    shared_cases = compose.read_file(engine / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "NINJA_BEAST_CASTLE_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        raw = compose.read_file(HERE / label)
        fixtures[label] = compose.identity(raw)
        compose.need(fixtures[label]["sha256"] == want, "NINJA_BEAST_CASTLE_CASE_PIN:" + label)
        cases.append(raw.decode("utf-8"))
    corpus = "\n".join(cases)
    compose.need(corpus.count(CLIENT_INSERT) == 1, "NINJA_BEAST_CASTLE_CLIENT_INSERT")

    sources = profile["sources"]
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "NINJA_BEAST_CASTLE_PROFILE_STAGE")
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in sources.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    changed = profile[FOLLOWUP]["rows"]
    scope = {ART_LOD, *(routes[name] for name in ("Host", "SevenRoleCombat", "InteractionGuard"))}
    compose.need(set(changed) == scope
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] == before[name] for name, row in changed.items())
                 and {name for name in after if after[name] != before[name]} == scope, "NINJA_BEAST_CASTLE_PROFILE_SCOPE")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    on_root = source_root.parent / compose.SPRING_MIST_FOREST_OFF / "sources" if index else source_root
    off_root = source_root.parent / compose.NINJA_BEAST_CASTLE_OFF / "sources"

    generated = {}
    for name, root in ((ON_PROGRAM, on_root), (OFF_PROGRAM, off_root)):
        bodies = common._sources(root, pins[name], compose)
        # The actual hashed client payload, including its prior physical OFF
        # body, runs in the isolated original author client scenario.
        text = corpus.replace(CLIENT_INSERT, bodies[ART_LOD], 1)
        generated[name] = common._program(bodies, routes, template, text, compose)
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "NINJA_BEAST_CASTLE_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "NINJA_BEAST_CASTLE_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "NINJA_BEAST_CASTLE_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "NINJA_BEAST_CASTLE_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "NINJA_BEAST_CASTLE_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "NINJA_BEAST_CASTLE_OUTPUT")
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
        compose.need(result.returncode == 0, "NINJA_BEAST_CASTLE_EXIT:" + case)
    run_cases(EXPECTED, run_case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
