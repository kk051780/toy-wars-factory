#!/usr/bin/env python3
"""P0 #361/#364 PRIVATE-only composite of five existing PREP features, on official66.

NOT a second RC branch or an RC writer. Never invoke from canonical build.
Only B #220 may select/rebase/adopt after authenticated current-head checks.
All imported authorship is immutable/pinned; overlay applied atomically to a
throwaway 66-source dist. Do not double-adopt upstream standalone PRs.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path

import apply_core_round_ready as ready
import apply_fb007_lobby as lobby
import apply_fb005_solo_bots as solo
import apply_owner361_castle as castle
import apply_hud_clean as hud

ROOT=Path(__file__).resolve().parent
GAME="server/Game.server.luau"
V4="server/V4TrainingBridge.server.luau"
HUD="client/HUD.client.luau"
CONFIG="shared/Config.luau"
CHANGED={GAME,V4,HUD,CONFIG}
BASE_RC="43543378f976374e2cac2d68b3136ac355d3191b"
# Trusted 66 authored script manifest generated from verified pinned official RC CI.
# Pin exact digest before handing this composite to B #220; never trust self-authored locks.
BASE66_BLOBS_SHA256="5fb70b5af83d217ef67bc5c71f467d71d9cfc3a0a1485c8dd58ebec93e93f728"
INPUTS={
    "ready":("apply_core_round_ready.py","9460fd8a0bcc95af9eff765aa28960b45fde5e12"),
    "lobby":("apply_fb007_lobby.py","9fcf93b03efd5567f6c5197453fc1817a5105928"),
    "solo":("apply_fb005_solo_bots.py","d8e15526f144838063003aa853151d02b599f282"),
    "castle":("apply_owner361_castle.py","bc1fa66e33f42f0117377615976ff505b4932af5"),
    "hud":("apply_hud_clean.py","a4e2d73c3e48ba3fa660a7b227f8dca98b377b65"),
}
FEATURE_IDS=[
    ready.FEATURE,lobby.FEATURE,solo.ID,castle.FEATURE,hud.FEATURE,
]
ADDED={
    lobby.DEST:(lobby.MODULE,lobby.MODULE_BLOB),
    solo.DEST:(solo.MODULE,solo.MODULE_BLOB),
    castle.DEST:(castle.SOURCE,castle.PIN),
    hud.DEST:(hud.SOURCE,hud.BLOB),
}
ID="OWNER361_FIVE_PREP_COMPOSITE70_STUDIO_REVIEW_ONLY_V1"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def reject_symlink_tree(dist:Path):
    # Fail before a single write: a forged symlink must not overwrite external
    # files while checksums and receipts appear self-consistent.
    assert dist.is_dir() and not dist.is_symlink(), "INVALID_OR_LINKED_DIST"
    allowed=dist.resolve()
    for p in dist.rglob("*"):
        assert not p.is_symlink(), ("P0_SYMLINK_REFUSED",str(p))
        assert p.resolve().is_relative_to(allowed), ("P0_PATH_ESCAPES_DIST",str(p))

def source_map(dist:Path)->dict[str,bytes]:
    reject_symlink_tree(dist)
    root=dist/"src"
    return {f.relative_to(root).as_posix():f.read_bytes()
        for f in sorted(root.rglob("*.luau"))}

def check_authors():
    for _,(rel,pin) in INPUTS.items():
        assert blob((ROOT/rel).read_bytes())==pin,("AUTHOR_ADAPTER_DRIFT",rel)
    for dest,(file,pin) in ADDED.items():
        assert blob(file.read_bytes())==pin,("AUTHOR_MODULE_DRIFT",dest)
    castle.check_authored(castle.SOURCE.read_bytes())
    assert len(set(ADDED))==4 and len(set(FEATURE_IDS))==5

def patch_owner_game(base:str)->str:
    # Requirements are deliberately deterministic; these adapters CANNOT be
    # called individually after the 66-source count has changed.
    # Bot first: READY inserts a results-phase reset into bot-annotated stopRound;
    # lobby last: its phase and spawn transforms see the actual combined owner.
    script=solo.patch_game(base)
    script=ready.patch_game(script)
    script=lobby.patch_game(script)
    # The standalone lobby was tested with the 250x142 legacy arena. Here the
    # castle extends the floor to 370x294: leaving its old x130/z76 ACTIVE
    # death-plane would teleport players on BOTH intended flank routes.
    old='math.abs(position.X) > 130 or math.abs(position.Z) > 76'
    new='math.abs(position.X) > 182 or math.abs(position.Z) > 144'
    assert script.count(old)==1,("CASTLE_LOBBY_BOUNDARY_DRIFT",script.count(old))
    assert 'grass.Size = Vector3.new(370, 4, 294)' in castle.SOURCE.read_text("utf8")
    script=script.replace(old,new,1)
    assert script.count('remote.OnServerEvent:Connect(')==1
    assert script.count('local function tickRound()')==1
    assert script.count('local function resetRound()')==1
    assert script.count('pcall(SoloTeamBots.start,map,')==1
    assert script.count('local function applyReady(')==1
    assert script.count('LobbyIsland.build(map.model)')==1
    assert script.count('SoloTeamBots.stop()')>=2
    assert 'everybodyReady() and StudioSolo.canStart(' in script
    assert 'Bot.start' not in script # only original Game's approved callback identifier
    return script

def compose(before:dict[str,bytes])->dict[str,bytes]:
    assert len(before)==66 and CHANGED.issubset(before)
    assert all(dest not in before for dest in ADDED)
    game=patch_owner_game(before[GAME].decode("utf8"))
    v4=lobby.patch_v4(before[V4].decode("utf8"))
    client=ready.patch_hud(before[HUD].decode("utf8"))
    config=ready.patch_config(before[CONFIG].decode("utf8"))
    after={**before,
        GAME:game.encode("utf8"),V4:v4.encode("utf8"),
        HUD:client.encode("utf8"),CONFIG:config.encode("utf8")}
    for dest,(file,_) in ADDED.items():
        after[dest]=file.read_bytes()
    assert len(after)==70
    assert {k for k in before if before[k]!=after[k]}==CHANGED
    assert set(after)-set(before)==set(ADDED)
    assert all(after[k]==before[k] for k in before if k not in CHANGED)
    assert after[GAME].count(b'OnServerEvent:Connect(')==1
    return after

def apply(dist:Path,enabled:bool,out_dir:Path|None=None)->bool:
    if not enabled:
        print("OWNER361_PRIVATE70_OFF_ZERO_WRITE")
        return False
    assert out_dir is not None, "PRIVATE_COMPOSITE_REQUIRES_SEPARATE_OUTPUT"
    out_dir=out_dir.absolute()
    assert out_dir.parent.is_dir() and not out_dir.exists() and not out_dir.is_symlink(), "OUTPUT_ALREADY_EXISTS"
    assert out_dir != dist.absolute() and not out_dir.is_relative_to(dist.absolute()), "OUTPUT_INSIDE_INPUT"
    check_authors()
    before=source_map(dist)
    assert len(before)==66 and CHANGED.issubset(before),("REQUIRE_CANONICAL_RC66",len(before))
    initial={p:blob(v) for p,v in sorted(before.items())}
    sl=dist/"SOURCE_LOCK.json";fl=dist/"RC_FEATURE_LOCK.json"
    pj=dist/"default.project.json"
    source_lock=json.loads(sl.read_text("utf8"))
    feature_lock=json.loads(fl.read_text("utf8"))
    project=json.loads(pj.read_text("utf8"))
    assert source_lock["total_scripts"]==66 and source_lock["blobs"]==initial
    assert feature_lock["total_sources"]==66 and feature_lock["source_gitblobs"]==initial
    assert set(FEATURE_IDS).isdisjoint(feature_lock["feature_flags"])
    verified_digest=hashlib.sha256(json.dumps(initial,sort_keys=True,separators=(",",":")).encode("utf8")).hexdigest()
    print("P0_RECONSTRUCTED_OFFICIAL66_SOURCE_FINGERPRINT",verified_digest)
    assert verified_digest==BASE66_BLOBS_SHA256, "WRONG_66_SOURCE_DISTRIBUTION"
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    starter=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert "BattleHUDGovernor" not in starter
    assert any(isinstance(v,dict) and v.get("$path")=="src/client/HUD.client.luau" for v in starter.values())
    # No writes until ALL auth pins, source-lock checks and Game source
    # transformations succeed. Any drift aborts without a half-written dist.
    after=compose(before)
    newpins={p:blob(v) for p,v in sorted(after.items())}
    expected_modules={p:pin for p,(_,pin) in ADDED.items()}
    assert all(newpins[k]==v for k,v in expected_modules.items())
    starter["BattleHUDGovernor"]={"$path":"src/"+hud.DEST}
    flags=dict(feature_lock["feature_flags"])
    for f in FEATURE_IDS: flags[f]=True
    receipt={
        "id":ID,"base_rc":BASE_RC,"source_count":70,
        "feature_ids":FEATURE_IDS,"parent_prep_prs":[365,376,378,366,367],
        "modified_original":sorted(CHANGED),"added":sorted(ADDED),
        "62_original_byte_exact":True,
        "sole_Game_damage_egg_score_winner_authority":True,
        "solo_classic_only":True,"five_egg_bot":"NOT_SUPPORTED",
        "castle_flank_teleport_bounds_fixed":"X182/Z144_ACTIVE_ONLY",
        "full_studio_fun":"NOT_TESTED","android":"NOT_TESTED",
        "owner_approval":"NO_GO","formal_rc_adoption":False,
        "rollback":"omit full composite overlay; original locked official66 unchanged",
        "no_merge_publish_payment":True,
    }
    source_lock["total_scripts"]=70
    source_lock["blobs"]=newpins
    source_lock["owner361_p0_composite_private70"]=receipt
    feature_lock["total_sources"]=70
    feature_lock["source_gitblobs"]=newpins
    feature_lock["feature_flags"]=flags
    feature_lock["owner361_p0_composite_private70"]=receipt
    # Build to a fresh private sibling directory; publish the complete
    # candidate with ONE atomic rename. The immutable original66 remains
    # available if interrupted, and the destination is never half-written.
    scratch=Path(tempfile.mkdtemp(prefix=".p0d_p0_stage_",dir=str(out_dir.parent)))
    staged=scratch/"candidate"
    try:
        shutil.copytree(dist,staged,symlinks=False)
        for path in sorted(after):
            if path not in before or after[path]!=before[path]:
                out=staged/"src"/path
                out.parent.mkdir(parents=True,exist_ok=True)
                out.write_bytes(after[path])
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(source_lock,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(feature_lock,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"default.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n","utf8")
        assert source_map(staged)==after
        assert json.loads((staged/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==newpins
        assert json.loads((staged/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==newpins
        assert out_dir.exists()==False, "PRIVATE_OUTPUT_RACE"
        os.replace(staged,out_dir)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    assert source_map(dist)==before, "CANONICAL_INPUT_MODIFIED"
    print("OWNER361_P0_PRIVATE70_COMPOSITE_SOURCE_EXACT_PASS")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dist",required=True,type=Path)
    parser.add_argument("--out",type=Path,help="NEW private candidate directory; input official66 remains immutable")
    parser.add_argument("--enabled",required=True,choices=("true","false"))
    args=parser.parse_args()
    apply(args.dist,args.enabled=="true",args.out)
