#!/usr/bin/env python3
"""Build a source-locked *native Luau CLI* test file, never a Roblox Game/Place."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "EggRelayPolicy.luau"
CASES = ROOT / "tests" / "native_policy_cases.luau"
MANIFEST = ROOT / "SOURCE_MANIFEST.json"
EXPECTED_SOURCE_SHA256 = "7515fecbb4994d39bccdd7dba49229bcb151ab64d084da84e332c41f7bc5dfa0"
EXPECTED_SOURCE_GITBLOB = "ef9b65bd6520231f299f21c5cfe2aa250798c8d0"
EXPECTED_CASES_GITBLOB = "801ac8f52cc3fec9bc159b73803853aea845a582"


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def verify(source: bytes, cases: bytes, manifest: dict):
    """Fail closed if the previously approved policy drifts or test cases shrink."""
    assert hashlib.sha256(source).hexdigest() == EXPECTED_SOURCE_SHA256, "SOURCE_SHA256_MISMATCH"
    assert blob_sha(source) == EXPECTED_SOURCE_GITBLOB, "SOURCE_GIT_BLOB_MISMATCH"
    assert blob_sha(cases) == EXPECTED_CASES_GITBLOB, "NATIVE_CASES_DRIFT"
    entry = next((x for x in manifest.get("files", [])
                  if x.get("path") == "src/EggRelayPolicy.luau"), None)
    assert entry and entry.get("sha256") == EXPECTED_SOURCE_SHA256, "MANIFEST_SOURCE_MISMATCH"
    assert entry.get("git_blob_sha") == EXPECTED_SOURCE_GITBLOB, "MANIFEST_BLOB_MISMATCH"
    assert manifest.get("official_rc_adopted") is False, "FORBIDDEN_OFFICIAL_RC_CLAIM"
    assert manifest.get("product_selected") is False, "FORBIDDEN_PRODUCT_SELECTED_CLAIM"
    assert manifest.get("roblox_studio") == "NOT_TESTED", "FORBIDDEN_STUDIO_PASS_CLAIM"
    assert len(re.findall(rb'\bcheck\("', cases)) == 41, "NATIVE_CASE_COUNT_MISMATCH"
    assert b"P0D_EGG_RELAY_NATIVE_POLICY_41_CASES_PASS" in cases, "NATIVE_PASS_MARKER_MISSING"


def render(source: bytes, cases: bytes, manifest: dict) -> str:
    verify(source, cases, manifest)
    header = "-- AUTO GENERATED. Native Luau CLI only, not Roblox Studio.\n"
    s = source.decode("utf-8")
    c = cases.decode("utf-8")
    assert s.endswith("\n") and c.endswith("\n")
    return header + "local Relay = (function()\n" + s + "end)()\n" + c


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    generated = render(SOURCE.read_bytes(), CASES.read_bytes(),
                       json.loads(MANIFEST.read_text("utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(generated, encoding="utf-8")
    print("P0D_EGG_RELAY_NATIVE_TEST_GENERATED_SOURCE_LOCK_PASS")


if __name__ == "__main__":
    main()
