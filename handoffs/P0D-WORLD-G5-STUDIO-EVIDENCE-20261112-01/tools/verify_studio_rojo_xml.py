"""Inspect real Rojo .rbxlx: 2 exact frozen origin modules + new server Plan and disabled probe."""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT.parent/"P0D-WORLD-LINK-G5-20261112-01"
MAP={
  "ServerScriptService/WorldLinkScene":("ModuleScript",ORIGINAL/"src/WorldLinkScene.luau"),
  "ServerScriptService/WorldLinkRoutes":("ModuleScript",ORIGINAL/"src/WorldLinkRoutes.luau"),
  "ServerScriptService/G5StudioCheckpointPlan":("ModuleScript",ROOT/"src/G5StudioCheckpointPlan.luau"),
  "ServerScriptService/WorldG5StudioEvidence":("Script",ROOT/"src/WorldG5StudioEvidence.server.luau"),
}
FROZEN_BLOBS={"WorldLinkScene":"645e5ecc213a0e7463b77e419f3764d3395cd1d8",
              "WorldLinkRoutes":"3ff7debee01839ee595479b1cdefa169f8b153d3"}
class GateError(ValueError):pass

def req(value,message):
    if not value: raise GateError(message)

def prop(node,name):
    p=node.find("Properties")
    if p is None:return None
    for x in p:
        if x.get("name")==name:return x.text or ""
    return None

def walk(xml):
    try:root=ET.fromstring(xml)
    except ET.ParseError as e:raise GateError("invalid rbxlx XML") from e
    req(root.tag=="roblox","invalid root")
    objects=[]
    def descend(node,parents):
        for c in node:
            if c.tag!="Item":continue
            cl=c.get("class");name=prop(c,"Name")
            req(bool(cl and name),"no instance name/class")
            path=parents if cl=="DataModel" else (*parents,name)
            objects.append(("/".join(path),cl,prop(c,"Source")))
            descend(c,path)
    descend(root,())
    return objects

def verify(xml):
    scripts=[(p,c,s) for p,c,s in walk(xml) if c in {"Script","LocalScript","ModuleScript"}]
    req(len(scripts)==4,"wrong script count; fail closed")
    observed=set()
    for p,c,source in scripts:
        req(p in MAP and p not in observed,"unlisted/duplicate script")
        klass,path=MAP[p]
        req(klass==c,"script class mismatch")
        req(source is not None,"source missing")
        req(source.encode("utf-8")==path.read_bytes(),"source bytes mismatch: "+p)
        observed.add(p)
    req(observed==set(MAP),"missing expected module")
    req(sum(c=="Script" for _,c,_ in scripts)==1,"server script authority count")
    probe=next(s for p,c,s in scripts if p=="ServerScriptService/WorldG5StudioEvidence")
    req("ENABLE_G5_STUDIO_EVIDENCE = false" in probe,"probe default not safe")
    req("RunService:IsStudio()" in probe,"nonStudio import guard missing")
    req("G5_REAL_STUDIO_LOCAL_EVIDENCE" in probe,"no actual Studio receipt marker")
    req("OnServerEvent" not in probe and "FireServer" not in probe,"untrusted remotes")
    return {"file_format":"G5_STUDIO_PROBE_REAL_ROJO_REVIEW_ONLY",
       "rbxlx_sha256":hashlib.sha256(xml).hexdigest(),"rbxlx_bytes":len(xml),
       "original_module_sources_exact":2,"probe_and_plan_sources_exact":2,
       "all_four_script_bytes_exact":True,"probe_initially_disabled":True,
       "actual_roblox_studio_play_2clients":False,
       "actual_mobile_physics_tested":False,
       "real_game_included":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--place",required=True)
    p.add_argument("--receipt",required=True)
    args=p.parse_args()
    xml=Path(args.place).read_bytes()
    req(len(xml)>5000,"invalid tiny Place file")
    receipt=verify(xml)
    Path(args.receipt).write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("G5_STUDIO_PROBE_REAL_ROJO_EXACT_SOURCE_4_OF_4_PASS")
    print("G5_STUDIO_PROBE_RBXLX_SHA256="+receipt["rbxlx_sha256"])
    print("G5_STUDIO_PROBE_RBXLX_BYTES="+str(receipt["rbxlx_bytes"]))
    print("G5_STUDIO_PROBE_ACTUAL_STUDIO_NOT_TESTED")
if __name__=="__main__":main()
