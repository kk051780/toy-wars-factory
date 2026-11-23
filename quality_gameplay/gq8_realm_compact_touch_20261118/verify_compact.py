#!/usr/bin/env python3
"""GQ8: zero-new-authority compact realm mobile HUD, original-author source exactness."""
import argparse
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
ORIGINAL=REPO/"_realm764/handoffs/EGGRUMBLE-REALM-CORE-20261118/EGGRUMBLE_RealmBattleControls.client.luau"
CANDIDATE=HERE/"EGGRUMBLE_RealmBattleControls.client.luau"
ORIGINAL_BLOB="058af03e9f43ac9aa45e8833d7bd99534902189d"
ANCHOR=' notice.Visible=isFlight\n if isFlight then'
INSERT=''' notice.Visible=isFlight
 -- GQ8 mobile: compact non-flight controls so one action does not cover battle.
 -- Re-layout only when the mounted mode changes; no new remote or authority.
 if currentKind~=previous then
  local panelHeight=isFlight and 260 or 90
  frame.Size=UDim2.fromOffset(218,panelHeight)
  frame.Position=UDim2.new(1,-230,1,-(panelHeight+16))
  gun.Position=UDim2.fromOffset(5,isFlight and 122 or 34)
  cannon.Position=UDim2.fromOffset(5,34)
  breath.Position=UDim2.fromOffset(5,34)
  hydro.Position=UDim2.fromOffset(5,34)
 end
 if isFlight then'''
ROUTE=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls")

def git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def exact_source():
    original=ORIGINAL.read_bytes()
    candidate=CANDIDATE.read_bytes()
    assert git_blob(original)==ORIGINAL_BLOB,"RED_ORIGINAL_REALM_CLIENT_DRIFT"
    before=original.decode("utf-8")
    after=candidate.decode("utf-8")
    assert before.count(ANCHOR)==1,"RED_ANCHOR_DRIFT"
    assert after==before.replace(ANCHOR,INSERT,1),"RED_UNREVIEWED_CLIENT_DELTA"
    assert after.count('remote:FireServer(')==before.count('remote:FireServer('),"RED_NEW_REMOTE"
    for token in ("pilotKind()","cannon.Visible=isShip",
                  "breath.Visible=isBeast","hydro.Visible=isDiver",
                  'frame.Visible=active','held[k]=false'):
        assert token in after,"RED_LOST_ORIGINAL_CONTROL_"+token
    return original,candidate

def flatten(project):
    project=Path(project).resolve(strict=True)
    tree=json.loads(project.read_text(encoding="utf-8"))["tree"]
    files={}
    def walk(n,route=()):
        for k,v in n.items():
            if k.startswith("$"):continue
            p=route+(k,)
            if "$path" in v:
                assert p not in files,"RED_DUPLICATE_SOURCE"
                files[p]=(project.parent/v["$path"]).resolve(strict=True)
            else:walk(v,p)
    walk(tree)
    return files

def compose(official36,off31,out):
    original,candidate=exact_source()
    official36=Path(official36).resolve(strict=True)
    off31=Path(off31).resolve(strict=True)
    out=Path(out).resolve()
    assert not out.exists(),"RED_DO_NOT_OVERWRITE"
    assert out.parent==official36.parent,"RED_SAME_PARENT_REQUIRED"
    files=flatten(official36)
    back=flatten(off31)
    assert len(files)==36 and len(back)==31,"RED_NOT_REAL36_OFF31"
    assert ROUTE in files and files[ROUTE].read_bytes()==original,"RED_REALM_AUTHOR_NOT_ORIGINAL"
    assert ROUTE not in back,"RED_BASE_HAS_REALM_CLIENT"
    model=json.loads(official36.read_text(encoding="utf-8"))
    node=model["tree"]
    for x in ROUTE:node=node[x]
    node["$path"]=os.path.relpath(CANDIDATE,out.parent).replace(os.sep,"/")
    out.write_text(json.dumps(model,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    new=flatten(out)
    assert set(new)==set(files),"RED_SOURCE_SET_CHANGED"
    assert new[ROUTE].read_bytes()==candidate,"RED_COMPACT_NOT_SELECTED"
    for r in files:
        if r!=ROUTE:assert files[r].read_bytes()==new[r].read_bytes(),"RED_OTHER_LANE_MUTATION"
    record={"feature_id":"GQ8_REALM_COMPACT_TOUCH_HUD_20261118",
      "count":36,"original_count":31,"patched_routes":["/".join(ROUTE)],
      "original_client_git_blob":ORIGINAL_BLOB,
      "patched_client_git_blob":git_blob(candidate),
      "exact_only_one_client_difference":True,
      "off31_byte_exact":True,"no_new_remote_or_authority":True,
      "production_published":False,"studio_2client":"NOT_TESTED",
      "android_15min":"NOT_TESTED","fun":"NO_GO","official_rc_adopted":False}
    out.with_suffix(".receipt.json").write_text(json.dumps(record,indent=2)+"\n")
    return record

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--off31",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    print(json.dumps(compose(a.project,a.off31,a.out),ensure_ascii=False))
