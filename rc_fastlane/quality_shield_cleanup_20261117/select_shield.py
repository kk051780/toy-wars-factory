#!/usr/bin/env python3
"""GQ8 unique: remove ALL prior-round ITEM shields during replay, not just first.
No new Game/Remote/Store, no item acquisition changes; 31-source RC overlay.
"""
import argparse, copy, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET

FEATURE="GQ8_MULTI_SHIELD_REPLAY_CLEANUP_20261117"
MODULE="EGGRUMBLE_RoundReplay"
BEFORE=''' local shield=ch and ch:FindFirstChild("EGGRUMBLE_ItemShield")
 if shield and shield:IsA("ForceField") then shield:Destroy() end'''
AFTER=''' -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN
 -- A player can acquire multiple distinct SHIELD pickups during one round.
 -- Destroy only our own ForceFields, including every copy, before replay.
 if ch then
  for _,effect in ipairs(ch:GetChildren()) do
   if effect.Name=="EGGRUMBLE_ItemShield" and effect:IsA("ForceField") then
    effect:Destroy()
   end
  end
 end
 -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_END'''
FILE="EGGRUMBLE_RoundReplay_GQ8_MULTI_SHIELD.luau"
RECEIPT="GQ8_MULTI_SHIELD_RECEIPT.json"

def mapping(path):
    project=json.loads(path.read_text(encoding="utf-8"))
    found={}
    def walk(node,route=()):
        for name,obj in node.items():
            if name.startswith("$"):continue
            if not isinstance(obj,dict):raise ValueError("RED_NON_SCRIPT_NODE")
            key=route+(name,)
            if "$path" in obj:
                if set(obj)!={"$path"} or key in found:raise ValueError("RED_INVALID_SOURCE_ENTRY")
                found[key]=(path.parent/obj["$path"]).resolve(strict=True)
            else:walk(obj,key)
    walk(project["tree"])
    matched=[k for k in found if k[-1]==MODULE]
    if len(found)!=31 or len(matched)!=1 or len(set(k[-1] for k in found))!=31:
        raise ValueError("RED_SOURCE_COUNT_OR_ROUND_REPLAY_SINGLETON")
    return project,found,matched[0]

def patch(src):
    if src.count(BEFORE)!=1 or "GQ8_MULTI_SHIELD_REPLAY_CLEANUP" in src:
        raise ValueError("RED_ORIGINAL_REPLAY_SHIELD_ANCHOR_DRIFT")
    if "function Replay.resetHuman(" not in src or "function Replay.captureWalkBaseline(" not in src:
        raise ValueError("RED_ORIGINAL_REPLAY_OWNER_MISSING")
    new=src.replace(BEFORE,AFTER,1)
    if unpatch(new)!=src:raise ValueError("RED_OFF_ROLLBACK_NOT_EXACT")
    return new

def unpatch(src):
    if src.count(AFTER)!=1:raise ValueError("RED_PATCHED_REPLAY_ANCHOR_DRIFT")
    return src.replace(AFTER,BEFORE,1)

def prepare(base,out):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent:raise ValueError("RED_COLLIDING_OUTPUT")
    obj,files,key=mapping(base)
    old=files[key].read_text(encoding="utf-8")
    new=patch(old)
    target=out.parent/FILE
    if target.exists():raise ValueError("RED_COLLIDING_FILE")
    target.write_text(new,encoding="utf-8")
    selected=copy.deepcopy(obj)
    cursor=selected["tree"]
    for k in key:cursor=cursor[k]
    cursor["$path"]=FILE
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,latest,_=mapping(out)
    changes=[k for k in files if files[k].read_bytes()!=latest[k].read_bytes()]
    if changes!=[key]:raise ValueError("RED_OTHER_DOMAIN_SOURCE_CHANGED")
    if unpatch(new)!=old:raise ValueError("RED_ROLLBACK")
    evidence={"feature_id":FEATURE,"base_project":base.name,
              "selected_project":out.name,"source_count":31,
              "changed_script":MODULE,"other30_exact":True,
              "one_source_off_rollback_exact":True,
              "script_count_delta":0,"new_remote_store_game":0,
              "original_blob_anchor":"a97e7aeffc988fe9ccde5bf7544b01deb5f243ff",
              "original_code_sha256":hashlib.sha256(old.encode()).hexdigest(),
              "selected_code_sha256":hashlib.sha256(new.encode()).hexdigest(),
              "native":"PENDING","rojo":"PENDING","official_adopted":False,
              "studio_android_owner_fun":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print("GQ8_MULTI_SHIELD_PREP_ONE_REPLAY_OTHER30_OFF_EXACT_PASS")

def verify(base,out,place):
    _,old,key=mapping(base)
    _,new,newkey=mapping(out)
    if set(old)!=set(new) or newkey!=key or len(new)!=31:
        raise ValueError("RED_SCRIPT_MAP_CHANGED")
    orig=old[key].read_text(encoding="utf-8")
    patched=new[key].read_text(encoding="utf-8")
    if patch(orig)!=patched or unpatch(patched)!=orig:
        raise ValueError("RED_UNEXPECTED_REPLAY_DELTA")
    if [k for k in old if old[k].read_bytes()!=new[k].read_bytes()]!=[key]:
        raise ValueError("RED_OTHER30_DRIFT")
    real={}
    for item in ET.parse(place).getroot().iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        p=item.find("Properties")
        if p is None:raise ValueError("RED_MISSING_PROPERTIES")
        name=p.findtext("string[@name='Name']")
        src=p.findtext("ProtectedString[@name='Source']")
        if src is None:src=p.findtext("string[@name='Source']")
        if not name or src is None or name in real:raise ValueError("RED_EMBEDDED_SOURCE")
        real[name]=(klass,src.replace("\r\n","\n"))
    if len(real)!=31 or set(real)!={k[-1] for k in new}:
        raise ValueError("RED_PLACE_NOT_CURRENT31")
    for key,path in new.items():
        klass="Script" if path.name.endswith(".server.luau") else ("LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if real[key[-1]]!=(klass,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_CLASS "+key[-1])
    receipt=out.parent/RECEIPT
    data=json.loads(receipt.read_text())
    data.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
                place_sha256=hashlib.sha256(place.read_bytes()).hexdigest())
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    print("GQ8_MULTI_SHIELD_REAL_ROJO31_NATIVE31_EXACT_PASS",data["place_bytes"])

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("command",choices=["prepare","verify"])
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--place",type=Path)
    v=a.parse_args()
    if v.command=="prepare":prepare(v.base,v.out)
    else:
        if v.place is None:a.error("--place required")
        verify(v.base,v.out,v.place)
