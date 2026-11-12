"""Actual Rojo binary 8-source unmodified originals + new Book source byte audit."""
from pathlib import Path
import argparse,hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT.parent/"P0D-WORLD-RARE-NEUTRAL-ENCOUNTERS-20261112-01"
WORLD=ROOT.parent/"P0D-WORLD-RARE-4REALMS-3D-20261112-01"
MAP={
 "ServerScriptService/RareRealmCatalog":("ModuleScript",WORLD/"src/RareRealmCatalog.luau"),
 "ServerScriptService/RareRealmScene":("ModuleScript",WORLD/"src/RareRealmScene.luau"),
 "ServerScriptService/RareEncounterPolicy":("ModuleScript",PREV/"src/RareEncounterPolicy.luau"),
 "ServerScriptService/RareEncounterModels":("ModuleScript",PREV/"src/RareEncounterModels.luau"),
 "ServerScriptService/RareDiscoveryBook":("ModuleScript",ROOT/"src/RareDiscoveryBook.luau"),
 "ServerScriptService/RareDiscoveryHUD":("ModuleScript",ROOT/"src/RareDiscoveryHUD.luau"),
 "ServerScriptService/RareDiscoveryQAPlan":("ModuleScript",ROOT/"src/RareDiscoveryQAPlan.luau"),
 "ServerScriptService/RareDiscoveryStudio":("Script",ROOT/"src/RareDiscoveryStudio.server.luau"),
}
class Reject(ValueError):pass
def req(v,reason):
    if not v:raise Reject(reason)
def prop(node,name):
    parent=node.find("Properties")
    if parent is None:return None
    for item in parent:
        if item.get("name")==name:return item.text or ""
    return None
def parse(raw):
    try:root=ET.fromstring(raw)
    except ET.ParseError as err:raise Reject("invalid original Rojo rbxlx") from err
    req(root.tag=="roblox","non Roblox root")
    result=[]
    def visit(node,names):
        for ch in node:
            if ch.tag!="Item":continue
            kind,name=ch.get("class"),prop(ch,"Name")
            req(bool(kind and name),"unnamed Roblox Instance")
            path=names if kind=="DataModel" else (*names,name)
            result.append(("/".join(path),kind,prop(ch,"Source")))
            visit(ch,path)
    visit(root,())
    return result
def verify(raw):
    manifest={}
    for package in (ROOT,PREV,WORLD):
        m=json.loads((package/"BUILD_MANIFEST.json").read_text("utf-8"))
        for line in m["files"]:
            manifest[(package/line["path"]).resolve()]=line
    for kind,path in MAP.values():
        source=path.read_bytes()
        record=manifest.get(path.resolve())
        req(record is not None,"source not locked")
        req(hashlib.sha256(source).hexdigest()==record["sha256"] and
            len(source)==record["size"],"source changed on disk")
    scripts=[(path,kind,source) for path,kind,source in parse(raw)
        if kind in ("Script","ModuleScript","LocalScript")]
    req(len(scripts)==8,"wrong number of Roblox server script sources")
    seen=set()
    for path,kind,source in scripts:
        req(path in MAP and path not in seen,"unexpected/duplicate script")
        expected,original=MAP[path]
        req(kind==expected,"client game source replacement")
        req(source is not None and source.encode("utf-8")==original.read_bytes(),
            "genuine Rojo source bytes mismatch "+path)
        seen.add(path)
    req(seen==set(MAP),"missing one script")
    req(sum(kind=="Script" for _,kind,source in scripts)==1,"extra script authority")
    demo=next(source for path,kind,source in scripts if path=="ServerScriptService/RareDiscoveryStudio")
    req("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false" in demo,"dangerous auto run")
    req("RunService:IsStudio()" in demo and "RunService:IsServer()" in demo,
        "server and nonproduction guard gone")
    req("TRAP_RAIDERS_S1" in demo,"official S1 overlap guard gone")
    req("OnServerEvent" not in demo and "FireServer" not in demo,"untrusted remote")
    return {"format":"RARE_BOOK_REAL_ROJO_REVIEW_ONLY",
        "place_sha256":hashlib.sha256(raw).hexdigest(),"place_bytes":len(raw),
        "embedded_original_sources_exact":8,
        "prior_frozen_world_sources_exact":2,
        "prior_frozen_neutral_sources_exact":2,
        "new_journal_sources_exact":4,
        "default_enabled":False,
        "actual_roblox_studio_2client":False,"mobile_qa":False,
        "game_published":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--place",required=True)
    p.add_argument("--receipt",required=True)
    a=p.parse_args()
    raw=Path(a.place).read_bytes()
    req(len(raw)>5000,"too small for authentic source")
    data=verify(raw)
    Path(a.receipt).write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print("RARE_BOOK_ACTUAL_ROJO_8_EXACT_LUAU_SOURCES_PASS")
    print("RARE_BOOK_ACTUAL_ROJO_BINARY_SHA256="+data["place_sha256"])
    print("RARE_BOOK_ACTUAL_ROJO_BYTES="+str(data["place_bytes"]))
    print("RARE_BOOK_ACTUAL_STUDIO_TWO_CLIENT_NOT_TESTED")
if __name__=="__main__":main()
