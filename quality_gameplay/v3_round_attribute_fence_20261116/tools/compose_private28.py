#!/usr/bin/env python3
"""Add ONLY the original neutral combo round-exit addon to #484's actual 26-source game.
Read-only source composition, no Game/Remote/Score/AI/ART/ITEM rewrite.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

ADDONS = {
    "EGGRUMBLE_RoundAttributeFence": "EGGRUMBLE_RoundAttributeFence.luau",
    "EGGRUMBLE_RoundAttributeFenceServer": "EGGRUMBLE_RoundAttributeFence.server.luau",
}

def mapped(project, base):
    out = {}
    def walk(node, path=()):
        for name, item in node.items():
            if name.startswith("$") or not isinstance(item, dict):
                continue
            loc = path + (name,)
            if "$path" in item:
                assert set(item) == {"$path"}, ("INVALID_SCRIPT_SPEC", name)
                file = (base / item["$path"]).resolve(strict=True)
                assert loc not in out, ("DUPLICATE_SCRIPT", loc)
                out[loc] = file
            else:
                walk(item, loc)
    walk(project["tree"])
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base26", type=Path, required=True)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    source_project = args.base26.resolve(strict=True)
    target = args.out.resolve()
    assert target.parent.is_dir() and target != source_project
    addon_root = args.root.resolve(strict=True)
    src = json.loads(source_project.read_text(encoding="utf-8"))
    originals = mapped(src, source_project.parent)
    assert len(originals) == 26 and len(set(originals.values())) == 26
    server = src["tree"]["ServerScriptService"]
    assert "EGGRUMBLE_LobbyCastleModesPreview" in server
    assert "EGGRUMBLE_CastleMatchRules" in server
    assert "EGGRUMBLE_ScoreBalance" in server
    assert "EGGRUMBLE_HeroSilhouetteArt" in server
    assert "EGGRUMBLE_RoundAttributeFence" not in server
    assert "EGGRUMBLE_RoundAttributeFenceServer" not in server
    # Strictly two added sources. Existing 26 retain their paths and SHA bytes.
    for name, file in ADDONS.items():
        p = (addon_root / file).resolve(strict=True)
        server[name] = {"$path": os.path.relpath(p, target.parent).replace(os.sep, "/")}
    src["name"] = "EGGRUMBLE_V3_GQ_COMBO_ONLY_ART_SCORE28_PRIVATE_NOT_RC"
    target.write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    after = mapped(src, target.parent)
    assert len(after) == 28 and len(set(after.values())) == 28
    for loc, original_file in originals.items():
        assert loc in after and after[loc] == original_file, ("ORIGINAL_REMAP", loc)
    for name, file in ADDONS.items():
        assert after[("ServerScriptService", name)] == (addon_root / file).resolve(strict=True)
    assert len([k for k in after if k[0] == "ServerScriptService"]) == 25
    assert len([k for k in after if k[0] == "StarterPlayer"]) == 3
    receipt = {
        "release": "PRIVATE_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "base": "PR484 original 26-source composer / original PR482, PR485, PR487",
        "original_count": 26, "added_count": 2, "mapped_sources": len(after),
        "changed_original_source_paths": 0, "new_server_game": 0, "new_remotes": 0,
        "owner": "PR512 COMBO ONLY", "boss_credit_owner": "PR514",
        "source_sha256": {"/".join(loc): hashlib.sha256(path.read_bytes()).hexdigest()
                          for loc, path in sorted(after.items())},
        "studio_play": "NOT_TESTED", "android": "NOT_TESTED", "owner_fun": "NO_GO",
        "official_rc_integrated": False,
    }
    (target.parent / "GQ_COMBO28_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GQ_COMBO_28_SOURCE_MAP_PASS; ORIGINAL_26_PATHS_BYTE_SAME")

if __name__ == "__main__":
    main()
