#!/usr/bin/env python3
"""Prove real Real55 original unchanged except one Host; patch is guarded.
This is source/authority validation, NOT a Roblox Studio video acceptance test.
"""
from pathlib import Path
import argparse,hashlib,sys,json
from copy import deepcopy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from compose_real56 import flatten,HOST,CLIENT,patch_host

def check(parent,candidate):
    _,original=flatten(parent)
    _,built=flatten(candidate)
    assert len(original)==55 and len(built)==56
    assert set(built)-set(original)=={CLIENT}
    assert sum(original[k].read_bytes()!=built[k].read_bytes() for k in original)==1
    for route in original:
        if route!=HOST:
            assert original[route].read_bytes()==built[route].read_bytes(),("RED_UNEXPECTED_ORIGINAL_CHANGE",route)
    src=original[HOST].read_text()
    compiled=built[HOST].read_text()
    assert patch_host(src)==compiled,"RED_COMPOSITION_NOT_REAL_SOURCE"
    for symbol in ('gq8ViralEpoch','EGGRUMBLE_ViralSeq','EGG_STEAL','EGG_DELIVER',
                   'CASTLE_DANGER','COMEBACK','VICTORY'):
        assert symbol in compiled,"RED_EVENT_MISSING_"+symbol
    assert compiled.count('gq8CaptureHint(')==5,"RED_UNKNOWN_EXTRA_HINT" # function + four event hooks
    assert len(compiled)>len(src) and compiled.count('local function startSession(mode:string)')==1
    # All accepted theft/delivery cues occur after a protected successful rules mutation.
    assert compiled.index('if ok and taker and (taker.heldEggs or 0)>before')<compiled.index('gq8CaptureHint(p,session,"EGG_STEAL")')
    assert compiled.index('if (c.depositedEggs or 0)>before then')<compiled.index('gq8CaptureHint(p,session,"EGG_DELIVER")')
    client=built[CLIENT].read_text()
    for check in ('local armed = false','StartVideoCaptureAsync','PromptSaveCapturesToGallery',
                  'StopVideoCapture','EGGRUMBLE_ViralSeq','RunService:IsStudio()'):
        assert check in client, "RED_CLIENT_CONSENT_"+check
    for bad in ('FireServer(', 'RemoteEvent', 'DataStoreService', 'MarketplaceService',
                'HttpService', 'TeleportService', 'UploadCaptureAsync(', 'PromptShareCapture(',
                'https://','http://'):
        assert bad not in client,"RED_USER_DATA_OR_GAME_AUTHORITY_"+bad
    for bad in ('new RemoteEvent','FireServer(','DataStoreService','MarketplaceService'):
        assert bad not in compiled[len(src):],"RED_NEW_GAME_AUTHORITY_"+bad
    # Fail closed if another Chat modified an owned anchor.
    mutants=[
        src.replace('local function startSession(mode:string)','local function startSession_v2(mode:string)',1),
        src.replace('session.world.Name=mode.."_Arena";session.world.Parent=folder','-- removed',1),
        src.replace('if c.alive and c.heldEggs>0 then','if c.alive and false then',1),
        src.replace('pcall(function() Rules.takeEggs(session.rules,tostring(p.UserId),1,entry.id) end)','-- removed',1),
        src.replace('if session.rules.winner~=nil then','if session.rules.winner==nil then',1),
    ]
    for i,bad in enumerate(mutants):
        assert bad!=src,"RED_UNAVAILABLE_MUTATION_"+str(i)
        try:patch_host(bad)
        except ValueError:pass
        else:raise AssertionError("RED_ACCEPTED_CHANGED_OWNER_ANCHOR_"+str(i))
    receipt=json.loads((candidate.parent/'GQ8_VIRAL56_RECEIPT.json').read_text())
    assert receipt['candidate']==56 and receipt['unchanged_original_source_count']==54
    assert receipt['new_remote_owners']==0 and receipt['new_store_owners']==0
    for record in receipt['sources']:
        route=tuple(record['route'].split('/'))
        b=built[route].read_bytes()
        assert hashlib.sha256(b).hexdigest()==record['sha256'] and len(b)==record['bytes']
    print('GQ8_VIRAL_REAL56_TRUE_EGG_CASTLE_WIN_54_SOURCE_EXACT_AND_MUTANT_PASS')

# Current69 is opt-in; the original legacy prefix and entry below are preserved.
import os
import re
import shutil
import stat
import subprocess
import zipfile
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from compose_real56 import (
    current69_load_lock, current69_require, current69_pin,
    current69_validate_tree, current69_inverse, current69_verify_api,
    current69_extract_archive, current69_source_binding, current69_json,
)

CURRENT69_TEST_HERE = Path(__file__).resolve().parent
CURRENT69_BODY_MARKER = b"-- __EXACT_FULL_CLIENT_BODY__\n"
CURRENT69_CONTRACT_ORDER = (
    "epoch_original", "epoch_v3", "completion_v2", "completion_v3",
)


