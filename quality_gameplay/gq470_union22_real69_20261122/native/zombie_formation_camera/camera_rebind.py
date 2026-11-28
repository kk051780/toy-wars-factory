"""Pure #981 program and output assertions for the two physical Native profiles."""

from hashlib import sha256
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills.client.luau"
CASES = {"ON": "camera_rebind_on", "OFF": "camera_rebind_off"}
PROCESS_COUNT = len(CASES)
FILES = {
    f"{case}.{suffix}"
    for case in CASES.values()
    for suffix in ("luau", "stdout.log", "stderr.log", "status.txt")
}
AUTHOR = {
    "pr": 981,
    "head": "5479b9875620ca6466259d17e61b68be86df8442",
    "blob": "b236015df1279904013e4b6e0a6ba230d3321be8",
    "native_fixture_blob": "2d2f99966a2244f0b646e8571ba9324128a77b6a",
    "soft_scope": "https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7056914098",
    "run": 44864259996,
    "artifact": 14691376335,
}
SOURCE_PINS = {
    "ON": {"bytes": 15056, "sha256": "a92531ecc7e50321d9bc34f8491829ea20ceb249a5be1d4cff5eb7837156b370"},
    "OFF": {"bytes": 11568, "sha256": "2d4145fdbd05359e89cf52ca41117ec416c7b6e7ad3d95aedac5c857bc3e34fe"},
}
FIXTURE_PINS = {
    "fixture.luau": {"bytes": 3580, "sha256": "859435f57caa6b0ff9633c73764cc7aad18667a6043f3941e71fdb1330b8d18a"},
    "cases.luau": {"bytes": 5408, "sha256": "0e595b36d00d13d30a860cfdc6ef1d01079181b0b8ee3b96143023de8ca14043"},
}
MARKERS = {
    "ON": (
        b"CAMERA_981_NIL_SUBJECT_FIVE_RETRIES_PASS",
        b"CAMERA_981_DEAD_CURRENT_AND_PROVEN_PREVIOUS_OWN_PASS",
        b"CAMERA_981_FOREIGN_DETACHED_RIG_SEAT_SCRIPTABLE_FIXED_AND_VALID_SUBJECT_PASS",
        b"CAMERA_981_STALE_CHARACTER_WRONG_PLAYER_AND_CAMERA_REPLACEMENT_PASS",
        b"CAMERA_981_INITIAL_NIL_CAMERA_LATE_HUMANOID_AND_WINDOW_EXPIRY_PASS",
        b"CAMERA_981_ELIMINATED_DOWNED_AND_EXISTING_BASIC_SKILL_LIFECYCLE_PASS",
    ),
    "OFF": (b"CAMERA_981_PHYSICAL_OFF_PREVIOUS_MOTION_ONLY_PASS",),
}


def _pin(raw):
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def _need(condition, label):
    if not condition:
        raise ValueError(f"CAMERA_REBIND_{label}")


def program(source_root, mode):
    """Wrap the full selected client Lua bytes with pinned API fixtures and cases."""
    _need(mode in CASES, "MODE")
    source = (Path(source_root) / ROUTE).read_bytes()
    _need(_pin(source) == SOURCE_PINS[mode], "SOURCE_PIN")
    inputs = {}
    for name, expected in FIXTURE_PINS.items():
        raw = (HERE / name).read_bytes()
        _need(_pin(raw) == expected, "FIXTURE_PIN_" + name)
        inputs[name] = raw
    boundary = b"local case=(...)\n"
    cases = inputs["cases.luau"]
    _need(cases.count(boundary) == 1, "MODE_ANCHOR")
    selected = cases.replace(boundary, f'local case="{mode}"\n'.encode("ascii"), 1)
    return b"\n".join((inputs["fixture.luau"], source, selected))


def assert_result(mode, stdout, stderr, exit_code):
    """Return ordered marker text only for a clean, complete Native execution."""
    _need(mode in CASES, "MODE")
    _need(type(exit_code) is int and exit_code == 0 and stderr == b"", "NATIVE_STATUS_" + mode)
    expected = b"\n".join(MARKERS[mode]) + b"\n"
    _need(stdout in (expected, expected.replace(b"\n", b"\r\n")), "NATIVE_MARKERS_" + mode)
    return tuple(marker.decode("ascii") for marker in MARKERS[mode])
