"""Execute source-extracted client cues on the existing four-voice test boundary."""
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel.client.luau"
OUTPUT = "fixed_cues"
PROGRAM = "generated.luau"
PROGRAM_ARG = f"{OUTPUT}/{PROGRAM}"
FILES = {PROGRAM, "stdout.log", "stderr.log", "status.txt", "receipt.json"}
PROCESS_COUNT = 1
FIXTURES = {
    "fixture.luau": "4c585bbb1cae484deab3ceca08929d019200eac584ea114847f6d8e753aa28a7",
    "legacy_cases.luau": "7bfac605f54a4bd7f769fefdce0cf468e32986e7044f912635a717ffbd314ad1",
    "ability_cases.luau": "93cfe1fd7ce6747c37bd24761d6c2b1aecb8c5400a1bc37d0fd9ab869866aa52",
}
MARKERS = (
    b"MAGE_CAST_CUE_THREE_DISTINCT_LOCAL_DIRECTIONS_AND_EXISTING_AUDIO_POOL_PASS",
    b"MAGE_CAST_CUE_OFF_LEGACY_OTHER_SLOT_AMBIGUITY_AND_LIFECYCLE_PASS",
    b"MAGE_CAST_CUE_LEGACY_HIT_POOL_PREEMPTION_PASS",
    b"FIXED_PRIVATE_CAST_IDS_15_USE_EXISTING_CLIENT_RENDER_AND_AUDIO_PASS",
    b"FIXED_PRIVATE_CAST_CUE_ROLE_GATE_AND_CANCELLATION_PASS",
)


def _prepare(source_root, profile, compose):
    raw = compose.read_file(source_root / ROUTE)
    pin = compose.identity(raw)
    compose.need(pin == profile["sources"][ROUTE]["after"], "FIXED_CUES_SOURCE_PIN")
    material = {name: compose.read_file(HERE / name) for name in FIXTURES}
    pins = {name: compose.identity(payload) for name, payload in material.items()}
    compose.need({name: info["sha256"] for name, info in pins.items()} == FIXTURES,
                 "FIXED_CUES_FIXTURE_PINS")
    body = raw.decode("utf-8")

    def between(start, stop):
        compose.need(body.count(start) == body.count(stop) == 1 and body.index(start) < body.index(stop),
                     "FIXED_CUES_SELECTED_BOUNDARY")
        return body[body.index(start):body.index(stop)]

    old_tones = 'local tones={MAGE=Color3.fromRGB(97,212,255),WARRIOR=Color3.fromRGB(255,214,91)}'
    fixture = material["fixture.luau"].decode("utf-8")
    compose.need(fixture.count(old_tones) == 1, "FIXED_CUES_FIXTURE_TONE_PIN")
    fixture = fixture.replace(old_tones, between("local tones={", "-- Small, short-lived hit reticle"))
    program = "\n".join((
        fixture,
        between("local function reduced():boolean", "-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 END"),
        between("-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117",
                "-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117"),
        between("-- MAGE_PROJECTILE_CAST_AUDIO_BEGIN", "-- MAGE_PROJECTILE_CAST_AUDIO_END"),
        material["legacy_cases.luau"].decode("utf-8"), material["ability_cases.luau"].decode("utf-8"),
    )).encode("utf-8")
    return program, pin, pins


def _receipt(source_root, output, binary, binary_pin, context, profile, compose):
    body, source_pin, fixtures = _prepare(source_root, profile, compose)
    compose.need(compose.identity(compose.read_file(binary)) == binary_pin, "FIXED_CUES_BINARY")
    compose.need(compose.read_file(output / PROGRAM) == body, "FIXED_CUES_GENERATED_BYTES")
    stdout = compose.read_file(output / "stdout.log")
    stderr = compose.read_file(output / "stderr.log")
    status = compose.read_file(output / "status.txt")
    compose.need(status == b"0\n" and stderr == b"" and tuple(stdout.splitlines()) == MARKERS,
                 "FIXED_CUES_NATIVE_OBSERVED")
    evidence = {name: compose.identity(compose.read_file(output / name)) for name in FILES - {"receipt.json"}}
    return {"schema": "UNION22_FIXED_CAST_CUE_NATIVE_V1", "context": context, "source": source_pin,
            "fixtures": fixtures, "binary": binary_pin, "argv": [binary.name, PROGRAM_ARG],
            "output_files": evidence, "studio_audio": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = Path(source_root), Path(out_folder), Path(binary)
    compose.need(output.name == OUTPUT and output.is_dir() and not output.is_symlink()
                 and {p.name for p in output.iterdir()} == FILES, "FIXED_CUES_EVIDENCE_FILE_SET")
    record = _receipt(source_root, output, binary, binary_pin, context, profile, compose)
    compose.need(compose.strict_json(compose.read_file(output/"receipt.json")) == record,
                 "FIXED_CUES_RECEIPT")
    return record


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = Path(source_root), Path(out_folder), Path(binary)
    compose.need(output.name == OUTPUT and compose.identity(compose.read_file(binary)) == binary_pin,
                 "FIXED_CUES_RUN_INPUT")
    program, _, _ = _prepare(source_root, profile, compose)
    output.mkdir()
    (output / PROGRAM).write_bytes(program)
    result = subprocess.run([str(binary.resolve()), PROGRAM_ARG], cwd=output.parent, env=environment,
                            capture_output=True, timeout=60)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    (output / "status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
    compose.write_json(output / "receipt.json", _receipt(
        source_root, output, binary, binary_pin, context, profile, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
