#!/usr/bin/env python3
"""Strictly build a NONPUBLISHABLE Studio QA copy of an authentic 8-safe S1 Place.

Only injects two previously QA-vetted, read-only Studio observer Lua scripts.
The exact original 21 scripts and all other Roblox Place XML are preserved.
No Roblox Studio is executed; this is a source/preparation check only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[3]
PREVIEW_SHA = "3120b9d3c0a5ec58c9f2613c5d186f3493b54f83"
PROBE_SHA = "e2662b540f2312c95af67a1761ea05842482919d"
PROBE_ROOT = "handoffs/P0D-S1-AUTHORITY-ABUSE-SOURCE-GATE-20261112-01"
BASE_PLACE_SHA256 = "b27f401cd6aed7242665098a4cf323184fe13f2ef964b59a3c97b82daf998d04"
BASE_PLACE_BYTES = 159080
CLIENT_PROBE_FILE = "StudioPassiveClientProbe.client.luau"
SERVER_PROBE_FILE = "StudioPassiveServerProbe.server.luau"
CLIENT_BLOB = "c0fb0a8ff39ba02277bd4484604b80f3207d7756"
SERVER_BLOB = "6272cbd587c714046685aba82be775c6dad21057"
INJECTED_CLIENT = "P0D_QA_ONLY_ReadOnlyClientObserver"
INJECTED_SERVER = "P0D_QA_ONLY_ReadOnlyServerObserver"
PREVIOUS_ROJO_VERIFY = (
    "handoffs/P0D-S1-EIGHT-SAFE-HUD-REVIEW-20261113-01/"
    "verify_eight_real_rojo.py"
)
FORBIDDEN_MUTATION_TOKENS = (
    r":\s*FireServer\s*\(",
    r":\s*FireClient\s*\(",
    r":\s*FireAllClients\s*\(",
    r"\bDataStoreService\b",
    r"\bMarketplaceService\b",
    r"\bPublishAsync\b",
    r"Instance\.new\s*\(\s*['\"]RemoteEvent['\"]",
)
PROBES = (
    ("client", CLIENT_PROBE_FILE, CLIENT_BLOB, "StarterPlayerScripts",
     "LocalScript", INJECTED_CLIENT),
    ("server", SERVER_PROBE_FILE, SERVER_BLOB, "ServerScriptService",
     "Script", INJECTED_SERVER),
)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def git_read(commit: str, path: str) -> bytes:
    cmd = ["git", "-C", str(REPO), "show", f"{commit}:{path}"]
    p = subprocess.run(cmd, check=False, capture_output=True, timeout=30)
    if p.returncode:
        raise ValueError("PINNED_GITHUB_SOURCE_UNAVAILABLE_" + path)
    return p.stdout


def upstream():
    # The earlier complete real Rojo exact-source validation is reused,
    # not reconstructed or downgraded here.
    file = REPO / PREVIOUS_ROJO_VERIFY
    spec = importlib.util.spec_from_file_location("p0d_prior_rojo_source_verify", file)
    if spec is None or spec.loader is None:
        raise ValueError("EXACT_ORIGINAL_EIGHT_SAFE_ROJO_VERIFIER_MISSING")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = module.expected_sources()
    if len(expected) != 21:
        raise ValueError("NOT_21_GENUINE_ORIGINAL_LUAU_SOURCES")
    return module, expected


def safe_probes() -> dict[str, str]:
    found = {}
    for label, file, sha, _, _, _ in PROBES:
        raw = git_read(PROBE_SHA, PROBE_ROOT + "/" + file)
        if git_blob(raw) != sha:
            raise ValueError("PINNED_PASSIVE_PROBE_GIT_BLOB_CHANGED_" + label)
        body = raw.decode("utf-8")
        if 'RunService:IsStudio()' not in body or 'return end' not in body:
            raise ValueError("PROBE_MUST_RUN_ONLY_IN_STUDIO_" + label)
        if any(re.search(pat, body) for pat in FORBIDDEN_MUTATION_TOKENS):
            raise ValueError("PROBE_CONTAINS_FORBIDDEN_GAMEPLAY_WRITE_" + label)
        if "P0D_STUDIO_PROBE_V1" not in body:
            raise ValueError("ORIGINAL_PASSIVE_PROBE_LOG_PREFIX_MISSING_" + label)
        found[label] = body
    return found


def get_named_item(root: ET.Element, name: str, expected_class: str) -> ET.Element:
    items = [x for x in root.iter("Item")
             if x.get("class") == expected_class
             and any(p.get("name") == "Name" and p.text == name
                     for p in x.findall("./Properties/*"))]
    if len(items) != 1:
        raise ValueError("ORIGINAL_PLACE_UNEXPECTED_PARENT_" + name)
    return items[0]


def create_probe(parent: ET.Element, name: str, cls: str, body: str):
    item = ET.SubElement(parent, "Item", {
        "class": cls, "referent": "P0D_QA_READONLY_" + name
    })
    props = ET.SubElement(item, "Properties")
    ET.SubElement(props, "string", {"name": "Name"}).text = name
    ET.SubElement(props, "string", {"name": "Source"}).text = body
    return item


def verify_injected(raw: bytes, verifier, expected, probes):
    root, scripts = verifier.parse(raw)
    if len(scripts) != 23:
        raise ValueError("QA_CLONE_MUST_CONTAIN_21_ORIGINAL_PLUS_2_PROBES")
    original = {path: (cls, content) for path, cls, content in scripts}
    if len(original) != 23:
        raise ValueError("QA_CLONE_SCRIPT_DUPLICATE_PATH")
    if len(set(expected)) != 21 or not set(expected).issubset(set(original)):
        raise ValueError("ORIGINAL_21_SCRIPTS_MISSING_FROM_QA_PLACE")
    for path, (cls, payload) in expected.items():
        actual = original[path]
        if cls != actual[0] or payload != (actual[1] or "").encode("utf8"):
            raise ValueError("ORIGINAL_GAME_LUAU_CHANGED_" + path)
    extra = set(original) - set(expected)
    intended = {
        "ServerScriptService/" + INJECTED_SERVER:
            ("Script", probes["server"]),
        "StarterPlayer/StarterPlayerScripts/" + INJECTED_CLIENT:
            ("LocalScript", probes["client"]),
    }
    if extra != set(intended):
        raise ValueError("QA_CLONE_UNEXPECTED_ADDITIONAL_SCRIPT_" + repr(extra))
    for path, expected_pair in intended.items():
        if original[path] != expected_pair:
            raise ValueError("PINNED_PROBE_SOURCE_CHANGED_IN_XML_" + path)
    original_script_type = [v[0] for v in expected.values()]
    clone_script_type = [x[1] for x in scripts]
    if (clone_script_type.count("Script"),
            clone_script_type.count("LocalScript"),
            clone_script_type.count("ModuleScript")) != (2, 4, 17):
        raise ValueError("QA_CLONE_SCRIPT_CLASS_COUNT_BROKEN")
    if (original_script_type.count("Script"),
            original_script_type.count("LocalScript"),
            original_script_type.count("ModuleScript")) != (1, 3, 17):
        raise ValueError("ORIGINAL_GAME_SCRIPT_CLASS_COUNT_BROKEN")
    if len(root.findall("./Item")) < 1:
        raise ValueError("INVALID_ROBLOX_DATAMODEL")
    return {
        "original_scripts_preserved": 21,
        "added_safe_probe_scripts": 2,
        "all_script_count": len(scripts),
        "server_scripts": 2,
        "client_scripts": 4,
        "module_scripts": 17,
        "verified_original_original_Git_blobs": 21,
    }


def generate(original_xml: bytes, probes: dict[str, str], verify):
    if len(original_xml) != BASE_PLACE_BYTES or \
            hashlib.sha256(original_xml).hexdigest() != BASE_PLACE_SHA256:
        raise ValueError("ACTUAL_GENUINE_EIGHT_SAFE_PLACE_SHA256_MISMATCH")
    verifier, expected = verify
    verifier.verify_place(original_xml, expected)
    root = ET.fromstring(original_xml)
    if root.tag != "roblox":
        raise ValueError("NOT_ROBLOX_PLACE")
    for label, _, _, name, cls, unique in PROBES:
        parent = get_named_item(
            root, name,
            "ServerScriptService" if label == "server" else "StarterPlayerScripts"
        )
        create_probe(parent, unique, cls, probes[label])
    output = ET.tostring(root, encoding="utf8", xml_declaration=True)
    proof = verify_injected(output, verifier, expected, probes)
    return output, proof


def record(original: bytes, created: bytes, tested: dict):
    return {
        "format": "P0D_S1_EIGHT_SAFE_STUDIO_QA_ONLY_PROBED_PLACE_V1",
        "game_id": "TRAP_RAIDERS",
        "base_game_git_sha": PREVIEW_SHA,
        "base_source_review_only": True,
        "base_place_sha256": BASE_PLACE_SHA256,
        "base_place_size": BASE_PLACE_BYTES,
        "qa_place_sha256": hashlib.sha256(created).hexdigest(),
        "qa_place_size": len(created),
        "probe_source_git_commit": PROBE_SHA,
        "original_probes": {
            CLIENT_PROBE_FILE: CLIENT_BLOB,
            SERVER_PROBE_FILE: SERVER_BLOB,
        },
        "test": tested,
        "studio_tested": False,
        "real_two_clients_tested": False,
        "real_mobile_tested": False,
        "owner_publish_approved": False,
        "published": False,
        "ONLY_OPEN_AS_LOCAL_UNPUBLISHED_QA_CLONE": True,
        "DO_NOT_PUBLISH_OR_SAVE_TO_ROBLOX": True,
    }


def safe_create(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as f:
            f.write(data)
    except FileExistsError:
        raise ValueError("OUTPUT_EXISTS_REFUSING_TO_OVERWRITE_" + str(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--place", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()
    if args.output.resolve() == args.place.resolve() or \
            args.output.resolve() == args.receipt.resolve():
        raise ValueError("QA_CLONE_CANNOT_OVERWRITE_ORIGINAL_OR_RECEIPT")
    if args.output.exists() or args.receipt.exists():
        raise ValueError("QA_OUTPUT_ALREADY_EXISTS_OVERWRITE_FORBIDDEN")
    raw = args.place.read_bytes()
    actual, proof = generate(raw, safe_probes(), upstream())
    receipt = record(raw, actual, proof)
    safe_create(args.output, actual)
    safe_create(args.receipt, (
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n"
    ).encode("utf8"))
    print("P0D_QA_ONLY_ORIGINAL_21_OF_21_SOURCE_BYTES_VERIFIED")
    print("P0D_QA_ONLY_VETTED_PASSIVE_OBSERVERS_2_OF_2_EXACT")
    print("P0D_QA_ONLY_23_SCRIPTS_XML_VERIFIED")
    print("P0D_QA_ONLY_INSTRUMENTED_PLACE_SHA256=" + receipt["qa_place_sha256"])
    print("P0D_QA_ONLY_STUDIO_AND_MOBILE_NOT_TESTED_PUBLISH_PROHIBITED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, UnicodeError, ET.ParseError) as e:
        print("P0D_QA_INSTRUMENTED_BUILD_BLOCKED " + str(e), file=sys.stderr)
        sys.exit(2)
