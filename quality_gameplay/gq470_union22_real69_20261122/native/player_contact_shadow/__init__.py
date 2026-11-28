"""Native gate for the exact #1001 contact shadow and protected inherited art."""
from importlib.util import module_from_spec, spec_from_file_location
import inspect
import io
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "player_contact_shadow"
FOLLOWUP = "player_contact_shadow_followup"
ART = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD.client.luau"
PROGRAMS = {"ON": "client_on.luau", "OFF": "client_off.luau"}
ART_PINS = {
    "ON": "0b61e7d3cc4fdefcbd024f8151713bc9a59a3efb62c23fbbc6125983fab3a52a",
    "OFF": "ead4f14c1f7bed5bc331e581f4e58680a15bfe0cbda997b79ca2b3a67394db70",
}
ON_SHADOW_BODY = "f6784da50a737cc4301101368b039ad96f8256b6bda0876df25acdcb6f58e8e6"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
INPUT_PINS = {
    "author_shadow.luau": "fa7876e3383ff85318e86457e3c90439773bcc749b941599d1b810cc6e6b3577",
    "author_gate.py": "bfe6aa77869541dc928f5f0218868bcb8f01ee2b1588133bf27d67c9129925b5",
    "shadow_cases.luau": "360a4236110cb028b321593134c3a49e7b896c6963bae1ac4cd18f09b1b86613",
    "mobility_crests/crest_cases.luau": "d5b778229d37f778acc980eae179fe98a5a98cf561f966d4bc47aa9ef7da87b2",
    "mobility_crests/crest_fixture.luau": "a919b6545aed764d80ab3dc57a5594d4b308dedfae71889879e71d8c0d28073f",
    "navigation_entry_sky/sky_cases.luau": "1c33954500212b66fc28c5d7c716249ab3124c7278d51b7908c35993df326cd3",
    "ninja_beast_castle/castle_cases.luau": "5ff9b42632571072f969a98eba70c9ac7fcd0317a5919d0482016562f8d085f7",
}
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
EXPECTED = {
    "shadow1001_desktop": "author desktop 75 studs and 0.10s; one reusable matte disc, exact fade",
    "shadow1001_touch": "author Touch 55 studs and 0.16s; one reusable matte disc, exact fade",
    "shadow1001_floor_safety": "actual cast rejects steep, transparent, non-solid, water, actor-supported and missing floor",
    "shadow1001_camera_avatar": "Scriptable, observer, first-person and old avatar excluded; own death clears immediately",
    "shadow1001_flags_and_lifetime": "runtime OFF, reduced effects, underwater, stealth and script teardown own cleanup",
    "shadow1001_physical_off": "physical OFF retains original ArtDistanceLOD and has zero contact shadow work",
    "crest976_touch": "two nearest real TEAM peers, four passive wedges maximum",
    "sky959_touch": "touch keeps nine owned matte wedges in three original offsets beyond the playable field",
    "approach_touch": "existing current Host CastleAccessRamp receives at most 16 touch matte marks; physical door, ramp and HP preserved",
}
PROCESS_COUNT = len(EXPECTED)
FILES = set(PROGRAMS.values()) | {"receipt.json"} | {
    f"{case}.{extension}" for case in EXPECTED for extension in ("stdout.log", "stderr.log", "status.txt")
}
SIDE = {case: "OFF" if case == "shadow1001_physical_off" else "ON" for case in EXPECTED}


def _load(path, name):
    entry = spec_from_file_location(name, path)
    result = module_from_spec(entry)
    entry.loader.exec_module(result)
    return result


def _pinned(path, sha, compose):
    raw = compose.read_file(path)
    compose.need(compose.identity(raw)["sha256"] == sha, "CONTACT_SHADOW_INPUT:" + path.name)
    return raw


def _source_pins(profile, compose):
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "CONTACT_SHADOW_STAGE")
    index = stages.index(FOLLOWUP)
    current = profile["sources"]
    on = (compose.trial_sources_before(profile, stages[index - 1]) if index else
          {name: row["after"] for name, row in current.items()})
    off = compose.trial_sources_before(profile, FOLLOWUP)
    rows = profile[FOLLOWUP]["rows"]
    compose.need(len(on) == 69 and set(on) == set(off) == set(current) and set(rows) == {ART}
                 and {name for name in on if on[name] != off[name]} == {ART},
                 "CONTACT_SHADOW_PROFILE_SCOPE")
    compose.need(rows[ART]["parent"]["before"] == current[ART]["before"]
                 and rows[ART]["parent"]["after"] == off[ART], "CONTACT_SHADOW_PROFILE_PARENT")
    for mode, pins in (("ON", on), ("OFF", off)):
        compose.need(pins[ART]["sha256"] == ART_PINS[mode], "CONTACT_SHADOW_PROFILE_ART:" + mode)
    return {"ON": on, "OFF": off}


