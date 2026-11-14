#!/usr/bin/env python3
"""FB-018: repair Roblox default 'Button' label in the real RC80 battle HUD.
Source-locked atomic 80->80 override. No Game, score, HP, UI authority changes.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
TARGET="client/HUD.client.luau"
OLD="e853b2d6d7ff3e84036f096fab704dbc8beb1d83"
FEATURE="FB018_ACTION_BUTTON_TEXT_INIT"
LABEL_OLD="    b.Name = name\n    b.Size = size"
LABEL_NEW="    b.Name = name\n    b.Text = text\n    b.Size = size"
POWER_OLD="    awakenButton.Visible=isPower"
POWER_NEW="    awakenButton.Visible=isPower and (pLv>=10 or s.powerAwakened==true or tell>0)"
def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def read(dist:Path)->dict[str,bytes]:
    assert dist.is_dir() and not dist.is_symlink()
    for p in dist.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(dist.resolve()),p
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes() for p in sorted(root.rglob("*.luau"))}
def patch(data:bytes)->bytes:
    src=data.decode("utf8")
    assert src.count(LABEL_OLD)==1,("BUTTON_HELPER_DRIFT",src.count(LABEL_OLD))
    assert src.count(POWER_OLD)==1,("POWER_CONTROL_DRIFT",src.count(POWER_OLD))
    fixed=src.replace(LABEL_OLD,LABEL_NEW,1).replace(POWER_OLD,POWER_NEW,1)
    assert fixed.count("    b.Text = text\n")==1
    assert fixed.count(POWER_NEW)==1
    assert "button(gui, \"Attack\"" in fixed
    assert "button(gui,\"ShortCaptureNet\"" in fixed
    assert "button(gui,\"SummonRealScout\"" in fixed
    assert "button(gui,\"EarnedAwakening\"" in fixed
    return fixed.encode("utf8")
def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists()
        print("FB018_OFF_ZERO_WRITES_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert out.parent.is_dir() and not out.exists() and not out.is_relative_to(base)
    original=read(base)
    assert len(original)==80 and blob(original[TARGET])==OLD
    locks=[json.loads((base/name).read_text("utf8")) for name in ("SOURCE_LOCK.json","RC_FEATURE_LOCK.json")]
    sl,fl=locks
    before={p:blob(data) for p,data in sorted(original.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==before
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"] is True
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"] is True
    assert FEATURE not in fl["feature_flags"]
    after=dict(original)
    after[TARGET]=patch(original[TARGET])
    assert len(after)==80 and {p for p in original if original[p]!=after[p]}=={TARGET}
    pins={p:blob(data) for p,data in sorted(after.items())}
    receipt={
        "feedback":"FB-018","id":FEATURE,
        "problem":"Red attack TextButton used default Roblox Button label",
        "fix":"Shared button helper assigns b.Text=text before parenting",
        "unneeded_locked_awakening_button_hidden":True,
        "source_count":80,"changed_sources":[TARGET],
        "other79_byte_exact":True,"old_hud_blob":OLD,"new_hud_blob":pins[TARGET],
        "game_remote_store_hp_score_egg_unchanged":True,
        "owner_studio_retest":"REQUIRED",
        "rollback":"omit FB018 post-composition to recover RC80 NO GUIDES",
    }
    sl["blobs"]=pins;sl["fb018_button_label"]=receipt
    fl["source_gitblobs"]=pins;fl["feature_flags"][FEATURE]=True;fl["fb018_button_label"]=receipt
    temp=Path(tempfile.mkdtemp(prefix=".fb018_",dir=str(out.parent)))
    candidate=temp/"dist"
    try:
        shutil.copytree(base,candidate,symlinks=False)
        (candidate/"src"/TARGET).write_bytes(after[TARGET])
        for name,value in (("SOURCE_LOCK.json",sl),("RC_FEATURE_LOCK.json",fl)):
            (candidate/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(candidate)==after and read(base)==original
        os.replace(candidate,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("FB018_BUTTON_TEXT_INIT_RC80_OTHER79_BYTE_EXACT_PASS")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
