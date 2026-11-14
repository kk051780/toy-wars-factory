#!/usr/bin/env python3
"""P0 FB-015 source exact PRIVATE77 -> PRIVATE78 minion motion overlay.

Reuse the source-authored #390 motion script by its immutable Git blob, not a
second animation system. Source77 is separately pinned and never modified.
This is PRIVATE Studio preview only; formal RC remains the sole writer's task.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
MOTION = ROOT / "features/p0_motion78/P0DNeutralMotion.client.luau"
MOTION_PIN = "c9f481dba1a108534292e927b398915ab67bcd60"
DEST = "client/P0DNeutralMotion.client.luau"
CLIENT_ID = "P0DNeutralMotion"
FEATURE_ID = "FB015_MINION_MOTION_VISUAL_ONLY_V1"
ORIGINAL_ART = "server/ArtMinionSilhouette.server.luau"
BASE_RC = "43543378f976374e2cac2d68b3136ac355d3191b"
ORIGINAL_ART_PIN = "ed5cd56789abc4a7bc8ee3a44b8982aae4f3ff62"
AUTHOR_MOTION_TEST = "P0D_MOTION78_SOURCE_QA_ONLY_NO_STUDIO_ACCEPTANCE"

def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink(), "MOTION78_MISSING_DIR"
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()), ("MOTION78_SYMLINK_OR_ESCAPE",p)
    src=root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def author_source()->bytes:
    raw=MOTION.read_bytes()
    assert gitblob(raw)==MOTION_PIN, "MOTION78_AUTHOR_BLOB_DRIFT"
    for term in (
        b"RunService:IsStudio()", b"MAX_MODELS = 16",
        b"MAX_ACTIVE_COSMETIC_PARTS = 56", b"VIEW_RANGE_STUDS = 105",
        b"ANIM_STEP = 1 / 25", b"core.CFrame:ToObjectSpace(art.CFrame)",
        b"core.CFrame * visual.offset * localMotion",
        b"P0D_ART_MINION_V1", b"horde.ChildAdded", b"model.Destroying",
        b"script.Destroying",
    ):
        assert term in raw, ("MOTION78_REQUIRED_ANCHOR_DRIFT",term)
    for forbidden in (
        b"FireServer(", b"OnServerEvent", b"DataStoreService",
        b"TakeDamage(", b"MarketplaceService", b"UpdateAsync(",
        b'Instance.new("Part")', b'Instance.new("RemoteEvent")',
    ):
        assert forbidden not in raw, ("MOTION78_FORBIDDEN_AUTHORITY",forbidden)
    return raw

def compose(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_OFF_ZERO_WRITE")
        return False
    base=base.absolute();out=out.absolute()
    assert out.parent.is_dir() and not out.exists(), "MOTION78_OUTPUT_EXISTS"
    assert out!=base and not out.is_relative_to(base) and not base.is_relative_to(out),"MOTION78_TREE_OVERLAP"
    before=read(base)
    assert len(before)==77 and DEST not in before, ("MOTION78_INPUT_77_REQUIRED",len(before))
    assert "server/Game.server.luau" in before
    assert before["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(")==1
    assert ORIGINAL_ART in before and gitblob(before[ORIGINAL_ART])==ORIGINAL_ART_PIN, "MOTION78_ORIGINAL_MINION_DRIFT"
    assert "client/ConfirmedSlashFX.client.luau" in before
    pins={path:gitblob(raw) for path,raw in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    project=json.loads((base/"default.project.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==77
    assert sl["blobs"]==fl["source_gitblobs"]==pins, "MOTION78_INPUT_LOCK_DRIFT"
    receipt77=fl["p0_private77"]
    assert receipt77["official_base"]==BASE_RC and receipt77["source_count"]==77
    assert len(receipt77["added_art_feature_ids"])==7
    assert fl["feature_flags"]["ART_MINION_THREE_SILHOUETTES_V1"] is True
    assert FEATURE_ID not in fl["feature_flags"],"MOTION78_ALREADY_ADOPTED"
    starters=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert CLIENT_ID not in starters and "P0DConfirmedCombatFX" in starters
    motion=author_source()
    after=dict(before);after[DEST]=motion
    assert len(after)==78
    assert all(after[k]==before[k] for k in before)
    pins78={path:gitblob(raw) for path,raw in sorted(after.items())}
    starters[CLIENT_ID]={"$path":"src/"+DEST}
    fl["feature_flags"][FEATURE_ID]=True
    receipt={
        "id":FEATURE_ID,"author_pr":390,"source_gitblob":MOTION_PIN,
        "source_count":78,"parent_scripts":77,"original77_byte_exact":True,
        "solo_game_and_minion_authority_unchanged":True,"new_script_count":1,
        "studio_engine":"NOT_TESTED","two_clients":"NOT_TESTED","android":"NOT_TESTED",
        "owner_visual_accepted":False,"formal_rc_adoption":False,
        "follow_motion_art_budget":"max16 models/max56 attached accessory parts/25fps/105 studs",
        "rollback":"omit PRIVATE78 overlay (PRIVATE77 exact unchanged)",
    }
    sl["total_scripts"]=78
    sl["blobs"]=pins78
    sl["p0_motion78"]=receipt
    fl["total_sources"]=78
    fl["source_gitblobs"]=pins78
    fl["p0_motion78"]=receipt
    stage_root=Path(tempfile.mkdtemp(prefix=".p0_motion78_",dir=out.parent))
    stage=stage_root/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/DEST).write_bytes(motion)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"default.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins78
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins78
        assert not out.exists(),"MOTION78_OUTPUT_RACE"
        os.replace(stage,out)
    finally:
        shutil.rmtree(stage_root,ignore_errors=True)
    assert read(base)==before,"MOTION78_PARENT77_CHANGED"
    print("P0_PRIVATE78_REAL_SOURCE77_PLUS_1_MOTION_PIN_LOCK_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args()
    compose(a.base,a.out,a.enabled=="true")
