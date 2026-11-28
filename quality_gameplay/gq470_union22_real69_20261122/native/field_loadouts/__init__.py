"""Replay the selected PRIVATE field kits and their immediate physical parent."""
import importlib.util
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "field_loadouts"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
CASE_INPUTS = {
    "builder_cases.luau": "13d7a716e527373c04fd425be58749273984e8b20abb08ced3e155e6689ac47c",
    "beast_cases.luau": "2b9af379092760b6217c6d7505cb1f809b79da5edb23584eb7c2c6d83ee529ee",
    "trapper_cases.luau": "b3fb6d701ebce62cae2c9e1753894e59a9067e85ab68a1a6dfa18b7739a4063c",
    # Exact case block in the approved author's native-locked generated evidence.
    "sky_cases.luau": "7ea251ef268976467731823dcadad9ce5a0514a5edbab8009f31f11f05ae9cd7",
}
EXPECTED = {
    "builder_combo": "real air-to-ground D charges once and uses two bounded original-author timed neutral HP shots",
    "builder_cannon_ko": "standalone B cannon damages and credits exactly one actual Swarm KO",
    "builder_flight_only": "standalone flight reuses guarded steering and releases without damage",
    "builder_cover_muzzle": "existing live neutral remains unharmed behind muzzle sight cover",
    "beast_grounded_discharge": "original summon and single owned escort issue one exact server neutral discharge after warning",
    "beast_los_ko": "same Swarm verifies cover and credits one actual neutral Humanoid death",
    "beast_negative_unregistered": "unregistered craft and replicated owner tag do not admit a discharge",
    "beast_negative_carry": "pending ground discharge cancels on carry",
    "gravity_cap_and_release": "real S0 Tool charges E40, 0.30 tell then two neutral pulls and .32 release; no HP/KO/players",
    "gravity_release_wall": "new obstacle after committed pull blocks release independently of initial LOS",
    "gravity_cancel_carry": "real optional movement safely retires after carry without a stale release",
    "gravity_budget": "same server Tool enforces exact 24s cooldown and E40 once per cast",
    "sky_combo": "real D moves then grounds, gives one second fan preview, and hits at most two S0 neutrals",
    "sky_rain_cover": "actual grounded standalone B uses fixed reach, late LOS and current target pose",
    "sky_flight_only": "standalone C uses checked flight then its existing-role neutral landing wave",
    "sky_negative_avatar": "real sky cast cannot release after avatar",
    "sky_to_fire": "real existing F remains reachable with original metadata after new G selection",
    "builder_off_parent": "exact physical parent keeps old Builder Tools and no D",
    "beast_physical_parent_off": "original Beast A/B/C and one live companion remain on unchanged physical rollback",
    "gravity_physical_off": "actual legacy B still reaches original combat with its own damage and no growth cost",
    "sky_physical_parent_off": "exact previous source retains unselected physical Warrior A/B/C",
}
OFF_CASES = {"builder_off_parent", "beast_physical_parent_off", "gravity_physical_off", "sky_physical_parent_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _template(raw, compose):
    edits = (
        ("local fixturePrint=print", "local fixturePrint=print;math.randomseed(12345)"),
        # The legacy Gravity kit's C is restored by the later follow-up's public rollback switch.
        ("-- MAGE_RUNTIME_CASES\n", "Vector3.zero=Vector3.new(0,0,0)\n"
         "workspace:SetAttribute('P0D_ENABLE_PRIVATE_TRAPPER_RETURN',false)\n-- MAGE_RUNTIME_CASES\n"),
        ("local function ready(label)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')\n",
         "local function ready(label,role)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_'..(role or 'MAGE')),'職業選択')\n"),
    )
    template = raw.decode("utf-8")
    for old, new in edits:
        compose.need(template.count(old) == 1, "FIELD_LOADOUTS_FIXTURE_BOUNDARY")
        template = template.replace(old, new, 1)
    return template


def _isolate_beast_ko(case_source, compose):
    # The unchanged escort can score a KO while summoning, before this attack.
    # Measure only the chosen Tool cast; the blocked and legal HP witnesses stay exact.
    start = " local t=now\n activate(player,'D')\n check(tell(live) and energy(live)==60,'current companion authorizes actual cast')"
    check = "check(blocked.hp.Health==10 and legal.hp.Health==0 and live.swarm.getTotal()==1 and witness(live)==pet,"
    compose.need(case_source.count(start)==case_source.count(check)==1, "FIELD_LOADOUTS_BEAST_KO_BOUNDARY")
    case_source = case_source.replace(start, " local koBefore=live.swarm.getTotal()\n" + start, 1)
    return case_source.replace(check, check.replace("getTotal()==1", "getTotal()==koBefore+1"), 1)


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    mage = native / "mage_water_chain"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "FIELD_LOADOUTS_MANIFEST")
    audited = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == audited["fixtures"]["engine_fixture.luau"], "FIELD_LOADOUTS_ENGINE_FIXTURE")
    template = _template(fixture, compose)

    spec = importlib.util.spec_from_file_location("union22_field_shared_mage_native", mage / "__init__.py")
    shared_mage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared_mage)
    retained = compose.read_file(mage / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(retained)
    compose.need(fixtures["mage_water_cases"]["sha256"] == shared_mage.CASES_SHA, "FIELD_LOADOUTS_SHARED_CASES")
    cases = [retained.decode("utf-8")]
    for name, sha in CASE_INPUTS.items():
        raw = compose.read_file(HERE / name)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == sha, "FIELD_LOADOUTS_CASE_PIN:" + name)
        fixtures[name] = pin
        body = raw.decode("utf-8")
        if name == "beast_cases.luau":
            body = _isolate_beast_ko(body, compose)
            fixtures["beast_ko_relative_case"] = compose.identity(body.encode("utf-8"))
        cases.append(body)

    routes = audited["runtime_routes"]
    after = {name: row["after"] for name, row in profile["sources"].items()}
    changed = profile["field_loadouts_followup"]["rows"]
    compose.need(set(changed) == {FIRST90, routes["Host"], routes["SwarmCombat"], routes["SevenRoleCombat"],
                                 routes["InteractionGuard"]}
                 and all(row["parent"]["before"] == profile["sources"][name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "FIELD_LOADOUTS_PROFILE_SCOPE")
    later = profile["return_convert_followup"]["rows"]
    latest = profile["ground_night_followup"]["rows"]
    cover_orders = profile["cover_orders_followup"]["rows"]
    mage_field_arcs = profile["mage_field_arcs_followup"]["rows"]
    before = (after | {name: row["parent"]["after"] for name, row in mage_field_arcs.items()}
              | {name: row["parent"]["after"] for name, row in cover_orders.items()}
              | {name: row["parent"]["after"] for name, row in latest.items()}
              | {name: row["parent"]["after"] for name, row in later.items()}
              | {name: row["parent"]["after"] for name, row in changed.items()})
    off_root = source_root.parent / compose.FIELD_LOADOUTS_OFF / "sources"
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    corpus = "\n".join(cases)
    generated = {name: shared_mage._program(shared_mage._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "FIELD_LOADOUTS_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "FIELD_LOADOUTS_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "FIELD_LOADOUTS_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "FIELD_LOADOUTS_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "FIELD_LOADOUTS_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "FIELD_LOADOUTS_OUTPUT")
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
        compose.need(result.returncode == 0, "FIELD_LOADOUTS_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
