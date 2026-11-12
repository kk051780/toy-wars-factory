"""Audit authentic Rojo .rbxlx with exactly four ORIGINAL Luau source scripts, OFF by default."""
from pathlib import Path
import argparse,hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
MAP={
  "ServerScriptService/RareRealmDemo":("Script","src/RareRealmDemo.server.luau"),
  "ServerScriptService/RareRealmCatalog":("ModuleScript","src/RareRealmCatalog.luau"),
  "ServerScriptService/RareRealmCycle":("ModuleScript","src/RareRealmCycle.luau"),
  "ServerScriptService/RareRealmScene":("ModuleScript","src/RareRealmScene.luau"),
}
class AuditError(ValueError):pass
def req(v,msg):
    if not v:raise AuditError(msg)
def prop(item,name):
    properties=item.find("Properties")
    if properties is None:return None
    for p in properties:
        if p.get("name")==name:return p.text or ""
    return None
def all_items(raw):
    try:root=ET.fromstring(raw)
    except ET.ParseError as e:raise AuditError("bad Roblox XML") from e
    req(root.tag=="roblox","wrong XML root")
    items=[]
    def visit(node,ancestors):
        for c in node:
            if c.tag!="Item":continue
            cls,name=c.get("class"),prop(c,"Name")
            req(bool(cls and name),"unnamed Instance")
            p=ancestors if cls=="DataModel" else (*ancestors,name)
            items.append(("/".join(p),cls,prop(c,"Source")))
            visit(c,p)
    visit(root,())
    return items
def verify(raw,root=ROOT):
    manifest=json.loads((root/"BUILD_MANIFEST.json").read_text("utf-8"))
    locked={v["path"]:v for v in manifest["files"]}
    for _,path in MAP.values():
        req(path in locked,"script source missing manifest")
        source=(root/path).read_bytes()
        req(len(source)==locked[path]["size"] and hashlib.sha256(source).hexdigest()==locked[path]["sha256"],
            "input source does not match SHA256")
    scripts=[v for v in all_items(raw) if v[1] in ("Script","LocalScript","ModuleScript")]
    req(len(scripts)==4,"wrong script instance count")
    seen=set()
    for path,cls,src in scripts:
        req(path in MAP and path not in seen,"unlisted or duplicate script")
        expected_class,original=MAP[path]
        req(cls==expected_class,"client or game script class substitution")
        req(src is not None and src.encode("utf-8")== (root/original).read_bytes(),
            "Luau original source bytes mismatch: "+path)
        seen.add(path)
    req(seen==set(MAP),"missing source")
    req(sum(v[1]=="Script" for v in scripts)==1,"multiple game authority scripts")
    demo=next(v[2] for v in scripts if v[0]=="ServerScriptService/RareRealmDemo")
    req("ENABLE_FOUR_RARE_REALMS_DEMO = false" in demo,"nonproduction demo accidentally enabled")
    req("RunService:IsStudio()" in demo and "TRAP_RAIDERS_S1" in demo,
        "nonproduction/official source overlap guards missing")
    req("OnServerEvent" not in demo and "FireServer" not in demo,"client authority injected")
    return {"type":"RARE4_TRUE_ROJO_REVIEW_ONLY","rbxlx_sha256":hashlib.sha256(raw).hexdigest(),
      "rbxlx_bytes":len(raw),"four_source_modules_byte_exact":True,"server_entry_disabled":True,
      "real_studio_2client":False,"mobile":False,"actual_rare_ai":False,"published":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--place",required=True)
    p.add_argument("--receipt",required=True)
    a=p.parse_args()
    raw=Path(a.place).read_bytes()
    req(len(raw)>5000,"Place too small")
    receipt=verify(raw)
    Path(a.receipt).write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("RARE4_REAL_ROJO_ORIGINAL_SOURCE_4_OF_4_PASS")
    print("RARE4_REAL_ROJO_RBXLX_SHA256="+receipt["rbxlx_sha256"])
    print("RARE4_REAL_ROJO_RBXLX_BYTES="+str(receipt["rbxlx_bytes"]))
    print("RARE4_ACTUAL_STUDIO_NOT_TESTED")
if __name__=="__main__":main()