def _original_author_checks(inputs, art, compose):
    open_marker = "-- #1001 contact shadow, bound to this client script's lifetime.\ndo\n(function()\n"
    close_marker = "end)()\nend\n\nfor _,instance in ipairs(workspace:GetDescendants()) do register(instance) end"
    art = art.replace("\r\n", "\n")
    compose.need(art.count(open_marker) == art.count(close_marker) == 1, "CONTACT_SHADOW_MOUNTED_BODY")
    embedded = art.split(open_marker, 1)[1].split(close_marker, 1)[0]
    compose.need(compose.identity(embedded.encode())["sha256"] == ON_SHADOW_BODY, "CONTACT_SHADOW_MOUNT_PIN")

    # Run the unchanged writer-authored tests without constructing scratch source files.
    script = inputs["author_gate.py"]
    scope = {"__name__": "contact_shadow_original_author_gate", "__file__": str(HERE / "author_gate.py")}
    exec(compile(script, scope["__file__"], "exec"), scope)
    bodies = {"donor": inputs["author_shadow.luau"], "mounted": embedded.encode()}
    archive = {}
    for name, code in bodies.items():
        scope["SOURCE_PATH"] = SimpleNamespace(read_text=lambda **kwargs: code.decode("utf-8"))
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(scope["LocalAvatarContactShadow"])
        result = unittest.TextTestRunner(stream=io.StringIO()).run(tests)
        compose.need(result.wasSuccessful() and result.testsRun == 2, "CONTACT_SHADOW_AUTHOR_GATE:" + name)
        archive[name] = {"source": compose.identity(code), "tests": 2, "negative_mutations": 24}
    return archive


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    raw_manifest = _pinned(shared / "INPUTS.json", MANIFEST_SHA, compose)
    manifest = compose.strict_json(raw_manifest)
    engine = compose.read_file(shared / "engine_fixture.luau")
    pose = {"manifest": compose.identity(raw_manifest), "engine": compose.identity(engine)}
    compose.need(pose["engine"] == manifest["fixtures"]["engine_fixture.luau"], "CONTACT_SHADOW_ENGINE")
    helpers = {}
    for name, sha in TEMPLATE_PINS.items():
        helper = _load(native / name / "__init__.py", "contact_shadow_" + name)
        body = inspect.getsource(helper._template).replace("\r\n", "\n").encode()
        compose.need(compose.identity(body)["sha256"] == sha, "CONTACT_SHADOW_TEMPLATE:" + name)
        pose[name + "_template"] = compose.identity(body)
        helpers[name] = helper
    template = helpers["footing_wards"]._template(engine, helpers, compose)
    pose["rendered_template"] = compose.identity(template.encode("utf-8"))

    water = native / "mage_water_chain"
    common = _load(water / "__init__.py", "contact_shadow_existing_native")
    common_cases = _pinned(water / "cases.luau", common.CASES_SHA, compose)
    pose["existing_common_cases"] = compose.identity(common_cases)
    fixture = {}
    for path, sha in INPUT_PINS.items():
        fixture[path] = _pinned((native if "/" in path else HERE) / path, sha, compose)
        pose[path] = compose.identity(fixture[path])
    corpus = "\n".join(body.decode() for body in (
        fixture["mobility_crests/crest_fixture.luau"], common_cases, fixture["shadow_cases.luau"],
        fixture["mobility_crests/crest_cases.luau"], fixture["navigation_entry_sky/sky_cases.luau"],
        fixture["ninja_beast_castle/castle_cases.luau"],
    ))
    insert = "-- INSERT_PHYSICAL_ART_LOD"
    compose.need(corpus.count(insert) == 4, "CONTACT_SHADOW_PHYSICAL_ART_INSERT")
    pins = _source_pins(profile, compose)
    off_root = source_root.parent / compose.PLAYER_CONTACT_SHADOW_OFF / "sources"
    programs, author = {}, None
    for mode, root in (("ON", source_root), ("OFF", off_root)):
        bodies = common._sources(root, pins[mode], compose)
        if mode == "ON":
            author = _original_author_checks(fixture, bodies[ART], compose)
        programs[PROGRAMS[mode]] = common._program(
            bodies, manifest["runtime_routes"], template, corpus.replace(insert, bodies[ART]), compose)
    return programs, pins, pose, author


def _argv(case, binary):
    return [binary.name, f"{OUTPUT_NAME}/{PROGRAMS[SIDE[case]]}", "-a", case]


def _binary(binary, binary_pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == binary_pin, "CONTACT_SHADOW_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    _binary(binary, binary_pin, compose)
    programs, pins, fixtures, author = prepared
    for name, data in programs.items():
        compose.need(compose.read_file(output / name) == data, "CONTACT_SHADOW_PROGRAM:" + name)
    cases = {}
    for case, label in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{label}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode()
                     and stderr == b"" and status == b"0\n", "CONTACT_SHADOW_RESULT:" + case)
        cases[case] = {"argv": _argv(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                       "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "author_gate": author, "process_count": PROCESS_COUNT,
            "generated": {key: compose.identity(program) for key, program in programs.items()},
            "cases": cases, "studio": "NOT_TESTED", "android": "NOT_TESTED", "art": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {entry.name for entry in output.iterdir()} == FILES
                 and all(entry.is_file() and not entry.is_symlink() for entry in output.iterdir()),
                 "CONTACT_SHADOW_FILESET")
    receipt = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == receipt, "CONTACT_SHADOW_RECEIPT")
    return receipt


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    from case_batch import run_cases

    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "CONTACT_SHADOW_OUTPUT")
    _binary(binary, binary_pin, compose)
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, program in prepared[0].items():
        (output / name).write_bytes(program)

    def execute(case):
        proc = subprocess.run([str(binary.resolve()), *_argv(case, binary)[1:]], cwd=output.parent,
                              capture_output=True, timeout=90, env=environment)
        (output / f"{case}.stdout.log").write_bytes(proc.stdout)
        (output / f"{case}.stderr.log").write_bytes(proc.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{proc.returncode}\n".encode("ascii"))
        compose.need(proc.returncode == 0, "CONTACT_SHADOW_EXIT:" + case)

    run_cases(EXPECTED, execute)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
