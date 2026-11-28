"""Bounded Native verification of the selected #1029 two-source shop cleanup."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "shop_lifecycle"
FOLLOWUP = "shop_lifecycle_followup"
KIOSK = "StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient.client.luau"
VIEW = "ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopView.luau"
CATALOG = "ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopCatalog.luau"
BODY_PINS = {
    KIOSK: ("14a8ce530a0c7134a17241feadef09e09838b5dad87d8292fcdbc78ce7094974",
            "b381bf0e4db6c5382f3621524eb3bc1e20f63b2977f3809c79adab85774b176d"),
    VIEW: ("f13044a08a1ee839c53c480f39eef9a497afed22c90af83584b97cb353f2231e",
           "6beac564c1875ed77786fbd094ac1aea18dbee449dfc507acac40b32dde123fe"),
}
CATALOG_SHA = "c9418ebec21b6ca1550a2f3aa1970631127087d1cc0fbd4e866d71b7644dc792"
FIXTURE_PINS = {
    "original38.luau": "c7e5ee363124d14d6356e697d0cb614491755c5f6596770a240e7440b33919a6",
    "strict_close_cases.luau": "ba54286619cfa155bc0644f81102c4a0d6c774ce44a747e5128a571e02e2b713",
    "residual_cases.luau": "89011b50f8a7e3082702be8d3432d89e98d448227861975be0d2e3f3adc70b7f",
    "independent_cases.luau": "b95492cb1c99f47ca67e80462df4b57717d2eb14759593f9cb4a88101312bd1f",
    "external_destroy.luau": "e2735210d0e010aa8adec2f612ad137acd9498586ffd647e3dcada982dcb9edc",
    "compatibility_cases.luau": "7f13f0c375e30a583746f1762dac6d8f718561d98be8fa8b1ebac2b63f73c923",
    "RESULT_LOCK.json": "752ee0e60e20af3dad8adeaaff5e14c17818145d8b36e0b150b7fb1ada09e449",
}
STRICT_DESTROY = b"""  self._properties.DestroyAttempts=(self._properties.DestroyAttempts or 0)+1
  if self._properties.DestroyInProgress then error("recursive Destroy on locked "..self.Name) end
  if self._properties.Destroyed then return end"""
DEFERRED_NOTICE = b"""  if self==f.queueThis then
   local captured={}
   for _,c in ipairs(self.Destroying.connections) do
    if c.Connected then table.insert(captured,c.callback) end
   end
   f.delivery=function() for _,cb in ipairs(captured) do launch(cb) end end
  else self.Destroying:Fire() end"""
CASE_COUNTS = {
    "on_main": (40, 40, 0),
    "on_locked": (41, 41, 0),
    "on_external": (50, 50, 0),
    "off_original": (38, 14, 24),
    "mixed_missing_owned": (3, 3, 0),
    "mixed_old_kiosk": (2, 2, 0),
}
PROCESS_COUNT = len(CASE_COUNTS)
FILES = {"receipt.json"} | {
    f"{case}.{suffix}" for case in CASE_COUNTS for suffix in ("luau", "stdout.log", "stderr.log", "status.txt")
}


def _read_fixture(compose):
    inputs = {}
    inputs_pins = {}
    for path, pin in FIXTURE_PINS.items():
        raw = compose.read_file(HERE / path)
        inputs_pins[path] = compose.identity(raw)
        compose.need(inputs_pins[path]["sha256"] == pin, "SHOP_FIXTURE:" + path)
        inputs[path] = raw
    expected = compose.strict_json(inputs["RESULT_LOCK.json"])
    compose.need(set(expected) == set(CASE_COUNTS), "SHOP_NATIVE_LOCK_CASES")
    return inputs, inputs_pins, expected


def _source_pins(profile, compose):
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "SHOP_PROFILE_STAGE")
    index = stages.index(FOLLOWUP)
    current = profile["sources"]
    on = (compose.trial_sources_before(profile, stages[index - 1]) if index else
          {name: row["after"] for name, row in current.items()})
    off = compose.trial_sources_before(profile, FOLLOWUP)
    rows = profile[FOLLOWUP]["rows"]
    scope = set(BODY_PINS)
    compose.need(len(on) == 69 and set(on) == set(off) == set(current) and set(rows) == scope
                 and {name for name in on if on[name] != off[name]} == scope,
                 "SHOP_PROFILE_SCOPE")
    compose.need(all(row["parent"]["before"] == current[name]["before"]
                     and row["parent"]["after"] == off[name] for name, row in rows.items()),
                 "SHOP_PROFILE_ROWS")
    for route, pins in BODY_PINS.items():
        compose.need((on[route]["sha256"], off[route]["sha256"]) == pins, "SHOP_SOURCE_BODY:" + route)
    compose.need(on[CATALOG]["sha256"] == off[CATALOG]["sha256"] == CATALOG_SHA, "SHOP_CATALOG_BODY")
    return {"ON": on, "OFF": off}


def _read_sources(source_root, pins, compose, profile):
    source_validator = Path(compose.__file__).resolve().parent / "native/mage_water_chain/__init__.py"
    definition = spec_from_file_location("shop_lifecycle_source_reader", source_validator)
    reader = module_from_spec(definition)
    definition.loader.exec_module(reader)
    previous = tuple(compose.RECENT_TRIAL_STAGES).index(FOLLOWUP) > 0
    on_root = source_root.parent / compose.PLAYER_CONTACT_SHADOW_OFF / "sources" if previous else source_root
    off_root = source_root.parent / compose.SHOP_LIFECYCLE_OFF / "sources"
    return {mode: reader._sources(root, pins[mode], compose)
            for mode, root in (("ON", on_root), ("OFF", off_root))}


def _programs(all_sources, inputs, compose):
    def once(raw, before, after):
        compose.need(raw.count(before) == 1, "SHOP_NATIVE_TEMPLATE:" + repr(before[:48]))
        return raw.replace(before, after, 1)

    original = inputs["original38.luau"]
    anchor = b"local passed=0;local failed=0"
    strict = once(original, b"  if self._properties.Destroyed or self._properties.DestroyInProgress then return end",
                  STRICT_DESTROY)
    strict = once(strict, b"  self.Destroying:Fire()", DEFERRED_NOTICE)

    def extended(raw, *names):
        additions = b"\n".join(inputs[name] for name in names)
        return once(raw, anchor, additions + b"\n" + anchor)

    def mixed(expect_mount):
        cases = inputs["compatibility_cases.luau"]
        marker = b"case('existing_38_readonly_controls'"
        compose.need(original.count(marker) == original.count(anchor) == 1, "SHOP_NATIVE_MIXED_TEMPLATE")
        return (original[:original.index(marker)]
                + once(cases, b"@EXPECTED_MOUNT@", b"true" if expect_mount else b"false")
                + original[original.index(anchor):])

    plan = {
        "on_main": (extended(original, "residual_cases.luau"), "ON", "ON"),
        "on_locked": (extended(strict, "strict_close_cases.luau"), "ON", "ON"),
        "on_external": (extended(strict, "independent_cases.luau", "external_destroy.luau"), "ON", "ON"),
        "off_original": (original, "OFF", "OFF"),
        "mixed_missing_owned": (mixed(False), "ON", "OFF"),
        "mixed_old_kiosk": (mixed(True), "OFF", "ON"),
    }
    programs = {}
    for case, (program, kiosk, view) in plan.items():
        for marker, role, route in (("KIOSK", kiosk, KIOSK), ("VIEW", view, VIEW), ("CATALOG", "OFF", CATALOG)):
            program = once(program, f"--@@FULL_SOURCE_{marker}@@".encode(), all_sources[role][route].encode())
        programs[case] = program
    return programs


def _prepare(source_root, profile, compose):
    inputs, fixture_pins, expected = _read_fixture(compose)
    source_pins = _source_pins(profile, compose)
    programs = _programs(_read_sources(source_root, source_pins, compose, profile), inputs, compose)
    return programs, fixture_pins, source_pins, expected


def _normalized(raw, filename):
    raw = raw.replace(b"\r\n", b"\n")
    for prefix in (b"./", b".\\", b""):
        for sep in (b"/", b"\\"):
            raw = raw.replace(prefix + b"shop_lifecycle" + sep + filename, b"@program@")
    return raw


def _args(case, binary):
    return [binary.name, f"{OUTPUT_NAME}/{case}.luau"]


def _validate_case(case, output, binary, expected, compose):
    stdout = compose.read_file(output / f"{case}.stdout.log")
    stderr = compose.read_file(output / f"{case}.stderr.log")
    status = compose.read_file(output / f"{case}.status.txt")
    exit_status = int(CASE_COUNTS[case][2] > 0)
    compose.need(expected["exit"] == exit_status and status == f"{exit_status}\n".encode(), "SHOP_NATIVE_EXIT:" + case)
    filename = (case + ".luau").encode()
    actual = {stream: _normalized(raw, filename) for stream, raw in (("stdout", stdout), ("stderr", stderr))}
    compose.need(all(compose.identity(raw) == expected[stream] for stream, raw in actual.items()),
                 "SHOP_NATIVE_RESULT:" + case)
    lines = actual["stdout"].decode("utf-8").splitlines()
    expected_summary = "\t".join(("SUMMARY", *map(str, CASE_COUNTS[case]), "NOT_STUDIO"))
    compose.need(lines[-1] == expected["summary"] == expected_summary, "SHOP_NATIVE_SUMMARY:" + case)
    reds = [line.split("\t", 3)[1:] for line in lines if line.startswith("CASE\t") and "\tFAIL\t" in line]
    compose.need(reds == expected["expected_red"] and len(reds) == CASE_COUNTS[case][2], "SHOP_NATIVE_RED_SCOPE:" + case)
    return {"argv": _args(case, binary), "stdout": compose.identity(stdout), "stderr": compose.identity(stderr),
            "status": compose.identity(status), "summary": expected_summary, "expected_red": reds}


def _binary(binary, binary_pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == binary_pin, "SHOP_NATIVE_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    _binary(binary, binary_pin, compose)
    programs, fixtures, pins, expected = prepared
    for case, source in programs.items():
        compose.need(compose.read_file(output / (case + ".luau")) == source, "SHOP_NATIVE_PROGRAM:" + case)
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "process_count": PROCESS_COUNT,
            "generated": {case: compose.identity(raw) for case, raw in programs.items()},
            "cases": {case: _validate_case(case, output, binary, expected[case], compose) for case in CASE_COUNTS},
            "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {entry.name for entry in output.iterdir()} == FILES
                 and all(entry.is_file() and not entry.is_symlink() for entry in output.iterdir()),
                 "SHOP_NATIVE_FILESET")
    receipt = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == receipt, "SHOP_NATIVE_RECEIPT")
    return receipt


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    from case_batch import run_cases

    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "SHOP_NATIVE_OUTPUT")
    _binary(binary, binary_pin, compose)
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for case, source in prepared[0].items():
        (output / (case + ".luau")).write_bytes(source)

    def execute(case):
        result = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                                capture_output=True, timeout=90, env=environment)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        _validate_case(case, output, binary, prepared[3][case], compose)

    run_cases(CASE_COUNTS, execute)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