def current69_test_write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with Path(path).open("xb") as stream:
        current69_require(stream.write(raw) == len(raw), "TEST_RECEIPT_SHORT_WRITE")


def current69_test_file(path):
    return {"path": str(Path(path).resolve()), **current69_pin(Path(path))}


def current69_test_expected_pin(value):
    return {key: value[key] for key in ("bytes", "sha256")}


def current69_test_binding(lock, source_head):
    binding = current69_source_binding(lock, source_head)
    hosted = os.environ.get("GITHUB_ACTIONS") == "true"
    if hosted:
        event = os.environ.get("GITHUB_EVENT_NAME")
        current69_require(event in ("push", "pull_request", "workflow_dispatch"), "TEST_UNEXPECTED_ACTIONS_EVENT")
        if event == "pull_request":
            event_path = Path(os.environ["GITHUB_EVENT_PATH"])
            payload = current69_json(event_path.read_bytes())
            event_head = payload["pull_request"]["head"]["sha"]
        else:
            event_head = os.environ.get("GITHUB_SHA")
        current69_require(event_head == source_head, "TEST_ACTIONS_ACTUAL_SOURCE_HEAD")
    binding.update({
        "hosted_github_actions_execution": hosted,
        "hosted_ci_completed_or_approved": False,
        "local_execution_label": None if hosted else "NOT_HOSTED_CI",
        "remote_source_head_verified_by_this_test": False,
    })
    return binding


def current69_test_assets(lock, root=CURRENT69_TEST_HERE):
    root = Path(root)
    native = root / "native"
    current69_require(native.is_dir() and not native.is_symlink(), "ASSET_DIRECTORY_REQUIRED")
    observed = set()
    for path in native.rglob("*"):
        current69_require(not path.is_symlink(), "ASSET_SYMLINK_REJECTED")
        if path.is_file():
            observed.add(path.relative_to(root).as_posix())
    current69_require(len(lock["assets"]) == 5 and observed == set(lock["assets"]), "ASSET_PATH_MEMBERSHIP")
    assets = {}
    for rel, expected in lock["assets"].items():
        raw = (root / rel).read_bytes()
        current69_require(current69_pin(raw) == current69_test_expected_pin(expected), "ASSET_BYTES_DRIFT_" + rel)
        raw.decode("utf-8", errors="strict")
        assets[rel] = raw
    cases = assets["native/epoch_cases.luau"]
    first = b'do\n    local name="normal_15s_save"\n'
    following = b'do\n    local name="epoch_pending_success"\n'
    current69_require(cases.count(first) == cases.count(following) == 1, "NORMAL_CONTROL_ANCHORS")
    normal = cases[cases.index(first):cases.index(following)].rstrip(b"\n") + b"\n"
    current69_require(current69_pin(normal) == lock["normal_shared_control"], "NORMAL_CONTROL_BYTES")
    current69_require(lock["shared_normal_observations"] == 6, "NORMAL_OVERLAP_COUNT")
    return assets, normal


def current69_test_bundle(bundle, lock, binding):
    bundle = Path(bundle)
    current69_require(bundle.is_dir() and not bundle.is_symlink(), "TEST_BUNDLE_DIRECTORY")
    trees = {
        "input": current69_validate_tree(bundle / "input", lock, "original"),
        "ON": current69_validate_tree(bundle / "ON", lock, "candidate"),
        "OFF": current69_validate_tree(bundle / "OFF", lock, "original"),
    }
    client = trees["ON"][CLIENT].read_bytes()
    original = current69_inverse(client, lock)
    v2 = current69_inverse(client, lock, v2_only=True)
    current69_require(trees["input"][CLIENT].read_bytes() == original == trees["OFF"][CLIENT].read_bytes(), "TEST_REAL_INVERSE_OFF")
    changed = []
    for route in trees["input"]:
        parent = trees["input"][route].read_bytes()
        current69_require(parent == trees["OFF"][route].read_bytes(), "TEST_OFF_SOURCE_DRIFT_" + "/".join(route))
        if parent != trees["ON"][route].read_bytes():
            changed.append(route)
    current69_require(changed == [CLIENT], "TEST_EXACT_ONE_SOURCE_CHANGE")
    expected_output_files = {row["path"] for row in lock["sources"]} | {lock["input"]["project"]["path"]}
    for label in ("ON", "OFF"):
        files = set()
        for path in (bundle / label).rglob("*"):
            current69_require(not path.is_symlink(), "TEST_OUTPUT_SYMLINK")
            if path.is_file():
                files.add(path.relative_to(bundle / label).as_posix())
        current69_require(files == expected_output_files, "TEST_OUTPUT_FILE_MEMBERSHIP_" + label)
    for field in ("place", "legacy_intake_receipt"):
        spec = lock["input"][field]
        current69_require(current69_pin(bundle / "input" / spec["path"]) == current69_test_expected_pin(spec), "TEST_OFFICIAL_INPUT_" + field)
    archive = bundle / "input_archive.zip"
    current69_require(archive.is_file() and not archive.is_symlink(), "TEST_ARCHIVE_REQUIRED")
    current69_require(current69_pin(archive) == current69_test_expected_pin(lock["archive"]), "TEST_ARCHIVE_PIN")
    api_paths = [bundle / "input_api" / name for name in ("formal-ref.json", "official-run.json", "official-artifact.json")]
    api = current69_verify_api(lock, *api_paths)
    receipt_path = bundle / "COMPOSITION_RECEIPT.json"
    receipt = current69_json(receipt_path.read_bytes())
    current69_require(receipt["schema"] == "GQ8_CAPTURE_CURRENT69_COMPOSITION_V1", "TEST_COMPOSITION_SCHEMA")
    for key in ("source_head", "source_tree", "source_context", "source_manifest"):
        current69_require(receipt[key] == binding[key], "TEST_COMPOSITION_" + key)
    current69_require(receipt["base_rc"] == receipt["official_input_head"] == lock["base_rc"], "TEST_INPUT_SOURCE_HEAD_SEPARATION")
    current69_require(receipt["canonical_build"] is False and receipt["formal_rc_adoption_proven"] is False
                      and receipt["provider_authentication_proven"] is False, "TEST_COMPOSITION_NOT_ADOPTION")
    current69_require(receipt["input_api"] == api and receipt["input_lock"] == current69_pin(CURRENT69_TEST_HERE / "INPUT_LOCK.json"), "TEST_COMPOSITION_INPUT_BINDING")
    current69_require(receipt["input_archive"] == {"path": "input_archive.zip", **current69_pin(archive)}, "TEST_COMPOSITION_ARCHIVE_BINDING")
    current69_require(receipt["source_count"] == 69 and receipt["unchanged_sources"] == 68
                      and receipt["changed_sources"] == ["/".join(CLIENT)], "TEST_COMPOSITION_COUNTS")
    current69_require(receipt["candidate"] == current69_pin(client)
                      and receipt["inverse_original"] == current69_pin(original), "TEST_COMPOSITION_BODY_PINS")
    return trees, {"epoch_original": original, "epoch_v3": client, "completion_v2": v2, "completion_v3": client}


