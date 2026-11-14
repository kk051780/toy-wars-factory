#!/usr/bin/env python3
"""FB-017 P0: source-exact RC80→RC80 without persistent gameplay guidance.
Patch only the existing HUD governor, retaining all 79 other Luau bytes.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"features/fb017_no_guides/BattleHUDGovernor.client.luau"
TARGET="client/BattleHUDGovernor.client.luau"
OLD_SHA="ad9bf4f5a9c1c8683319dd476faa91ad30c68185"
NEW_SHA="e8d6810c745f3d234c8aa25db3375840e4fe9e47"
FEATURE="FB017_NO_PERSISTENT_BATTLE_GUIDES"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("UNSAFE_SYMLINK",p)
    src=root/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"DISABLE_MEANS_ZERO_WRITES"
        print("FB017_SWITCH_OFF_ZERO_WRITES_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==80,("REQUIRE_PRECISE_RC80",len(before))
    assert TARGET in before and "server/Game.server.luau" in before
    assert blob(before[TARGET])==OLD_SHA,"HUD_GOVERNOR_SOURCE_DRIFT"
    old_pins={p:blob(b) for p,b in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==old_pins
    assert fl["feature_flags"].get("FB016_FOLIAGE_PASSAGE_20261114") is True
    assert FEATURE not in fl["feature_flags"]
    patched=SOURCE.read_bytes()
    assert blob(patched)==NEW_SHA,"NO_GUIDE_ARTIST_SOURCE_DRIFT"
    assert patched.startswith(before[TARGET].rstrip()+b"\n")
    text=patched.decode("utf8")
    for s in (
        "FB-017 OWNER P0 / NO PERSISTENT",
        "noGuidanceActive=true",
        "coreGui.DescendantAdded:Connect(silenceLabel)",
        "playerGui.ChildAdded:Connect(silenceScreen)",
        "workspace.DescendantAdded:Connect(silenceWorld)",
        "Score=true",
        "BattleSelfHPNumerical=true",
        "MusouHitFlash=true",
        "restoreLobbyGuideState()",
        'packet.phase=="ACTIVE"',
    ):
        assert s in text,("HUD_GUARD_MISSING",s)
    for s in ("DataStoreService","MarketplaceService","FireServer(","TakeDamage("):
        assert s not in text,("UNAUTHORIZED_GAME_OPERATION",s)
    after=dict(before);after[TARGET]=patched
    assert len(after)==80 and sum(before[p]!=after[p] for p in before)==1
    pins={p:blob(b) for p,b in sorted(after.items())}
    receipt={
        "id":FEATURE,"source_count":80,"source_replaced":TARGET,
        "prior_source_blob":OLD_SHA,"new_source_blob":NEW_SHA,
        "79_other_gameplay_sources_byte_exact":True,
        "single_game_remote_store_hp_egg_authority_unchanged":True,
        "kept_active_elements":["Score","BattleSelfHPNumerical","CombatActionButtons","MusouHitFlash"],
        "suppressed":"all always-visible guides and nonessential world BillboardGuis during ACTIVE",
        "lobby_and_results_state":"restored when exiting ACTIVE",
        "studio_visual":"NOT_TESTED",
        "owner_acceptance":"NOT_TESTED",
        "rollback":"omit FB017 patch to restore exact verified RC80",
    }
    sl["blobs"]=pins;sl["fb017_no_guides"]=receipt
    fl["source_gitblobs"]=pins;fl["feature_flags"][FEATURE]=True
    fl["fb017_no_guides"]=receipt
    temp=Path(tempfile.mkdtemp(prefix=".fb017_",dir=str(out.parent)))
    staged=temp/"dist"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/TARGET).write_bytes(patched)
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("FB017_NO_GUIDES_FINAL_RC80_79_OTHER_SOURCES_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
