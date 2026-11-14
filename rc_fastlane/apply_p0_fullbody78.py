#!/usr/bin/env python3
"""P0D FB015 full-body QA child #392: source-exact, compatible private78 overlay.

The original author source is preserved at its exact immutable Git blob.
One disabled/missing optional outbound CombatSignal must not block all costume
motion in the older private78 Horde. Use the already-existing confirmed server
damage popup for hit/KO animation fallback, never claim extra damage.
"""
from __future__ import annotations
import argparse,json,os,shutil,tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,DEST,FEATURE_ID,BASE_RC
from apply_p0_results78 import GAME,REPAIR

ROOT=Path(__file__).resolve().parent
AUTHOR=ROOT/"features/p0_fullbody78/NeutralMotionAuthor392.client.luau"
ORIGINAL_BLOB="5488d27d7cc5f24f7a4fc24098a368dff2b390c0"
OLD_MOTION_BLOB="c9f481dba1a108534292e927b398915ab67bcd60"
ART_ORIGINAL="server/ArtMinionSilhouette.server.luau"
FLAG="FB015_MINION_MOTION_FULL_41_PARTS_QA_V1"
FULL_COUNT=41

def exactly_once(body:str,a:str,b:str)->str:
    assert body.count(a)==1,("FULLBODY_AUTHORED_ANCHOR_DRIFT",a[:120],body.count(a))
    return body.replace(a,b,1)

