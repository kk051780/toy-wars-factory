#!/usr/bin/env python3
"""RC81 short confirmed-hit readability port into the EXISTING V3 client LocalScript.
No second HUD owner, Game/Remote/damage changes, or runtime script count increase.
Fail closed on a drifting official/author source. OFF restores base 31 exactly.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROUTE=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFeel")
AUTHOR_BLOB="5509326beed0827b020d967cd9562724d8abbd2a"
AUTHOR_HEAD="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
FEATURE="GQ81_CONFIRMED_HIT_042_V3_PORT_20261117"
LABEL_ANCHOR="mark.Parent=gui\n"
PULSE_ANCHOR=" mark.Visible=true;mark.Size=UDim2.fromOffset(12,12)\n"
LABEL_ADD='''local hitToast=Instance.new("TextLabel")
hitToast.Name="ConfirmedHit042"
hitToast.AnchorPoint=Vector2.new(.5,.5)
hitToast.Position=UDim2.new(.5,6,.49,34)
hitToast.Size=UDim2.fromOffset(62,20)
hitToast.BackgroundColor3=Color3.fromRGB(12,20,29)
hitToast.BackgroundTransparency=.28
hitToast.BorderSizePixel=0
hitToast.TextColor3=Color3.new(1,1,1)
hitToast.TextStrokeTransparency=.65
hitToast.TextScaled=true
hitToast.Font=Enum.Font.GothamBold
hitToast.Text="";hitToast.Visible=false
hitToast.Parent=gui
'''
PULSE_ADD=''' hitToast.Text="HIT x"..tostring(math.floor(power))
 hitToast.Visible=true
 task.delay(.42,function()
  if thisPulse==pulse and hitToast.Parent then hitToast.Visible=false end
 end)
'''
def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sha256(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()
def flatten(path:Path):
    path=path.resolve(strict=True)
    obj=json.loads(path.read_text(encoding="utf-8"))
    found={}
    def walk(node,prefix=()):
        for name,val in node.items():
            if name.startswith("$"):continue
            if not isinstance(val,dict):raise ValueError("RED_NON_PROJECT_NODE")
            route=prefix+(name,)
            if "$path" in val:
                if set(val)!={"$path"} or route in found:raise ValueError("RED_DUPLICATE_ROUTE")
                found[route]=(path.parent/val["$path"]).resolve(strict=True)
            else:walk(val,route)
    walk(obj["tree"])
    if len(found)!=31 or ROUTE not in found or len({r[-1] for r in found})!=31:
        raise ValueError("RED_NOT_EXACT_CURRENT31")
    return obj,found
def patch(old:str)->str:
    for token in ("if not RunService:IsStudio() then return end",
                  'player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',
                  "local thisPulse=pulse",
                  "local RECENT_CD=.12","task.delay(.17,function()"):
        if old.count(token)!=1:raise ValueError("RED_EXISTING_CLIENT_DRIFT "+token)
    if old.count("if reduced() then return end")!=2:
        raise ValueError("RED_REDUCED_EFFECTS_GATE_DRIFT")
    for anchor in (LABEL_ANCHOR,PULSE_ANCHOR):
        if old.count(anchor)!=1:raise ValueError("RED_ANCHOR_DRIFT")
    if "ConfirmedHit042" in old:raise ValueError("RED_ALREADY_PORTED")
    new=old.replace(LABEL_ANCHOR,LABEL_ANCHOR+LABEL_ADD,1)
    new=new.replace(PULSE_ANCHOR,PULSE_ANCHOR+PULSE_ADD,1)
    if new.replace(PULSE_ADD,"",1).replace(LABEL_ADD,"",1)!=old:
        raise ValueError("RED_ROLLBACK_NOT_EXACT")
    return new
def class_for(p:Path):
    if p.name.endswith(".server.luau"):return "Script"
    if p.name.endswith(".client.luau"):return "LocalScript"
    return "ModuleScript"
def ensure_author(path:Path):
    raw=path.read_bytes()
    if gitblob(raw)!=AUTHOR_BLOB:raise ValueError("RED_ORIGINAL_482_COMBATFEEL_BLOB")
    return raw
def prepare(args):
    base=Path(args.base).resolve(strict=True)
    out=Path(args.out).resolve()
    if out.exists():raise ValueError("RED_DONT_OVERWRITE")
    author=ensure_author(Path(args.author))
    obj,before=flatten(base)
    if before[ROUTE].read_bytes()!=author:
        raise ValueError("RED_CURRENT_CLIENT_NOT_IMMUTABLE_AUTHOR_482")
    after=patch(author.decode("utf-8")).encode("utf-8")
    out.parent.mkdir(parents=True,exist_ok=True)
    selected_path=out.parent/"EGGRUMBLE_GQ81_ConfirmedHit042.client.luau"
    if selected_path.exists():raise ValueError("RED_EXISTING_PATCH_FILE")
    selected_path.write_bytes(after)
    edited=copy.deepcopy(obj)
    edited["name"]="EGGRUMBLE_V3_31_GQ81_SHORT_TRUE_HIT_SELECT"
    def remap(node,prefix=()):
        for name,val in node.items():
            if name.startswith("$"):continue
            route=prefix+(name,)
            if "$path" in val:
                selected=selected_path if route==ROUTE else before[route]
                val["$path"]=os.path.relpath(selected,out.parent).replace(os.sep,"/")
            else:remap(val,route)
    remap(edited["tree"])
    out.write_text(json.dumps(edited,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,now=flatten(out)
    changed={r for r in before if before[r].read_bytes()!=now[r].read_bytes()}
    if changed!={ROUTE}:raise ValueError("RED_OTHER_30_CHANGED")
    if now[ROUTE].read_bytes()!=after:raise ValueError("RED_PORT_CONTENT")
    print("GQ81_HIT042_V3_ONE_EXISTING_LOCAL_ONLY_OTHER30_EXACT_OFF_PASS")
def verify(args):
    _,before=flatten(Path(args.base))
    _,after=flatten(Path(args.out))
    author=ensure_author(Path(args.author))
    if before[ROUTE].read_bytes()!=author:raise ValueError("RED_AUTHOR_DRIFT")
    expected=patch(author.decode("utf-8")).encode("utf-8")
    if set(before)!=set(after):raise ValueError("RED_SOURCE_ROUTES")
    for r in before:
        if r==ROUTE:
            if after[r].read_bytes()!=expected:raise ValueError("RED_CLIENT_MISMATCH")
        elif after[r].read_bytes()!=before[r].read_bytes():
            raise ValueError("RED_NON_TARGET_CHANGE "+"/".join(r))
    place=Path(args.place)
    if not place.is_file():raise ValueError("RED_NO_ROJO")
    embed={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_NO_PROP")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in embed:raise ValueError("RED_ROJO_NAME_OR_SOURCE")
        embed[name]=(kind,source.replace("\r\n","\n"))
    if len(embed)!=31 or set(embed)!={r[-1] for r in after}:
        raise ValueError("RED_ROJO31_SOURCE_COUNT_OR_NAMES")
    for r,p in after.items():
        if embed[r[-1]]!=(class_for(p),p.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_CLASS "+"/".join(r))
    receipt={
        "feature_id":FEATURE,"base_sources":31,"selected_sources":31,
        "only_changed_script":"/".join(ROUTE),
        "other30_bytes_exact":True,"off_returns_all31_to_base":True,
        "true_server_impact_attribute_only":True,"timer_seconds":.42,
        "author482_head":AUTHOR_HEAD,"author482_blob":AUTHOR_BLOB,
        "changed_local_sha256":sha256(expected),
        "rojo_source_and_class_exact":"31/31",
        "place_bytes":place.stat().st_size,"place_sha256":sha256(place.read_bytes()),
        "studio_android_owner":"NOT_TESTED","rc_adopted":False}
    target=Path(args.out).parent/"GQ81_HIT042_V3_RC31_RECEIPT.json"
    target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ81_HIT042_V3_ROJO31_NATIVE31_SOURCE_EXACT_PASS",receipt["place_bytes"])
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    p.add_argument("--base",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--author",required=True)
    p.add_argument("--place")
    a=p.parse_args()
    if a.action=="prepare":prepare(a)
    else:
        if not a.place:p.error("--place required")
        verify(a)
if __name__=="__main__":main()
