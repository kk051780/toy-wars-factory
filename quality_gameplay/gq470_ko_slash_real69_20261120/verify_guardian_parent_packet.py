#!/usr/bin/env python3
"""Independently check the exact official Guardian artifact used as the KO PREP parent."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile

PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
PROJECT = "EGGRUMBLE_REAL69.project.json"
ADMISSION = "UNION22_FINAL_ADMISSION.json"
MANIFEST = "UNION22_DELIVERY_MANIFEST.json"
PROFILE = "UNION22_PROFILE_LOCK.json"
SOURCE = "ServerScriptService/EGGRUMBLE_CastleGuardianRuntime.luau"
GUARD = "native_evidence/guardian_target/"
FINAL_PLACE = "ab6c1242a4df6d905b8abaf6662f78b704a15f707e2c6f2a838357f1feb511e5"
ROLLBACKS = {
    "OFF69_GUARDIAN_BEAST_PARENT_ROLLBACK.tar.gz": (71, "guardian_only_beast_parent_inverse_place"),
    "OFF69_BEAST_H72_PARENT_ROLLBACK.tar.gz": (71, "beast_only_h72_parent_inverse_place"),
    "OFF69_BOT_VAULT_HUD_PARENT_ROLLBACK.tar.gz": (71, "bot_only_hud_parent_inverse_place"),
    "OFF69_HUD_CONTEXT_CURRENT_RC_ROLLBACK.tar.gz": (71, "hud_only_current_rc_inverse_place"),
    "OFF69_UNION22_PRIOR_BR_ROLLBACK.tar.gz": (75, "inverse_place"),
}


def require(ok, code):
    if not ok:
        raise ValueError("RED_KO_PARENT_" + code)


def pin(raw):
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def path_name(name):
    route = PurePosixPath(name)
    require(route.parts and not route.is_absolute() and ".." not in route.parts and "\\" not in name
            and str(route) == name, "SAFE_ARCHIVE_ROUTE")
    return route


def load_archive(raw):
    with ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        require(archive.testzip() is None and len(infos) == len({row.filename for row in infos}), "ZIP_CRC")
        data = {}
        for row in infos:
            require(not stat.S_ISLNK(row.external_attr >> 16), "NO_SYMLINK")
            if not row.is_dir():
                name = row.filename
                path_name(name)
                data[name] = archive.read(row)
        return data


def mounted_place(raw):
    source, props = {}, []
    def walk(parent, path):
        for node in parent.findall("Item"):
            fields = node.find("Properties")
            route = (*path, fields.find("*[@name='Name']").text)
            body = fields.find("*[@name='Source']")
            props.append((route, node.attrib["class"], tuple(ET.tostring(v) for v in fields if v.attrib.get("name") != "Source")))
            if body is not None:
                key = "/".join(route)
                require(key not in source, "XML_MOUNTED_UNIQUE")
                source[key] = (body.text or "").encode()
            walk(node, route)
    walk(ET.fromstring(raw), ())
    require(len(source) == 69 and len(props) == 75, "XML_INVENTORY_69_75")
    return source, props


def guard_matrix(data, admission, profile):
    envelope = json.loads(data[GUARD + "GUARDIAN_DIAGNOSTIC_RECEIPT.json"])
    contract = json.loads(data[GUARD + "GUARDIAN_DONOR_CONTRACT.json"])
    official_lock_pin = {"bytes": 39478, "sha256": "f37a9500da30d08fcd1baf30fec340d86733b18fd9c9d34f5e5917f271347dcb"}
    original_root = "quality_gameplay/gq8_guardian_runtime_20261118/"
    inputs = {
        "stealth_target/INPUT_LOCK.json": official_lock_pin,
        "stealth_target/run.py": {"bytes": 18363, "sha256": "fbe55545d5d427a37ae3bf7d30d6f7bc6a427d4d3dd997516970c140a666ef09"},
    }
    inputs.update({"stealth_target/" + name: contract["package_pins"][name]
                   for name in ("apply_stealth_target.py", "case.luau", "fixture_boundary.luau")})
    require(len(contract["existing_pr_files"]) == 12 and all(name.startswith(original_root)
            for name in contract["existing_pr_files"]), "FROZEN_12_ROLE_DEPENDENCY_PATHS")
    inputs.update({name.removeprefix(original_root): value for name, value in contract["existing_pr_files"].items()})
    require(pin(data[GUARD + "GUARDIAN_DIAGNOSTIC_RECEIPT.json"]) == admission["guardian_target_diagnostic"]["receipt"]
            and pin(data[GUARD + "GUARDIAN_DONOR_CONTRACT.json"]) == envelope["contract"] == official_lock_pin
            and len(envelope["donor_inputs"]) == len(inputs) == 17 and envelope["donor_inputs"] == inputs
            and envelope["donor_head"] == "ab284dfd5ecfb45fe3af0537260946a5ed2b26ee",
            "GUARDIAN_FROZEN_MATRIX_RECEIPT")
    unique = {(row["role"], row["mode"]) for row in contract["matrix"]}
    require(len(contract["matrix"]) == len(envelope["results"]) == 40 and len(unique) == 13, "GUARDIAN_MATRIX_SIZE")
    groups, observed, body_count = Counter(), {}, 0
    prior = "baseline_"
    for expected, result in zip(contract["matrix"], envelope["results"], strict=True):
        group, role, mode = (expected[k] for k in ("group", "role", "mode"))
        relative = f"matrix/{group}/{role}/{mode}"
        prefix = GUARD + relative + "/"
        require(result["receipt_path"] == relative + "/receipt.json"
                and result["native_exit_code"] == expected["expected_exit"]
                and result["receipt"] == pin(data[prefix + "receipt.json"]), "GUARDIAN_CASE_PIN")
        files = ("generated.luau", "stdout.log", "stderr.log", "receipt.json")
        observed.update({relative + "/" + name: pin(data[prefix + name]) for name in files})
        receipt = json.loads(data[prefix + "receipt.json"])
        rows = [line.split("\t", 3) for line in data[prefix + "stdout.log"].decode().splitlines() if line.startswith("CASE\t")]
        require([row[1:3] for row in rows] == expected["expected_case_vector"]
                and receipt["generated"] == observed[relative + "/generated.luau"]
                and receipt["stdout"] == observed[relative + "/stdout.log"]
                and receipt["stderr"] == observed[relative + "/stderr.log"], "GUARDIAN_CASE_RAW")
        if expected["expected_exit"] == 1:
            require(expected["baseline_error"].encode() in data[prefix + "stderr.log"], "ACTUAL_EXPECTED_RED")
            groups["expected_baseline_failure"] += 1
        else:
            require(data[prefix + "stderr.log"] == b"", "GUARDIAN_STDERR")
            groups["baseline_control_pass" if group.startswith(prior) else "candidate_pass"] += 1
        spans = receipt["full_source_ranges"].values()
        require(len(spans) == len({row["path"] for row in spans}) == 28, "GUARDIAN_28_SPANS")
        program = data[prefix + "generated.luau"]
        for span in spans:
            path = span["path"]
            start, end = span["byte_start"], span["byte_end_exclusive"]
            body = program[start:end]
            flavor, variant = group.split("_", 1)
            frozen = "input" if flavor == "baseline" else "candidate"
            expected_source = (contract["guardian"]["variants"][variant][frozen]
                               if path == SOURCE else profile["sources"][path]["after"])
            require(0 <= start < end <= len(program) and pin(body) == expected_source
                    and pin(body) == {key: span[key] for key in ("bytes", "sha256")}, "GUARDIAN_ACTUAL_SOURCE_SPAN")
            body_count += 1
    expected_groups = {"candidate_pass": 26, "baseline_control_pass": 6, "expected_baseline_failure": 8}
    require(groups == expected_groups == envelope["counts"] and body_count == 1120
            and observed == envelope["files"]
            and {name.removeprefix(GUARD) for name in data if name.startswith(GUARD)}
            == {*observed, "GUARDIAN_DIAGNOSTIC_RECEIPT.json", "GUARDIAN_DONOR_CONTRACT.json"}, "GUARDIAN_EVIDENCE_EXACT")
    return {"processes": 40, "scenarios": 13, "compiled_body_spans": body_count, "cases": dict(groups), "inputs": 17}


def read_inverse(raw, expected_count, profile, mounted_classes):
    with tarfile.open(fileobj=BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        require(len(members) == expected_count and len({row.name for row in members}) == expected_count
                and all(row.isfile() for row in members), "ROLLBACK_EXACT_MEMBER_SET")
        prefixes = {path_name(row.name).parts[0] for row in members}
        require(len(prefixes) == 1, "ROLLBACK_SCOPE_ROOT")
        data = {row.name.split("/", 1)[1]: archive.extractfile(row).read() for row in members}
    source, instances = mounted_place(data[PLACE])
    require(instances == mounted_classes and data[PROJECT], "ROLLBACK_NO_NON_SOURCE_DRIFT")
    require(len({key for key in data if key.startswith("sources/")}) == 69
            and all(source[v["route"]] == data["sources/" + p] for p, v in profile["sources"].items()),
            "ROLLBACK_ALL_SOURCE_BODIES")
    return {"archive": pin(raw), "place": pin(data[PLACE]), "members": len(data), "project": pin(data[PROJECT])}


def standard_native(data, admission, profile):
    prefix = "native_evidence/"
    aggregate = json.loads(data[prefix + "receipt.json"])
    build = json.loads(data[prefix + "build_receipt.json"])
    require(aggregate["native_process_count"] == admission["native_process_count"] == 13
            and aggregate["native_evidence_file_count"] == admission["native_evidence_file_count"] == 67
            and build["source_commit"] == "f46d879e28302a430029304f7f6a162aed66f103"
            and build["source_tree"] == "2432c996fc9fa73680b5e2cfe172d36114fe3746"
            and build["binary_before_suites"] == build["binary_after_suites"]
            and build["status"] == "PASS_NEW_BUILD"
            and build["execution_context"] == aggregate["execution_context"]
            and build["execution_context"]["official_build_head"] == admission["official_build_head"]
            and aggregate["build_receipt"] == pin(data[prefix + "build_receipt.json"])
            and admission["native_build_receipt"] == aggregate["build_receipt"]
            and all(pin(data[prefix + name]) == expected for name, expected in build["evidence_files"].items()),
            "ARCHIVED_F46_STANDARD_RECEIPTS")
    counts = {"combined_clear_los": 10, "objective_full_clear_los": 7, "beast_target_selection": 12}
    for suite, expected in counts.items():
        path = prefix + suite + "/"
        receipt = json.loads(data[path + "receipt.json"])
        program = data[path + "generated.luau"]
        stdout = data[path + "stdout.log"]
        rows = [line.split("\t", 3) for line in stdout.decode().splitlines() if line.startswith("CASE\t")]
        require(len(rows) == expected and all(len(row) == 4 and row[2] == "PASS" for row in rows)
                and [row[1] for row in rows] == receipt["expected_case_names"]
                and receipt["exit_code"] == 0 and receipt["native"] == build["binary_before_suites"]
                and receipt["generated"] == pin(program) and receipt["stdout"] == pin(stdout)
                and data[path + "stderr.log"] == b"" and receipt["stderr"] == pin(b"")
                and aggregate["suites"][suite] == pin(data[path + "receipt.json"]), "STANDARD_NATIVE_RAW_PASS")
        ranges = receipt["full_body_byte_ranges"]
        require(len(ranges) == 28, "STANDARD_NATIVE_BODY_SET")
        for name, span in ranges.items():
            require(pin(program[span["start"]:span["end"]]) == profile["sources"][name]["after"],
                    "STANDARD_NATIVE_SELECTED_BODY")
    hud = prefix + "selected_hud_layout/"
    bot = prefix + "bot_vault/"
    require(pin(data[hud + "receipt.json"]) == aggregate["selected_hud_layout"]
            and data[hud + "native.stdout.log"] == b"GQ8_REAL63_UI_SQUARE_COLLISIONS_14_CASES_PASS\n"
            and data[hud + "native.stderr.log"] == b"", "STANDARD_NATIVE_HUD14")
    require(pin(data[bot + "receipt.json"]) == aggregate["bot_vault_supplement"], "STANDARD_NATIVE_BOT9")
    bot_receipts = [name for name in data if name.startswith(bot) and name != bot + "receipt.json" and name.endswith("/receipt.json")]
    require(len(bot_receipts) == 9, "STANDARD_BOT_CASE_SET")
    for name in bot_receipts:
        row = json.loads(data[name])
        folder = name.removesuffix("receipt.json")
        require(row["process"]["exit_code"] == 0 and data[folder + "stderr.log"] == b"",
                "STANDARD_BOT_PROCESS_EXIT")
    return {"processes": 13, "native_files": 67, "frozen_standard_cases": counts, "hud_layout": 14, "bot_scenarios": 9}


def audit(archive, expected_head, expected_sha):
    raw_zip = archive.read_bytes()
    require(pin(raw_zip)["sha256"] == expected_sha, "RAW_OFFICIAL_ARCHIVE")
    data = load_archive(raw_zip)
    manifest, admission, profile = (json.loads(data[name]) for name in (MANIFEST, ADMISSION, PROFILE))
    require(len(data) == 326 and manifest["files"] == {k: pin(v) for k, v in data.items() if k != MANIFEST}
            and manifest["manifest_self_excluded"] is True and manifest["current_place"] == PLACE, "ALL_MANIFEST_PAYLOAD")
    require(admission["receipt_provenance"] == "OFFICIAL" and admission["formal_rc_adoption_proven"] is True
            and admission["candidate_build_head"] == admission["official_build_head"] == expected_head
            and admission["status"] == "PASS_SOURCE_AND_NATIVE_ONLY"
            and admission["profile_lock"] == pin(data[PROFILE])
            and admission["current_place"] == pin(data[PLACE]) == {"bytes": 829822, "sha256": FINAL_PLACE}
            and admission["guardian_only_beast_parent_inverse_place"] == {"bytes": 829328, "sha256": "4c35d93b6d8243ecff753ddaef39de0d45d0793085435a21d8f33e4814e78b5a"},
            "ACTUAL_OFFICIAL_HEAD_AND_PLACE")
    for field in ("studio_solo", "studio_two_client", "android_15min"):
        require(admission[field] == "NOT_TESTED", "RUNTIME_SCOPE")
    body, instances = mounted_place(data[PLACE])
    require(all(body[row["route"]] == data["sources/" + path]
                and pin(body[row["route"]]) == row["after"] for path, row in profile["sources"].items()),
            "CURRENT_ALL_MOUNTED_SOURCES")
    require(sum(k.startswith("native_evidence/") for k in data) == 229, "STANDARD_PLUS_GUARDIAN_NATIVE_LAYOUT")
    standard = standard_native(data, admission, profile)
    native = guard_matrix(data, admission, profile)
    inverses = {}
    for name, (count, field) in ROLLBACKS.items():
        result = read_inverse(data[name], count, profile, instances)
        require(result["place"] == admission[field], "KNOWN_EXACT_PARENT_PLACE")
        require(result["project"] == pin(data[PROJECT]), "ROLLBACK_IDENTICAL_PROJECT")
        inverses[name] = result
    return {
        "status": "PASS_EXACT_OFFICIAL_1033_ARCHIVE_INDEPENDENT_REREAD",
        "official_head": expected_head, "zip": pin(raw_zip), "manifest": pin(data[MANIFEST]), "members": len(data),
        "place": pin(data[PLACE]), "script_count": len(body), "instances": len(instances),
        "native_guardian": native, "native_standard": standard, "inverses": inverses,
    }, data


def main():
    parser = ArgumentParser()
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--head", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--unpack", required=True, type=Path)
    args = parser.parse_args()
    result, payload = audit(args.zip, args.head, args.sha256)
    args.unpack.mkdir(exist_ok=False)
    for name, raw in payload.items():
        dest = args.unpack / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    result["verifier"] = pin(Path(__file__).read_bytes())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
