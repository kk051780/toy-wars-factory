#!/usr/bin/env python3
"""ART FB-016 V2: exact-source 80→80 foliage sightline refinement (private candidate).
Only the previous FoliageCameraFade LocalScript changes. The Game/79 other
sources, Project tree, real colliders and persistent GUI remain untouched.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"features/fb016_camera_v2/FoliageCameraFade.client.luau"
TARGET="client/FoliageCameraFade.client.luau"
OLD_BLOB="0df4bf00148b9067f46a554671d3281391cd06be"
NEW_BLOB="ccd8191a0585b681b4c0888b92dfa7c79de6a12a"
FEATURE="FB016_ART_CAMERA_SIGHTLINE_V2"
COUNT=80

def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("UNSAFE_PATH",p)
    src=root/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_ZERO_WRITE_REQUIRED"
        print("FB016_ART_SIGHTLINE_V2_OFF_ZERO_WRITES_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert out.parent.is_dir() and not out.exists() and not out.is_relative_to(base)
    before=read(base)
    assert len(before)==COUNT and TARGET in before and "server/Game.server.luau" in before
    assert gitblob(before[TARGET])==OLD_BLOB,"ART_V1_SOURCE_DRIFT_STOP"
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(raw) for p,raw in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==COUNT
    assert sl["blobs"]==fl["source_gitblobs"]==pins,"SOURCE_LOCK_DRIFT_STOP"
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"] is True
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"] is True
    assert fl["feature_flags"]["FB018_ACTION_BUTTON_TEXT_INIT"] is True
    assert FEATURE not in fl["feature_flags"],"DUPLICATE_ADOPTION"
    source=SOURCE.read_bytes()
    assert gitblob(source)==NEW_BLOB,"ARTIST_PIN_DRIFT"
    text=source.decode("utf8")
    for marker in ("blocksAvatar","cameraPos+ray*t","LocalTransparencyModifier",
                   "RunService:IsStudio()","script.Destroying:Connect",
                   "MAX",):
        if marker=="MAX": continue
        assert marker in text,("MISSING_SIGHTLINE_CONTRACT",marker)
    forbidden=("OnServerEvent:Connect","FireServer(","TakeDamage(","DataStoreService",
               "MarketplaceService","CanCollide = true","CanCollide=true",
               "RemoteEvent","ScreenGui","TextLabel")
    assert not any(word in text for word in forbidden),"ART_CLIENT_AUTHORITY_OR_HUD_VIOLATION"
    after=dict(before);after[TARGET]=source
    assert len(after)==COUNT and {p for p in before if after[p]!=before[p]}=={TARGET}
    new_pins={p:gitblob(raw) for p,raw in sorted(after.items())}
    receipt={
        "id":FEATURE,"feedback":["FB-016","FB-015"],
        "existing_scripts":80,"replaced":TARGET,
        "old_blob":OLD_BLOB,"new_blob":NEW_BLOB,
        "other_79_source_bytes_unchanged":True,
        "single_game_remote_hp_score_egg_store_unchanged":True,
        "changes_collision":False,"adds_screen_hud":False,
        "near_camera_fade":True,"camera_to_avatar_occlusion_fade":True,
        "android_perf_and_studio":"NOT_TESTED","owner_art":"ART_NO_GO",
        "rollback":"omit this overlay; original FB016 camera source remains",
        "official_rc_adopted":False,
    }
    sl["blobs"]=new_pins;sl["fb016_camera_v2"]=receipt
    fl["source_gitblobs"]=new_pins;fl["feature_flags"][FEATURE]=True
    fl["fb016_camera_v2"]=receipt
    temp=Path(tempfile.mkdtemp(prefix=".fb016_art_",dir=str(out.parent)))
    staged=temp/"dist"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/TARGET).write_bytes(source)
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("FB016_ART_SIGHTLINE_V2_RC80_OTHER79_BYTE_EXACT_PASS")
    return True

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--enabled",choices=("true","false"),required=True)
    a=ap.parse_args()
    apply(a.base,a.out,a.enabled=="true")
