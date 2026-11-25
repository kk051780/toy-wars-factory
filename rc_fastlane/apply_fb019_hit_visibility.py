#!/usr/bin/env python3
"""FB-019 stage2: repair server-confirmed real-hit visibility with no guide spam.
Generated RC80 -> RC80. Only Game & BattleHUDGovernor change, 78 others exact.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
GAME="server/Game.server.luau"
GOV="client/BattleHUDGovernor.client.luau"
GAME_BASE="7ad806322554499ca91cef7c36f31aad438642b4"
GOV_BASE="e8d6810c745f3d234c8aa25db3375840e4fe9e47"
FEATURE="FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2"
GAME_OLD="            mobLastKOs[player]=defeated\n"
GAME_NEW=("            mobLastKOs[player]=defeated\n"
    "            -- FB019: emit current server-owned damage receipt immediately.\n"
    "            -- Only after real Horde:hit touched >0, never for miss or fake KO.\n"
    "            if player.Parent==Players then\n"
    "                remote:FireClient(player,snapshotFor(player))\n"
    "            end\n")
WORLD_OLD='    if not obj:IsA("BillboardGui") or obj.Name == "S1_CARRIED_EGG" then return end\n'
WORLD_NEW='    if not obj:IsA("BillboardGui") or obj.Name == "S1_CARRIED_EGG" or obj.Name=="RealDamagePopup" then return end\n'
GOV_OLD='    if not node:IsA("BillboardGui") or node.Name=="S1_CARRIED_EGG" then return end\n'
GOV_NEW=GOV_OLD+'''    -- FB019: do not suppress the ORIGINAL server-owned 0.72s NPC damage marker.
    -- This is brief real combat evidence, NOT a persistent guidance billboard.
    if node.Name=="RealDamagePopup" then
        local core=node.Parent
        local npc=if core then core.Parent else nil
        local arena=workspace:FindFirstChild("TRAP_RAIDERS_S1")
        if arena and core and core:IsA("BasePart") and core.Name=="Core"
            and npc and npc:IsA("Model") and npc:IsDescendantOf(arena)
            and (npc.Name=="MUSOU_ELITE_TELEGRAPH"
                or string.match(npc.Name,"^MUSOU_MINION_%d+$")) then
            return -- server Horde owns Enabled and auto-hides it after .72s
        end
    end
'''
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def read(dist:Path)->dict[str,bytes]:
    assert dist.is_dir() and not dist.is_symlink()
    for p in dist.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(dist.resolve()),("UNSAFE_LINK",p)
    src=dist/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}
def only_once(s:str,old:str,new:str)->str:
    assert s.count(old)==1,(old[:75],s.count(old))
    return s.replace(old,new,1)
def patched(src:dict[str,bytes])->dict[str,bytes]:
    assert blob(src[GAME])==GAME_BASE,("GAME_DRIFT",blob(src[GAME]))
    assert blob(src[GOV])==GOV_BASE,("GOVERNOR_DRIFT",blob(src[GOV]))
    game=src[GAME].decode("utf8")
    gov=src[GOV].decode("utf8")
    assert 'local touched,defeated = horde:hit(' in game
    assert 'if touched>0 then' in game and 'snapshotFor = function(player: Player)' in game
    assert 'm.popup.Enabled=true' not in game # one real Horde authority instead
    assert '"RealDamagePopup"' not in gov # confirms old FB017 suppressed it
    game=only_once(game,GAME_OLD,GAME_NEW)
    gov=only_once(gov,WORLD_OLD,WORLD_NEW)
    gov=only_once(gov,GOV_OLD,GOV_NEW)
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count("remote:FireClient(player,snapshotFor(player))")>=1
    assert "noGuidanceActive=true" in gov
    return {**src,GAME:game.encode("utf8"),GOV:gov.encode("utf8")}
def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_NO_WRITE"
        print("FB019_V2_OFF_ZERO_WRITE_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==80
    origpins={p:blob(v) for p,v in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==origpins
    for k in ("FB019_RESPONSIVE_ATTACK_INPUT_SWING","FB018_ACTION_BUTTON_TEXT_INIT",
              "FB017_NO_PERSISTENT_BATTLE_GUIDES","FB016_FOLIAGE_PASSAGE_20261114"):
        assert fl["feature_flags"].get(k) is True,("MISSING_PARENT",k)
    assert FEATURE not in fl["feature_flags"]
    after=patched(before)
    assert len(after)==80 and {p for p in before if before[p]!=after[p]}=={GAME,GOV}
    pins={p:blob(v) for p,v in sorted(after.items())}
    receipt={
        "id":FEATURE,"feedback":"FB-019","source_count":80,
        "two_modified_sources":[GAME,GOV],
        "other78_byte_exact":True,"previous_real_hit_horde_source_unchanged":True,
        "input_touch_F_swing_from_previous_FB019_unchanged":True,
        "Horde_real_damage_source_only":True,
        "server_snapshot_only_after_touched_positive":True,
        "damage_popup_duration_seconds":0.72,
        "no_always_visible_guides":True,
        "new_Remote_or_UI_instances":False,
        "original_Game_authority_count":1,
        "owner_engine_retest":"NOT_TESTED","owner_fun":"FUN_NO_GO",
        "rollback":"omit second FB019 overlay, preserve 846d4be RC80",
        "source_blobs_before":{GAME:GAME_BASE,GOV:GOV_BASE},
        "source_blobs_after":{GAME:pins[GAME],GOV:pins[GOV]},
    }
    sl["blobs"]=pins;sl["fb019_hit_visibility"]=receipt
    fl["source_gitblobs"]=pins
    fl["feature_flags"][FEATURE]=True
    fl["fb019_hit_visibility"]=receipt
    temp=Path(tempfile.mkdtemp(prefix=".fb019v2_",dir=str(out.parent)))
    staged=temp/"dist"
    try:
        shutil.copytree(base,staged,symlinks=False)
        for name in (GAME,GOV):
            (staged/"src"/name).write_bytes(after[name])
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("FB019_V2_SERVER_REAL_HIT_VISIBLE_80_SOURCE_LOCK_PASS")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
