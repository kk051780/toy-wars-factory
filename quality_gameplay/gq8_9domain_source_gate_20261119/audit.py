#!/usr/bin/env python3
"""GQ8: cross-domain source selection audit. This is not an in-game test.
Exact source/route/class inventory + 9 domain SOURCE-PRESENCE matrix, fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DOMAINS = {
    "character": ("EGGRUMBLE_SevenRoleCombat",),
    "field": ("EGGRUMBLE_RealmBattleCore",),
    "combat": ("EGGRUMBLE_MusouFeverPolicy", "EGGRUMBLE_InvulRuntime"),
    "castle": ("EGGRUMBLE_CastleGuardianRuntime", "EGGRUMBLE_CastleSiegeBridge"),
    "neutral": ("EGGRUMBLE_SwarmCombat", "EGGRUMBLE_CurseConversionPolicy"),
    "item": ("EGGRUMBLE_FieldItemPickups",),
    "lobby": ("GQ805_LobbyGuildShop",),
    "ui": ("EGGRUMBLE_LobbyShopView", "EGGRUMBLE_MusouAuraClient"),
    "balance": ("EGGRUMBLE_MusouFeverPolicy", "EGGRUMBLE_InvulnerabilityPolicy"),
}
SINGLETONS = {
    "EGGRUMBLE_SevenRoleCombat", "EGGRUMBLE_SwarmCombat",
    "EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_RealmBattleCore",
}
FATAL_TOKENS = (
    "MarketplaceService:PromptProductPurchase(",
    "MarketplaceService:PromptGamePassPurchase(",
    "MarketplaceService.ProcessReceipt =",
)


def script_class(path: Path) -> str:
    s = path.name
    if s.endswith(".server.luau"):
        return "Script"
    if s.endswith(".client.luau"):
        return "LocalScript"
    if s.endswith(".luau"):
        return "ModuleScript"
    raise ValueError("RED_NON_LUAU_SOURCE_" + s)


def flatten(project: Path):
    data = json.loads(project.read_text(encoding="utf8"))
    result = {}
    def walk(node, route):
        if not isinstance(node, dict):
            raise ValueError("RED_INVALID_ROJO_NODE")
        if "$path" in node:
            if any(k not in ("$path", "$className") for k in node):
                raise ValueError("RED_MIXED_ROJO_SOURCE_NODE")
            raw = (project.parent / node["$path"]).resolve()
            # no traversal outside the candidate package
            if not raw.is_relative_to(project.parent.resolve()) or not raw.is_file():
                raise ValueError("RED_MISSING_OR_ESCAPING_SOURCE_" + "/".join(route))
            if route in result:
                raise ValueError("RED_DUPLICATE_ROUTE_" + "/".join(route))
            derived = script_class(raw)
            cls = node.get("$className", derived)
            if cls != derived:
                raise ValueError("RED_CLASS_ROUTE_MISMATCH_" + "/".join(route))
            result[route] = (raw, derived)
            return
        for key, value in node.items():
            if key.startswith("$"):
                continue
            walk(value, (*route, key))
    walk(data["tree"], ())
    return result


def audit(project: Path, receipt: Path, expected: int, strict: bool = True) -> dict:
    sources = flatten(project)
    if len(sources) != expected:
        raise ValueError("RED_SELECTED_SOURCE_COUNT")
    evidence = json.loads(receipt.read_text(encoding="utf8"))
    if evidence.get("new_selected_source_count", evidence.get("selected_script_count", evidence.get("selected_real55_count"))) != expected:
        raise ValueError("RED_RECEIPT_SOURCE_COUNT")
    rows = evidence.get("sources", [])
    records = {}
    for row in rows:
        route = tuple(row["route"].split("/"))
        if route in records:
            raise ValueError("RED_DUPLICATED_RECEIPT_ROUTE")
        records[route] = row
    if set(records) != set(sources):
        raise ValueError("RED_SOURCE_RECEIPT_SET_MISMATCH")
    by_name = {}
    full_text = {}
    for route, (path, klass) in sources.items():
        data = path.read_bytes()
        item = records[route]
        if (item.get("bytes") != len(data)
                or item.get("sha256") != hashlib.sha256(data).hexdigest()
                or item.get("class") != klass):
            raise ValueError("RED_SOURCE_CLASS_OR_HASH_" + "/".join(route))
        by_name.setdefault(route[-1], []).append(route)
        full_text[route] = data.decode("utf8")
    for name in SINGLETONS:
        if len(by_name.get(name, ())) != 1:
            raise ValueError("RED_MISSING_OR_DUPLICATE_SINGLETON_" + name)

    domains = {}
    for domain, names in DOMAINS.items():
        missing = [name for name in names if len(by_name.get(name, ())) != 1]
        domains[domain] = {"source_present": not missing, "missing": missing,
                           "evidence_level": "SOURCE_PRESENCE_ONLY"}
    calls = 0
    wrapped = 0
    for source in full_text.values():
        for line in source.splitlines():
            executable = line.split("--", 1)[0]
            calls += executable.count(":TakeDamage(")
            wrapped += executable.count(":TakeDamage(InvulRuntime.filterDamage(")
    # All previous 53/55 direct calls had inline pre-hit checks.
    if 49 <= expected < 65 and (calls != 13 or wrapped != 13):
        raise ValueError(f"RED_INVUL_DIRECT_DAMAGE_BYPASS_{wrapped}_OF_{calls}")
    # Actual formal REAL65 has twelve inline pre-hit guards and two
    # precomputed pre-hit guards, both inside the ONE original Combat owner.
    # Fail closed on any extra HP writer, missing guard or damage-site drift.
    if expected >= 65:
        if calls != 14 or wrapped != 12:
            raise ValueError(f"RED_REAL65_DAMAGE_SITE_DRIFT_{wrapped}_OF_{calls}")
        external = []
        for route, source in full_text.items():
            for index, line in enumerate(source.splitlines()):
                executable=line.split("--",1)[0].strip()
                if ":TakeDamage(" in executable and ":TakeDamage(InvulRuntime.filterDamage(" not in executable:
                    external.extend((route,index,executable) for _ in range(executable.count(":TakeDamage(")))
        expected_calls={
            'enemyHum:TakeDamage(originalAttackDamage)':
                'local originalAttackDamage=InvulRuntime.filterDamage(enemyHum,damage*duel*mark*musou,"PLAYER",p.UserId)',
            'atHum:TakeDamage(realDamage)':
                'local realDamage=InvulRuntime.filterDamage(atHum,amount,"PLAYER",enemyPlayer.UserId)',
        }
        owner=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
        if len(external)!=2 or any(route!=owner or call not in expected_calls for route,_,call in external):
            raise ValueError("RED_REAL65_PRECOMPUTED_DAMAGE_OWNER_OR_CALL")
        if {call for _,_,call in external}!=set(expected_calls):
            raise ValueError("RED_REAL65_MISSING_PRECOMPUTED_DAMAGE_SITE")
        combat=full_text[owner].splitlines()
        for _route,idx,call in external:
            # Require exact recipient, source, damage, actor and ordering.
            # Both observed sites have a guarded local within prior 9 lines.
            window="\n".join(combat[max(0,idx-9):idx])
            if expected_calls[call] not in window:
                raise ValueError("RED_REAL65_MISSING_PRECOMPUTED_INVUL_GUARD")
    if expected >= 53:
        shop = next((v for k, v in full_text.items()
                     if k[-1] == "GQ805_ShopKioskClient"), "")
        if not shop or "robuxEnabled=false" not in shop:
            raise ValueError("RED_READONLY_SHOP_CONTRACT")
    if expected >= 55:
        if len(by_name.get("GQ8_LobbySocialPlaza", ())) != 1:
            raise ValueError("RED_SOCIAL_SOURCE_MISSING")
        if len(by_name.get("GQ8_TradePolicy", ())) != 1:
            raise ValueError("RED_TRADE_POLICY_MISSING")
        trade = next(v for k, v in full_text.items() if k[-1] == "GQ8_TradePolicy")
        if any(token in trade for token in FATAL_TOKENS) or "requiresExistingStoreAtomicJournal" not in trade:
            raise ValueError("RED_TRADE_SETTLEMENT_UNSAFE")
    if strict and any(not v["source_present"] for v in domains.values()):
        missing = ",".join(k for k,v in domains.items() if not v["source_present"])
        raise ValueError("RED_NINE_DOMAIN_SOURCE_GAP_" + missing)
    return {
        "contract": "GQ8_9DOMAIN_ACTUAL_SOURCE_20261119",
        "source_count": expected,
        "verified_hash_class_routes": len(sources),
        "direct_damage_calls": calls,
        "prehit_wired_damage_calls": wrapped,
        "domains": domains,
        "source_coverage_count": sum(v["source_present"] for v in domains.values()),
        "domain_count": 9,
        "audit_performs_rc_adoption": False,
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "fun_art": "NO_GO",
        "warning": "SOURCE presence is not gameplay reachability or visual/fun acceptance",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--out", type=Path)
    p.add_argument("--no-strict", action="store_true")
    a = p.parse_args()
    result = audit(a.project, a.receipt, a.count, not a.no_strict)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                         encoding="utf8")
    print(f"GQ8_9DOMAIN_SOURCE_AUDIT_PASS {result['source_coverage_count']}/9 {a.count} scripts")
    print("WARN: NOT OFFICIAL RC; SOURCE-ONLY; STUDIO/ANDROID/FUN NOT TESTED")


if __name__ == "__main__":
    main()
