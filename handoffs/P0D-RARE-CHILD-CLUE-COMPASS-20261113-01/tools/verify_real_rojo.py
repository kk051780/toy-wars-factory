"""Audit actual generated Rojo .rbxlx: TEN exact Luau source bytes and authority.
This checks file packaging, NEVER actual Roblox Studio gameplay.
"""
from pathlib import Path
import argparse,hashlib,json,xml.etree.ElementTree as ET
from verify_candidate_delta import verify as verify_delta
ROOT=Path(__file__).resolve().parents[1]
W=ROOT.parent/"P0D-WORLD-RARE-4REALMS-3D-20261112-01"
N=ROOT.parent/"P0D-WORLD-RARE-NEUTRAL-ENCOUNTERS-20261112-01"
B=ROOT.parent/"P0D-RARE-DISCOVERY-BOOK-20261112-01"
M={
 "ServerScriptService/RareRealmCatalog":("ModuleScript",W/"src/RareRealmCatalog.luau"),
 "ServerScriptService/RareRealmScene":("ModuleScript",W/"src/RareRealmScene.luau"),
 "ServerScriptService/RareEncounterPolicy":("ModuleScript",N/"src/RareEncounterPolicy.luau"),
 "ServerScriptService/RareEncounterModels":("ModuleScript",N/"src/RareEncounterModels.luau"),
 "ServerScriptService/RareDiscoveryBook":("ModuleScript",B/"src/RareDiscoveryBook.luau"),
 "ServerScriptService/RareDiscoveryHUD":("ModuleScript",B/"src/RareDiscoveryHUD.luau"),
 "ServerScriptService/RareDiscoveryQAPlan":("ModuleScript",B/"src/RareDiscoveryQAPlan.luau"),
 "ServerScriptService/RareCluePolicy":("ModuleScript",ROOT/"src/RareCluePolicy.luau"),
 "ServerScriptService/RareClueHUD":("ModuleScript",ROOT/"src/RareClueHUD.luau"),
 "ServerScriptService/RareDiscoveryCluePreview":("Script",ROOT/"src/RareDiscoveryCluePreview.server.luau")
}
class Reject(ValueError):pass
def check(value,why):
    if not value:raise Reject(why)
def prop(item,name):
    ps=item.find("Properties")
    if ps is None:return None
    for p in ps:
        if p.get("name")==name:return p.text or ""
    return None
def parse(raw):
    try:root=ET.fromstring(raw)
    except ET.ParseError as e:raise Reject("broken genuine Roblox XML") from e
    check(root.tag=="roblox","non-Roblox document")
    found=[]
    def go(node,anc):
        for x in node:
            if x.tag!="Item":continue
            typ,name=x.get("class"),prop(x,"Name")
            check(bool(typ and name),"invalid unnamed item")
            path=anc if typ=="DataModel" else (*anc,name)
            found.append(("/".join(path),typ,prop(x,"Source")))
            go(x,path)
    go(root,())
    return found
def verify(raw):
    verify_delta()
    manifests={}
    for folder in (W,N,B,ROOT):
        doc=json.loads((folder/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
        for row in doc["files"]:
            manifests[(folder/row["path"]).resolve()]=row
    for expected_cls,path in M.values():
        rawfile=path.read_bytes()
        record=manifests.get(path.resolve())
        check(record is not None and len(rawfile)==record["size"] and
              hashlib.sha256(rawfile).hexdigest()==record["sha256"],
              "original candidate source SHA mismatch before real Rojo")
    sources=[x for x in parse(raw) if x[1] in ("Script","ModuleScript","LocalScript")]
    check(len(sources)==10,"wrong script count")
    seen=set()
    for loc,cls,content in sources:
        check(loc in M and loc not in seen,"unlisted/duplicate source")
        expected,sourcepath=M[loc]
        check(cls==expected,"wrong Script class / game authority")
        check(content is not None and content.encode("utf-8")==sourcepath.read_bytes(),
              "embedded original source bytes not exact "+loc)
        seen.add(loc)
    check(seen==set(M),"missing one of 10 source scripts")
    check(sum(x[1]=="Script" for x in sources)==1,"more than one server authority")
    studio=next(source for loc,cls,source in sources
        if loc=="ServerScriptService/RareDiscoveryCluePreview")
    check("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false" in studio,"unpublished demo auto-enabled")
    check("RunService:IsStudio()" in studio and "RunService:IsServer()" in studio and
          "TRAP_RAIDERS_S1" in studio,"official source overlap or server guard missing")
    check("OnServerEvent" not in studio and "FireServer" not in studio,
          "client remote game authority in source")
    return {
       "format":"P0D_CHILD_CLUE_REAL_ROJO_SOURCE_REVIEW_V1",
       "rbxlx_bytes":len(raw),
       "rbxlx_sha256":hashlib.sha256(raw).hexdigest(),
       "source_byte_exact_count":len(seen),
       "new_clue_modules_byte_exact":2,
       "original_full_server_plus_only_four_hooks":True,
       "preview_default_enabled":False,
       "actual_studio_2client":False,
       "actual_mobile_qa":False,
       "production_release":False
    }
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--place",required=True)
    ap.add_argument("--receipt",required=True)
    args=ap.parse_args()
    raw=Path(args.place).read_bytes()
    check(len(raw)>5000,"not a real Roblox Place")
    result=verify(raw)
    Path(args.receipt).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                                 encoding="utf-8")
    print("P0D_CHILD_CLUE_ACTUAL_ROJO_TEN_EXACT_SCRIPTS_PASS")
    print("P0D_CHILD_CLUE_ACTUAL_ROJO_RBXLX_SHA256="+result["rbxlx_sha256"])
    print("P0D_CHILD_CLUE_ACTUAL_ROJO_RBXLX_BYTES="+str(result["rbxlx_bytes"]))
    print("P0D_CHILD_CLUE_REAL_ROBLOX_STUDIO_NOT_TESTED")
if __name__=="__main__":
    main()
