"""Run the original Mage contact cases on the selected and byte-exact OFF builds."""

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from growth_musou import load_contracts


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1] / "gq470_mage_contact_20261127"
ROLES = ("WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE")
PRIORITY = ((26, 24, False), (26, 23, False), (50, 48, True), (50, 47, True))
TIES = ((24, 2, False), (23, 3, False), (26, 4, False), (46, 5, True), (47, 5, True), (48, 5, True), (49, 5, True))
ARMS = ("OFF", "V3")


def workloads(inputs, arm):
    roles = inputs["role.luau"]
    mage = b"local role='MAGE'\n" + roles.split(b"local shots={}", 1)[0]
    result = {"author": (inputs["cases.luau"], b"CLOSE\t")}
    result.update({role: (f"local role='{role}'\n".encode() + roles, b"REVIEW\t") for role in ROLES})
    for population, count, wall in PRIORITY:
        parameters = f"local population,originalCount,obstructed,preserves={population},{count},{str(wall).lower()},true\n"
        result[f"priority{count}"] = (mage + parameters.encode() + inputs["priority.luau"], b"PRIORITY\t")
    for count, extra, wall in TIES:
        parameters = f"\nlocal variant,oldCount,extraCount,blocked='{arm}',{count},{extra},{str(wall).lower()}\n"
        result[f"old{count}_added{extra}_wall{int(wall)}"] = (mage + parameters.encode() + inputs["ties.luau"], b"TIE\t")
    return result


def collect(root, folder, binary_pin, context, lock, compose, execute=None):
    repair = lock["mage_contact_followup"]
    pins = repair["native_fixtures"]
    compose.need(set(pins) == {"mage_close_v3.patch", "cases.luau", "role.luau", "priority.luau", "ties.luau", "vectors.json"},
                 "MAGE_CONTACT_INPUT_SET")
    inputs = {name: compose.read_file(PACKAGE / name) for name in pins}
    compose.need({name: compose.identity(raw) for name, raw in inputs.items()} == pins, "MAGE_CONTACT_INPUT_PINS")
    vectors = compose.strict_json(inputs["vectors.json"])
    compose.need(set(vectors) == set(ARMS), "MAGE_CONTACT_VECTOR_ARMS")
    compose.need(all(vectors["OFF"][role] == vectors["V3"][role] for role in ROLES if role != "MAGE"),
                 "MAGE_CONTACT_OTHER_ROLES")
    compose.need(len(vectors["OFF"]["author"]) == 25 and len(vectors["V3"]["author"]) == 25
                 and vectors["OFF"]["author"][0].endswith("\t32->32")
                 and vectors["V3"]["author"][0].endswith("\t32->23"), "MAGE_CONTACT_COUNTERFACTUAL")
    adapter, _, _ = load_contracts(lock, compose)
    profile = adapter.load_native_contract()
    records, files = {}, {"receipt.json"}
    snapshots = {}
    with TemporaryDirectory(prefix="union22-mage-") as work:
        scratch = Path(work)
        history = scratch / "frozen"
        orig_pins = adapter.materialize_historical_inputs(profile["historical_inputs"], history)
        _, parts, frozen, historical, _, helpers = adapter.load_inputs(history)
        from run_profile import load_lock, source_snapshot

        geometry = compose.read_file(HERE / "fixtures/guardian_wall_geometry.luau")
        compose.need(compose.identity(geometry) == load_lock()["fixtures"]["guardian_wall_geometry.luau"],
                     "MAGE_CONTACT_EXACT_PHYSICS")
        parts["SERVER_ENGINE"] += b"\n" + geometry
        for arm, selected in (("OFF", root / compose.MAGE_CONTACT_OFF / "sources"),
                              ("V3", root / compose.RELAY_ELIGIBILITY_OFF / "sources")):
            before = arm == "OFF"
            identity = repair["parent_place" if before else "repaired_place"]
            compose.need(compose.identity(compose.read_file(selected.parent / compose.PLACE)) == identity,
                         "MAGE_CONTACT_PLACE")
            expected = {name: row["after"] for name, row in lock["sources"].items()}
            expected.update({name: row["parent"]["after"] for name, row in lock["ground_night_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["return_convert_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["field_loadouts_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["wing_warrior_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["ninja_s4_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["mage_water_chain_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["mage_projectile_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["fractional_hp_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["team_win_rule_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["shorefoam_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["portrait_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["private_touch_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["moguron_followup"]["rows"].items()})
            expected.update({name: row["parent"]["after"] for name, row in lock["relay_eligibility_followup"]["rows"].items()})
            if before:
                expected.update({name: row["parent"]["after"] for name, row in repair["rows"].items()})
            compose.need(source_snapshot(selected) == expected, "MAGE_CONTACT_ACTUAL_SOURCE_SNAPSHOT")
            snapshots[arm] = {route: expected[route] for route in compose.MAGE_CONTACT_SOURCES}
            cases = workloads(inputs, arm)
            compose.need(len(cases) == 19 and set(vectors[arm]) == set(cases), "MAGE_CONTACT_EXACT_CASES")
            for name, (case, prefix) in cases.items():
                body = (b"local patched=false\n" if before else b"local patched=true\n") + case
                program, _, bodies = adapter.server_program(frozen, historical, parts | {"MAGE": body},
                                                              helpers, selected, arm, case_section="MAGE")
                compose.need(len(bodies) == 28, "MAGE_CONTACT_FULL_NATIVE_BODIES")
                key = f"{arm}_{name}"
                stdout, stderr = folder / (key + ".stdout"), folder / (key + ".stderr")
                if execute is not None:
                    script = scratch / (key + ".luau")
                    script.write_bytes(program)
                    run = subprocess.run([str(execute), str(script)], capture_output=True, timeout=90)
                    stdout.write_bytes(run.stdout)
                    stderr.write_bytes(run.stderr)
                    compose.need(run.returncode == 0, "MAGE_CONTACT_NATIVE_EXIT:" + key)
                raw = compose.read_file(stdout)
                tagged = [line.decode() for line in raw.splitlines() if line.startswith(prefix)]
                compose.need(compose.read_file(stderr) == b"" and tagged == vectors[arm][name],
                             "MAGE_CONTACT_EXACT_VECTOR:" + key)
                files.update({stdout.name, stderr.name})
                records[key] = {"program": compose.identity(program), "stdout": compose.identity(raw),
                                "cases": tagged, "full_bodies": len(bodies)}
            compose.need(source_snapshot(selected) == expected, "MAGE_CONTACT_SOURCE_CHANGED")
        adapter.revalidate_historical_inputs(profile["historical_inputs"], history, orig_pins)
    return {"status": "PASS", "binary": binary_pin, "context": context, "source_pins": snapshots,
            "program_count": 38, "source_only": True, "cases": records}, files


def run(root, folder, binary, pin, context, lock, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "MAGE_CONTACT_EXACT_BINARY")
    folder.mkdir()
    row, files = collect(root, folder, pin, context, lock, compose, execute=binary)
    (folder / "receipt.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8", newline="\n")
    compose.need({entry.name for entry in folder.iterdir()} == files
                 and compose.identity(compose.read_file(binary)) == pin, "MAGE_CONTACT_EXECUTION_OUTPUT_SET")
    print("mage_contact: 38 exact ON/OFF full-body programs; close Mage contact, six other roles and 24/48 caps PASS",
          flush=True)
