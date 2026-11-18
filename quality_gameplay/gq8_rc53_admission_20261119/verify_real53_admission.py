#!/usr/bin/env python3
"""Independent release-admission verifier for immutable Real53, not a replacement gameplay author.

This never publishes Roblox, modifies the formal RC or treats source QA as Studio acceptance.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

PINNED_PR_HEAD = "96ac3b4caa2f649f98c9e093c864c39555f3616a"
PINNED_PARENT_RUN = 44389905538
PINNED_PLACE_SIZE = 572030
PINNED_PLACE_SHA256 = "47b49a5d8ae758071af8eb5faf1ae8bd247d01f6dfe39557a502bd98dce15690"
FORMAL_BASE = "f77b4d4393d9e9b19b65566413432a7a9f13962b"

class GateError(ValueError):
    pass

def require(ok, marker):
    if not ok:
        raise GateError(marker)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def source_class(path):
    name = path.name
    if name.endswith(".server.luau") or name.endswith(".server.lua"):
        return "Script"
    if name.endswith(".client.luau") or name.endswith(".client.lua"):
        return "LocalScript"
    if name.endswith(".luau") or name.endswith(".lua"):
        return "ModuleScript"
    raise GateError("RED_UNSUPPORTED_SOURCE_SUFFIX:" + name)

def extract_paths(project):
    doc = json.loads(project.read_text(encoding="utf8"))
    root = project.parent.resolve()
    found = {}
    def walk(node, route):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            path = (root / node["$path"]).resolve()
            require(path.is_relative_to(root), "RED_SOURCE_PATH_TRAVERSAL")
            require(path.is_file(), "RED_MISSING_SOURCE:" + "/".join(route))
            require(route not in found, "RED_DUPLICATE_ROUTE")
            found[route] = (path, source_class(path))
            return
        for name, value in node.items():
            if not name.startswith("$"):
                walk(value, route + (name,))
    walk(doc["tree"], ())
    return found

def validate_receipt(r):
    require(r.get("schema") == "GQ8_REAL53_PRIVATE_MUSOU_INVUL_CURSE_READONLY_SHOP", "RED_RECEIPT_SCHEMA")
    for key, value in {"original49_sources_unchanged": 49,
                       "original44_unchanged_within49": 37,
                       "added_original_shop_sources": 4,
                       "selected_script_count": 53,
                       "actual_original_invul_prehit_routes": 13,
                       "parent49_immutable_success_run": PINNED_PARENT_RUN,
                       "current_intake_head": PINNED_PR_HEAD}.items():
        require(r.get(key) == value, "RED_RECEIPT_FIELD:" + key)
    require(r.get("transactions_enabled") is False, "RED_TRANSACTIONS_ENABLED")
    require(r.get("official_rc_adopted") is False, "RED_FALSE_FORMAL_ADOPTION")
    require(r.get("native49_53") == "PASS", "RED_NATIVE_EVIDENCE")
    require(r.get("rojo_source_class53") == "PASS", "RED_ROJO_EVIDENCE")
    require(r.get("off49") == "BYTE_IDENTICAL", "RED_OFF49_EVIDENCE")
    require(r.get("actual_private_place_bytes") == PINNED_PLACE_SIZE, "RED_RECEIPT_PLACE_SIZE")
    require(r.get("actual_private_place_sha256") == PINNED_PLACE_SHA256, "RED_RECEIPT_PLACE_SHA")
    sources = r.get("sources")
    require(isinstance(sources, list) and len(sources) == 53, "RED_RECEIPT_SOURCE_COUNT")
    routes = [x.get("route") for x in sources]
    require(len(set(routes)) == 53, "RED_RECEIPT_DUPLICATE_ROUTES")
    origin_counts = {}
    for item in sources:
        origin = item.get("origin")
        origin_counts[origin] = origin_counts.get(origin, 0) + 1
        require(re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")) is not None, "RED_RECEIPT_HASH")
    require(origin_counts == {"verified_exact_real49":49, "original_816":2, "original_808":2},
            "RED_UNTRUSTED_ORIGIN")
    return routes

def run(root, current_rc):
    root = root.resolve()
    require(current_rc == FORMAL_BASE, "RED_OFFICIAL_RC_MOVED_RECHECK_REQUIRED")
    project = root / "EGGRUMBLE_REAL53.project.json"
    receipt_path = root / "B_REAL53_INTAKE_RECEIPT.json"
    place = root / "EGGRUMBLE_REAL53.rbxlx"
    off = root / "OFF49.rbxlx"
    for path in (project, receipt_path, place, off):
        require(path.is_file(), "RED_MISSING_ARTIFACT:" + path.name)
    receipt = json.loads(receipt_path.read_text(encoding="utf8"))
    routes = validate_receipt(receipt)
    sources = extract_paths(project)
    require(len(sources) == 53, "RED_PROJECT_SOURCE_COUNT")
    require(set(routes) == {"/".join(x) for x in sources}, "RED_RECEIPT_PROJECT_ROUTE_MISMATCH")
    for item in receipt["sources"]:
        route = tuple(item["route"].split("/"))
        path, cls = sources[route]
        raw = path.read_bytes()
        require(sha(raw) == item["sha256"], "RED_SOURCE_HASH:" + item["route"])
        require(len(raw) == item["bytes"], "RED_SOURCE_SIZE:" + item["route"])
        require(cls == item["class"], "RED_SOURCE_CLASS:" + item["route"])
    require(place.stat().st_size == PINNED_PLACE_SIZE and sha(place.read_bytes()) == PINNED_PLACE_SHA256,
            "RED_PLACE_HASH_OR_SIZE")
    require(off.stat().st_size > 0, "RED_ROLLBACK_OFF49_EMPTY")
    byname = {}
    for route, (path, cls) in sources.items():
        byname.setdefault(route[-1], []).append(path)
    for name in ("EGGRUMBLE_SevenRoleCombat", "EGGRUMBLE_SwarmCombat",
                 "EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_InvulRuntime",
                 "EGGRUMBLE_MusouFeverPolicy", "EGGRUMBLE_LobbyShopCatalog",
                 "EGGRUMBLE_LobbyShopView"):
        require(len(byname.get(name, [])) == 1, "RED_SINGLE_OWNER_OR_SHOP_MISSING:" + name)
    hits = sum(line.split("--",1)[0].count(":TakeDamage(InvulRuntime.filterDamage(")
               for paths in byname.values() for path in paths
               for line in path.read_text(encoding="utf8").splitlines())
    require(hits == 13, "RED_LOST_INVUL_DAMAGE_ROUTES")
    # Source-presence signals are *not* engine or fun acceptance.
    signs = {
      "character": r"SevenRoleCombat",
      "field": r"RealmBattleCore|LandSeaSky",
      "battle": r"MusouFeverPolicy|InvulRuntime",
      "castle": r"LobbyCastleModesPreview",
      "neutral": r"SwarmCombat",
      "item": r"Item|Pickup|Loot|Chest|Consumable",
      "lobby": r"LobbyGuildShop|LobbyCastleModesPreview",
      "ui": r"RealmBattleControls|MusouAuraController|ShopView",
      "balance": r"PassiveRegenPolicy|NaturalRegen|ElementalAffinity",
    }
    names = sorted(byname)
    pillars = {k: {"source_signal": bool(any(re.search(p, x, re.I) for x in names)),
                    "verified_playability": False}
               for k,p in signs.items()}
    for critical in ("character", "field", "battle", "castle", "neutral", "lobby", "ui"):
        require(pillars[critical]["source_signal"], "RED_MISSING_DOMAIN_SOURCE:" + critical)
    report = {
      "schema": "GQ8_REAL53_RC_ADMISSION_REHEARSAL_V1",
      "feature_id": "GQ8_REAL53_FORMAL_ADMISSION_GUARD_20261119",
      "expected_formal_rc": FORMAL_BASE,
      "observed_formal_rc": current_rc,
      "selected_upstream_pr": 826,
      "upstream_exact_head": PINNED_PR_HEAD,
      "upstream_green_run": 44390806767,
      "selected_source_count": 53,
      "source_and_class_verified": 53,
      "combat_singleton_count": 1,
      "neutral_singleton_count": 1,
      "invul_prehit_routes": hits,
      "candidate_place_bytes": place.stat().st_size,
      "candidate_place_sha256": sha(place.read_bytes()),
      "rollback_off49_bytes": off.stat().st_size,
      "pillar_signals": pillars,
      "official_rc_write_performed": False,
      "official_rc_integrated": False,
      "studio_2client": "NOT_TESTED",
      "android15": "NOT_TESTED",
      "fun_art": "NO_GO",
      "transactions_enabled": False,
      "required_followup": "B authenticated writer, source profile adoption, non-force expected-SHA CAS, new official same-HEAD native/Rojo/OFF and readback, Studio/mobile/fun",
    }
    (root / "RC53_ADMISSION_REHEARSAL_RECEIPT.json").write_text(
      json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print("GQ8_REAL53_53_SOURCE_ADMISSION_REHEARSAL_PASS")
    print(json.dumps({"place_bytes":report["candidate_place_bytes"],
                      "signals":{k:v["source_signal"] for k,v in pillars.items()}},sort_keys=True))
    return report

def negative_probes(root):
    good = json.loads((root/"B_REAL53_INTAKE_RECEIPT.json").read_text(encoding="utf8"))
    def must_reject(change):
        bad = copy.deepcopy(good)
        change(bad)
        try:
            validate_receipt(bad)
        except GateError:
            return
        raise GateError("RED_NEGATIVE_MUTATION_NOT_REJECTED")
    must_reject(lambda x: x.update(transactions_enabled=True))
    must_reject(lambda x: x["sources"][0].update(sha256="0"*63))
    must_reject(lambda x: x.update(current_intake_head="0"*40))
    must_reject(lambda x: x["sources"].pop())
    print("GQ8_REAL53_FOUR_ADVERSARIAL_RECEIPT_MUTANTS_REJECTED")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-root",type=Path,required=True)
    p.add_argument("--current-rc",required=True)
    a=p.parse_args()
    run(a.artifact_root,a.current_rc)
    negative_probes(a.artifact_root)

if __name__ == "__main__":
    main()
