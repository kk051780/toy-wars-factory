"""Audit actual Rojo-produced .rbxlx for original source bytes and safe disabled demo.
This does not prove Studio rendering or player movement.
"""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
MAP={
    "ServerScriptService/WorldLinkDemo":("Script","src/WorldLinkDemo.server.luau"),
    "ServerScriptService/WorldLinkScene":("ModuleScript","src/WorldLinkScene.luau"),
    "ServerScriptService/WorldLinkRoutes":("ModuleScript","src/WorldLinkRoutes.luau"),
}
SCRIPT_TYPES={"Script","ModuleScript","LocalScript"}

class AuditError(ValueError): pass
def require(condition,reason):
    if not condition: raise AuditError(reason)
def prop(item,name):
    block=item.find("Properties")
    if block is None: return None
    for item_prop in block:
        if item_prop.get("name")==name: return item_prop.text or ""
    return None
def parse(xml):
    try: node=ET.fromstring(xml)
    except ET.ParseError as e: raise AuditError("malformed real Rojo XML") from e
    require(node.tag=="roblox","not a Roblox XML")
    result=[]
    def visit(element,names):
        for child in element:
            if child.tag!="Item": continue
            kind=child.get("class")
            name=prop(child,"Name")
            require(kind and name,"unnamed Instance")
            path=names if kind=="DataModel" else (*names,name)
            result.append(("/".join(path),kind,prop(child,"Source")))
            visit(child,path)
    visit(node,())
    return result
def verify(xml,root=ROOT):
    manifest=json.loads((root/"BUILD_MANIFEST.json").read_text("utf-8"))
    expected={x["path"]:x for x in manifest["files"]}
    for _,path in MAP.values():
        require(path in expected,"source not in lock: "+path)
        raw=(root/path).read_bytes()
        row=expected[path]
        require(row["size"]==len(raw) and hashlib.sha256(raw).hexdigest()==row["sha256"],
                "bad source in manifest")
    actual=[(p,c,s) for p,c,s in parse(xml) if c in SCRIPT_TYPES]
    require(len(actual)==3,"unexpected script count")
    seen=set()
    for path,kind,source in actual:
        require(path not in seen,"duplicate script path")
        require(path in MAP,"unlisted script "+path)
        klass,srcpath=MAP[path]
        require(kind==klass,"wrong script class")
        require(source is not None,"missing original source")
        require(source.encode("utf-8")== (root/srcpath).read_bytes(),
                "source bytes differ: "+path)
        seen.add(path)
    require(seen==set(MAP),"missing script path")
    scripts={p:s for p,kind,s in actual if kind=="Script"}
    require(len(scripts)==1,"duplicate executable Game authority")
    require("ENABLE_WORLD_G5_DEMO = false" in scripts["ServerScriptService/WorldLinkDemo"],
            "dangerous auto-run")
    return {"format":"P0D_WORLD_G5_ACTUAL_ROJO_BYTE_RECEIPT_V1",
            "place_sha256":hashlib.sha256(xml).hexdigest(),"place_bytes":len(xml),
            "full_source_paths":sorted(seen),"three_source_bytes_match":True,
            "standalone_demo_enabled":False,"real_roblox_studio":False,
            "real_2client":False,"mobile":False,"real_game_published":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--place",required=True)
    ap.add_argument("--receipt",required=True)
    args=ap.parse_args()
    xml=Path(args.place).read_bytes()
    require(len(xml)>4096,"tiny Place file")
    r=verify(xml)
    Path(args.receipt).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WORLD_LINK_G5_REAL_ROJO_THREE_SOURCE_BYTES_PASS")
    print("WORLD_LINK_G5_REAL_ROJO_SHA256="+r["place_sha256"])
    print("WORLD_LINK_G5_REAL_ROJO_BYTES="+str(r["place_bytes"]))
    print("WORLD_LINK_G5_REAL_STUDIO_NOT_TESTED")

if __name__=="__main__":
    main()
