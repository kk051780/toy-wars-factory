"""Exercise the original growth and aura contracts on the composed game."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType


HUD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau"
HERO = "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt.server.luau"
CONTROLLER = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraController.client.luau"
CLIENT = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraClient.luau"
RECEIPT = "receipt.json"


def replace_once(source, old, new, compose):
    compose.need(source.count(old) == 1, "GROWTH_MUSOU_FIXTURE_BOUNDARY")
    return source.replace(old, new, 1)


def load_contracts(lock, compose):
    from verify_union22 import visual_author

    repair = lock["growth_musou_followup"]
    paths = repair["donor_files"]
    growth_path = repair["origins"]["growth"]["package"] + "/native/run_growth.py"
    aura_path = repair["origins"]["aura"]["package"] + "/run_native.py"
    growth = visual_author(growth_path, paths[growth_path], "GROWTH_NATIVE_ORIGINAL")
    aura = visual_author(aura_path, paths[aura_path], "MUSOU_NATIVE_ORIGINAL")
    fixture_name = repair["origins"]["aura"]["package"] + "/native_fixture.luau"
    fixture = compose.read_file(compose.REPO / fixture_name)
    compose.need(compose.identity(fixture) == paths[fixture_name], "MUSOU_NATIVE_FIXTURE_PIN")
    return growth, aura, fixture


def ui_original_adapter(growth, originals, fixed_profile, geometry, compose):
    """Keep the old expectations while using current pins and historical callback bytes."""
    path = Path(growth.__file__)
    raw = compose.read_file(path)
    alterations = (
        (b'baseline == frozen_lock["sources"]', b'baseline == CURRENT_PARENT'),
        (b'set(changed).issubset(mutable)', b'set(changed).issubset(mutable | {AURA_CONTROLLER})'),
        (b'base_raw = runner.read(baseline_root / relative)', b'base_raw = HISTORICAL_CALLBACKS[relative]'),
        (b'    for name, raw in (\n        ("observers", observers_bytes)',
         b'    append(GUARDIAN_GEOMETRY + b"\\n")\n    for name, raw in (\n        ("observers", observers_bytes)'),
    )
    for old, new in alterations:
        raw = replace_once(raw, old, new, compose)
    adapter = ModuleType("union22_growth_current_ui")
    adapter.__file__ = str(path)
    adapter.__dict__.update(CURRENT_PARENT=fixed_profile, HISTORICAL_CALLBACKS=originals,
                            AURA_CONTROLLER=CONTROLLER, GUARDIAN_GEOMETRY=geometry)
    exec(compile(raw, str(path), "exec"), adapter.__dict__)
    return adapter


def relayed_ui_cases(raw, parent_hud, candidate_hud, compose):
    """Account for registrations of the unchanged, already accepted relay block."""
    start = b"-- Existing relay visibility V2 (private Studio)\n"
    end = b'local Players=game:GetService("Players")\n'
    compose.need(parent_hud.count(start) == 1, "GROWTH_MUSOU_RELAY_START")
    begin = parent_hud.index(start)
    relay = parent_hud[begin:parent_hud.index(end, begin)]
    compose.need(candidate_hud.count(relay) == 1, "GROWTH_MUSOU_RELAY_BYTES")
    first = candidate_hud[:candidate_hud.index(relay)].count(b"\n") + 1
    last = first + relay.count(b"\n") - 1
    classifier = f"""local function isAcceptedRelayConnection(entry)
 if entry.source~='HudIntelRuntime' then return false end
 local relative=entry.line-fullSourceRanges.HudIntelRuntime.first+1
 return relative>={first} and relative<={last}
