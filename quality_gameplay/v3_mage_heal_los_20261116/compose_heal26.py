#!/usr/bin/env python3
"""Overlay a single original-owner MAGE-heal source onto #484's 26-script composer.

Never duplicate a Game/Remote/Script, and never edit the original producer tree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import os

SCRIPT = "EGGRUMBLE_SevenRoleCombat"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--receipt", required=True, type=Path)
    args = ap.parse_args()
    project = args.project.resolve(strict=True)
    candidate = args.candidate.resolve(strict=True)
    receipt = args.receipt.resolve(strict=True)
    data = json.loads(project.read_text(encoding="utf-8"))
    server = data["tree"]["ServerScriptService"]
    clients = data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert len(server) - 1 == 23 and len(clients) - 1 == 3, "26 source composer drift"
    assert SCRIPT in server and set(server[SCRIPT]) == {"$path"}, "existing MAGE script not found"
    old_source = (project.parent / server[SCRIPT]["$path"]).resolve(strict=True)
    old = old_source.read_text(encoding="utf-8")
    new = candidate.read_text(encoding="utf-8")
    assert "local function healAllies(" in old
    assert "local function healAllies(" in new
    assert "sourceCharacter,char)) then" not in old
    assert new.count("sourceCharacter,char)) then") == 1
    assert old != new and new.count("function HeroCombat.equip") == old.count("function HeroCombat.equip")
    server[SCRIPT] = {"$path": os.path.relpath(candidate, project.parent).replace(os.sep, "/")}
    data["name"] = "EGGRUMBLE_V3_GQ_MAGE_HEAL_LOS26_PRIVATE_NOT_RC"
    project.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads(receipt.read_text(encoding="utf-8"))
    assert manifest["script_count"] == 26
    assert manifest["source_sha256"][SCRIPT] == hashlib.sha256(old_source.read_bytes()).hexdigest()
    manifest["source_sha256"][SCRIPT] = hashlib.sha256(candidate.read_bytes()).hexdigest()
    manifest["mage_heal_los"] = {
        "status": "SOURCE_ONLY_NO_OFFICIAL_RC",
        "author_original_blob": "66e666418b7c23d41f87faa5d61eb6e2770a463e",
        "affected_scripts": [SCRIPT],
        "original_scripts_replaced_in_manifest": 1,
        "new_luau_script_count": 0,
        "rollback": "select original SevenRoleCombat path in #484 private composer",
    }
    receipt.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert sum(1 for v in server.values() if isinstance(v, dict) and "$path" in v) == 23
    print("MAGE_HEAL_ONLY_OVERLAY26_MANIFEST_PASS", SCRIPT)

if __name__ == "__main__":
    main()