def derived_source()->bytes:
    original=AUTHOR.read_bytes()
    assert gitblob(original)==ORIGINAL_BLOB, "FULLBODY_ORIGINAL_AUTHOR_GITBLOB_DRIFT"
    text=original.decode("utf8")
    # The #392 parent art-combat private69 emits a new server outbound
    # CombatSignal, but THIS cumulative private78 uses the preexisting
    # confirmed RealDamagePopup only. An unconditional WaitForChild would
    # suspend the animation forever before Heartbeat subscribes.
    text=exactly_once(text,
        'local cue = horde:WaitForChild("P0D_ART_COMBAT_SIGNAL_V1")',
        'local cue = horde:FindFirstChild("P0D_ART_COMBAT_SIGNAL_V1")')
    text=exactly_once(text,
        'if cue:IsA("RemoteEvent") then',
        'if cue and cue:IsA("RemoteEvent") then')
    src='''            entry.speed = (entry.speed * .7) + (.3 * (delta.Magnitude / stepDt))'''
    change=src+'''
            -- Private78 older Horde has no new outbound art Remote. Detect
            -- ONLY its server-authored GUI cue; no fabricated client hit.
            if not cueConnection then
                local popup = core:FindFirstChild("RealDamagePopup")
                local hit = popup and popup:IsA("BillboardGui") and popup.Enabled == true
                if hit and not entry.lastHit then entry.hitAt = now end
                entry.lastHit = hit == true
                local combatCue = core:FindFirstChild("CombatCue")
                local label = combatCue and combatCue:FindFirstChildWhichIsA("TextLabel")
                local ko = label and string.find(label.Text,"撃破",1,true) ~= nil
                if ko and entry.koAt < 0 then entry.koAt = now end
            end'''
    text=exactly_once(text,src,change)
    required=(
        "MAX_ACTIVE_COSMETIC_PARTS = 104",
        "local copy = source:Clone()",
        "original.LocalTransparencyModifier = visual.initialModifier",
        "visual.original.LocalTransparencyModifier = 1",
        "visual.copy.CFrame = core.CFrame * visual.offset * localMotion",
        "visual.copy.Transparency = 1",
        "core.CFrame:ToObjectSpace(source.CFrame)",
    )
    for marker in required:assert marker in text,("FULLBODY_REQUIRED_SOURCE_ANCHOR_MISSING",marker)
    for forbidden in ('TakeDamage(', 'FireServer(', 'OnServerEvent:', 'DataStoreService',
                     'Instance.new("RemoteEvent")','MarketplaceService','UpdateAsync('):
        assert forbidden not in text,("FULLBODY_GIVES_GAMEPLAY_AUTHORITY",forbidden)
    assert text.count('local cue = horde:FindFirstChild("P0D_ART_COMBAT_SIGNAL_V1")')==1
    assert 'horde:WaitForChild("P0D_ART_COMBAT_SIGNAL_V1")' not in text
    assert 'local MAX_MODELS = 16' in text and 'ANIM_STEP = 1 / 25' in text
    return text.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_FULLBODY_OFF_ZERO_WRITE");return False
    base=base.absolute();out=out.absolute()
    assert out.parent.is_dir() and not out.exists(),"FULLBODY_OUTPUT_EXISTS"
    assert out!=base and not out.is_relative_to(base) and not base.is_relative_to(out),"FULLBODY_INPUT_OUTPUT_OVERLAP"
    before=read(base)
    assert len(before)==78 and DEST in before and GAME in before
    assert gitblob(before[DEST])==OLD_MOTION_BLOB, "FULLBODY_REQUIRE_OLD_P78_MOTION"
    assert before[GAME].decode().count(REPAIR)==1, "FULLBODY_REQUIRE_DEFEATED_PLAYER_FIX"
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    old_pins={k:gitblob(v) for k,v in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==old_pins
    assert fl["feature_flags"][FEATURE_ID] is True
    assert fl["p0_results78"]["no_new_source"] is True
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert "p0_fullbody78" not in sl and "p0_fullbody78" not in fl
    rewritten=derived_source()
    after=dict(before);after[DEST]=rewritten
    assert len(after)==78
    assert set(k for k in before if before[k]!=after[k])=={DEST}
    new_pin=gitblob(rewritten)
    pins={k:gitblob(v) for k,v in sorted(after.items())}
    sl["blobs"]=pins;fl["source_gitblobs"]=pins
    receipt={
        "id":FLAG,"authored_qa_pr":392,"author_head":"f77e38d42fc3690eb02b3156450abc7bd457ed92",
        "author_source_gitblob":ORIGINAL_BLOB,"adapted_source_gitblob":new_pin,
        "original78_motion_source_gitblob":OLD_MOTION_BLOB,
        "single_existing_source_replaced":DEST,
        "other77_byte_identical":True,"original_count":78,"new_count":78,
        "models":9,"authored_parts_per_kind":{"KNIGHT":10,"WRAITH":10,"BRUTE":11,"ELITE":10},
        "visible_part_budget":104,"animation_hz":25,
        "original_Horde_new_remote":"ABSENT_OR_OPTIONAL",
        "fallback":"READ_ONLY_SERVER_CONFIRMED_POPUP",
        "studio_engine":"NOT_TESTED","android_fps":"NOT_TESTED",
        "owner_art":"ART_NO_GO","formal_rc_adoption":False,
        "rollback":"skip this cosmetic overlay; parent private78 and Game recovery unchanged",
    }
    sl["p0_fullbody78"]=receipt;fl["p0_fullbody78"]=receipt
    # The original motion receipt remains historical; mark the pinned source
    # which actually resides in the new complete Game.
    sl["p0_motion78"]["original_source_gitblob"]=OLD_MOTION_BLOB
    sl["p0_motion78"]["source_gitblob"]=new_pin
    fl["p0_motion78"]["original_source_gitblob"]=OLD_MOTION_BLOB
    fl["p0_motion78"]["source_gitblob"]=new_pin
    stage_root=Path(tempfile.mkdtemp(prefix=".p0d_fullbody78_",dir=str(out.parent)))
    stage=stage_root/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/DEST).write_bytes(rewritten)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(stage_root,ignore_errors=True)
    assert read(base)==before,"FULLBODY_PARENT78_CHANGED"
    print("P0_PRIVATE78_FULLBODY_41_PARTS_OTHER77_EXACT_SOURCE_LOCK_PASS",new_pin)
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
