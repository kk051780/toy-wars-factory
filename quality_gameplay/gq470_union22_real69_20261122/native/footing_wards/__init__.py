"""Exercise physical footing, wind wards, Trapper reversal, and Zombie waves."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "footing_wards"
FOLLOWUP = "footing_wards_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
}
CASE_PINS = {
    "footing_cases.luau": "71db032cf1a731ba39afb3630339dc24533ba3454293378b97cb102db4722189",
    "mage_ward_cases.luau": "32396ad652aeee396839620ca3e7190d3f7daf6b1177b61f43d007e5af4c1f14",
    "reversal_cases.luau": "a837a94706936d200c497c72bd67e732ec3f999cbda64c3b83a4b8e0490c0415",
    "zombie_waves_cases.luau": "2db6395a72db08e6f145811e449aef2076612cbb6faf9ae9505f4aaf8fcd2a24",
    "builder_forms/zombie_rune_cases.luau": "b6aeb896c23e1fed1c079f5fbc0c2f71c73792ecdcad22f1fef43278363aa600",
    "eclipse_sweep/swap_hover_cases.luau": "e507745cbdb17a3086f34fdc5b8c837b3dd404083f3f783f5d458bda5f47bfd9",
}
EXPECTED = {
    **{f"footing_role_{role.lower()}": f"{role} current authorized C placed a collidable S0 platform at its real position"
       for role in ("WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE")},
    "footing_loadout_exclusive": "shared C keeps recipe component selection consistent and restores the previous Mage kit",
    "footing_obstacle": "real overlapping world geometry denies placement before spending",
    "footing_combo_landing": "D uses one E80, own contact, finite front 8%, and immediate contact loss",
    "footing_stage_four": "real active-time stage four grows the support footprint and duration to the fixed S4 values",
    "footing_combo_wrong_contact": "another actual surface never satisfies the ownership-checked landing receipt",
    "footing_live_off": "live independent OFF restores the native skill and destroys the existing support",
    "footing_physical_off": "immediate exact parent has no common footing or new prompt",
    "ward_membrane": "real hostile Warrior skill takes 41.36 HP; one-hit membrane removed",
    "ward_light_hit": "actual hostile Warrior skill takes 40.48 HP; one-hit Light shield removed",
    "ward_wind_excludes_melee": "real 44 HP non-flight attack leaves wind active; no category spoofing",
    "ward_guardian_hit": "10 siege prompts create actual Ice Mage guardian; one swept front bolt deals 5.64 HP, old period holds",
    "ward_guardian_dodge": "same real targeted flight deals zero after lateral dodge and retires at the range bound",
    "ward_guardian_wall": "late wall added after actual Ice Mage launch cancels impact without HP writes",
    "ward_combo": "one E80, all three shared deadlines; Wind arms, then actual same-world Swarm pursuit damages one tracked neutral",
    "ward_combo_wall": "late solid blocker on actual pursuit leaves neutral HP intact and clears owned ward",
    "ward_invalid_or_off": "no debit while carrying/airborne; observed physical live OFF removes queued combo, stance, and old Tool",
    "ward_physical_off": "ancestor 69 sources: original Mage tools, no ward or true-flight conversion; old 6 HP Guardian hit",
    "reversal040": "040 one-second warning reverses only three actual neutral tracks, with unchanged HP, clocks and resumed AI",
    "reversal060": "060 existing bounded flight performs one real neutral-only hit after confirmed landing",
    "reversal012": "012 real CONTROL then FLIGHT then LAND commits one E80, all deadlines, and zero damaging side effect",
    "reversal_deny_static": "012 denied for static without flight, damage, or E80",
    "reversal_deny_latewall": "012 denied for latewall without flight, damage, or E80",
    "reversal_deny_off": "012 denied for off without flight, damage, or E80",
    "reversal_switch": "physical Trapper stand keeps F/Y gravity, G/X swap, J/B reversal and exclusive selection",
    "reversal_physical_off": "physical parent retains standard A/B/C and no new Trapper authority",
    "wave093": "093 straight warning and narrow real projectile hit one authorized neutral after .30s",
    "wave093_growth": "093 live S2 uses eleven-stud geometry to hit two original neutral targets and exclude the third",
    "wave098": "098 warns three actual directions for one second then splits 10 HP across only two distinct live targets",
    "wave098_wall": "098 late wall limits each actual lane while the remaining legal lanes retain the one budget",
    "wave_independent_off": "separate J OFF cancels pending damage and restores standard even with old G OFF",
    "wave_physical_off": "exact physical predecessor keeps G rune loadout and no new J entry",
    "rune073_stage_budget": "073 actual S1 two neutral hits share one 10 HP base budget, with a third unit excluded",
    "swap_combo": "D performs exchange, hover and landing after one paid opportunity",
}
OFF_CASES = {"footing_physical_off", "ward_physical_off", "reversal_physical_off", "wave_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def _template(fixture, helpers, compose):
    template = helpers["eclipse_sweep"]._template(fixture, compose, helpers["cover_orders"])
    start = "local function ready(label,role)\n"
    peer_selection = " trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')\n"
    compose.need(template.count(start) == template.count(peer_selection) == 1, "FOOTING_WARDS_PEER_FIXTURE")
    return template.replace(start, "local function ready(label,role,peerRole)\n", 1).replace(
        peer_selection,
        " trigger(second,scenes:FindFirstChild('ROLE_'..(peerRole or 'WARRIOR')),'職業選択')\n", 1)


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "FOOTING_WARDS_MANIFEST")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "FOOTING_WARDS_ENGINE")
    helpers = {}
    for label, want in TEMPLATE_PINS.items():
        helper = _module(native / label / "__init__.py", "union22_footing_wards_" + label)
        source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[label + "_template"] = compose.identity(source)
        compose.need(fixtures[label + "_template"]["sha256"] == want, "FOOTING_WARDS_TEMPLATE_PIN:" + label)
        helpers[label] = helper
    template = _template(fixture, helpers, compose)
    engine = native / "mage_water_chain"
    common = _module(engine / "__init__.py", "union22_footing_wards_shared_cases")
    shared_cases = compose.read_file(engine / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "FOOTING_WARDS_SHARED_CASES")
    cases = {}
    for label, want in CASE_PINS.items():
        path = (native if "/" in label else HERE) / label
        raw = compose.read_file(path)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == want, "FOOTING_WARDS_CASE_PIN:" + label)
        fixtures[label] = pin
        cases[label] = raw.decode("utf-8")
    # Keep the exact authored shared Zombie fixture lexical scope and register
    # the new cases after its original helpers, without copying those helpers.
    runes = cases.pop("builder_forms/zombie_rune_cases.luau")
    compose.need(runes.endswith("end\n"), "FOOTING_WARDS_RUNE_CASE_BOUNDARY")
    waves = runes.removesuffix("end\n") + cases.pop("zombie_waves_cases.luau") + "\nend\n"
    corpus = "\n".join((shared_cases.decode("utf-8"), *cases.values(), waves))

    routes = upstream["runtime_routes"]
    sources = profile["sources"]
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "FOOTING_WARDS_PROFILE_STAGE")
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in sources.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    changed = profile[FOLLOWUP]["rows"]
    scope = {FIRST90, *(routes[name] for name in ("Host", "SevenRoleCombat", "InvulRuntime",
              "InteractionGuard", "CastleGuardianRuntime", "SwarmCombat"))}
    compose.need(set(changed) == scope
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] == before[name] for name, row in changed.items())
                 and {name for name in after if after[name] != before[name]} == scope, "FOOTING_WARDS_PROFILE_SCOPE")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.FOOTING_WARDS_OFF / "sources"
    generated = {name: common._program(common._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "FOOTING_WARDS_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "FOOTING_WARDS_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "FOOTING_WARDS_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "FOOTING_WARDS_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "FOOTING_WARDS_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "FOOTING_WARDS_OUTPUT")
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
        compose.need(result.returncode == 0, "FOOTING_WARDS_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
