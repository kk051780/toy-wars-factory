"""Pure source and result validators for the two fixed field-cast Native processes."""

from hashlib import sha256
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel.client.luau"
CASES = {"ON": "cast_cues_on", "OFF": "cast_cues_off"}
PROCESS_COUNT = len(CASES)
FILES = {
    f"{case}.{suffix}"
    for case in CASES.values()
    for suffix in ("luau", "stdout.log", "stderr.log", "status.txt")
}
SOURCE_PINS = {
    "ON": {
        "bytes": 44000,
        "sha256": "5bf9dbb028d9f434540c286f4c5f19eaa0047b29e5cfc374606a7e33feeb612c",
    },
    "OFF": {
        "bytes": 39654,
        "sha256": "5749d58239a7be9029722808f732d3f5d0108a650bdfd1aaf6d403321048b39c",
    },
}
FIXTURE_PINS = {
    "fixture.luau": "4c585bbb1cae484deab3ceca08929d019200eac584ea114847f6d8e753aa28a7",
    "legacy_cases.luau": "7bfac605f54a4bd7f769fefdce0cf468e32986e7044f912635a717ffbd314ad1",
    "ability_cases.luau": "de65e1d8c72b17bcc4fa1c8803e149e709b5f3565457a24f14155776ab10055d",
    "field_cases.luau": "0e578bbfeb7b87569cd053032631642204d28fbd10aa72dfd3a26dae5347db33",
    "field_off_cases.luau": "638a0e3d2262954e9c0d8d61cf0190c3e974851d57db9cd83a6460c61d9947a3",
}
LEGACY_MARKERS = (
    b"MAGE_CAST_CUE_THREE_DISTINCT_LOCAL_DIRECTIONS_AND_EXISTING_AUDIO_POOL_PASS",
    b"MAGE_CAST_CUE_OFF_LEGACY_OTHER_SLOT_AMBIGUITY_AND_LIFECYCLE_PASS",
    b"MAGE_CAST_CUE_LEGACY_HIT_POOL_PREEMPTION_PASS",
    b"FIXED_PRIVATE_CAST_IDS_35_PASS",
    b"FIXED_PRIVATE_CAST_CUE_ROLE_GATE_AND_CANCELLATION_PASS",
    b"FIXED_PRIVATE_RETURN_REQUIRES_GRAVITY_AND_CANCELS_PASS",
)
MARKERS = {
    "ON": LEGACY_MARKERS
    + (
        b"FIELD_CAST_18_FIXED_ROLE_SLOT_AUDIO_AND_MOTION_PROFILES_PASS",
        b"FIELD_CAST_ACTOR_SLOT_AMBIGUITY_PHASE_AND_LIVE_OFF_PASS",
        b"FIELD_CAST_MUTE_REDUCED_EFFECTS_OLD_AVATAR_AND_R6_R15_FIXTURE_PASS",
        b"FIELD_CAST_CONFIRMED_HIT_PRIORITY_AND_SIX_HIT_FOUR_VOICE_CAP_PASS",
    ),
    "OFF": LEGACY_MARKERS + (b"FIELD_CAST_PHYSICAL_OFF_18_GENERIC_AND_NO_NEW_AUDIO_PASS",),
}
ASSETS = {
    "CLIP": "rbxasset://sounds/action_jump.mp3",
    "STEP": "rbxasset://sounds/action_jump_land.mp3",
    "WATER": "rbxasset://sounds/impact_water.mp3",
    "GET_UP": "rbxasset://sounds/action_get_up.mp3",
}
# Expected values are independent of the client parser and fixed tool dispatch table.
EXPECTED = (
    ("WARRIOR-004", "WARRIOR", "A", .20, -9, "STEP", .88, .107, .016, 0),
    ("WARRIOR-006", "WARRIOR", "B", .22, 5, "GET_UP", .86, .108, .023, .008),
    ("WARRIOR-009", "WARRIOR", "C", .24, 72, "CLIP", 1.44, .094, 0, -.022),
    ("WARRIOR-013", "WARRIOR", "A", .19, 32, "STEP", 1.26, .111, .009, -.014),
    ("WARRIOR-014", "WARRIOR", "B", .23, 3, "GET_UP", 1.05, .099, 0, .018),
    ("WARRIOR-017", "WARRIOR", "C", .25, 86, "STEP", .71, .101, 0, .026),
    ("NINJA-001", "NINJA", "A", .16, 16, "CLIP", 1.68, .082, .016, 0),
    ("NINJA-002", "NINJA", "B", .17, -33, "GET_UP", 1.78, .081, -.014, -.009),
    ("NINJA-004", "NINJA", "C", .18, 34, "CLIP", 1.24, .087, -.02, .007),
    ("NINJA-005", "NINJA", "A", .23, -22, "WATER", 1.14, .078, .005, -.012),
    ("NINJA-006", "NINJA", "B", .20, -15, "CLIP", 1.51, .091, .022, -.004),
    ("NINJA-008", "NINJA", "C", .22, 9, "WATER", 1.83, .083, .025, 0),
    ("MAGE-005", "MAGE", "A", .19, 18, "GET_UP", 1.46, .096, .022, -.009),
    ("MAGE-079", "MAGE", "C", .23, -9, "CLIP", 1.72, .097, .028, 0),
    ("MAGE-047", "MAGE", "B", .24, 90, "WATER", 1.40, .107, 0, -.023),
    ("BEAST-061", "BEAST", "A", .20, 20, "STEP", 1.12, .098, .018, .007),
    ("BEAST-062", "BEAST", "C", .21, -12, "WATER", 1.58, .086, .014, -.013),
    ("BEAST-067", "BEAST", "D", .23, -28, "GET_UP", 1.68, .092, .022, -.014),
)
SECTIONS = (
    ("local function reduced():boolean", "-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 END"),
    ("-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117", "-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117"),
    ("-- MAGE_PROJECTILE_CAST_AUDIO_BEGIN", "-- MAGE_PROJECTILE_CAST_AUDIO_END"),
)


