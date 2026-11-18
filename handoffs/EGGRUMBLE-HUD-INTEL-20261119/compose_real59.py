#!/usr/bin/env python3
"""Rebase HUD/Fog to actual same-head canonical Real55, preserving every real original."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from compose_real40 import ADDITIONS, PREFIX, contents, project_for, digest

CANONICAL_SHA="a6020867fac80fa3b2ca47478625873fc6f3678e"
def run(place:Path,receipt:Path,out:Path):
    r=json.loads(receipt.read_text(encoding="utf8"))
    assert r.get("selected_official_branch_sha")==CANONICAL_SHA,"RED_WRONG_REAL55_OFFICIAL_HEAD"
    assert r.get("official_rc_adopted") is True, "RED_NOT_OFFICIAL_REAL55"
    assert r.get("source_profile")=="eggrumble_v3_real55","RED_WRONG_PROFILE"
    assert r.get("private_place_sha256")==digest(place),"RED_REAL55_PLACE_DRIFT"
    original,classes=contents(ET.parse(place).getroot())
    assert len(original)==55,("RED_REAL55_COUNT",len(original))
    assert ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview") in original
    assert ("ServerScriptService","EGGRUMBLE_SwarmCombat") in original
    combat=original[("ServerScriptService","EGGRUMBLE_SevenRoleCombat")][1]
    swarm=original[("ServerScriptService","EGGRUMBLE_SwarmCombat")][1]
    invul=original[("ServerScriptService","EGGRUMBLE_InvulRuntime")][1]
    client=(PREFIX/"EGGRUMBLE_HudIntelRuntime.client.luau").read_text(encoding="utf8")
    assert combat.count('musouTool.Name="EGGRUMBLE_MUSOU_AWAKEN"')==1, "RED_MUSOU_TOOL_ID_CHANGED_IN_REAL55"
    assert 'musouTool.Activated:Connect(' in combat, "RED_MUSOU_TOOL_SERVER_ACTION_MISSING"
    assert invul.count('tool.Name="迎撃覚醒"')==1, "RED_V2_INVUL_TOOL_ID_CHANGED_IN_REAL55"
    assert 'table.insert(r.connections,tool.Activated:Connect(' in invul, "RED_V2_INVUL_TOOL_ACTIVATION_MISSING"
    assert 'SetAttribute("EGGRUMBLE_MusouReadyIn",' in swarm, "RED_MUSOU_READINESS_REPLICATION_MISSING"
    assert 'SetAttribute("EGGRUMBLE_MusouPhase",' in swarm, "RED_MUSOU_PHASE_REPLICATION_MISSING"
    assert 'SetAttribute("EGGRUMBLE_InvulPhase",' in invul, "RED_V2_INVUL_PHASE_REPLICATION_MISSING"
    assert 'ownedToolByName("EGGRUMBLE_MUSOU_AWAKEN")' in client, "RED_CLIENT_MUSOU_TARGET_MISMATCH"
    assert 'ownedToolByName("迎撃覚醒")' in client, "RED_CLIENT_INVUL_TARGET_MISMATCH"
    assert 'EGGRUMBLE_MusouReadyIn' in client and 'EGGRUMBLE_InvulPhase' in client, "RED_CLIENT_REAL_POWER_STATE_MISMATCH"
    print("GQ828_REAL55_ACTUAL_MUSOU_INVUL_TOOL_NAMES_PHASE_WIRING_VERIFIED")
    assert not out.exists(),"RED_REFUSE_OVERWRITE"
    out.mkdir(parents=True)
    off=out/"off55";off.mkdir()
    offProject,offIndex=project_for(original,classes,off,"GQ828_OFF55")
    combined=dict(original)
    for route,(cls,filename) in ADDITIONS.items():
        key=tuple(route.split("/"))
        assert key not in combined,("RED_DUPLICATE_SOURCE",route)
        combined[key]=(cls,(PREFIX/filename).read_text(encoding="utf8"))
        classes[key]=cls
        for i in range(1,len(key)):
            prefix=key[:i]
            classes.setdefault(prefix,"Folder" if len(prefix)>1 else prefix[0])
    assert len(combined)==59
    for key,item in original.items():
        assert combined[key]==item,("RED_ORIGINAL55_OVERWRITTEN",key)
    assert len({key[-1] for key in combined})==59
    on=out/"on59";on.mkdir()
    onProject,onIndex=project_for(combined,classes,on,"GQ828_REAL59_HUD_MAP")
    m={
      "feature":"GQ8_HUD_INTEL_FOG_20261119",
      "official_rc_head":CANONICAL_SHA,
      "baseline_profile":"eggrumble_v3_real55",
      "baseline_place_sha256":digest(place),
      "baseline_real55_source_count":55,
      "candidate_real59_source_count":59,
      "baseline55_exact_sources_unchanged":True,
      "new_routes":list(ADDITIONS),
      "on_sources":onIndex,"off_sources":offIndex,
      "on_project":str(onProject),"off_project":str(offProject),
      "actual_native":"PENDING","actual_rojo":"PENDING","off55":"PENDING",
      "official_rc_adopted":False,"roblox_published":False,
      "real_studio_2client":"NOT_TESTED","android_15_min":"NOT_TESTED",
      "fun":"NOT_TESTED","spending_enabled":False,
      "new_remote":"EGGRUMBLE_MapIntelUpdate_V1 server send-only",
      "next":"Scoped authenticated writer must CAS source-selected 59 onto latest formal RC",
      "rollback":"EXACT_REAL55_OFF55_FROM_ARTIFACT",
    }
    (out/"GQ828_REAL59_RECEIPT.json").write_text(
        json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("GQ828_REAL59_EXISTING55_BYTE_EXACT_PRESERVED_PASS",digest(place))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--place",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    run(a.place,a.receipt,a.out)
