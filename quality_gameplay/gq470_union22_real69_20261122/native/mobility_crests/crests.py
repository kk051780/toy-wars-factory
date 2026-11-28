"""Build and assert the six exact #976 physical-profile Native cases."""

import importlib.util
import inspect
from pathlib import Path


HERE = Path(__file__).resolve().parent
LOD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD.client.luau"
PROGRAMS = {"ON": "crests976_on.luau", "OFF": "crests976_off.luau"}
EXPECTED = {
    "crest976_desktop": "first real TEAM epoch zero; R6/R15 author RED width and BLUE height, six passive wedges maximum",
    "crest976_touch": "two nearest real TEAM peers, four passive wedges maximum",
    "crest976_view": "nearby on-screen ray-gated targets only; observer and Scriptable cameras remove and suppress all crests",
    "crest976_cloak_stream": "R6 transparency, server cloak and stream-out withdraw instantly; current avatar alone owns the decoration",
    "crest976_lifecycle": "round, mode, reduced effects, runtime OFF, arena phase, script disposal retire their own bindings",
    "crest976_physical_off": "physical old ArtDistanceLOD keeps far sky and no player crests",
}
CASES = {case: "OFF" if case == "crest976_physical_off" else "ON" for case in EXPECTED}
PROCESS_COUNT = len(CASES)
FILES = set(PROGRAMS.values()) | {
    f"{case}.{extension}" for case in CASES for extension in ("stdout.log", "stderr.log", "status.txt")
}
LOD_PINS = {
    "ON": "ead4f14c1f7bed5bc331e581f4e58680a15bfe0cbda997b79ca2b3a67394db70",
    "OFF": "8ae7d624cd2b6cd38bf8b94824ec648ee920d43b663ae82930530b6beb8ccba9",
}
CASE_SHA = "d5b778229d37f778acc980eae179fe98a5a98cf561f966d4bc47aa9ef7da87b2"
FIXTURE_SHA = "a919b6545aed764d80ab3dc57a5594d4b308dedfae71889879e71d8c0d28073f"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pinned(path, sha, compose):
    raw = compose.read_file(path)
    compose.need(compose.identity(raw)["sha256"] == sha, "CREST976_INPUT:" + path.name)
    return raw


def program(source_root, mode, compose, source_pins):
    compose.need(mode in PROGRAMS, "CREST976_PROFILE")
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.strict_json(_pinned(shared / "INPUTS.json", MANIFEST_SHA, compose))
    engine = compose.read_file(shared / "engine_fixture.luau")
    compose.need(compose.identity(engine) == manifest["fixtures"]["engine_fixture.luau"], "CREST976_ENGINE")
    helpers = {}
    for name, sha in TEMPLATE_PINS.items():
        helper = _load(native / name / "__init__.py", "union22_crest976_" + name)
        body = inspect.getsource(helper._template).replace("\r\n", "\n").encode()
        compose.need(compose.identity(body)["sha256"] == sha, "CREST976_TEMPLATE:" + name)
        helpers[name] = helper
    template = helpers["footing_wards"]._template(engine, helpers, compose)
    water = native / "mage_water_chain"
    common = _load(water / "__init__.py", "union22_crest976_common")
    old = _pinned(water / "cases.luau", common.CASES_SHA, compose)
    fixture = _pinned(HERE / "crest_fixture.luau", FIXTURE_SHA, compose)
    cases = _pinned(HERE / "crest_cases.luau", CASE_SHA, compose).decode()
    bodies = common._sources(Path(source_root), source_pins, compose)
    compose.need(source_pins[LOD]["sha256"] == LOD_PINS[mode], "CREST976_ART_PROFILE:" + mode)
    marker = "-- INSERT_PHYSICAL_ART_LOD"
    compose.need(cases.count(marker) == 1, "CREST976_LOD_INSERT")
    corpus = "\n".join((fixture.decode(), old.decode(), cases.replace(marker, bodies[LOD])))
    return common._program(bodies, manifest["runtime_routes"], template, corpus, compose)


def assert_result(case, stdout, stderr, exit_code):
    if case not in EXPECTED:
        raise ValueError("CREST976_CASE:" + str(case))
    marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{EXPECTED[case]}"
    if exit_code != 0 or stderr != b"" or stdout.replace(b"\r\n", b"\n") != (marker + "\n").encode():
        raise ValueError("CREST976_RESULT:" + case)
    return marker
