#!/usr/bin/env python3
"""Replay the pinned Guardian donor matrix against the current canonical build."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import run_profile as native

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compose_union22 as compose

DONOR_HEAD = "ab284dfd5ecfb45fe3af0537260946a5ed2b26ee"
DONOR_PACKAGE = "quality_gameplay/gq8_guardian_runtime_20261118"
EVIDENCE_DIRECTORY = "guardian_target"
SUMMARY = "GUARDIAN_DIAGNOSTIC_RECEIPT.json"
CONTRACT = "GUARDIAN_DONOR_CONTRACT.json"
STEALTH_INPUTS = {
    "stealth_target/run.py": (18363, "fbe55545d5d427a37ae3bf7d30d6f7bc6a427d4d3dd997516970c140a666ef09"),
    "stealth_target/INPUT_LOCK.json": (39478, "f37a9500da30d08fcd1baf30fec340d86733b18fd9c9d34f5e5917f271347dcb"),
    "stealth_target/apply_stealth_target.py": (3815, "4e41345d4f22983ccb58b907b0d5cbd49d0e70246a9eb4ad0c56fcb39e4d7b45"),
    "stealth_target/case.luau": (7386, "3b85a61ded6c0585030f7ea515b4b14f4fc9ab055fc03420359fb2a9f906e6d2"),
    "stealth_target/fixture_boundary.luau": (4933, "794d566cc99d73da827877368e47e2f35618cd3d2c080a8fd43745ab781d8e9e"),
}
ROLE_INPUT_NAMES = {
    "role_los": ("INPUT_LOCK.json", "README.md", "apply_existing_repairs.py", "case.luau", "fixture_boundary.luau", "run.py"),
    "role_session": ("INPUT_LOCK.json", "README.md", "apply_role_snapshot.py", "case.luau", "fixture_boundary.luau", "run.py"),
}
COUNTS = {"expected_baseline_failure": 8, "candidate_pass": 26, "baseline_control_pass": 6}


def donor_input_pins(package):
    pins = {relative: {"bytes": size, "sha256": sha} for relative, (size, sha) in STEALTH_INPUTS.items()}
    raw = native.read(native.safe_root(package / "stealth_target/INPUT_LOCK.json"))
    native.require(native.identity(raw) == pins["stealth_target/INPUT_LOCK.json"], "GUARDIAN_PINNED_STEALTH_CONTRACT")
    previous = native.strict_json(raw)["existing_pr_files"]
    expected = {f"{folder}/{name}" for folder, names in ROLE_INPUT_NAMES.items() for name in names}
    native.require(set(previous) == {f"{DONOR_PACKAGE}/{relative}" for relative in expected},
                   "GUARDIAN_EXACT_FROZEN_ROLE_AND_LOS_FILE_SET")
    return pins | {relative: previous[f"{DONOR_PACKAGE}/{relative}"] for relative in sorted(expected)}


def checked_donor(checkout):
    head = subprocess.check_output(["git", "-C", checkout, "rev-parse", "HEAD"],
                                   env=native.clean_environment(), timeout=25).decode().strip()
    native.require(head == DONOR_HEAD, "GUARDIAN_DONOR_HEAD")
    return observe_donor(checkout)


def observe_donor(checkout):
    package = checkout / DONOR_PACKAGE
    expected = donor_input_pins(package)
    pins = {relative: native.identity(native.read(native.safe_root(package / relative))) for relative in expected}
    native.require(pins == expected, "GUARDIAN_DONOR_EXACT_INPUTS")
    return package, pins


def load_hosted_donor(checkout):
    native.require(os.environ.get("GITHUB_REPOSITORY") == compose.REPOSITORY and os.environ.get("GH_TOKEN"),
                   "GUARDIAN_PINNED_API_CONTEXT")
    package = checkout / DONOR_PACKAGE

    def fetch(relative, pin):
        result = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw+json",
                                 f"repos/{compose.REPOSITORY}/contents/{DONOR_PACKAGE}/{relative}?ref={DONOR_HEAD}"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=35, check=False)
        native.require(result.returncode == 0 and native.identity(result.stdout) == pin,
                       "GUARDIAN_PINNED_API_INPUT:" + relative)
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(result.stdout)

    for relative, (size, sha) in STEALTH_INPUTS.items():
        fetch(relative, {"bytes": size, "sha256": sha})
    for relative, pin in donor_input_pins(package).items():
        if relative not in STEALTH_INPUTS:
            fetch(relative, pin)


def source_contract(root, profile, input_lock):
    current = root / "sources"
    previous = root / compose.GUARDIAN_OFF / "sources"
    current_pins, previous_pins = native.source_snapshot(current), native.source_snapshot(previous)
    repair = profile["guardian_followup_repair"]
    item = profile["item_cleanup_followup"]
    vault = profile["empty_vault_followup"]
    castle = profile["castle_release_stock_followup"]
    score = profile["score_relay_followup"]
    relay = profile["relay_presentation_followup"]
    canyon = profile["br_canyon_followup"]
    role = profile["role_readability_followup"]
    field = profile["field_prompt_followup"]
    neutral_names = profile["neutral_names_followup"]
    wall = profile["guardian_wall_followup"]
    combat = profile["combat_visual_followup"]
    growth = profile["growth_musou_followup"]
    art = profile["art_polish_followup"]
    mage = profile["mage_contact_followup"]
    eligibility = profile["relay_eligibility_followup"]
    moguron = profile["moguron_followup"]
    private_touch = profile["private_touch_followup"]
    portrait = profile["portrait_followup"]
    shorefoam = profile["shorefoam_followup"]
    team_win = profile["team_win_rule_followup"]
    hp = profile["fractional_hp_followup"]
    projectiles = profile["mage_projectile_followup"]
    water_chain = profile["mage_water_chain_followup"]
    ninja_s4 = profile["ninja_s4_followup"]
    wing_warrior = profile["wing_warrior_followup"]
    field_loadouts = profile["field_loadouts_followup"]
    return_convert = profile["return_convert_followup"]
    ground_night = profile["ground_night_followup"]
    cover_orders = profile["cover_orders_followup"]
    mage_field_arcs = profile["mage_field_arcs_followup"]
    eclipse_sweep = profile["eclipse_sweep_followup"]
    builder_forms = profile["builder_forms_followup"]
    rel = compose.GUARDIAN_SOURCE
    wall_parent = root / compose.GUARDIAN_WALL_OFF / "sources"
    builder_forms_parent_pins = compose.trial_sources_before(profile, "builder_forms_followup")
    eclipse_sweep_parent_pins = builder_forms_parent_pins | {
        name: row["parent"]["after"] for name, row in eclipse_sweep["rows"].items()}
    mage_field_arcs_parent_pins = eclipse_sweep_parent_pins | {
        name: row["parent"]["after"] for name, row in mage_field_arcs["rows"].items()}
    cover_orders_parent_pins = mage_field_arcs_parent_pins | {
        name: row["parent"]["after"] for name, row in cover_orders["rows"].items()}
    ground_night_parent_pins = cover_orders_parent_pins | {
        name: row["parent"]["after"] for name, row in ground_night["rows"].items()}
    return_convert_parent_pins = ground_night_parent_pins | {
        name: row["parent"]["after"] for name, row in return_convert["rows"].items()}
    field_loadouts_parent_pins = return_convert_parent_pins | {
        name: row["parent"]["after"] for name, row in field_loadouts["rows"].items()}
    wing_warrior_parent_pins = field_loadouts_parent_pins | {
        name: row["parent"]["after"] for name, row in wing_warrior["rows"].items()}
    ninja_s4_parent_pins = wing_warrior_parent_pins | {
        name: row["parent"]["after"] for name, row in ninja_s4["rows"].items()}
    water_chain_parent_pins = ninja_s4_parent_pins | {
        name: row["parent"]["after"] for name, row in water_chain["rows"].items()}
    projectile_parent_pins = water_chain_parent_pins | {
        name: row["parent"]["after"] for name, row in projectiles["rows"].items()}
    hp_parent_pins = projectile_parent_pins | {
        name: row["parent"]["after"] for name, row in hp["rows"].items()}
    team_win_parent_pins = hp_parent_pins | {
        name: row["parent"]["after"] for name, row in team_win["rows"].items()}
    shorefoam_parent_pins = team_win_parent_pins | {
        name: row["parent"]["after"] for name, row in shorefoam["rows"].items()}
    portrait_parent_pins = shorefoam_parent_pins | {
        name: row["parent"]["after"] for name, row in portrait["rows"].items()}
    touch_parent_pins = portrait_parent_pins | {
        name: row["parent"]["after"] for name, row in private_touch["rows"].items()}
    moguron_parent_pins = touch_parent_pins | {name: row["parent"]["after"] for name, row in moguron["rows"].items()}
    eligibility_parent_pins = moguron_parent_pins | {
        name: row["parent"]["after"] for name, row in eligibility["rows"].items()}
    mage_parent_pins = eligibility_parent_pins | {name: row["parent"]["after"] for name, row in mage["rows"].items()}
    art_parent_pins = mage_parent_pins | {name: row["parent"]["after"] for name, row in art["rows"].items()}
    growth_parent_pins = art_parent_pins | {name: row["parent"]["after"] for name, row in growth["rows"].items()}
    combat_parent_pins = growth_parent_pins | {
        name: row["parent"]["after"] for name, row in combat["rows"].items()}
    wall_parent_pins = combat_parent_pins | {rel: wall["rows"][rel]["parent"]["after"]}
    neutral_parent_pins = wall_parent_pins | {
        name: row["parent"]["after"] for name, row in neutral_names["rows"].items()}
    field_parent_pins = neutral_parent_pins | {
        compose.VAULT_SOURCE: field["rows"][compose.VAULT_SOURCE]["parent"]["after"]}
    role_parent_pins = field_parent_pins | {name: row["parent"]["after"] for name, row in role["rows"].items()}
    canyon_parent_pins = role_parent_pins | {name: row["parent"]["after"] for name, row in canyon["rows"].items()}
    relay_parent_pins = canyon_parent_pins | {name: row["parent"]["after"] for name, row in relay["rows"].items()}
    score_parent_pins = relay_parent_pins | {compose.SCORE_SOURCE: score["parent_score_row"]["after"]}
    castle_parent_pins = score_parent_pins | {compose.VAULT_SOURCE: castle["parent_host_row"]["after"]}
    vault_parent_pins = score_parent_pins | {compose.VAULT_SOURCE: vault["parent_host_row"]["after"]}
    item_parent_pin = item["parent_item_row"]["after"]
    item_parent = root / compose.ITEM_OFF / "sources"
    item_parent_pins = vault_parent_pins | {compose.ITEM_SOURCE: item_parent_pin}
    native.require(current_pins == input_lock["sources"] and current_pins[rel] == profile["sources"][rel]["after"]
                   and native.source_snapshot(root / compose.RETURN_CONVERT_OFF / "sources") == return_convert_parent_pins
                   and native.source_snapshot(root / compose.GROUND_NIGHT_OFF / "sources") == ground_night_parent_pins
                   and native.source_snapshot(root / compose.COVER_ORDERS_OFF / "sources") == cover_orders_parent_pins
                   and native.source_snapshot(root / compose.MAGE_FIELD_ARCS_OFF / "sources") == mage_field_arcs_parent_pins
                   and native.source_snapshot(root / compose.ECLIPSE_SWEEP_OFF / "sources") == eclipse_sweep_parent_pins
                   and native.source_snapshot(root / compose.BUILDER_FORMS_OFF / "sources") == builder_forms_parent_pins
                   and native.source_snapshot(root / compose.FIELD_LOADOUTS_OFF / "sources") == field_loadouts_parent_pins
                   and native.source_snapshot(root / compose.WING_WARRIOR_OFF / "sources") == wing_warrior_parent_pins
                   and native.source_snapshot(root / compose.NINJA_S4_OFF / "sources") == ninja_s4_parent_pins
                   and native.source_snapshot(root / compose.MAGE_WATER_CHAIN_OFF / "sources")
                   == water_chain_parent_pins
                   and native.source_snapshot(root / compose.MAGE_PROJECTILES_OFF / "sources")
                   == projectile_parent_pins
                   and native.source_snapshot(root / compose.FRACTIONAL_HP_OFF / "sources") == hp_parent_pins
                   and native.source_snapshot(root / compose.TEAM_WIN_RULE_OFF / "sources") == team_win_parent_pins
                   and native.source_snapshot(root / compose.SHOREFOAM_OFF / "sources") == shorefoam_parent_pins
                   and native.source_snapshot(root / compose.PORTRAIT_OFF / "sources") == portrait_parent_pins
                   and native.source_snapshot(root / compose.PRIVATE_TOUCH_OFF / "sources") == touch_parent_pins
                   and native.source_snapshot(root / compose.MOGURON_OFF / "sources") == moguron_parent_pins
                   and native.source_snapshot(root / compose.RELAY_ELIGIBILITY_OFF / "sources") == eligibility_parent_pins
                   and native.source_snapshot(root / compose.MAGE_CONTACT_OFF / "sources") == mage_parent_pins
                   and native.source_snapshot(root / compose.ART_POLISH_OFF / "sources") == art_parent_pins
                   and native.source_snapshot(root / compose.GROWTH_MUSOU_OFF / "sources") == growth_parent_pins
                   and native.source_snapshot(root / compose.COMBAT_VISUAL_OFF / "sources") == combat_parent_pins
                   and native.source_snapshot(wall_parent) == wall_parent_pins
                   and wall_parent_pins[rel] == repair["repaired_guardian"]
                   and native.source_snapshot(root / compose.NEUTRAL_NAMES_OFF / "sources") == neutral_parent_pins
                   and native.source_snapshot(root / compose.FIELD_PROMPT_OFF / "sources") == field_parent_pins
                   and native.source_snapshot(root / compose.ROLE_READABILITY_OFF / "sources") == role_parent_pins
                   and native.source_snapshot(root / compose.BR_CANYON_OFF / "sources") == canyon_parent_pins
                   and native.source_snapshot(root / compose.RELAY_PRESENTATION_OFF / "sources") == relay_parent_pins
                   and native.source_snapshot(root / compose.SCORE_OFF / "sources") == score_parent_pins
                   and native.source_snapshot(root / compose.CASTLE_OFF / "sources") == castle_parent_pins
                   and native.source_snapshot(root / compose.VAULT_OFF / "sources") == vault_parent_pins
                   and native.source_snapshot(item_parent) == item_parent_pins
                   and previous_pins == (item_parent_pins | {rel: repair["parent_guardian"]}),
                   "GUARDIAN_SOURCE69_CONTEXT")
    donor_candidate = native.read(wall_parent / rel)
    bodies = {path: native.read(previous / path) for path in previous_pins}
    native.require({path: native.identity(body) for path, body in bodies.items()} == previous_pins
                   and native.identity(donor_candidate) == repair["repaired_guardian"], "GUARDIAN_SOURCE_READ_DRIFT")
    native.require(native.identity(native.read(root / compose.PLACE)) == profile["final_place"]
                   == builder_forms["repaired_place"]
                   and native.identity(native.read(root / compose.BUILDER_FORMS_OFF / compose.PLACE))
                   == builder_forms["parent_place"] == eclipse_sweep["repaired_place"]
                   and native.identity(native.read(root / compose.ECLIPSE_SWEEP_OFF / compose.PLACE))
                   == eclipse_sweep["parent_place"] == mage_field_arcs["repaired_place"]
                   and native.identity(native.read(root / compose.MAGE_FIELD_ARCS_OFF / compose.PLACE))
                   == mage_field_arcs["parent_place"] == cover_orders["repaired_place"]
                   and native.identity(native.read(root / compose.COVER_ORDERS_OFF / compose.PLACE))
                   == cover_orders["parent_place"] == ground_night["repaired_place"]
                   and native.identity(native.read(root / compose.GROUND_NIGHT_OFF / compose.PLACE))
                   == ground_night["parent_place"] == return_convert["repaired_place"]
                   and native.identity(native.read(root / compose.RETURN_CONVERT_OFF / compose.PLACE))
                   == return_convert["parent_place"] == field_loadouts["repaired_place"]
                   and native.identity(native.read(root / compose.FIELD_LOADOUTS_OFF / compose.PLACE))
                   == field_loadouts["parent_place"] == wing_warrior["repaired_place"]
                   and native.identity(native.read(root / compose.WING_WARRIOR_OFF / compose.PLACE))
                   == wing_warrior["parent_place"] == ninja_s4["repaired_place"]
                   and native.identity(native.read(root / compose.NINJA_S4_OFF / compose.PLACE))
                   == ninja_s4["parent_place"] == water_chain["repaired_place"]
                   and native.identity(native.read(root / compose.MAGE_WATER_CHAIN_OFF / compose.PLACE))
                   == water_chain["parent_place"] == projectiles["repaired_place"]
                   and native.identity(native.read(root / compose.MAGE_PROJECTILES_OFF / compose.PLACE))
                   == projectiles["parent_place"] == hp["repaired_place"]
                   and native.identity(native.read(root / compose.FRACTIONAL_HP_OFF / compose.PLACE))
                   == hp["parent_place"] == team_win["repaired_place"]
                   and native.identity(native.read(root / compose.TEAM_WIN_RULE_OFF / compose.PLACE))
                   == team_win["parent_place"] == shorefoam["repaired_place"]
                   and native.identity(native.read(root / compose.SHOREFOAM_OFF / compose.PLACE))
                   == shorefoam["parent_place"] == portrait["repaired_place"]
                   and native.identity(native.read(root / compose.PORTRAIT_OFF / compose.PLACE))
                   == portrait["parent_place"] == private_touch["repaired_place"]
                   and native.identity(native.read(root / compose.PRIVATE_TOUCH_OFF / compose.PLACE))
                   == private_touch["parent_place"] == moguron["repaired_place"]
                   and native.identity(native.read(root / compose.MOGURON_OFF / compose.PLACE))
                   == moguron["parent_place"] == eligibility["repaired_place"]
                   and native.identity(native.read(root / compose.RELAY_ELIGIBILITY_OFF / compose.PLACE))
                   == eligibility["parent_place"] == mage["repaired_place"]
                   and native.identity(native.read(root / compose.MAGE_CONTACT_OFF / compose.PLACE))
                   == mage["parent_place"] == art["repaired_place"]
                   and native.identity(native.read(root / compose.ART_POLISH_OFF / compose.PLACE))
                   == art["parent_place"] == growth["repaired_place"]
                   and native.identity(native.read(root / compose.GROWTH_MUSOU_OFF / compose.PLACE))
                   == growth["parent_place"] == combat["repaired_place"]
                   and native.identity(native.read(root / compose.COMBAT_VISUAL_OFF / compose.PLACE))
                   == combat["parent_place"] == wall["repaired_place"]
                   and native.identity(native.read(root / compose.GUARDIAN_WALL_OFF / compose.PLACE))
                   == wall["parent_place"] == neutral_names["repaired_place"]
                   and native.identity(native.read(root / compose.NEUTRAL_NAMES_OFF / compose.PLACE))
                   == neutral_names["parent_place"] == field["repaired_place"]
                   and native.identity(native.read(root / compose.FIELD_PROMPT_OFF / compose.PLACE))
                   == field["parent_place"] == role["repaired_place"]
                   and native.identity(native.read(root / compose.ROLE_READABILITY_OFF / compose.PLACE))
                   == role["parent_place"] == canyon["repaired_place"]
                   and native.identity(native.read(root / compose.BR_CANYON_OFF / compose.PLACE))
                   == canyon["parent_place"] == relay["repaired_place"]
                   and native.identity(native.read(root / compose.RELAY_PRESENTATION_OFF / compose.PLACE))
                   == relay["parent_place"] == score["repaired_place"]
                   and native.identity(native.read(root / compose.SCORE_OFF / compose.PLACE))
                   == score["parent_place"] == castle["repaired_place"]
                   and native.identity(native.read(root / compose.CASTLE_OFF / compose.PLACE))
                   == castle["parent_place"] == vault["repaired_place"]
                   and native.identity(native.read(root / compose.VAULT_OFF / compose.PLACE))
                   == vault["parent_place"] == item["repaired_place"]
                   and native.identity(native.read(root / compose.ITEM_OFF / compose.PLACE))
                   == item["parent_place"] == repair["repaired_place"]
                   and native.identity(native.read(root / compose.GUARDIAN_OFF / compose.PLACE))
                   == repair["parent_place"], "GUARDIAN_PLACE_PAIR")
    return current, previous, current_pins, previous_pins, bodies, donor_candidate


def run(root, native_output, checkout, output, head, donor=checked_donor):
    root, native_output, checkout, output = map(native.safe_root, (root, native_output, checkout, output))
    native.require(not output.exists()
                   and all(not output.is_relative_to(source) for source in (root, checkout))
                   and (not output.is_relative_to(native_output) or output == native_output / EVIDENCE_DIRECTORY),
                   "GUARDIAN_NEW_OUTPUT_REQUIRED")
    profile, input_lock = compose.load_lock(), native.load_lock()
    current, previous, current_pins, previous_pins, bodies, candidate = source_contract(root, profile, input_lock)
    receipt = native.read(root / compose.RECEIPT)
    core_raw = native.read(root / "CORE_BUILD_REPORT.json")
    aggregate = native.strict_json(native.read(native_output / "receipt.json"))
    built_raw = native.read(native_output / "build_receipt.json")
    built = native.strict_json(built_raw)
    context = built["execution_context"]
    compose.validate_context(context, native.strict_json(receipt))
    native.require(context["build_head"] == head == native.strict_json(core_raw)["context"]["build_head"]
                   and aggregate["execution_context"] == context
                   and aggregate["build_receipt"] == native.identity(built_raw)
                   and built["source_receipt"] == native.identity(receipt)
                   and built["source_commit"] == input_lock["toolchain"]["source_commit"],
                   "GUARDIAN_SAME_HEAD_F46_AND_SOURCE_RECEIPT")
    binary = native.safe_root(built["binary_path"])
    binary_pin = native.identity(native.read(binary))
    native.require(binary_pin == built["binary_before_suites"] == built["binary_after_suites"],
                   "GUARDIAN_SAME_F46_BINARY")
    native.fixture_snapshot(input_lock)
    package, pins = donor(checkout)
    stealth = _donor_module("union22_guardian_donor_stealth", package / "stealth_target/run.py")
    role_los = _donor_module("union22_guardian_donor_role_los", package / "role_los/apply_existing_repairs.py")
    filter_target = _donor_module("union22_guardian_donor_filter", package / "stealth_target/apply_stealth_target.py")
    lock_raw = native.read(package / "stealth_target/INPUT_LOCK.json")
    native.require(native.identity(lock_raw)["sha256"] == stealth.INPUT_LOCK_SHA256, "GUARDIAN_DONOR_LOCK")
    lock = native.strict_json(lock_raw)
    baseline = bodies[compose.GUARDIAN_SOURCE]
    role = role_los.transform(baseline, "baseline", "combined")
    variants = {"baseline_h93": baseline, "baseline_pr796": role,
                "candidate_h93": filter_target.apply(baseline, "h93"),
                "candidate_pr796": filter_target.apply(role, "pr796")}
    native.require(variants["candidate_pr796"] == candidate
                   and filter_target.apply(candidate, "pr796", inverse=True) == role
                   and role_los.transform(role, "combined", "baseline") == baseline,
                   "GUARDIAN_ACTUAL_COMBINED_BODY_AND_INVERSE")
    output.mkdir(parents=True)
    results = []
    for case in lock["matrix"]:
        key = (case["group"], case["role"], case["mode"])
        program, ranges = stealth.assemble(bodies, HERE, checkout, lock, variants[key[0]], *key[1:])
        dest = output.joinpath("matrix", *key)
        row = stealth.execute(binary, native.clean_environment(), program, ranges, dest, case)
        row["receipt_path"] = (dest / "receipt.json").relative_to(output).as_posix()
        results.append(row)
    counts = Counter("expected_baseline_failure" if row["expected_baseline_red"]
                     else "candidate_pass" if row["group"].startswith("candidate")
                     else "baseline_control_pass" for row in results)
    native.require(counts == COUNTS
                   and len({(row["role"], row["mode"]) for row in results}) == 13, "GUARDIAN_MATRIX_40_EXACT")
    native.fixture_snapshot(input_lock)
    native.require(donor(checkout)[1] == pins
                   and native.source_snapshot(current) == current_pins
                   and native.source_snapshot(previous) == previous_pins
                   and native.read(root / compose.RECEIPT) == receipt and native.read(root / "CORE_BUILD_REPORT.json") == core_raw
                   and native.read(native_output / "build_receipt.json") == built_raw
                   and native.identity(native.read(binary)) == binary_pin, "GUARDIAN_INPUT_DRIFT_AFTER_MATRIX")
    source_contract(root, profile, input_lock)
    evidence = native.evidence_snapshot(output)
    native.require(len(evidence) == 160, "GUARDIAN_MATRIX_EVIDENCE_160")
    (output / CONTRACT).write_bytes(lock_raw)
    native.write_json(output / SUMMARY,
                      {"schema": "UNION22_GUARDIAN_DONOR_MATRIX_V1", "status": "SOURCE_NATIVE_PASS",
                       "context": context, "donor_head": DONOR_HEAD, "donor_inputs": pins,
                       "binary": binary_pin, "source_receipt": native.identity(receipt),
                       "native_build_receipt": native.identity(built_raw),
                       "place": profile["guardian_followup_repair"]["repaired_place"],
                       "immediate_inverse_place": profile["guardian_followup_repair"]["parent_place"],
                       "source_pin": native.identity(candidate), "unchanged_other_sources": 68,
                       "unique_scenarios": 13, "native_executions": len(results),
                       "counts": dict(counts), "results": results, "files": evidence,
                       "contract": native.identity(lock_raw),
                       "studio": "NOT_TESTED", "gameplay_delivery_status_inferred": False})
    print("UNION22_GUARDIAN_DONOR_MATRIX_40_EXACT_26_PASS_8_EXPECTED_RED_6_CONTROLS")
    return native.identity(native.read(output / SUMMARY))


def run_from_profile(root, native_output, context):
    output = native_output / EVIDENCE_DIRECTORY
    if context["kind"] == "LOCAL_SOURCE_REVIEW":
        local = os.environ.get("UNION22_GUARDIAN_DONOR_CHECKOUT")
        return run(root, native_output, Path(local), output, context["build_head"]) if local else None
    with TemporaryDirectory(prefix="union22-guardian-donor-") as temp:
        checkout = Path(temp)
        load_hosted_donor(checkout)
        return run(root, native_output, checkout, output, context["build_head"], donor=observe_donor)


def _donor_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    native.require(spec is not None and spec.loader is not None, "GUARDIAN_DONOR_MODULE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("root", "native-output", "donor-checkout", "out"):
        parser.add_argument("--" + field, required=True, type=Path)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    run(args.root, args.native_output, args.donor_checkout, args.out, args.head)
