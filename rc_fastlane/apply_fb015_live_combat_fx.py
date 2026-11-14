#!/usr/bin/env python3
"""P0 #431: first real-live art layer, real-hit-only client combat FX.

Source-locked, one LocalScript modified, original 79 untouched.
No server damage, Game, Remote, egg, score, store, collision or new GUI.
Green CI means SOURCE_READY only; actual live PC/Android/OWNER is NOT_TESTED.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path

TARGET = "client/ConfirmedSlashFX.client.luau"
BASE_BLOB = "4b1dce5635b709d349ab3f00bba7a7cf9d9883bd"
BASE_HEAD = "3dfbb52104fac44b71bf3adcaa82933153670099"
FEATURE = "FB015_LIVE_COMBAT_FX_ANDROID_BOUNDED_V1"
OLD_GUARD = 'local RunService = game:GetService("RunService")\nif not RunService:IsStudio() then return end'
NEW_GUARD = '''local RunService = game:GetService("RunService")
local studioPreview = RunService:IsStudio()
local UserInputService = game:GetService("UserInputService")
-- FB015 LIVE ART: the original real-hit cosmetic works outside Studio too.
-- A PREP only. Low-end touch clients receive a hard effect/visibility budget.
local touchDevice = UserInputService.TouchEnabled'''
OLD_BUDGET = '''local MAX_ACTIVE_PARTS = 48
local VIEW_DISTANCE = 115
local MIN_PER_TARGET_INTERVAL = .09
local BURST_DURATION = .23'''
NEW_BUDGET = '''-- Do not spawn expensive parts outside visible fights on touch hardware.
-- Desktop remains capped; both are below the previous Studio-only budget 48.
local MAX_ACTIVE_PARTS = if touchDevice then 16 else 32
local VIEW_DISTANCE = if touchDevice then 70 else 110
local MIN_PER_TARGET_INTERVAL = if touchDevice then .16 else .09
local BURST_DURATION = if touchDevice then .17 else .23'''

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink(),"NO_INPUT_ROOT"
    for item in root.rglob("*"):
        assert not item.is_symlink() and item.resolve().is_relative_to(root.resolve()),("SYMLINK",item)
    src=root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def once(s:str,original:str,replacement:str)->str:
    assert s.count(original)==1,("SOURCE_ANCHOR_DRIFT",original[:80],s.count(original))
    assert replacement not in s,"DUPLICATE_FEATURE"
    return s.replace(original,replacement,1)

def patch(raw:bytes)->bytes:
    assert blob(raw)==BASE_BLOB,("AUTHORED_COMBAT_SOURCE_PIN_DRIFT",blob(raw))
    src=raw.decode("utf8")
    for required in (
        'local MAX_ACTIVE_PARTS = 48','local VIEW_DISTANCE = 115',
        'popup:GetPropertyChangedSignal("Enabled"):Connect(',
        'if not alive or not popup.Enabled or not model.Parent then return end',
        'local horde = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)',
        'if not alive or not container.Parent or active >= MAX_ACTIVE_PARTS then return nil end',
        'p.CanCollide = false','p.CanTouch = false','p.CanQuery = false',
        'Debris:AddItem(p, .34)',
    ):
        assert required in src,("ORIGINAL_RUNTIME_CONTRACT_DRIFT",required)
    assert src.count('Instance.new("ScreenGui")')==0
    assert src.count('FireServer(')==0 and src.count('TakeDamage(')==0
    src=once(src,OLD_GUARD,NEW_GUARD)
    src=once(src,'container:SetAttribute("PreviewOnly", true)',
             'container:SetAttribute("PreviewOnly", studioPreview)\ncontainer:SetAttribute("LiveParitySourceCandidate", true)')
    src=once(src,OLD_BUDGET,NEW_BUDGET)
    src=once(src,'FB008_CONFIRMED_HIT_SLASH_VFX_ATTACHED_STUDIO_ART_NO_GO',
             'FB008_CONFIRMED_HIT_SLASH_VFX_ATTACHED_LIVE_PARITY_ART_NO_GO')
    assert 'if not RunService:IsStudio() then return end' not in src
    assert 'local touchDevice = UserInputService.TouchEnabled' in src
    assert src.count('local MAX_ACTIVE_PARTS = if touchDevice then 16 else 32')==1
    for banned in ('FireServer(', 'TakeDamage(', 'GetDataStore(', 'OnServerEvent:Connect(',
                   'Instance.new("ScreenGui")','CanCollide = true','CanQuery = true',
                   'CanTouch = true','MarketplaceService'):
        assert banned not in src,("NEW_AUTHORITY_OR_GAMEPLAY_RISK",banned)
    return src.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"DISABLED_ZERO_WRITE_REQUIRED"
        print("LIVE_COMBAT_FX_OFF_ZERO_WRITE_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    original=read(base)
    assert len(original)==80 and TARGET in original,"OFFICIAL_REAL80_REQUIRED"
    src_lock=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    feature_lock=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(v) for p,v in sorted(original.items())}
    assert src_lock["total_scripts"]==feature_lock["total_sources"]==80
    assert src_lock["blobs"]==feature_lock["source_gitblobs"]==pins,"SOURCE_LOCK_DRIFT"
    assert pins[TARGET]==BASE_BLOB
    for prior in (
       "FB016_FOLIAGE_PASSAGE_20261114",
       "FB017_NO_PERSISTENT_BATTLE_GUIDES",
       "FB018_ACTION_BUTTON_TEXT_INIT",
       "FB019_RESPONSIVE_ATTACK_INPUT_SWING",
       "FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2",
       "FB015_FOREST_BIOMES_MONUMENTS_V2",
       "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
    ):
        assert feature_lock["feature_flags"].get(prior) is True,("MISSING_PARENT_FEATURE",prior)
    assert FEATURE not in feature_lock["feature_flags"],"DUPLICATE_LIVE_FX"
    updated={**original,TARGET:patch(original[TARGET])}
    assert len(updated)==80 and {p for p in original if original[p]!=updated[p]}=={TARGET}
    newpins={p:blob(v) for p,v in sorted(updated.items())}
    receipt={
        "id":FEATURE,"parent_official_head":BASE_HEAD,
        "source_count":80,"changed_source":[TARGET],"other79_byte_exact":True,
        "original_blob":BASE_BLOB,"new_blob":newpins[TARGET],
        "studio_only_top_guard_removed":True,
        "mobile_touch_max_parts":16,"mobile_touch_max_distance_studs":70,
        "desktop_max_parts":32,"server_game_unmodified":True,
        "server_horde_unmodified":True,"new_remote_or_damage":False,
        "studio_test":"NOT_TESTED","production_private_test":"NOT_TESTED",
        "android_15min":"NOT_TESTED","owner_fun":"FUN_NO_GO",
        "owner_art":"ART_NO_GO","live_art":"LIVE_ART_NO_GO",
        "owner_accepted":False,"official_adopted":False,
        "rollback":"omit this overlay and retain canonical original FB008 combat cosmetic",
    }
    src_lock["blobs"]=newpins
    feature_lock["source_gitblobs"]=newpins
    src_lock["live_combat_fx"]=receipt
    feature_lock["live_combat_fx"]=receipt
    feature_lock["feature_flags"][FEATURE]=True
    scratch=Path(tempfile.mkdtemp(prefix=".live_fx_",dir=str(out.parent)))
    staged=scratch/"stage"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/TARGET).write_bytes(updated[TARGET])
        for file,data in (("SOURCE_LOCK.json",src_lock),("RC_FEATURE_LOCK.json",feature_lock)):
            (staged/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==updated and read(base)==original
        os.replace(staged,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("P0D_LIVE_FX_ONE_CLIENT_SOURCE_79_UNCHANGED_OK")
    return True

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--enabled",required=True,choices=("true","false"))
    args=a.parse_args()
    apply(args.base,args.out,args.enabled=="true")