def current69_test_execute(command, out, cwd=None, timeout=60):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    command = [str(part) for part in command]
    started = datetime.now(timezone.utc).isoformat()
    current69_test_write(out / "COMMAND.json", {"command": command, "cwd": str(cwd) if cwd else None, "started_at": started})
    try:
        process = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)
        stdout, stderr, code, timed_out = process.stdout, process.stderr, process.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b"", exc.stderr or b"", None, True
    (out / "stdout.log").write_bytes(stdout)
    (out / "stderr.log").write_bytes(stderr)
    result = {"command": command, "cwd": str(cwd) if cwd else None,
              "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
              "exit_code": code, "timed_out": timed_out,
              "stdout": current69_test_file(out / "stdout.log"), "stderr": current69_test_file(out / "stderr.log")}
    current69_test_write(out / "COMMAND_RESULT.json", result)
    return result, stdout, stderr


def current69_test_program(contract, source, assets, normal):
    if contract["suite"] == "epoch27":
        fixture = assets["native/full_client_fixture.luau"]
        tail = b"\n" + assets["native/epoch_cases.luau"]
        executions = 6
    else:
        current69_require(contract["suite"] == "completion32", "TEST_UNKNOWN_NATIVE_SUITE")
        fixture = assets["native/full_client_fixture_extended.luau"]
        tail = (b"\n" + normal + b"\n" + assets["native/completion_cases.luau"]
                + b"\n" + assets["native/completion_additional_cases.luau"])
        executions = 5
    current69_require(fixture.count(CURRENT69_BODY_MARKER) == 1, "TEST_FULL_BODY_MARKER")
    prefix, suffix = fixture.split(CURRENT69_BODY_MARKER)
    suffix += tail
    skeleton = prefix + CURRENT69_BODY_MARKER + suffix
    current69_require(current69_pin(skeleton)["sha256"] == contract["skeleton_sha256"], "TEST_SKELETON_BYTES")
    current69_require(current69_pin(source) == contract["source"], "TEST_NATIVE_SOURCE_PIN")
    program = prefix + source + suffix
    start, end = len(prefix), len(prefix) + len(source)
    current69_require(program[start:end] == source and program.count(source) == 1, "TEST_FULL_SOURCE_ONCE")
    body = {"full_bodies": 1, "runtime_executions": executions, "occurrences": 1,
            "byte_start_zero_based": start, "byte_end_exclusive": end,
            "line_start_one_based": prefix.count(b"\n") + 1,
            "line_end_inclusive": prefix.count(b"\n") + len(source.splitlines()), "byte_exact": True,
            "source": current69_pin(source), "skeleton_sha256": current69_pin(skeleton)["sha256"]}
    return program, body


