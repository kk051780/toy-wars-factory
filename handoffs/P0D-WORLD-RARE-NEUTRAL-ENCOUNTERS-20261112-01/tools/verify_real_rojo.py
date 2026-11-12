"""Actually built Rojo .rbxlx exact original 5 Luau script source audit. Not Studio."""
from pathlib import Path
import argparse,hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/"P0D-WORLD-RARE-4REALMS-3D-20261112-01"
MAP={
    "ServerScriptService/RareRealmCatalog":("ModuleScript",OLD/"src/RareRealmCatalog.luau"),
    "ServerScriptService/RareRealmScene":("ModuleScript",OLD/"src/RareRealmScene.luau"),
    "ServerScriptService/RareEncounterPolicy":("ModuleScript",ROOT/"src/RareEncounterPolicy.luau"),
    "ServerScriptService/RareEncounterModels":("ModuleScript",ROOT/"src/RareEncounterModels.luau"),
    "ServerScriptService/RareEncounterPreview":("Script",ROOT/"src/RareEncounterPreview.server.luau")
}
class AuditError(ValueError):pass
def must(v,message):
    if not v:raise AuditError(message)
def prop(node,name):
    block=node.find("Properties")
    if block is None:return None
    for p in block:
        if p.get("name")==name:return p.text or ""
    return None
def walk(raw):
    try:root=ET.fromstring(raw)
    except ET.ParseError as e:raise AuditError("invalid Rojo XML") from e
    must(root.tag=="roblox","invalid root")
    result=[]
    def recurse(node,names):
        for c in node:
            if c.tag!="Item":continue
            klass,name=c.get("class"),prop(c,"Name")
            must(klass and name,"missing class or name")
            path=names if klass=="DataModel" else (*names,name)
            result.append(("/".join(path),klass,prop(c,"Source")))
            recurse(c,path)
    recurse(root,())
    return result
def verify(raw):
    ours=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
    old=json.loads((OLD/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
    ours_by={r["path"]:r for r in ours["files"]}
    old_by={r["path"]:r for r in old["files"]}
    for _,path in MAP.values():
        if path.is_relative_to(ROOT):
            rec=ours_by.get(path.relative_to(ROOT).as_posix())
        else:
            rec=old_by.get(path.relative_to(OLD).as_posix())
        must(rec is not None,"script source missing from locked manifest")
        body=path.read_bytes()
        must(hashlib.sha256(body).hexdigest()==rec["sha256"] and len(body)==rec["size"],
            "original source manifest mismatch "+path.name)
    scripts=[v for v in walk(raw) if v[1] in ("Script","ModuleScript","LocalScript")]
    must(len(scripts)==5,"not exactly five script instances")
    seen=set()
    for path,klass,source in scripts:
        must(path in MAP and path not in seen,"script path unknown or duplicate")
        actual_klass,origin=MAP[path]
        must(klass==actual_klass,"wrong source authority")
        must(source is not None and source.encode("utf-8")==origin.read_bytes(),
             "source bytes mismatch "+path)
        seen.add(path)
    must(seen==set(MAP),"missing original module")
    must(sum(k=="Script" for _,k,_ in scripts)==1,"multiple server script authorities")
    demo=next(s for p,k,s in scripts if p=="ServerScriptService/RareEncounterPreview")
    must("ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = false" in demo,"default preview not disabled")
    must("RunService:IsStudio()" in demo and "TRAP_RAIDERS_S1" in demo,
         "live/official guard missing")
    must("OnServerEvent" not in demo and "FireServer" not in demo,"client remote injection")
    return {"format":"RARE_NEUTRAL_ACTUAL_ROJO_SOURCE_ONLY",
        "rbxlx_sha256":hashlib.sha256(raw).hexdigest(),"rbxlx_bytes":len(raw),
        "all_five_sources_exact":True,"original_realm_sources_exact":2,
        "new_neutral_sources_exact":3,"server_preview_default_enabled":False,
        "real_roblox_studio_2client":False,"real_mobile_FPS_tested":False,
        "actual_d18_rare_character_adopted":False,"live_published":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--place",required=True)
    p.add_argument("--receipt",required=True)
    a=p.parse_args()
    raw=Path(a.place).read_bytes()
    must(len(raw)>5000,"file too small")
    receipt=verify(raw)
    Path(a.receipt).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("RARE_NEUTRAL_ACTUAL_ROJO_FIVE_SOURCE_BYTE_EXACT_PASS")
    print("RARE_NEUTRAL_ACTUAL_ROJO_RBXLX_SHA256="+receipt["rbxlx_sha256"])
    print("RARE_NEUTRAL_ACTUAL_ROJO_RBXLX_BYTES="+str(receipt["rbxlx_bytes"]))
    print("RARE_NEUTRAL_REAL_STUDIO_NOT_TESTED")
if __name__=="__main__":
    main()
