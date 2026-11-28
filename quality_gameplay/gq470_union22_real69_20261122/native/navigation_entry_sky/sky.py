"""Build and verify the exact #959 Native programs, without touching their outputs."""
import importlib.util
import inspect
from pathlib import Path


HERE = Path(__file__).resolve().parent
LOD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD.client.luau"
PROGRAMS = {"ON": "sky959_on.luau", "OFF": "sky959_off.luau"}
EXPECTED = {
    "sky959_desktop": "desktop exact author geometry and palette at twelve nonphysical matte wedges; camera swap preserves one bank group",
    "sky959_touch": "touch keeps nine owned matte wedges in three original offsets beyond the playable field",
    "sky959_reduced_flag": "reduced effects and runtime OFF independently prevent and retire all cloud geometry",
    "sky959_focus": "focus loss prevents background work; focus regain and script destruction own one group lifecycle",
    "sky959_expiry": "real arena phase expiration removes local cloud silhouettes immediately",
    "sky959_physical_off": "exact physical OFF retains original LOD without added sky geometry",
    "approach_touch": "existing current Host CastleAccessRamp receives at most 16 touch matte marks; physical door, ramp and HP preserved",
}
CASES = {name: "OFF" if name == "sky959_physical_off" else "ON" for name in EXPECTED}
PROCESS_COUNT = len(CASES)
FILES = set(PROGRAMS.values()) | {
    f"{case}.{extension}" for case in CASES for extension in ("stdout.log", "stderr.log", "status.txt")
}
SKY_CASE_SHA = "1c33954500212b66fc28c5d7c716249ab3124c7278d51b7908c35993df326cd3"
APPROACH_CASE_SHA = "5ff9b42632571072f969a98eba70c9ac7fcd0317a5919d0482016562f8d085f7"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}


def _load(path, name):
    entry = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(entry)
    entry.loader.exec_module(module)
    return module


def _pinned(path, sha, compose):
    raw = compose.read_file(path)
    compose.need(compose.identity(raw)["sha256"] == sha, "SKY959_INPUT:" + path.name)
    return raw


def program(source_root, mode, compose, source_pins):
    compose.need(mode in PROGRAMS, "SKY959_PROFILE")
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.strict_json(_pinned(shared / "INPUTS.json", MANIFEST_SHA, compose))
    engine = compose.read_file(shared / "engine_fixture.luau")
    compose.need(compose.identity(engine) == manifest["fixtures"]["engine_fixture.luau"], "SKY959_ENGINE")
    helpers = {}
    for name, sha in TEMPLATE_PINS.items():
        helper = _load(native / name / "__init__.py", "union22_sky959_" + name)
        body = inspect.getsource(helper._template).replace("\r\n", "\n").encode()
        compose.need(compose.identity(body)["sha256"] == sha, "SKY959_TEMPLATE:" + name)
        helpers[name] = helper
    template = helpers["footing_wards"]._template(engine, helpers, compose)
    water = native / "mage_water_chain"
    common = _load(water / "__init__.py", "union22_sky959_common")
    old = _pinned(water / "cases.luau", common.CASES_SHA, compose)
    sky = _pinned(HERE / "sky_cases.luau", SKY_CASE_SHA, compose)
    castle = _pinned(native / "ninja_beast_castle/castle_cases.luau", APPROACH_CASE_SHA, compose)
    cases = "\n".join(raw.decode() for raw in (old, sky, castle))
    insert = "-- INSERT_PHYSICAL_ART_LOD"
    compose.need(cases.count(insert) == 2, "SKY959_LOD_INSERT")
    bodies = common._sources(Path(source_root), source_pins, compose)
    cases = cases.replace(insert, bodies[LOD])
    return common._program(bodies, manifest["runtime_routes"], template, cases, compose)


def assert_result(case, stdout, stderr, exit_code):
    if case not in EXPECTED:
        raise ValueError("SKY959_CASE:" + str(case))
    marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{EXPECTED[case]}"
    if exit_code != 0 or stderr != b"" or stdout.replace(b"\r\n", b"\n") != (marker + "\n").encode():
        raise ValueError("SKY959_RESULT:" + case)
    return marker
