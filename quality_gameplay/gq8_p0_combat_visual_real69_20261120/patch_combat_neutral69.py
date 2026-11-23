#!/usr/bin/env python3
"""P0 source-exact repairs in existing REAL69 Combat + Swarm; never add a writer.

Authoritative combat defect: hitBotHeroes has parameter 'player', but line 401
used unbound 'p.UserId'.  Visual defect: default Humanoid names/health bars
crowd the owner's Studio horde scene.  This patch is *source-only*, not a
Studio / Android / FUN acceptance result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

COMBAT = "ServerScriptService/EGGRUMBLE_SevenRoleCombat"
SWARM = "ServerScriptService/EGGRUMBLE_SwarmCombat"
EXACT = {
    COMBAT: "c112b86984d7efe2daf24a9c11ad58c427c9916dab02e6565ac782beb5c81c75",
    SWARM: "3ca5b0ecfeced3dfdec204b0de6a9ae72c48c6793a65ec39d6b37e3ba431a6f1",
}
MARK_COMBAT = "GQ8_P0_COMBAT_BOT_USERID_SCOPE_20261120"
MARK_SWARM = "GQ8_P0_NEUTRAL_BILLBOARD_DISTANCE_20261120"
OLD_COMBAT = 'h:TakeDamage(InvulRuntime.filterDamage(h,damage*duel*mark,"PLAYER",p.UserId))'
NEW_COMBAT = ('-- ' + MARK_COMBAT + ': original hitBotHeroes parameter is player, never p.\n'
              '   h:TakeDamage(InvulRuntime.filterDamage(h,damage*duel*mark,"PLAYER",player.UserId))')
OLD_SWARM = 'h.MaxHealth=NEUTRAL_HEALTH;h.Health=NEUTRAL_HEALTH;h.BreakJointsOnDeath=false;h.Parent=m'
NEW_SWARM = ('-- ' + MARK_SWARM + ': hide repetitive internal HordeSoldier names and show nearby HP only.\n'
             ' h.NameDisplayDistance=0;h.HealthDisplayDistance=16\n '
             + OLD_SWARM)
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_P0_REAL69_" + why)


def patch_text(combat: str, swarm: str) -> tuple[str, str]:
    # One exactly identified existing combat function. Other p.UserId users
    # are deliberately untouched: some legitimately have local parameter p.
    first = combat.index("local function hitBotHeroes(")
    last = combat.index("\nend", first)
    function = combat[first:last]
    require("player:Player" in function and OLD_COMBAT in function,
            "BOT_FUNCTION_OR_SCOPE_DRIFT")
    require(combat.count(OLD_COMBAT) == 1 and MARK_COMBAT not in combat,
            "COMBAT_ANCHOR_DRIFT")
    require(swarm.count(OLD_SWARM) == 1 and MARK_SWARM not in swarm,
            "SWARM_ANCHOR_DRIFT")
    after_combat = combat.replace(OLD_COMBAT, NEW_COMBAT)
    after_swarm = swarm.replace(OLD_SWARM, NEW_SWARM)
    require(after_combat.count(MARK_COMBAT) == 1 and
            after_swarm.count(MARK_SWARM) == 1, "PATCH_MARKERS")
    require("h.NameDisplayDistance=0;h.HealthDisplayDistance=16" in after_swarm,
            "HP_VISIBILITY_NOT_BOUNDED")
    for forbidden in ("Instance.new(\"RemoteEvent\")", "DataStoreService",
                      "MarketplaceService"):
        require(forbidden not in NEW_COMBAT + NEW_SWARM,
                "FORBIDDEN_AUTHORITY")
    return after_combat, after_swarm


def selftest() -> None:
    old_combat = ('local function hitBotHeroes(session:any,player:Player)\n'
                  + OLD_COMBAT + '\nend')
    new_c, new_s = patch_text(old_combat, OLD_SWARM)
    require("player.UserId" in new_c and "HealthDisplayDistance=16" in new_s,
            "HAPPY_CASE")
    for corrupt_c, corrupt_s in [
        (old_combat.replace("player:Player", "p:Player"), OLD_SWARM),
        (old_combat.replace('p.UserId', 'player.UserId'), OLD_SWARM),
        (old_combat, OLD_SWARM.replace("h.Parent=m", "h.Parent=elsewhere")),
    ]:
        try:
            patch_text(corrupt_c, corrupt_s)
        except (ValueError, AssertionError):
            pass
        else:
            raise AssertionError("RED_NEGATIVE_MUTATION_DID_NOT_FAIL")
    print("GQ470_P0_COMBAT_SCOPE_AND_NEUTRAL_NAME_NEGATIVES_PASS")


def run(root: Path, head: str) -> None:
    before = project_scan(root, PROJECT)
    require(len(before) == 69 and set(EXACT).issubset(before),
            "SELECTED_69_ROUTES")
    require(all(before[r]["sha256"] == EXACT[r] and
                before[r]["class"] == "ModuleScript" for r in EXACT),
            "EXACT_SOURCE_PARENT")
    receipt_file = root / RECEIPT
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    require(receipt.get("selected_source_count") == 69 and
            len(receipt.get("source_hashes", {})) == 69 and
            all(receipt["source_hashes"].get(r) == x["sha256"]
                for r, x in before.items()), "OLD_RECEIPT_DRIFT")
    require(not (root / "off69_p0").exists(), "ROLLBACK_EXISTS")
    place = root / "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
    require(place.exists(), "PARENT_PLACE_MISSING")
    cpath, spath = (root / before[r]["path"] for r in (COMBAT, SWARM))
    combat, swarm = (p.read_text(encoding="utf-8") for p in (cpath, spath))
    patched_c, patched_s = patch_text(combat, swarm)
    off = root / "off69_p0"
    shutil.copytree(root / "sources", off / "sources")
    shutil.copy2(root / PROJECT, off / PROJECT)
    shutil.copy2(receipt_file, off / RECEIPT)
    shutil.copy2(place, root / "OFF69_PRE_GQ470_P0_EXACT.rbxlx")
    cpath.write_text(patched_c, encoding="utf-8")
    spath.write_text(patched_s, encoding="utf-8")
    after = project_scan(root, PROJECT)
    require(len(after) == 69 and set(after) == set(before),
            "ROUTE_NONLOSS")
    changed = {r for r in before if before[r]["sha256"] != after[r]["sha256"]}
    require(changed == set(EXACT), "ONLY_COMBAT_SWARM_CHANGED")
    require(all(before[r]["class"] == after[r]["class"] and
                before[r]["path"] == after[r]["path"] for r in before),
            "CLASS_PATH_NONLOSS")
    for route in EXACT:
        receipt["source_hashes"][route] = after[route]["sha256"]
    receipt["build_head"] = head
    receipt["gq470_p0_combat_neutral_visibility"] = {
        "scope": "Existing 69 selected Luau sources; Combat + Swarm only",
        "combat": MARK_COMBAT,
        "neutral": MARK_SWARM,
        "old_sha256": EXACT,
        "new_sha256": {r: after[r]["sha256"] for r in EXACT},
        "unrelated_source_bytes_unchanged": 67,
        "studio_solo": "NOT_TESTED",
        "studio_two_client": "NOT_TESTED",
        "android15min": "NOT_TESTED",
        "owner_accepted": False,
        "rollback": "off69_p0 + OFF69_PRE_GQ470_P0_EXACT.rbxlx",
    }
    receipt_file.write_text(json.dumps(receipt, ensure_ascii=False,
                                       sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    print("GQ470_P0_REAL69_COMBAT_SWARM_EXACT_TWO_SOURCE_PATCH_PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path)
    parser.add_argument("--head", default="CANDIDATE")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        selftest()
    else:
        require(args.base is not None, "BASE_MISSING")
        run(args.base, args.head)