def current69_test_observations(contract, stdout, stderr):
    observations, finishes = [], []
    for line in stdout.decode("utf-8", errors="strict").splitlines():
        if line.startswith("OBS\t"):
            fields = line.split("\t", 4)
            current69_require(len(fields) == 5 and fields[3] in ("PASS", "RED"), "TEST_MALFORMED_OBSERVATION")
            observations.append({"case": fields[1], "name": fields[2], "outcome": fields[3], "detail": fields[4]})
        if "\tFINISH\t" in line:
            finishes.append(line)
    triples = [[row["case"], row["name"], row["outcome"]] for row in observations]
    counts = {"total": len(observations), "pass": sum(row["outcome"] == "PASS" for row in observations),
              "red": sum(row["outcome"] == "RED" for row in observations)}
    current69_require(triples == contract["expected_observations"], "TEST_ORDERED_OBSERVATION_CONTRACT")
    current69_require(counts == contract["counts"], "TEST_OBSERVATION_COUNTS")
    current69_require(finishes == contract["expected_finish_records"], "TEST_EXACT_FINISH_RECORDS")
    current69_require(all("pending=0" in row and "activeCue=-1" in row for row in finishes), "TEST_FINISH_CLEANUP")
    current69_require(current69_pin(stdout)["sha256"] == contract["stdout_sha256"], "TEST_RAW_STDOUT_CONTRACT")
    current69_require(current69_pin(stderr)["sha256"] == contract["stderr_sha256"] and stderr == b"", "TEST_RAW_STDERR_CONTRACT")
    return {"observations": observations, "counts": counts, "finish_records": finishes,
            "case_names_in_order": list(dict.fromkeys(row["case"] for row in observations))}


def current69_test_xml(path, expected, lock):
    root = ET.fromstring(Path(path).read_bytes())
    current69_require(root.tag == "roblox", "TEST_XML_ROOT")
    rows, instance_count = {}, 0
    source_classes = {"Script", "LocalScript", "ModuleScript"}
    classes = {tuple(row["route"].split("/")): row["class"] for row in lock["sources"]}

    def visit(item, parent):
        nonlocal instance_count
        instance_count += 1
        properties = item.findall("Properties")
        current69_require(len(properties) == 1, "TEST_XML_PROPERTIES")
        props = properties[0]
        names = [node for node in props if node.get("name") == "Name"]
        current69_require(len(names) == 1 and bool(names[0].text), "TEST_XML_INSTANCE_NAME")
        route = parent + (names[0].text,)
        sources = [node for node in props if node.get("name") == "Source"]
        kind = item.get("class")
        if kind in source_classes:
            current69_require(len(sources) == 1 and route in expected and route not in rows, "TEST_XML_SOURCE_MEMBERSHIP")
            body = (sources[0].text or "").encode("utf-8")
            current69_require(kind == classes[route] and body == expected[route].read_bytes(), "TEST_XML_SOURCE_CLASS_BYTES_" + "/".join(route))
            rows[route] = {"route": "/".join(route), "class": kind, **current69_pin(body)}
            sources[0].text = ""
        else:
            current69_require(not sources, "TEST_XML_SOURCE_ON_NON_SCRIPT")
        for child in item.findall("Item"):
            visit(child, route)

    for item in root.findall("Item"):
        visit(item, ())
    current69_require(set(rows) == set(expected) and len(rows) == lock["source_count"] == 69, "TEST_XML_SOURCE_COUNT")
    current69_require(instance_count == lock["instance_count"] == 75, "TEST_XML_INSTANCE_COUNT")
    non_source = ET.tostring(root, encoding="utf-8")
    return {"place": current69_test_file(path), "source_count": len(rows), "instance_count": instance_count,
            "sources": [rows[key] for key in sorted(rows)], "non_source_xml": current69_pin(non_source)}, non_source


