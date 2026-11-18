#!/usr/bin/env python3
"""Real59 P0: source-exact Host ModuleScript -> runnable Script; no Luau edits."""
import argparse,hashlib,json,shutil
from pathlib import Path
from xml.etree import ElementTree as ET
OFFICIAL="38d11f0bf311491ba76fe03f818948e5d4b06889"
HOST="ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
PLACE="EGGRUMBLE_REAL59_HUD_MAP_PRIVATE.rbxlx"
PROJECT="on59/GQ828_REAL59_HUD_MAP.project.json"
RECEIPT="GQ828_REAL59_RECEIPT.json"
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def flat(project):
    found={}
    def visit(tree,parent=""):
        for name,node in tree.items():
            if name.startswith("$") or not isinstance(node,dict):continue
            route=parent+"/"+name if parent else name
            if "$path" in node:found[route]=node["$path"]
            visit(node,route)
    visit(project["tree"])
    return found
def scripts(place):
    found={}
    def visit(item,parent):
        props=item.find("Properties")
        name=props.find("string[@name='Name']")
        assert name is not None and name.text
        route=parent+"/"+name.text if parent else name.text
        cls=item.get("class")
        if cls in ("Script","LocalScript","ModuleScript"):
            source=props.find("string[@name='Source']")
            if source is None:source=props.find("ProtectedString[@name='Source']")
            assert source is not None and route not in found
            found[route]={"class":cls,"source":source.text or ""}
        for child in item.findall("Item"):visit(child,route)
    for item in ET.parse(place).getroot().findall("Item"):visit(item,"")
    return found
def verify(place,expect):
    found=scripts(place)
    assert len(found)==59,("COUNT",len(found))
    host=found[HOST]
    assert host["class"]==expect,("P0_HOST_NOT_STARTED",host["class"],expect)
    assert "local function startSession(" in host["source"]
    assert "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW" in host["source"]
    assert "Players.PlayerAdded:Connect" in host["source"]
    return {"source_count":len(found),"host_class":expect,"host_sha":sha(host["source"])}
def assemble(base,out):
    receipt=json.loads((base/RECEIPT).read_text())
    assert receipt["official_head"]==OFFICIAL
    assert receipt["candidate_real59_source_count"]==59
    original=json.loads((base/PROJECT).read_text())
    routes=flat(original)
    assert len(routes)==59
    assert routes[HOST]=="sources/EGGRUMBLE_LobbyCastleModesPreview.luau"
    expected={x["route"]:x for x in receipt["on_sources"]}
    actual=scripts(base/PLACE)
    assert verify(base/PLACE,"ModuleScript")
    assert set(actual)==set(routes)==set(expected)
    for route,data in actual.items():
        assert data["class"]==expected[route]["class"],("CLASS_DRIFT",route)
        assert sha(data["source"])==expected[route]["sha256"],("SOURCE_DRIFT",route)
        if route!=HOST:assert "EGGRUMBLE_LobbyCastleModesPreview" not in data["source"],("EXISTING_BOOTSTRAP",route)
        p=Path(routes[route]);assert not p.is_absolute() and ".." not in p.parts
        dst=out/p;dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(data["source"].encode())
        assert sha(dst.read_text())==expected[route]["sha256"]
    (out/"OFF59.project.json").write_text(json.dumps(original,indent=2)+"\n")
    before=out/routes[HOST]
    after=before.with_name("EGGRUMBLE_LobbyCastleModesPreview.server.luau")
    shutil.copyfile(before,after)
    assert before.read_bytes()==after.read_bytes()
    original["name"]="GQ8_REAL59_HOST_ACTIVE_CANDIDATE_NOT_OFFICIAL"
    original["tree"]["ServerScriptService"]["EGGRUMBLE_LobbyCastleModesPreview"]["$path"]=str(after.relative_to(out))
    new=flat(original)
    assert len(new)==59 and [r for r in routes if routes[r]!=new[r]]==[HOST]
    (out/"EGGRUMBLE_REAL59_HOST_ACTIVE.project.json").write_text(json.dumps(original,indent=2)+"\n")
    receipt_out={"feature_id":"GQ8_REAL59_HOST_AUTOSTART_P0_20261119","base_sha":OFFICIAL,
      "sources":59,"source_bytes_modified":0,"other_58_routes_unchanged":True,
      "host_old_class":"ModuleScript","host_new_class":"Script",
      "studio_solo":"NOT_TESTED","studio_two_client":"NOT_TESTED",
      "android":"NOT_TESTED","fun":"NO_GO","formal_rc_adopted":False}
    (out/"HOST_ACTIVE_RECEIPT.json").write_text(json.dumps(receipt_out,indent=2)+"\n")
    return receipt_out
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--verify",type=Path)
    p.add_argument("--original",action="store_true")
    a=p.parse_args()
    if a.verify:print(json.dumps(verify(a.verify,"ModuleScript" if a.original else "Script")))
    else:
        assert a.base and a.out
        print(json.dumps(assemble(a.base,a.out)))
