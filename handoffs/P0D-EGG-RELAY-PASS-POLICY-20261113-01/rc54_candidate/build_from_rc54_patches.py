#!/usr/bin/env python3
"""Build isolated 55-source egg-relay candidate from an exact original RC54 Place.
Never writes a canonical RC, main, Studio, or publisher. Not a Rojo/native test.
"""
from pathlib import Path
import argparse
import hashlib
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PATCHES=Path(__file__).resolve().parent
EXPECTED_BASE="1afdb2661b47eafa97985b27eaab5b0236d15f6f6e21863d089cebaf7e745758"
EXPECTED_PATCH={
    "Game.patch":"a20a1f2599af5ec9f62c5b05206b89886341906b",
    "H2FiveEggRules.patch":"92b04190d01483354a361e059559f7ac95fbef95",
}
EXPECTED_POLICY="ef9b65bd6520231f299f21c5cfe2aa250798c8d0"
EXPECTED_OUTPUT="c744765df52b572179dd8dc17a28c6592f1c489177ce5a570e40ac529bf78a8a"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def prop(item,name):
    return item.find("./Properties/string[@name='%s']"%name)

def scan(root):
    out={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","ModuleScript","LocalScript"):
            continue
        n,s=prop(item,"Name"),prop(item,"Source")
        if n is None or s is None:
            continue
        assert n.text not in out,("DUPLICATE_SCRIPT",n.text)
        out[n.text]=(item,item.get("class"),s.text or "")
    return out

def build(input_place,out):
    assert sha(input_place.read_bytes())==EXPECTED_BASE,"WRONG_REAL_RC54_BINARY"
    for name,expected in EXPECTED_PATCH.items():
        assert blob((PATCHES/name).read_bytes())==expected,("PATCH_DRIFT",name)
    assert blob((ROOT/"src"/"EggRelayPolicy.luau").read_bytes())==EXPECTED_POLICY,"POLICY_DRIFT"
    tree=ET.parse(input_place)
    root=tree.getroot()
    sources=scan(root)
    assert len(sources)==54
    assert sources["Game"][1]=="Script" and sources["H2FiveEggRules"][1]=="ModuleScript"

    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp)
        for name in ("Game","H2FiveEggRules"):
            (directory/(name+".luau")).write_text(sources[name][2],encoding="utf8")
            patch_file=(PATCHES/(name+".patch")).resolve()
            for option in (["--dry-run"],[]):
                result=subprocess.run([
                    "patch","-p1","--fuzz=0","--batch","--forward",
                    "--reject-file=-","-d",str(directory),"-i",str(patch_file),
                    *option,
                ],capture_output=True,text=True)
                assert result.returncode==0,(
                    "PATCH_NOT_EXACT",name,option,result.stdout,result.stderr)
            prop(sources[name][0],"Source").text=(directory/(name+".luau")).read_text("utf8")

    parents={child:parent for parent in root.iter() for child in parent}
    parent=parents[sources["Game"][0]]
    module=ET.SubElement(parent,"Item",{
        "class":"ModuleScript","referent":"P0D_EGG_RELAY_V1_AUTHOR_CANDIDATE",
    })
    properties=ET.SubElement(module,"Properties")
    ET.SubElement(properties,"string",{"name":"Name"}).text="EggRelayPolicy"
    ET.SubElement(properties,"string",{"name":"Source"}).text=(
        ROOT/"src"/"EggRelayPolicy.luau").read_text("utf8")

    out.parent.mkdir(parents=True,exist_ok=True)
    tree.write(out,encoding="utf-8",xml_declaration=True)
    rebuilt=scan(ET.parse(out).getroot())
    assert len(rebuilt)==55
    assert set(rebuilt)==set(sources)|{"EggRelayPolicy"}
    changed=sorted(n for n in sources if rebuilt[n][2]!=sources[n][2])
    assert changed==["Game","H2FiveEggRules"],changed
    assert sum(rebuilt[n][2]==sources[n][2] for n in sources)==52
    assert rebuilt["Game"][2].count("remote.OnServerEvent:Connect(")==1
    assert sha(out.read_bytes())==EXPECTED_OUTPUT,("REBUILD_SHA_DRIFT",sha(out.read_bytes()))
    print("P0D_EGG_RELAY_EXACT_RC54_BASE_PATCH55_SOURCE_PASS",EXPECTED_OUTPUT)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-place",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    build(args.original_place,args.output)