def current69_test_negatives(bundle, out, source_head):
    """Run the same byte/path guards under normal Python and -O, without a VM.

    Only synthetic archive *measurements* are rebound for structural ZIP cases;
    the immutable on-disk lock and its hardcoded hash guard remain unchanged.
    """
    bundle, out = Path(bundle).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    lock = current69_load_lock()
    binding = current69_test_binding(lock, source_head)
    current69_test_bundle(bundle, lock, binding)
    current69_test_assets(lock)
    checks = []
    result = {"schema": "GQ8_CAPTURE_CURRENT69_NEGATIVES_V1", "source_head": source_head,
              "python_optimization": sys.flags.optimize, "lock": current69_test_file(CURRENT69_TEST_HERE / "INPUT_LOCK.json"),
              "native_runs": 0, "compiler_runs": 0, "rojo_builds": 0,
              "source_mutations": 0, "checks": checks, "status": "INCOMPLETE"}

    def reject(name, action, expected_reason):
        try:
            action()
        except ValueError as exc:
            reason = str(exc)
            checks.append({"case": name, "expected_reason": expected_reason, "observed_reason": reason,
                           "rejected_at_expected_guard": reason == expected_reason})
            current69_require(reason == expected_reason, "TEST_NEGATIVE_WRONG_REJECTION_" + name)
        else:
            checks.append({"case": name, "expected_reason": expected_reason, "rejected_at_expected_guard": False})
            current69_require(False, "TEST_NEGATIVE_ACCEPTED_" + name)

    try:
        client_rel = next(row["path"] for row in lock["sources"] if row["route"] == "/".join(CLIENT))
        other = next(row for row in lock["sources"] if row["route"] != "/".join(CLIENT))
        tree_cases = (
            ("target_bytes", "CURRENT69_SOURCE_BYTES_" + "/".join(CLIENT)),
            ("other_68_bytes", "CURRENT69_SOURCE_BYTES_" + other["route"]),
            ("missing_source", "CURRENT69_SOURCE_PATH_MEMBERSHIP"),
            ("extra_source", "CURRENT69_SOURCE_PATH_MEMBERSHIP"),
            ("source_symlink_same_bytes", "CURRENT69_SOURCE_SYMLINK_REJECTED"),
            ("project_physical_crlf", "CURRENT69_PROJECT_PHYSICAL_BYTES_DRIFT"),
        )
        for name, reason in tree_cases:
            target = out / name
            shutil.copytree(bundle / "ON", target)
            if name in ("target_bytes", "other_68_bytes"):
                path = target / (client_rel if name == "target_bytes" else other["path"])
                path.write_bytes(path.read_bytes() + b"\n-- deliberate guard negative\n")
            elif name == "missing_source":
                (target / other["path"]).unlink()
            elif name == "extra_source":
                (target / "sources" / "UNGRANTED_EXTRA.luau").write_bytes(b"return {}\n")
            elif name == "source_symlink_same_bytes":
                path = target / client_rel
                path.unlink()
                path.symlink_to(bundle / "ON" / client_rel)
                current69_require(path.read_bytes() == (bundle / "ON" / client_rel).read_bytes(), "TEST_SYMLINK_CONTROL_BYTES")
            else:
                path = target / lock["input"]["project"]["path"]
                original = path.read_bytes()
                changed = original.replace(b"\n", b"\r\n")
                current69_require(changed != original, "TEST_CRLF_MUTANT_AVAILABLE")
                path.write_bytes(changed)
            reject(name, lambda t=target: current69_validate_tree(t, lock, "candidate"), reason)

        bad_lock = out / "mutated_lock.json"
        bad_lock.write_bytes((CURRENT69_TEST_HERE / "INPUT_LOCK.json").read_bytes() + b"\n")
        reject("lock_physical_bytes", lambda: current69_load_lock(bad_lock), "CURRENT69_LOCK_BYTES_DRIFT")
        asset_root = out / "asset_bytes"
        shutil.copytree(CURRENT69_TEST_HERE / "native", asset_root / "native")
        asset_rel = "native/epoch_cases.luau"
        (asset_root / asset_rel).write_bytes((asset_root / asset_rel).read_bytes() + b"\n")
        reject("frozen_case_bytes", lambda: current69_test_assets(lock, asset_root), "CURRENT69_ASSET_BYTES_DRIFT_" + asset_rel)
        reject("incorrect_actual_source_head", lambda: current69_test_binding(lock, "0" * 40), "CURRENT69_ACTUAL_SOURCE_HEAD_MISMATCH")

        api = [current69_json((bundle / "input_api" / name).read_bytes())
               for name in ("formal-ref.json", "official-run.json", "official-artifact.json")]
        for name, reason in (("formal_head", "CURRENT69_LIVE_FORMAL_MOVED_REBIND_REQUIRED"),
                             ("official_run_head", "CURRENT69_OFFICIAL_RUN_head_sha"),
                             ("artifact_digest", "CURRENT69_OFFICIAL_ARTIFACT_digest"),
                             ("artifact_expired", "CURRENT69_OFFICIAL_ARTIFACT_EXPIRED")):
            mutant = deepcopy(api)
            if name == "formal_head":
                mutant[0]["object"]["sha"] = "0" * 40
            elif name == "official_run_head":
                mutant[1]["head_sha"] = "0" * 40
            elif name == "artifact_digest":
                mutant[2]["digest"] = "sha256:" + "0" * 64
            else:
                mutant[2]["expired"] = True
            reject(name, lambda m=mutant: current69_verify_api(lock, *m), reason)

        archive = bundle / "input_archive.zip"
        extracted = out / "archive_positive"
        current69_extract_archive(archive, extracted, lock)
        checks.append({"case": "archive_exact_positive", "accepted": True, "sources": 69})
        reject("existing_extraction_output", lambda: current69_extract_archive(archive, extracted, lock), "CURRENT69_EXTRACT_OUTPUT_MUST_BE_NEW")
        drift_archive = out / "archive_bytes.zip"
        drift_archive.write_bytes(archive.read_bytes() + b"\n")
        reject("archive_physical_bytes", lambda: current69_extract_archive(drift_archive, out / "bad_zip_output", lock), "CURRENT69_ARCHIVE_BYTES_DRIFT")

        # Rebind test-only ZIP byte measurements so a path/link failure cannot be
        # mistaken for the earlier immutable archive digest rejection above.
        with zipfile.ZipFile(archive) as source_zip:
            members = [(deepcopy(info), source_zip.read(info)) for info in source_zip.infolist()]
        first_file = next(i for i, (info, _) in enumerate(members) if not info.is_dir())
        for name, reason in (("zip_traversal", "CURRENT69_ARCHIVE_UNSAFE_PATH"),
                             ("zip_duplicate_casefold", "CURRENT69_ARCHIVE_DUPLICATE_PATH"),
                             ("zip_symlink", "CURRENT69_ARCHIVE_LINK_OR_ENCRYPTED_MEMBER"),
                             ("zip_missing_member", "CURRENT69_ARCHIVE_MEMBER_COUNT")):
            entries = deepcopy(members)
            info, data = entries[first_file]
            if name == "zip_traversal":
                info.filename = "../outside.luau"
            elif name == "zip_duplicate_casefold":
                duplicate = deepcopy(info)
                duplicate.filename = info.filename.swapcase()
                current69_require(duplicate.filename != info.filename, "TEST_CASEFOLD_MUTANT_AVAILABLE")
                entries.append((duplicate, data))
            elif name == "zip_symlink":
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                entries[first_file] = (info, b"../outside.luau")
            else:
                del entries[first_file]
            mutated = out / (name + ".zip")
            with zipfile.ZipFile(mutated, "w", compression=zipfile.ZIP_DEFLATED) as target_zip:
                for entry, body in entries:
                    target_zip.writestr(entry, body)
            structural_lock = deepcopy(lock)
            structural_lock["archive"].update(current69_pin(mutated))
            structural_lock["archive"]["expanded_bytes"] = sum(len(body) for _, body in entries)
            structural_lock["archive"]["members"] = lock["archive"]["members"] if name == "zip_missing_member" else len(entries)
            output = out / (name + "_output")
            reject(name, lambda p=mutated, d=output, l=structural_lock: current69_extract_archive(p, d, l), reason)
            current69_require(not output.exists(), "TEST_UNSAFE_ARCHIVE_CREATED_OUTPUT")
            checks[-1]["synthetic_archive_measurements_only"] = True
            checks[-1]["archive"] = current69_test_file(mutated)

        # Reuse actual Native output from this run; no VM executes in this mode.
        raw_dir = bundle / "QA" / "native" / "epoch_v3" / "run"
        stdout, stderr = (raw_dir / "stdout.log").read_bytes(), (raw_dir / "stderr.log").read_bytes()
        contract = lock["contracts"]["epoch_v3"]
        current69_test_observations(contract, stdout, stderr)
        raw_lines = stdout.splitlines(keepends=True)
        indices = [i for i, line in enumerate(raw_lines) if line.startswith(b"OBS\t")]
        current69_require(len(indices) == 27, "TEST_NATIVE_OUTPUT_POSITIVE_REQUIRED")
        swapped = list(raw_lines)
        swapped[indices[0]], swapped[indices[1]] = swapped[indices[1]], swapped[indices[0]]
        reject("ordered_observations_not_counts_only", lambda: current69_test_observations(contract, b"".join(swapped), stderr), "CURRENT69_TEST_ORDERED_OBSERVATION_CONTRACT")
        no_finish = b"".join(line for line in raw_lines if b"\tFINISH\t" not in line)
        reject("complete_finish_records_required", lambda: current69_test_observations(contract, no_finish, stderr), "CURRENT69_TEST_EXACT_FINISH_RECORDS")
        reject("raw_event_stream_required", lambda: current69_test_observations(contract, stdout + b"UNEXPECTED_EVENT\n", stderr), "CURRENT69_TEST_RAW_STDOUT_CONTRACT")
        current69_require(current69_load_lock() == lock, "TEST_NEGATIVE_CHANGED_LOCK")
        current69_test_assets(lock)
        current69_test_bundle(bundle, lock, current69_test_binding(lock, source_head))
        result["status"] = "ALL_EXPECTED_REJECTIONS_AND_POSITIVE_CONTROLS_PASS"
        result["negative_cases"] = sum("expected_reason" in item for item in checks)
        current69_require(result["negative_cases"] == 22 and len(checks) == 23, "TEST_NEGATIVE_CASE_COVERAGE")
    except Exception as exc:
        result["status"] = "FAILED_PRESERVED"
        result["failure"] = {"type": type(exc).__name__, "reason": str(exc)}
        raise
    finally:
        current69_test_write(out / "RESULT.json", result)
    print(json.dumps({"status": result["status"], "python_optimization": sys.flags.optimize,
                      "negative_cases": result["negative_cases"], "native_runs": 0}, ensure_ascii=False))


