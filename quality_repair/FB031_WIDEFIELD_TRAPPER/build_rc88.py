#!/usr/bin/env python3
"""FB031 source exact patch: wide field Trapper portals, private RC87->RC88."""
from pathlib import Path
from lxml import etree
import hashlib,json,argparse

PARENT_SHA="994d08c141cbd53f7b163c13f61f13ad9266a10c59dc7439a904172d032f07e2"
PARENT_SIZE=845174
TARGET="TrapperWarpService"
BEFORE_A="""    local pos=root.Position+d.Unit*7
    if math.abs(pos.X)>104 or math.abs(pos.Z)>60 then return false end"""
AFTER_A="""    local pos=root.Position+d.Unit*7
    -- FB031: the live GrassArena may have been enlarged to 370x294.
    -- A hard-coded +/-104/60 rejects legitimate remote flanks and is a
    -- game-breaking mismatch with the OWNER's requested large battlefield.
    -- All coordinates come from the server avatar and the REAL arena geometry.
    local grass=folder:FindFirstChild("GrassArena")
    if not grass or not grass:IsA("BasePart") then return false end
    local maxX=math.min(178,grass.Size.X*.5-7)
    local maxZ=math.min(140,grass.Size.Z*.5-7)
    if maxX<25 or maxZ<25 then return false end
    local relative=grass.CFrame:PointToObjectSpace(pos)
    if math.abs(relative.X)>maxX or math.abs(relative.Z)>maxZ
        or math.abs(pos.X)>178 or math.abs(pos.Z)>140 then return false end
    local ray=RaycastParams.new()
    ray.FilterType=Enum.RaycastFilterType.Exclude
    ray.FilterDescendantsInstances={owner.Character}
    ray.RespectCanCollide=true
    -- Reject a portal on the other side of a closed castle gate/wall.
    if workspace:Raycast(root.Position+Vector3.new(0,1,0),d.Unit*7,ray) then
        return false
    end
    -- Resolve each pad's real floor height, including elevated walkable paths;
    -- NEVER plant all portals at the old world's fixed .45 Y coordinate.
    local ground=workspace:Raycast(Vector3.new(pos.X,root.Position.Y+5,pos.Z),
        Vector3.new(0,-18,0),ray)
    if not ground or ground.Normal.Y<.65
        or not ground.Instance:IsA("BasePart")
        or not ground.Instance.Anchored or not ground.Instance.CanCollide
        or math.abs(root.Position.Y-(ground.Position.Y+2.7))>6 then
        return false
    end"""
BEFORE_B="    local where=Vector3.new(pos.X,.45,pos.Z)"
AFTER_B="    local where=ground.Position+Vector3.new(0,.45,0)"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def blob(source):
    b=source.encode("utf8")
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def replace_once(s,a,b):
    if s.count(a)!=1:raise AssertionError("SOURCE_ANCHOR_DRIFT")
    return s.replace(a,b,1)

def extract(tree):
    found={}
    for item in tree.xpath("//Item"):
        props=item.find("Properties")
        if props is None:continue
        name=props.find('string[@name="Name"]')
        source=next((p for p in props if p.get("name")=="Source"),None)
        if name is not None and source is not None:
            assert name.text not in found
            found[name.text]=source
    assert len(found)==86,len(found)
    return found

def patch(s):
    a=replace_once(s,BEFORE_A,AFTER_A)
    a=replace_once(a,BEFORE_B,AFTER_B)
    for keep in ("MAX_USES=3","RIDE_COOLDOWN=2.5",
                 "record.canRide=canRide","Service.clearOwner(owner)"):
        assert keep in a, keep
    return a

def run(parent,output,receipt=None):
    parent,output=Path(parent),Path(output)
    assert parent.stat().st_size==PARENT_SIZE and sha(parent)==PARENT_SHA,"RC87_LOCK"
    tree=etree.parse(str(parent),etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True))
    nodes=extract(tree)
    old={name:blob(node.text or "") for name,node in nodes.items()}
    assert old[TARGET]=="61bcfea24c1ac318800b982b87dacc09c6889040","MODULE_LOCK"
    nodes[TARGET].text=patch(nodes[TARGET].text or "")
    new={name:blob(node.text or "") for name,node in nodes.items()}
    assert [name for name in old if old[name]!=new[name]]==[TARGET]
    assert old["Game"]==new["Game"] and old["TrapRaidersHUD"]==new["TrapRaidersHUD"]
    etree.ElementTree(tree.getroot()).write(str(output),encoding="utf-8",xml_declaration=False,pretty_print=True)
    written=extract(etree.parse(str(output),etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)))
    assert {n:blob(v.text or "") for n,v in written.items()}==new
    result={"sha256":sha(output),"bytes":output.stat().st_size,"source_count":86,
            "changed":[TARGET],"unchanged":85,"official_rc":False,
            "studio":"NOT_RUN","android":"NOT_RUN","owner":"NOT_APPROVED"}
    if receipt:Path(receipt).write_text(json.dumps(result,indent=2))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("parent");p.add_argument("output");p.add_argument("--receipt")
    v=p.parse_args()
    print(json.dumps(run(v.parent,v.output,v.receipt),indent=2))
