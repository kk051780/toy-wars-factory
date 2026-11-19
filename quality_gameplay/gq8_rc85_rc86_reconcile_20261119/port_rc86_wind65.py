#!/usr/bin/env python3
"""RC86 FB029 wind-run behavior port to existing single REAL65 HeroCombat.

Does NOT import an RC86 Game, HUD, Remote, Shop or second Combat authority.
Input is the existing formal 65-source composer after current Host/Realm repairs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

FEATURE = "RC85_RC86_FB029_ASSASSIN_WIND_SINGLE_COMBAT_PORT_20261119"
ROUTE = "ServerScriptService/EGGRUMBLE_SevenRoleCombat"
ORIGINAL_RC86_PROOF_RUN = 43754858996
ORIGINAL_RC86_PLACE_SHA256 = "d67f9f68912cb67de0e184844d57649fbe50e5b70ab30cffbe3ee320e6a15cd8"
ORIGINAL_RC86_WIND_POLICY_GITBLOB = "d66efccbf90028627cd65aa0fb33173506819c11"
OLD = '''   if owner.heldEggs==0 and safeMove(session,char,root,25) then
    p:SetAttribute("EGGRUMBLE_StealthUntil",now+3)
   end'''
NEW = '''   if owner.heldEggs==0 and safeMove(session,char,root,25) then
    p:SetAttribute("EGGRUMBLE_StealthUntil",now+3)
    -- RC86_FB029_WIND_SINGLE_COMBAT_PORT: reuse Ninja B, not another Game or Tool.
    -- Original FB029 constants: 18s cooldown, 2.5s burst, speed 27.
    -- Existing V3 safeMove validates walls, floor, arena; objective cargo cannot dash.
    if h.SeatPart==nil and h.FloorMaterial~=Enum.Material.Air then
     local windKey=tostring(session)..":NINJA:RC86_WIND"
     if now-(perPlayer[windKey] or -10000)>=18 then
      perPlayer[windKey]=now
      local oldSpeed=h.WalkSpeed
      local windSpeed=math.max(oldSpeed,27)
      local serial=(p:GetAttribute("EGGRUMBLE_RC86WindSerial") or 0)+1
      p:SetAttribute("EGGRUMBLE_RC86WindSerial",serial)
      p:SetAttribute("EGGRUMBLE_RC86WindUntil",now+2.5)
      h.WalkSpeed=windSpeed
      task.spawn(function()
       for _=1,10 do
        task.wait(.25)
        if p.Character~=char or h.Health<=0
         or not p.Parent or session.rules.phase~="ACTIVE"
         or not owner.alive or p:GetAttribute("EGGRUMBLE_Role")~="NINJA"
         or owner.heldEggs>0 or h.SeatPart~=nil then break end
       end
       -- Never stomp a newer slow/skill, a new round or a replacement avatar.
       if p.Character==char and p:GetAttribute("EGGRUMBLE_RC86WindSerial")==serial then
        if h.Parent and h.WalkSpeed==windSpeed then h.WalkSpeed=oldSpeed end
        p:SetAttribute("EGGRUMBLE_RC86WindUntil",0)
       end
      end)
     end
    end
   end'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch(source: str) -> str:
    if source.count(OLD) != 1:
        raise ValueError("RED_RC86_NINJA_WIND_ORIGINAL_SOURCE_DRIFT")
    if "RC86_FB029_WIND_SINGLE_COMBAT_PORT" in source:
        raise ValueError("RED_RC86_WIND_DOUBLE_PATCH")
    required = [
        'NINJA={name="暗殺者"',
        'if role=="NINJA" then',
        'local function safeMove(session:any,char:Model,root:BasePart,amount:number):boolean',
        'if session.swarm then count+=session.swarm.damageFromPlayer',
        'local perPlayer=lastByPlayer[p.UserId]',
    ]
    for marker in required:
        if source.count(marker) != 1:
            raise ValueError("RED_RC86_WIND_MISSING_OR_MULTIPLE_AUTHORITY_" + marker[:28])
    result = source.replace(OLD, NEW, 1)
    if result.count("RC86_FB029_WIND_SINGLE_COMBAT_PORT") != 1:
        raise ValueError("RED_RC86_WIND_NOT_INSTALLED")
    if result.replace(NEW, OLD, 1) != source:
        raise ValueError("RED_RC86_WIND_UNRELATED_GAME_SOURCE_MUTATION")
    for token in ("RemoteEvent", "ProcessReceipt", "DataStoreService"):
        if result.count(token) != source.count(token):
            raise ValueError("RED_RC86_WIND_NEW_REMOTE_STORE_OWNER")
    return result


def self_test() -> None:
    src = '\n'.join([
        'NINJA={name="暗殺者"',
        'if role=="NINJA" then',
        'local function safeMove(session:any,char:Model,root:BasePart,amount:number):boolean',
        'if session.swarm then count+=session.swarm.damageFromPlayer',
        'local perPlayer=lastByPlayer[p.UserId]',
        OLD, 'return true',
    ])
    good = patch(src)
    assert "now-(perPlayer[windKey] or -10000)>=18" in good
    assert "p:SetAttribute(\"EGGRUMBLE_RC86WindUntil\",now+2.5)" in good
    assert "h.WalkSpeed=windSpeed" in good
    assert good.replace(NEW, OLD, 1) == src
    for bad in (
        src.replace("safeMove(session,char,root,25)", "safeMove(session,char,root,100)"),
        src.replace('NINJA={name="暗殺者"', 'NINJA={name="忍者"'),
        src + "\n" + OLD,
        good,
    ):
        try:
            patch(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_RC86_WIND_MUTANT_ACCEPTED")
    print("RC86_WIND_NONLOSS_SOURCE_NEGATIVE_MUTATIONS_PASS")


def apply(project_path: Path, receipt_path: Path) -> None:
    project = json.loads(project_path.read_text(encoding="utf8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf8"))
    if (project.get("name") != "EGGRUMBLE_REAL65_PRIVATE_STUDIO" or
        len(receipt.get("sources", [])) != 65 or
        receipt.get("source_count", receipt.get("new_selected_source_count")) != 65):
        raise ValueError("RED_RC86_WIND_FORMAL_REAL65_PROFILE_DRIFT")
    if not receipt.get("late_host_world_watch", {}).get("no_20s_permanent_disarm"):
        raise ValueError("RED_RC86_WIND_MISSING_NEWEST_REAL65_HOST_FIX")
    if "legacy_rc86_wind" in receipt:
        raise ValueError("RED_RC86_WIND_RECEIPT_DOUBLE_PORT")
    rows = {row["route"]: row for row in receipt["sources"]}
    if len(rows) != 65 or ROUTE not in rows or rows[ROUTE]["class"] != "ModuleScript":
        raise ValueError("RED_RC86_WIND_ROUTE_OR_OWNER")
    chosen = None
    for route, row in rows.items():
        node = project["tree"]
        for segment in route.split("/"):
            node = node[segment]
        path = project_path.parent / node["$path"]
        if not path.is_file():
            raise ValueError("RED_RC86_MISSING_ROUTE_" + route)
        data = path.read_bytes()
        if len(data) != row["bytes"] or digest(data) != row["sha256"]:
            raise ValueError("RED_RC86_WIND_ORIGINAL_RECEIPT_HASH_" + route)
        if route == ROUTE:
            chosen = (path, data)
    assert chosen
    path, original = chosen
    new = patch(original.decode("utf8")).encode("utf8")
    assert digest(new) != digest(original)
    path.write_bytes(new)
    rows[ROUTE]["bytes"] = len(new)
    rows[ROUTE]["sha256"] = digest(new)
    receipt["legacy_rc86_wind"] = {
        "feature_id": FEATURE,
        "original_rc86_run": ORIGINAL_RC86_PROOF_RUN,
        "original_rc86_place_sha256": ORIGINAL_RC86_PLACE_SHA256,
        "original_rc86_wind_policy_gitblob": ORIGINAL_RC86_WIND_POLICY_GITBLOB,
        "adopted_behavior": "NINJA B bounded 18s cooldown, 2.5s speed27 with existing dash, single Combat owner",
        "original_65_source_count": 65,
        "changed_existing_source": ROUTE,
        "unchanged_other_sources": 64,
        "new_script_count": 0,
        "new_remote_count": 0,
        "new_damage_owner_count": 0,
        "rc85_undead_squad": "CURRENT_V3_HAS_OWN_3_SUMMONED_SERVANTS; EXACT_RC85_BEHAVIOR_RECONCILIATION_PENDING",
        "rc86_stage_loot": "CURRENT_V3_HAS_OWN_ITEMS_AND_SERVER_LOS; FULL_ITEM_VARIANT_RECONCILIATION_PENDING",
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "fun": "NO_GO",
        "rollback": "remove only this patch; keep previous formal REAL65 and byte-exact OFF63",
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf8")
    for route, row in rows.items():
        node = project["tree"]
        for segment in route.split("/"):
            node = node[segment]
        source = (project_path.parent / node["$path"]).read_bytes()
        if len(source) != row["bytes"] or digest(source) != row["sha256"]:
            raise ValueError("RED_RC86_WIND_FINAL_RECEIPT_HASH_" + route)
    print("RC86_FB029_ACTUAL_REAL65_NINJA_WIND_PORT_SOURCE_LOCK_PASS 65 64_UNCHANGED")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--project", type=Path)
    p.add_argument("--receipt", type=Path)
    a = p.parse_args()
    if a.self_test:
        self_test()
    else:
        if not a.project or not a.receipt:
            p.error("--project and --receipt required")
        apply(a.project, a.receipt)