def current69_test_run(args):
    bundle = args.bundle.resolve()
    qa = bundle / "QA"
    current69_require(not qa.exists() and not qa.is_symlink(), "TEST_OUTPUT_MUST_BE_NEW")
    qa.mkdir(parents=True, exist_ok=False)
    report = {"schema": "GQ8_CAPTURE_CURRENT69_QA_V1", "status": "INCOMPLETE",
              "started_at": datetime.now(timezone.utc).isoformat(), "native_runs": [],
              "compile_runs": [], "rojo_builds": [], "negative_runs": [],
              "registered_independent_approval": False, "formal_adoption": False,
              "studio": "NOT_TESTED", "capture_service": "NOT_TESTED", "android": "NOT_TESTED",
              "art": "NO_GO", "fun": "NOT_TESTED", "provider_authentication_proven": False,
              "test_author": "/root/map_review", "source_and_composer_author": "/root",
              "independent_reviewer": "/root/planning_gap (not a test author)"}
    phase = "input"
    try:
        lock = current69_load_lock()
        binding = current69_test_binding(lock, args.source_head)
        report.update(binding)
        report.update({"official_input_head": lock["base_rc"], "base_rc": lock["base_rc"],
                       "input_lock": current69_test_file(CURRENT69_TEST_HERE / "INPUT_LOCK.json"),
                       "composition_receipt": current69_test_file(bundle / "COMPOSITION_RECEIPT.json"),
                       "generator": current69_test_file(Path(__file__)), "limits": lock["limits"]})
        trees, variants = current69_test_bundle(bundle, lock, binding)
        assets, normal = current69_test_assets(lock)
        report["fixed_assets"] = [{"path": rel, **current69_pin(raw), "author": lock["assets"][rel]["author"]}
                                  for rel, raw in assets.items()]
        report["normal_control"] = {**current69_pin(normal), "shared_observations": 6,
                                     "note": "27 + 32 includes the same six normal observations; not 59 independent features"}
        phase = "toolchain"
        luau_source = args.luau_source.resolve()
        luau_head = subprocess.check_output(["git", "-C", str(luau_source), "rev-parse", "HEAD"]).decode().strip()
        current69_require(luau_head == lock["toolchain"]["luau_commit"], "TEST_LUAU_BUILD_SOURCE_REVISION")
        subprocess.run(["git", "-C", str(luau_source), "diff", "--exit-code", "HEAD", "--"], check=True, capture_output=True)
        binaries = {"native_vm": args.luau.resolve(), "compiler": args.compile.resolve(), "rojo": args.rojo.resolve()}
        report["toolchain"] = {key: current69_test_file(path) for key, path in binaries.items()}
        report["toolchain"]["luau_build_source"] = {"path": str(luau_source), "git_head": luau_head,
                                                   "binary_hashes_measured_above": True,
                                                   "binary_origin_attestation": "Build source revision and actual executable pins; hosted build commands remain separate evidence"}
        version, stdout, _ = current69_test_execute([binaries["rojo"], "--version"], qa / "rojo_version")
        current69_require(version["exit_code"] == 0 and stdout.decode().strip() == "Rojo " + lock["toolchain"]["rojo_version"], "TEST_ROJO_VERSION")
        report["toolchain"]["rojo_version_command"] = version
        report["toolchain"]["rojo_archive_sha256_required_by_workflow"] = lock["toolchain"]["rojo_archive_sha256"]

        phase = "native"
        current69_require(set(lock["contracts"]) == set(CURRENT69_CONTRACT_ORDER), "TEST_EXACT_FOUR_NATIVE_CONTRACTS")
        for label in CURRENT69_CONTRACT_ORDER:
            contract = lock["contracts"][label]
            program, body = current69_test_program(contract, variants[label], assets, normal)
            folder = qa / "native" / label
            folder.mkdir(parents=True, exist_ok=False)
            program_path = folder / "full_client_program.luau"
            program_path.write_bytes(program)
            run, stdout, stderr = current69_test_execute([binaries["native_vm"], program_path], folder / "run", timeout=30)
            native = {"label": label, "source_body": body, "program": current69_test_file(program_path),
                      "source_head": args.source_head, "native_vm": report["toolchain"]["native_vm"],
                      "native_vm_runs": 1, "command_result": run, "status": "INCOMPLETE_PRESERVED"}
            report["native_runs"].append(native)
            try:
                current69_require(run["exit_code"] == 0 and not run["timed_out"], "TEST_NATIVE_EXIT_" + label)
                native.update(current69_test_observations(contract, stdout, stderr))
                native["status"] = "EXACT_EXPECTED_CONTRACT_API_MODEL_ONLY"
            finally:
                current69_test_write(folder / "RECEIPT.json", native)
        normal_triples = [lock["contracts"][label]["expected_observations"][:6] for label in CURRENT69_CONTRACT_ORDER]
        current69_require(all(triples == normal_triples[0] for triples in normal_triples), "TEST_SHARED_NORMAL_SIX")

        phase = "compile"
        for index, (route, path) in enumerate(sorted(trees["ON"].items()), 1):
            run, stdout, _ = current69_test_execute([binaries["compiler"], "--binary", path], qa / "compile" / f"{index:02d}")
            report["compile_runs"].append({"route": "/".join(route), "source": current69_test_file(path), "command_result": run})
            current69_require(run["exit_code"] == 0 and bool(stdout) and not run["timed_out"], "TEST_COMPILE_" + "/".join(route))
        current69_require(len(report["compile_runs"]) == 69, "TEST_COMPILE_COUNT")

        phase = "rojo"
        places = {}
        for label in ("ON", "OFF"):
            project = bundle / label / lock["input"]["project"]["path"]
            place = qa / ("CAPTURE_CURRENT69_ON_NOT_RC.rbxlx" if label == "ON" else "EXACT_OFFICIAL_OFF.rbxlx")
            run, _, _ = current69_test_execute([binaries["rojo"], "build", project, "-o", place], qa / ("rojo_" + label), cwd=bundle / label)
            report["rojo_builds"].append({"label": label, "project": current69_test_file(project), "command_result": run})
            current69_require(run["exit_code"] == 0 and place.is_file() and not run["timed_out"], "TEST_ROJO_BUILD_" + label)
            places[label] = place
        phase = "place_readback"
        original_place = bundle / "input" / lock["input"]["place"]["path"]
        current69_require(places["OFF"].read_bytes() == original_place.read_bytes(), "TEST_ACTUAL_OFF_PLACE_BYTE_EXACT")
        xml = {}
        original_xml, original_non_source = current69_test_xml(original_place, trees["input"], lock)
        xml["official_input"] = original_xml
        for label in ("ON", "OFF"):
            readback, non_source = current69_test_xml(places[label], trees[label], lock)
            current69_require(non_source == original_non_source, "TEST_NON_SOURCE_PROPERTIES_" + label)
            xml[label] = readback
        xml["off_actual_place_byte_exact"] = True
        xml["non_source_xml_identical"] = True
        report["places"] = xml
        current69_test_write(qa / "PLACE_READBACK.json", xml)

        phase = "negatives"
        negative_case_orders = []
        for optimization in (0, 1):
            name = "normal" if optimization == 0 else "optimized"
            command = [sys.executable, "-B"] + (["-O"] if optimization else [])
            output = qa / "negatives" / name
            command += [str(Path(__file__).resolve()), "current69-negatives", "--bundle", str(bundle),
                        "--out", str(output), "--source-head", args.source_head]
            run, _, _ = current69_test_execute(command, qa / ("negative_command_" + name), timeout=120)
            report["negative_runs"].append({"optimization": optimization, "command_result": run})
            current69_require(run["exit_code"] == 0 and not run["timed_out"], "TEST_NEGATIVE_PROCESS_" + name)
            negative = current69_json((output / "RESULT.json").read_bytes())
            current69_require(negative["status"] == "ALL_EXPECTED_REJECTIONS_AND_POSITIVE_CONTROLS_PASS"
                              and negative["python_optimization"] == optimization
                              and negative["negative_cases"] == 22, "TEST_NEGATIVE_RESULT_" + name)
            negative_case_orders.append([item["case"] for item in negative["checks"]])
            report["negative_runs"][-1]["receipt"] = current69_test_file(output / "RESULT.json")
        current69_require(negative_case_orders[0] == negative_case_orders[1], "TEST_OPTIMIZED_NEGATIVE_CASE_ORDER")

        phase = "final_input_readback"
        current69_require(current69_load_lock() == lock, "TEST_LOCK_CHANGED_DURING_EXECUTION")
        current69_test_assets(lock)
        current69_require(current69_test_binding(lock, args.source_head) == binding, "TEST_SOURCE_CHANGED_DURING_EXECUTION")
        current69_test_bundle(bundle, lock, binding)
        for key, path in binaries.items():
            current69_require(current69_test_file(path) == report["toolchain"][key], "TEST_TOOL_CHANGED_DURING_EXECUTION_" + key)
        report.update({"status": "CURRENT69_SOURCE_QA_PASS_NOT_RC_OR_ENGINE_ACCEPTANCE",
                       "native_vm_run_count": 4, "compiler_run_count": 69, "rojo_build_count": 2,
                       "candidate_changed_sources": 1, "unchanged_sources": 68,
                       "source_count": 69, "instance_count": 75, "actual_off_place_matches_official": True})
    except Exception as exc:
        report.update({"status": "FAILED_PRESERVED", "failure_phase": phase,
                       "failure": {"type": type(exc).__name__, "reason": str(exc)}})
        raise
    finally:
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        current69_test_write(qa / "QA_RECEIPT.json", report)
    print(json.dumps({key: report[key] for key in ("status", "source_head", "source_tree", "source_context",
                     "official_input_head", "native_vm_run_count", "compiler_run_count", "rojo_build_count")}, ensure_ascii=False))


if __name__ == "__main__" and sys.argv[1:2] in (["current69"], ["current69-negatives"]):
    parser = argparse.ArgumentParser(description="Pinned Capture current69 QA; source/fixture evidence, not engine or adoption approval")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    if sys.argv[1] == "current69-negatives":
        parser.add_argument("--out", type=Path, required=True)
        current69_test_negatives(**vars(parser.parse_args(sys.argv[2:])))
    else:
        for argument in ("luau", "compile", "luau-source", "rojo"):
            parser.add_argument("--" + argument, type=Path, required=True)
        current69_test_run(parser.parse_args(sys.argv[2:]))
    raise SystemExit(0)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    a=p.parse_args()
    check(a.parent,a.candidate)