end
""".encode()
    alterations = (
        (b"local function requireHudConnectionContract()",
         classifier + b"local function requireHudConnectionContract()"),
        (b"if entry.source=='HudIntelRuntime'then\n   registered+=1",
         b"if entry.source=='HudIntelRuntime' and not isAcceptedRelayConnection(entry) then\n   registered+=1"),
        (b"if UIAcceptanceEngine.isUI(entry) and entry.owner==RunService then",
         b"if UIAcceptanceEngine.isUI(entry) and entry.owner==RunService and not isAcceptedRelayConnection(entry) then"),
    )
    for old, new in alterations:
        raw = replace_once(raw, old, new, compose)
    return raw


def profile_sources(root, lock, compose):
    final = root / compose.ART_POLISH_OFF / "sources"
    parent = root / compose.GROWTH_MUSOU_OFF / "sources"
    after = compose.trial_sources_before(lock, "mage_projectile_followup") | {
        name: row["parent"]["after"] for name, row in lock["fractional_hp_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in lock["team_win_rule_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in lock["shorefoam_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in lock["portrait_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in lock["private_touch_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in lock["moguron_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in lock["relay_eligibility_followup"]["rows"].items()
    } | {
        name: row["parent"]["after"] for name, row in lock["mage_contact_followup"]["rows"].items()
    } | {name: row["parent"]["after"] for name, row in lock["art_polish_followup"]["rows"].items()}
    before = after | {name: row["parent"]["after"]
                      for name, row in lock["growth_musou_followup"]["rows"].items()}
    return (("ON", final, after), ("OFF", parent, before))


def run(root, output, binary, binary_pin, context, lock, compose):
    growth, aura, aura_fixture = load_contracts(lock, compose)
    established = growth.load_native_contract()
    output.mkdir()
    geometry = compose.read_file(Path(__file__).parent / "fixtures/guardian_wall_geometry.luau")
    scopes = profile_sources(root, lock, compose)
    parent = scopes[1][1]
    before = scopes[1][2]
    with TemporaryDirectory(prefix="union22-growth-fixture-") as directory:
        fixture_root = Path(directory) / "h93"
        historic = growth.materialize_historical_inputs(established["historical_inputs"], fixture_root)
        _, sections, frozen, original, _, helpers = growth.load_inputs(fixture_root)
        from run_profile import load_lock

        observed = load_lock()
        compose.need(compose.identity(geometry) == observed["fixtures"]["guardian_wall_geometry.luau"],
                     "GROWTH_MUSOU_PHYSICS_FIXTURE_PIN")
        sections = sections | {"SERVER_ENGINE": sections["SERVER_ENGINE"] + b"\n" + geometry}
        original_ui = {HERO: compose.read_file(parent / HERO),
                       HUD: compose.read_file(root / compose.RELAY_PRESENTATION_OFF / "sources" / HUD)}
        compose.need(all(compose.identity(raw) == original["sources"][name] for name, raw in original_ui.items()),
                     "GROWTH_MUSOU_HISTORICAL_CALLBACK_BYTES")
        ui = ui_original_adapter(growth, original_ui, before, geometry, compose)
        for label, sources, pins in scopes:
            for case, spec in original["suites"].items():
                name = f"{label}_legacy_{case}"
                inputs = sections | {"LEGACY_CASES": compose.read_file(frozen.HERE / original["case_files"][case])}
                program, ranges, bodies = growth.server_program(frozen, original, inputs, b"", sources,
                                                                  "legacy_" + case, case_section="LEGACY_CASES")
                expected = {"exit": 0, "cases": [[x, "PASS"] for x in spec["expected_case_names"]]}
                growth.run_fixed(name, program, ranges, bodies, binary, binary_pin, sources, expected,
                                 output, frozen, original, pins)
            arm = "positive" if label == "ON" else "negative"
            for variant in established["server_profiles"][label]:
                spec = established["server_variants"][variant]
                program, ranges, bodies = growth.server_program(frozen, original, sections, helpers, sources, variant,
                        spec.get("extra_modules", []), spec.get("extra_engine", []), spec.get("case_section", "SERVER_CASES"))
                growth.run_fixed(f"{label}_server_{variant}", program, ranges, bodies, binary, binary_pin,
                                 sources, spec[arm], output, frozen, original, pins)
            cases = relayed_ui_cases(sections["UI_CASES"], compose.read_file(parent / HUD),
                                     compose.read_file(sources / HUD), compose)
            program, ranges, bodies = ui.ui_program(frozen, original, sections | {"UI_CASES": cases},
                                                     helpers, parent, sources)
            compose.need(CONTROLLER not in bodies, "GROWTH_MUSOU_DISTINCT_UI_SCOPE")
            growth.run_fixed(f"{label}_ui", program, ranges, bodies, binary, binary_pin, sources,
                             established["ui"][arm], output, frozen, original, pins)
        growth.revalidate_historical_inputs(established["historical_inputs"], fixture_root, historic)
    aura_output = output / "aura"
    aura_output.mkdir()
    aura_results = {}
    for label, sources, _ in reversed(scopes):
        name = "candidate" if label == "ON" else "baseline"
        expected = frozenset() if label == "ON" else aura.EXPECTED_BASELINE_FAILURES
        row = aura.execute(name, binary, aura_output, aura_fixture, compose.read_file(sources / CLIENT),
                           compose.read_file(sources / CONTROLLER), sources / CLIENT, sources / CONTROLLER, expected)
        compose.need(row["evidence_matches_expectation"], "MUSOU_AURA_NATIVE_MATRIX")
        aura_results[name] = {"passed": row["pass_count"], "expected_failure": row["fail_count"]}
    evidence = {p.relative_to(output).as_posix(): compose.identity(compose.read_file(p))
                for p in sorted(output.rglob("*")) if p.is_file()}
    compose.need(len(evidence) == 102, "GROWTH_MUSOU_NATIVE_EVIDENCE_COUNT")
    data = {"context": context, "binary": binary_pin, "source_only": True, "growth_runs": 24,
            "aura": aura_results, "files": evidence}
    (output / RECEIPT).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8", newline="\n")
    print("growth_musou: 24 existing growth suites and two existing aura suites matched the exact vectors", flush=True)
