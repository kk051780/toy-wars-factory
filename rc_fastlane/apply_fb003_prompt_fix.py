#!/usr/bin/env python3
"""#470 original FB003 V2/V3 prompt fixes, source-locked and reversible.
Only two original Luau sources change, 80 others byte-identical.
Real gameplay pass requires OWNER Studio/Android confirmation.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
GAME="server/Game.server.luau"
MAP="server/MapBuilder.luau"
GAME_PIN="6533f2b3ec106141508e70027f7dc9844c8cbcb0"
MAP_PIN="94655d019fdf9798fa24a350ebf49f8290465ac0"
FEATURE="FB003_OWNER_PROMPT_ACCESS_AND_H2_DISAMBIGUATION_V1"

def blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def read(root):
    assert root.is_dir() and not root.is_symlink()
    assert not any(p.is_symlink() for p in root.rglob("*"))
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def once(s,a,b):
    assert s.count(a)==1,("ANCHOR_MISMATCH",a[:60],s.count(a))
    return s.replace(a,b,1)

def patch(data):
    assert blob(data[GAME])==GAME_PIN and blob(data[MAP])==MAP_PIN,"ORIGINAL_82_SOURCE_DRIFT"
    g=data[GAME].decode("utf8");m=data[MAP].decode("utf8")
    # Reuse existing #470 V2 usability proposal, no server distance change.
    m=once(m,"    p.HoldDuration = 0.35\n","    p.HoldDuration = 0\n")
    m=once(m,"    p.MaxActivationDistance = 10\n","    p.MaxActivationDistance = 12\n")
    # Reuse #470 V3. Deposited SCORE_5 eggs appear only 4-4.5 studs
    # above the home score pad: separate egg F/Y from pad E/X.
    g=once(g,'        def.part.CFrame=CFrame.new(def.home)\n        def.part.Transparency=',
           '        def.part.CFrame=CFrame.new(def.home)\n'
           '        def.prompt.KeyboardKeyCode=Enum.KeyCode.E\n'
           '        def.prompt.GamepadKeyCode=Enum.KeyCode.ButtonX\n'
           '        def.part.Transparency=')
    g=once(g,'            def.part.Transparency=0\n'
           '            def.prompt.Enabled=match.phase=="ACTIVE" and h2ScoreState~=nil',
           '            def.part.Transparency=0\n'
           '            def.prompt.KeyboardKeyCode=Enum.KeyCode.E\n'
           '            def.prompt.GamepadKeyCode=Enum.KeyCode.ButtonX\n'
           '            def.prompt.Enabled=match.phase=="ACTIVE" and h2ScoreState~=nil')
    g=once(g,'    def.part.Transparency=0\n    def.prompt.Enabled=true\n    match.scores.RED=',
           '    def.part.Transparency=0\n'
           '    def.prompt.KeyboardKeyCode=Enum.KeyCode.F\n'
           '    def.prompt.GamepadKeyCode=Enum.KeyCode.ButtonY\n'
           '    def.prompt.Enabled=true\n    match.scores.RED=')
    assert g.count("remote.OnServerEvent:Connect(")==1
    assert g.count("H2Score.deposit(")==1 and g.count("H2Score.pickup(")==1
    assert g.count("def.prompt.KeyboardKeyCode=Enum.KeyCode.E")==2
    assert g.count("def.prompt.KeyboardKeyCode=Enum.KeyCode.F")==1
    assert g.count("def.prompt.GamepadKeyCode=Enum.KeyCode.ButtonY")==1
    after=dict(data);after[GAME]=g.encode("utf8");after[MAP]=m.encode("utf8")
    assert {p for p in data if after[p]!=data[p]}=={GAME,MAP}
    return after

def apply(base,out,enabled):
    assert not out.exists(),"OUTPUT_ALREADY_EXISTS"
    if not enabled:
        print("P0D_FB003_OFF_ZERO_WRITE");return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==82
    sl=json.loads((base/"SOURCE_LOCK.json").read_text())
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text())
    pins={p:blob(v) for p,v in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==82
    assert sl["blobs"]==fl["source_gitblobs"]==pins,"SOURCE_LOCK_DRIFT"
    assert FEATURE not in fl["feature_flags"],"ALREADY_APPLIED"
    after=patch(before)
    newpins={p:blob(v) for p,v in sorted(after.items())}
    receipt={"feature_id":FEATURE,"source_count":82,"changed":[GAME,MAP],
             "other80_byte_exact":True,"original_author":"#470 FB003 V2/V3",
             "real_studio_test":"NOT_TESTED","owner_accepted":False,
             "product_quality":"NO_GO","rollback":"omit overlay, old82 unchanged",
             "old_blobs":{p:pins[p] for p in (GAME,MAP)},
             "new_blobs":{p:newpins[p] for p in (GAME,MAP)}}
    sl["blobs"]=newpins;fl["source_gitblobs"]=newpins
    fl["feature_flags"][FEATURE]=True
    sl["fb003_prompt_v1"]=fl["fb003_prompt_v1"]=receipt
    temp=Path(tempfile.mkdtemp(prefix=".p0d_fb003_",dir=str(out.parent)))
    stage=temp/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        for p in (GAME,MAP):(stage/"src"/p).write_bytes(after[p])
        for name,obj in (("SOURCE_LOCK.json",sl),("RC_FEATURE_LOCK.json",fl)):
            (stage/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
        assert read(base)==before and read(stage)==after
        os.replace(stage,out)
    finally:shutil.rmtree(temp,ignore_errors=True)
    print("P0D_FB003_REAL82_GAME_MAP_PATCH_PASS",newpins[GAME],newpins[MAP])
    return True

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--enabled",choices=("true","false"),required=True)
    a=ap.parse_args()
    apply(a.base,a.out,a.enabled=="true")