def _need(condition, label):
    if not condition:
        raise ValueError(f"FIELD_CAST_{label}")


def _replacement(source, match, replacement):
    _need(source.count(match) == 1, "FIXTURE_ANCHOR")
    return source.replace(match, replacement, 1)


def _between(source, begin, end):
    _need(source.count(begin) == source.count(end) == 1 and source.index(begin) < source.index(end),
          "SOURCE_ANCHOR")
    return source[source.index(begin):source.index(end)]


def program(source_root, mode, fixture_root=None):
    """Return executable bytes for the exact ON or physical OFF CombatFeel source."""
    _need(mode in CASES, "MODE")
    shared = Path(fixture_root) if fixture_root is not None else HERE.parent / "fixed_cues"
    raw = (Path(source_root) / ROUTE).read_bytes()
    _need({"bytes": len(raw), "sha256": sha256(raw).hexdigest()} == SOURCE_PINS[mode], "SOURCE_PIN")
    source = raw.decode("utf-8")
    fixtures = {}
    for name, digest in FIXTURE_PINS.items():
        value = ((HERE if name.startswith("field_") else shared) / name).read_bytes()
        _need(sha256(value).hexdigest() == digest, "FIXTURE_PIN_" + name)
        fixtures[name] = value.decode("utf-8")
    fixture = _replacement(
        fixtures["fixture.luau"],
        "local tones={MAGE=Color3.fromRGB(97,212,255),WARRIOR=Color3.fromRGB(255,214,91)}",
        _between(source, "local tones={", "-- Small, short-lived hit reticle"),
    )
    matrix = "".join(
        f' {{"{id_}","{role}","{slot}",{time},{turn},"{ASSETS[clip]}",{pitch},{volume},{x},{y}}},\n'
        for id_, role, slot, time, turn, clip, pitch, volume, x, y in EXPECTED
    )
    suffix = "field_cases.luau" if mode == "ON" else "field_off_cases.luau"
    return "\n".join((
        fixture,
        *(_between(source, begin, end) for begin, end in SECTIONS),
        fixtures["legacy_cases.luau"],
        fixtures["ability_cases.luau"],
        _replacement(fixtures[suffix], " -- CUE_MATRIX\n", matrix),
    )).encode("utf-8")


def assert_result(mode, stdout, stderr, exit_code):
    """Reject substituted output or diagnostics and return ordered observed marker text."""
    _need(mode in CASES, "MODE")
    _need(type(exit_code) is int and exit_code == 0 and stderr == b"", "NATIVE_STATUS_" + mode)
    _need(tuple(stdout.splitlines()) == MARKERS[mode], "NATIVE_MARKERS_" + mode)
    return tuple(marker.decode("ascii") for marker in MARKERS[mode])
