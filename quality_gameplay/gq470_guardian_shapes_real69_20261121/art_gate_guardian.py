#!/usr/bin/env python3
"""#420 source-only visual art gate: no screenshots, FPS or human acceptance implied."""
import argparse,hashlib,json,re
from pathlib import Path
MARK="GQ470_CASTLE_GUARDIAN_SEVEN_SILHOUETTES_REAL69_20261121"
ROLES=("WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE")
OLD_SHA="3b8cf7e9b939213633fde964d81bb5e9508e4fe467ef932ddad0bfbe270bd96b"
NEW_SHA="8803926d71bdc233213a8bdad7589a5c0670061a7be898028872faac8f0fb2da"
def sha(data):return hashlib.sha256(data).hexdigest()
def need(cond,reason):
    if not cond:raise AssertionError("RED_GUARDIAN_ART_"+reason)
def inspect(old,new,lock=True):
    if lock:
        need(sha(old)==OLD_SHA,"ORIGINAL_SOURCE_HASH")
        need(sha(new)==NEW_SHA,"NEW_SOURCE_HASH")
    a=old.decode();b=new.decode()
    need(MARK not in a and b.count(MARK)==1,"MARKER")
    first=b.index("-- "+MARK)
    last=b.index("local function decorate(model:Model",first)
    style=b[first:last]
    need("local GUARDIAN_STYLE={" in style,"STYLE_OWNER")
    need(all(x not in style for x in ("Instance.new","part(","RemoteEvent","Enum.Material.Neon")),"NO_NEON_OR_NEW_INSTANCE")
    need("MAX_GLOBAL=12" in a and "MAX_GLOBAL=12" in b,"ACTOR_BUDGET")
    for fragment in ("part(model,","Instance.new(","CanCollide=true","RemoteEvent","DataStoreService","MarketplaceService","Heartbeat","RenderStepped"):
        need(a.count(fragment)==b.count(fragment),"NO_EXTRA_"+fragment)
    suffix="local function createActor(parent:Instance"
    need(a[a.index(suffix):]==b[b.index(suffix):],"GAMEPLAY_AND_SESSION_SUFFIX")
    keys=set(re.findall(r"^ ([A-Z]+)=\{id=",a,re.M))
    roles=set(re.findall(r"^ ([A-Z]+)=\{torso=Vector3.new",style,re.M))
    need(keys==roles==set(ROLES),"ROLE_COVERAGE")
    torso,head=[],[]
    for role in ROLES:
        m=re.search(r"^ "+role+r"=\{torso=Vector3.new\(([^)]+)\),head=Vector3.new\(([^)]+)\)",style,re.M)
        need(m is not None,"SHAPE_"+role)
        t=tuple(map(float,m.group(1).split(",")));h=tuple(map(float,m.group(2).split(",")))
        need(len(t)==len(h)==3 and all(.25<=v<=4.0 for v in (*t,*h)),"ROLE_BOUNDS_"+role)
        torso.append(t);head.append(h)
    need(len(set(torso))==len(set(head))==7,"SILHOUETTE_VARIETY")
    ratio=max(t[0] for t in torso)/min(t[0] for t in torso)
    need(ratio>1.5,"ROLE_WIDTH_SPREAD")
    need(len(new)-len(old)<4096,"SOURCE_BYTE_BUDGET")
    return {"schema":"GQ470_GUARDIAN_ART_SOURCE_GATE_V1","feature":MARK,"source_gate":"PASS_SOURCE_ONLY",
      "role_profiles":7,"unique_torso":7,"unique_helmet":7,"torso_width_span":round(ratio,3),
      "source_old_sha256":sha(old),"source_new_sha256":sha(new),
      "old_bytes":len(old),"new_bytes":len(new),"delta_bytes":len(new)-len(old),
      "selected_changed":1,"selected_unchanged":68,"new_parts":0,"new_authority":False,
      "art_gate":"ART_NO_GO","real_screenshots":{"required":32,"verified":0},
      "studio":"NOT_TESTED","android15m":"NOT_TESTED","kid3min":"NOT_TESTED",
      "human_art":"NOT_TESTED","owner_accepted":False}
def negative(old,new):
    mutants=[
      new.replace(MARK.encode(),b"BAD_MARK",1),
      new.replace(b" WARRIOR={torso",b" ALT={torso",1),
      new.replace(b"Enum.Material.Metal",b"Enum.Material.Neon",1),
      new.replace(b"local MAX_GLOBAL=12",b"local MAX_GLOBAL=14",1),
      new.replace(b"local function createActor(parent",b"local function createActorX(parent",1),
      new.replace(b' part(model,"Helm"',b' part(model,"Extra"\n part(model,"Helm"',1)]
    for i,m in enumerate(mutants):
        need(m!=new,"MUTATION_NOOP_"+str(i))
        try:inspect(old,m,False)
        except AssertionError:continue
        raise AssertionError("RED_NEGATIVE_ACCEPTED_"+str(i))
    return len(mutants)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--original",type=Path,required=True)
    p.add_argument("--candidate",type=Path,required=True);p.add_argument("--report",type=Path,required=True)
    a=p.parse_args();old=a.original.read_bytes();new=a.candidate.read_bytes()
    result=inspect(old,new);result["negative_mutants_rejected"]=negative(old,new)
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("GQ470_SEVEN_GUARDIAN_ART_SOURCE_GATE_PASS",json.dumps(result))
