#!/usr/bin/env python3
"""Source-pinned visual-only fix for crowded neutral labels in REAL69 Studio.

Produces a single changed existing Swarm Luau file from one authentic 69-script
artifact. Does not edit the formal RC, create Game authority, or claim Studio QA.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROUTE = "ServerScriptService/EGGRUMBLE_SwarmCombat"
MEMBER = "sources/ServerScriptService/EGGRUMBLE_SwarmCombat.luau"
PARENT_SHA256 = "3ca5b0ecfeced3dfdec204b0de6a9ae72c48c6793a65ec39d6b37e3ba431a6f1"
MARKER = "GQ8_FB008_NEUTRAL_LABEL_DENSITY_REAL69_20261120"
ANCHOR = ' local h=Instance.new("Humanoid");h.Name="Humanoid";h.RequiresNeck=false\n'
REPLACEMENT = ANCHOR + ''' -- GQ8_FB008_NEUTRAL_LABEL_DENSITY_REAL69_20261120
 -- Hide repeating HordeSoldier text; retain close-range HP as combat feedback.
 -- No new BillboardGui, per-frame listener, Part, Remote or gameplay authority.
 h.NameDisplayDistance=0
 h.HealthDisplayDistance=22
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patch(raw):
    if sha(raw) != PARENT_SHA256:
        raise ValueError("RED_REAL69_SWARM_SOURCE_DRIFT")
    original = raw.decode("utf-8")
    if original.count(ANCHOR) != 1 or MARKER in original:
        raise ValueError("RED_REAL69_HORDE_ANCHOR_OR_DUPLICATE")
    updated = original.replace(ANCHOR, REPLACEMENT).encode("utf-8")
    if updated.count(MARKER.encode()) != 1:
        raise ValueError("RED_REAL69_HORDE_PATCH_COUNT")
    if updated.replace(REPLACEMENT.encode(), ANCHOR.encode()) != raw:
        raise ValueError("RED_REAL69_HORDE_ROLLBACK_MISMATCH")
    for forbidden in (b'Instance.new("BillboardGui")', b'FireServer(', b'TakeDamage(', b'DataStoreService'):
        if forbidden in REPLACEMENT.encode():
            raise ValueError("RED_REAL69_HORDE_NEW_AUTHORITY_OR_GUI")
    return updated


def verified_package(path):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        receipt = json.loads(z.read("REAL69_LEGACY_INTAKE_RECEIPT.json"))
        project = json.loads(z.read("EGGRUMBLE_REAL69.project.json"))
        files = {n for n in names if n.startswith("sources/") and n.endswith(".luau")}
        if len(files) != 69 or receipt.get("selected_source_count") != 69:
            raise ValueError("RED_REAL69_SOURCE_COUNT")
        if not receipt.get("build_head") or len(receipt.get("source_hashes", {})) != 69:
            raise ValueError("RED_REAL69_RECEIPT")
        for route, digest in receipt["source_hashes"].items():
            target = project["tree"]
            for section in route.split("/"):
                target = target[section]
            member = target["$path"]
            if member not in files or sha(z.read(member)) != digest:
                raise ValueError("RED_REAL69_SOURCE_LOCK_" + route)
        if receipt["source_hashes"].get(ROUTE) != PARENT_SHA256:
            raise ValueError("RED_REAL69_SWARM_NOT_SELECTED")
        raw = z.read(MEMBER)
        return raw, receipt["build_head"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real69-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original, head = verified_package(args.real69_zip)
    updated = patch(original)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(updated)
    receipt = {
        "feature": MARKER,
        "base_artifact_head": head,
        "selected_source_count": 69,
        "one_changed_route": ROUTE,
        "before_sha256": sha(original),
        "after_sha256": sha(updated),
        "other_68_source_bodies_unchanged_by_this_candidate": True,
        "rollback": "replace changed script with before_sha256 exact original",
        "studio_android_art_fun": "NOT_TESTED",
        "official_rc_integrated": False,
    }
    args.out.with_suffix(".receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("GQ8_REAL69_HORDE_LABEL_SOURCE_PATCH_PASS", sha(updated))


if __name__ == "__main__":
    main()
