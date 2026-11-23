#!/usr/bin/env python3
"""Exact 44-source incoming-damage inventory for owner invulnerability #822.

Read-only QA. This NEVER applies invulnerability, creates a second HP writer,
or claims that an existing ForceField proves true zero damage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FEATURE = "GQ822_ACTUAL44_DIRECT_DAMAGE_ROUTE_COVERAGE_20261119"
SUPPORTED_SOURCE_COUNTS = (44, 48)
EXTRA_REAL48_MODULES = {
 "EGGRUMBLE_LobbyShopView.luau",
 "EGGRUMBLE_LobbyShopCatalog.luau",
 "GQ805_LobbyGuildShop.server.luau",
 "GQ805_ShopKioskClient.client.luau",
}

# The original 44-source private project is authority. The classes below refer
# to the victim, not the attacker. MIXED paths can also hit real players.
EXPECTED = {
 "EGGRUMBLE_SevenRoleCombat.luau": (
  ("h:TakeDamage(damage*duel*mark)", "BOT"),
  ("enemyHum:TakeDamage(damage*duel*mark)", "HUMAN"),
  ("h:TakeDamage(tick)", "MIXED"),
 ),
 "EGGRUMBLE_BotActors.luau": (
  ("nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)", "HUMAN"),
  ("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)", "BOT"),
 ),
 "EGGRUMBLE_SwarmCombat.luau": (
  ("h:TakeDamage(effectiveDamage)", "NEUTRAL"),
  ("candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)", "HUMAN"),
 ),
 "EGGRUMBLE_NeutralStoneGiant.luau": (
  ("h:TakeDamage(28)", "HUMAN"),
 ),
 "EGGRUMBLE_LobbyCastleModesPreview.server.luau": (
  ("closest.hum:TakeDamage(Policy.CONFIG[kind].damage)", "MIXED"),
 ),
 "EGGRUMBLE_RealmBattleCore.server.luau": (
  ("pilotHumanoid:TakeDamage(18)", "HUMAN"),
  ("h:TakeDamage(6)", "HUMAN"),
 ),
 "EGGRUMBLE_CastleGuardianRuntime.luau": (
  ("foe.hum:TakeDamage(c.damage)", "MIXED"),
  ("hum:TakeDamage(math.min(damage,45))", "MIXED"),
 ),
}

def code_lines(source: str):
    # This inventory targets direct calls, not strings, comments, indirect
    # callbacks, non-HP match elimination, or other CC pathways.
    for i, line in enumerate(source.splitlines(), 1):
        code = line.split("--", 1)[0]
        if ":TakeDamage(" in code:
            yield i, code.strip()

def scan(files: dict[str, str], required_count=None):
    if len(files) not in SUPPORTED_SOURCE_COUNTS or (required_count and len(files)!=required_count):
        raise ValueError("RED_NOT_ORIGINAL_REAL44_OR_REAL48_LUAU_COUNT")
    if len(files)==48 and not EXTRA_REAL48_MODULES.issubset(files):
        raise ValueError("RED_REAL48_SHOP_ADDITIONS_MISSING")
    expected_names = set(EXPECTED)
    if not expected_names.issubset(files):
        raise ValueError("RED_MISSING_EXPECTED_DAMAGE_OWNER")
    known = set()
    routes = []
    for name, patterns in EXPECTED.items():
        source = files[name]
        for exact, victim in patterns:
            found = [(i, line) for i, line in code_lines(source) if exact in line]
            if len(found) != 1:
                raise ValueError("RED_CHANGED_OR_DUPLICATED_DAMAGE_" + name + "/" + exact)
            i, line = found[0]
            if (name, i) in known:
                raise ValueError("RED_TWO_DAMAGE_RECEIPTS_SAME_LINE")
            known.add((name, i))
            routes.append({"source": name, "line": i, "call": exact,
                           "victim": victim, "human_risk": victim in ("HUMAN", "MIXED")})
    actual = {(name, i) for name, source in files.items()
              for i, _ in code_lines(source)}
    if actual != known:
        raise ValueError("RED_UNREGISTERED_OR_MISSING_DIRECT_DAMAGE_" + repr(sorted(actual ^ known)))
    return sorted(routes, key=lambda x: (x["source"], x["line"]))

def load_files(root: Path, required_count: int):
    root = root.resolve(strict=True)
    found = {}
    for p in root.rglob("*.luau"):
        if p.name in found:
            raise ValueError("RED_DUPLICATE_SOURCE_BASENAME_" + p.name)
        found[p.name] = p.read_text(encoding="utf-8")
    if len(found) != required_count or required_count not in SUPPORTED_SOURCE_COUNTS:
        raise ValueError("RED_EXPECTED_44_OR_48_SOURCE_DIRECTORY_NOT_EXACT")
    return found

def selftest(original: dict[str, str]):
    scan(original)
    fname = "EGGRUMBLE_SevenRoleCombat.luau"
    base = original[fname]
    first = "enemyHum:TakeDamage(damage*duel*mark)"
    cases = [
      base.replace(first, first + "\n    " + first, 1),
      base.replace(first, "enemyHum.Health=0", 1),
      base + "\nlocal shadow=humanoid:TakeDamage(999)\n",
    ]
    for changed in cases:
        data = dict(original)
        data[fname] = changed
        try:
            scan(data)
            raise AssertionError("RED_NEGATIVE_MUTANT_ACCEPTED")
        except ValueError as e:
            if not str(e).startswith("RED_"):
                raise
    data = dict(original)
    data.pop(fname)
    try:
        scan(data)
        raise AssertionError("RED_MISSING_REAL_OWNER_ACCEPTED")
    except ValueError as e:
        if not str(e).startswith("RED_"):
            raise
    print("GQ822_REAL44_DIRECT_DAMAGE_MUTATION_REJECT_4_OF_4_PASS")

def build(root: Path, out: Path, source_count: int):
    files = load_files(root, source_count)
    routes = scan(files, source_count)
    selftest(files)
    human = sum(x["human_risk"] for x in routes)
    # Explicit NO_GO: inventory is not the damage-bridge. An actual live
    # policy grant, same-match gate and zero-damage real engine tests are needed.
    report = {
      "feature_id": FEATURE,
      "source_profile": "original_verified_private_REAL"+str(source_count),
      "real48_readonly_shop_present": source_count==48,
      "source_count": len(files),
      "direct_humanoid_damage_sites": len(routes),
      "human_or_mixed_target_sites_requiring_bridge_review": human,
      "already_live_invulnerability_policy": False,
      "actual_complete_invulnerability_damage_zero": False,
      "status": "INVUL_DAMAGE_BRIDGE_NOT_WIRED",
      "missing_scope": ["direct_damage_bridge", "CC_and_knockback_bridge",
                        "DOT_and_weather_crossroads", "role_skill_activation",
                        "item_and_weapon_guard_activation", "Studio_2client_android_FUN"],
      "disclaimer": "Direct Humanoid:TakeDamage source scan ONLY; not all conceivable HP/CC or match reset paths",
      "source_sha256": {
        name: hashlib.sha256(data.encode("utf-8")).hexdigest()
        for name, data in sorted(files.items())
      },
      "routes": routes,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GQ822_ACTUAL_LATEST_REAL44_OR_48_DAMAGE_PATHS_INVENTORIED",
          len(files), len(routes), human, "REAL_IMMUNITY_NOT_WIRED")
    return report

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", required=True, type=Path)
    p.add_argument("--source-count", required=True, type=int, choices=SUPPORTED_SOURCE_COUNTS)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--require-wired", action="store_true")
    args = p.parse_args()
    report = build(args.source_root, args.out, args.source_count)
    if args.require_wired or report["already_live_invulnerability_policy"]:
        raise SystemExit("RED_INVULNERABILITY_UNPROVEN_IN_REAL44")
if __name__ == "__main__":
    main()
