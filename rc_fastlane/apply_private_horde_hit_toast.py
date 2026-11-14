#!/usr/bin/env python3
"""P0 #444 FB019: only real HIT toast in private nonStudio Horde sessions.

Stacked source-only PREP ON TOP of #452's already source-verified private
Horde reset + ATTACK + tick. We MUST NOT set musouActive=true outside Studio:
that flag also permanently enables objective coach, mob banner and net UI.
B is the only official RC writer. This 2-source patch is NEVER public-ready.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
GAME_V2_BLOB = "225bbf2fd06f5b3bab1fb3168d5f1d487df7813d"
HUD_V2_BLOB = "0cfa5b882ff44bf6ba12dfce96ca11e262dd3ec1"
FEATURE = "P0D_PRIVATE_LIVE_HORDE_HIT_TOAST_V3"
V2_FLAG = "P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2"
V1_FLAG = "P0D_PRIVATE_LIVE_HORDE_NINE_V1"

GAME_ANCHOR = '        musouActive = RunService:IsStudio() and match.phase=="ACTIVE",'
GAME_INSERT = (
    GAME_ANCHOR + "\n"
    + '        -- Only real server-confirmed HIT toast in private; all large Horde HUD stays Studio-only.\n'
    + '        musouHitFeedback = (RunService:IsStudio() or (game.PrivateServerId ~= "" and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true)) and match.phase=="ACTIVE",'
)
HUD_ANCHOR = (
    '    if s.musouActive==true then\n'
    '        local hitSeq=s.musouImpactSeq'
)
HUD_REPLACE = (
    '    -- Transient HIT is allowed for the private source-verified Horde path.\n'
    '    -- Do NOT enable coach / mobCue / net GUI outside Studio.\n'
    '    if s.musouActive==true or (s.musouHitFeedback==true and s.phase=="ACTIVE") then\n'
    '        local hitSeq=s.musouImpactSeq'
)
# Real official RC81 author Game contains three independent genuine hit paths:
# evolved-beast hits, normal touched>0 attack, and seven-job hits.
# All three increments must be inside their own true-hit branches.
def verify_all_real_hit_branches(source:str)->None:
    import re
    needle='mobImpactSeq[player]=(mobImpactSeq[player] or 0)+1'
    spots=[m.start() for m in re.finditer(re.escape(needle),source)]
    assert len(spots)==3,("EXACT_THREE_REAL_IMPACT_SOURCES",len(spots))
    guards=("if hits>0 then","if touched>0 then")
    for pos in spots:
        guard=max(source.rfind(g,0,pos) for g in guards)
        assert guard>=0 and 0<pos-guard<420,("IMPACT_NOT_UNDER_REAL_HIT",pos,guard)
        between=source[guard:pos]
        # A premature 'end' would put an increment outside its guarded HIT.
        # Keep 'else' allowed: original normal attack uses Luau if-expression.
        assert not re.search(r'\bend\b',between),("MISS_CAN_ADVANCE_IMPACT",pos)
        assert not re.search(r'\bfunction\b',between),("IMPACT_IN_NESTED_FUNCTION",pos)

def verify_original_toast_epoch(source:str)->None:
    # The original real HUD already uses a generation token; don't double
    # implement a second one via Instance attributes.
    assert source.count("impactDisplayEpoch+=1")>=2
    assert source.count("local epoch=impactDisplayEpoch")==1
    assert source.count("task.delay(.42,function()")==1
    assert source.count("if impactDisplayEpoch==epoch then impactToast.Visible=false end")==1

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def read(root:Path) -> dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("SYMLINK_REJECTED",str(p))
    src=root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix():p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def patch_game(raw:bytes) -> bytes:
    assert blob(raw)==GAME_V2_BLOB,("REAL_GAME_V2_SOURCE_DRIFT",blob(raw))
    text=raw.decode("utf8")
    assert text.count(GAME_ANCHOR)==1
    assert FEATURE not in text and "musouHitFeedback" not in text
    assert text.count("horde:reset(")==1 and text.count("horde:tick(")==1
    assert text.count("horde:hit(")>=1
    assert text.count('game.PrivateServerId ~= ""')==3
    assert 'if RunService:IsStudio() or (game.PrivateServerId ~= "" and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true) then horde:reset(match.serial,serverNow()) end' in text
    verify_all_real_hit_branches(text)
    updated=text.replace(GAME_ANCHOR,GAME_INSERT,1)
    verify_all_real_hit_branches(updated)
    assert updated.count("musouHitFeedback = ")==1
    assert updated.count(GAME_ANCHOR)==1
    assert updated.count('workspace:SetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE"')==0
    return updated.encode("utf8")

def patch_hud(raw:bytes) -> bytes:
    assert blob(raw)==HUD_V2_BLOB,("REAL_HUD_V2_SOURCE_DRIFT",blob(raw))
    text=raw.decode("utf8")
    assert text.count(HUD_ANCHOR)==1
    assert FEATURE not in text and "musouHitFeedback" not in text
    assert text.count('mobCue.Visible=s.musouActive==true')==1
    assert text.count('first90Cue.Visible=s.musouActive==true')==1
    assert text.count('netButton.Visible=s.musouActive==true')==1
    assert text.count('rescueButton.Visible=s.musouActive==true')==1
    updated=text.replace(HUD_ANCHOR,HUD_REPLACE,1)
    verify_original_toast_epoch(updated)
    assert updated.count("if s.musouActive==true or (s.musouHitFeedback==true") == 1
    assert updated.count('mobCue.Visible=s.musouActive==true')==1
    assert updated.count('first90Cue.Visible=s.musouActive==true')==1
    assert updated.count('netButton.Visible=s.musouActive==true')==1
    assert updated.count('rescueButton.Visible=s.musouActive==true')==1
    assert 'impactToast.Visible=true' in updated
    assert 'task.delay(.42,function()' in updated
    return updated.encode("utf8")

def apply(base:Path, out:Path,enabled:bool)->bool:
    assert not out.exists(),"OUTPUT_ALREADY_EXISTS"
    if not enabled:
        print("P0D_PRIVATE_HIT_TOAST_V3_OFF_ZERO_WRITE")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==81 and GAME in before and HUD in before
    assert blob(before[GAME])==GAME_V2_BLOB and blob(before[HUD])==HUD_V2_BLOB
    pins={p:blob(v) for p,v in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==pins,"CANONICAL_V2_SOURCE_LOCK_DRIFT"
    assert fl["feature_flags"].get(V1_FLAG) is True
    assert fl["feature_flags"].get(V2_FLAG) is True
    assert FEATURE not in fl["feature_flags"],"DUPLICATE_HIT_TOAST"
    after=dict(before)
    after[GAME]=patch_game(before[GAME])
    after[HUD]=patch_hud(before[HUD])
    assert len(after)==81
    assert {p for p in before if before[p]!=after[p]}=={GAME,HUD}
    afterpins={p:blob(v) for p,v in sorted(after.items())}
    receipt={
       "schema":"P0D_PRIVATE_HORDE_REAL_HIT_TRANSIENT_TOAST_V3",
       "parent":"#452 private source V2 (never a separate authority)",
       "feature":FEATURE,
       "source_count":81,
       "changed_sources":[GAME,HUD],
       "original_other79_byte_exact":True,
       "Game_parent_v2_gitblob":GAME_V2_BLOB,
       "HUD_parent_v2_gitblob":HUD_V2_BLOB,
       "Game_v3_gitblob":afterpins[GAME],
       "HUD_v3_gitblob":afterpins[HUD],
       "private_Horde_attack_tick_reset_unchanged":True,
       "studio_behavior_unchanged":True,
       "public_nonstudio_hit_toast":"OFF",
       "private_nonstudio_hit_toast":"SOURCE_ONLY_CANDIDATE",
       "trigger":"server mobImpactSeq advances only after genuine Horde hit",
       "transient_toast_duration_seconds":0.42,
       "first90_coach_changed":False,
       "persistent_mob_banner_changed":False,
       "net_rescue_controls_changed":False,
       "real_roblox_runtime":"NOT_TESTED",
       "low_end_android_15min":"NOT_TESTED",
       "owner_accepted":False,
       "official_rc_adopted":False,
       "live_horde_decision":"LIVE_HORDE_NO_GO",
       "art_decision":"ART_NO_GO",
       "mobile_decision":"MOBILE_NO_GO",
       "fun_decision":"FUN_NO_GO",
       "rollback":"disable V3; restore exactly pinned V2 Game/HUD, all other sources unchanged",
    }
    sl["blobs"]=afterpins
    fl["source_gitblobs"]=afterpins
    sl["horde_private_hit_toast_v3"]=receipt
    fl["horde_private_hit_toast_v3"]=receipt
    fl["feature_flags"][FEATURE]=True
    temp=Path(tempfile.mkdtemp(prefix=".p0d_private_hit_toast_",dir=str(out.parent)))
    staged=temp/"candidate"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/GAME).write_bytes(after[GAME])
        (staged/"src"/HUD).write_bytes(after[HUD])
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("P0D_PRIVATE_HORDE_REAL_HIT_TOAST_V3_SOURCE81_OTHER79_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
