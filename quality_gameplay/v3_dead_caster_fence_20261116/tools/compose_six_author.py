#!/usr/bin/env python3
"""Source-select only: #529 four Combat owners + #530 dead guard + #535
human membership + #531 one Host/member fence + #484 genuine AI BotActors.

Private 22-source Rojo, reversible #530 ON/OFF, no original author/RC writes.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from compose_five_author import (
    ORIGINAL_529_FOUR_SHA256, REPLACEMENT, ENTRY,
    apply_to_combined, four_author_module, sha256,
)

ROOT=Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")
MEMBER=Path("_gq_member/quality_gameplay/v3_human_combat_membership_20261116/compose.py")
HOST=Path("_gq_host/quality_gameplay/v3_bot_human_match_membership_20261116/compose.py")
AI=Path("_gq_ai")/ROOT/"EGGRUMBLE_BotActors.luau"
MEMBER_HEAD="6846e9d55d07f0204748bbb8f46eef08f46c1b04"
HOST_HEAD="e78bff41e70564d0b26578e3c3a85f4698e6110e"
AI_HEAD="6b52eaf1f2725496277998fe0c5532b7a8fcaab5"
MEMBER_BLOB="2ec2ee85229d9bf7c9e66bfb2d04ab5390f6c8ad"
HOST_BLOB="7ea28c922debfa25e64a93401a643a9f1babd932"
ORIGINAL_PROJECT_BLOB="1d3e5bdc9ac2ac3fb6e70110ff3c6636d70fc714"
COMBAT="EGGRUMBLE_SevenRoleCombat"
HOST_SCRIPT="EGGRUMBLE_LobbyCastleModesPreview"
BOT_SCRIPT="EGGRUMBLE_BotActors"

def import_author(path:Path,label:str,blob:str):
    four=four_author_module()
    if four.git_blob(path.read_bytes()) != blob:
        raise ValueError("RED_"+label+"_SOURCE_BLOB_DRIFT")
    spec=importlib.util.spec_from_file_location(label,path.resolve(strict=True))
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def source_union(enabled:bool):
    four=four_author_module()
    member=import_author(MEMBER,"current_human_535",MEMBER_BLOB)
    base,heads=four.build_union()
    if sha256(base)!=ORIGINAL_529_FOUR_SHA256:
        raise ValueError("RED_529_AUTHOR_CHANGED")
    five=apply_to_combined(base)
    combined=member.patch(five if enabled else base)
    if member.undo(combined)!=(five if enabled else base):
        raise ValueError("RED_535_ORIGINAL_ROLLBACK_FAILED")
    if combined.count("currentHumanMember(session,")!=4:
        raise ValueError("RED_CURRENT_HUMAN_GATE_NOT_FOUR")
    if enabled:
        rollback=combined.replace(REPLACEMENT,ENTRY,1)
        if rollback!=member.patch(base) or sha256(member.undo(combined))!=sha256(five):
            raise ValueError("RED_530_ROLLBACK_DID_NOT_PRESERVE_535")
        if combined.count("GQ_DEAD_CASTER_FENCE:")!=1:
            raise ValueError("RED_DEAD_CASTER_DUPLICATE")
    else:
        if "GQ_DEAD_CASTER_FENCE:" in combined:
            raise ValueError("RED_OFF_STILL_HAS_GUARD")
    if combined.count("humanCombatTargetable(")!=3:
        raise ValueError("RED_529_HUMAN_STEALTH_LOST")
    for k in ("StatusTickFence.canTick(","safeMove(session,char,root,",
              "botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)"):
        if k not in combined:
            raise ValueError("RED_510_516_524_MISSING "+k)
    return combined,heads

def build(out:Path,enabled:bool):
    four=four_author_module()
    member=import_author(MEMBER,"current_human_535",MEMBER_BLOB)
    host=import_author(HOST,"host_current_human_531",HOST_BLOB)
    rawproject=(ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_bytes()
    if four.git_blob(rawproject)!=ORIGINAL_PROJECT_BLOB:
        raise ValueError("RED_482_PROJECT_DRIFT")
    combined,heads=source_union(enabled)
    out.mkdir(parents=True,exist_ok=True)
    combat=out/("COMBAT_ON.luau" if enabled else "COMBAT_OFF.luau")
    combat.write_text(combined,encoding="utf-8")
    project=out/("ON22.project.json" if enabled else "OFF22.project.json")
    receipt=out/("ON22_RECEIPT.json" if enabled else "OFF22_RECEIPT.json")
    four.compose_private(combat,project,receipt,heads)
    # Existing #531 exact Host+Bot membership authors, with actual #484 AI duel.
    original_host=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_bytes()
    original_bot=(ROOT/"EGGRUMBLE_BotActors.luau").read_bytes()
    for name,blob in host.OWNER_BLOBS.items():
        source=original_host if name==host.HOST else original_bot
        if host.git_blob_sha(source)!=blob:
            raise ValueError("RED_482_HOST_BOT_DRIFT "+name)
    if host.git_blob_sha(AI.read_bytes())!=host.AI_BOT_BLOB:
        raise ValueError("RED_484_AI_DUEL_BLOB_DRIFT")
    source_dir=ROOT
    host_out=out/"reused_531_authors"
    host.run(source_dir,host_out,ai_bot_file=AI)
    selected=json.loads(project.read_text(encoding="utf-8"))
    server=selected["tree"]["ServerScriptService"]
    for slot,name in ((HOST_SCRIPT,host.HOST),(BOT_SCRIPT,host.BOT)):
        assert server[slot]["$path"].endswith(name)
        server[slot]["$path"]=os.path.relpath((host_out/name).resolve(),project.parent.resolve()).replace(os.sep,"/")
    selected["name"]=("EGGRUMBLE_GQ_530_535_531_484_PRIVATE22_ON_NOT_RC" if enabled
                       else "EGGRUMBLE_GQ_535_531_484_PRIVATE22_530_OFF_NOT_RC")
    project.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    observed=four.scripts(selected,project.parent)
    assert len(observed)==22
    original=four.scripts(json.loads(rawproject),ROOT)
    assert len(original)==21
    changed={COMBAT,HOST_SCRIPT,BOT_SCRIPT}
    assert set(observed)==set(original)|{"EGGRUMBLE_StatusTickFence"}
    for name in set(original)-changed:
        assert original[name][1].read_bytes()==observed[name][1].read_bytes(),name
    assert observed[COMBAT][1].read_text()==combined
    assert observed[HOST_SCRIPT][1].read_text().count("session.isCurrentHuman=function")==1
    assert observed[BOT_SCRIPT][1].read_text().count("session.isCurrentHuman(player)")==1
    bot=observed[BOT_SCRIPT][1].read_text()
    assert bot.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)")==1
    data=json.loads(receipt.read_text(encoding="utf-8"))
    data.update({
        "status":"PRIVATE_ONLY_NOT_FORMAL_RC",
        "member_535_head":MEMBER_HEAD,
        "host_531_head":HOST_HEAD,
        "ai_duel_484_head":AI_HEAD,
        "author_529_4_sha256":ORIGINAL_529_FOUR_SHA256,
        "combined_combat_sha256":sha256(combined),
        "dead_guard_530_enabled":enabled,
        "current_member_gate_535_enabled":True,
        "reuses_current_ai_484":True,
        "script_count":len(observed),
        "source_exact_expected":22,
        "original_author_source_untouched":18,
        "authoritative_host_modules":1,
        "authoritative_combat_modules":1,
        "no_authoritative_new_remote":True,
        "official_rc_adopted":False,
        "rc_writer_granted":False,
        "source_sha256":{name:hashlib.sha256(path.read_bytes()).hexdigest()
                          for name,(_,path) in observed.items()},
    })
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ530_GQ535_MEMBER_WITH_531_HOST_AND_484_LIVE_AI_PRIVATE22_MAP_PASS",len(observed),enabled)
    return project,receipt,combat

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--off",action="store_true")
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.place:
        four=four_author_module()
        stem="OFF22" if a.off else "ON22"
        four.verify_place(a.out/(stem+".project.json"),a.place,a.out/(stem+"_RECEIPT.json"))
    else:
        build(a.out,enabled=not a.off)

if __name__=="__main__":
    main()
