#!/usr/bin/env python3
"""Rebase the immutable EggRelay 2-patch source delta onto the genuine official RC55.
Isolated output only; never writes official RC, main, Studio or Roblox publication.
"""
import argparse,hashlib,subprocess,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCHES=ROOT/"rc54_candidate"
POLICY=ROOT/"src"/"EggRelayPolicy.luau"
EXPECTED_BASE="e439aa5d7372e77b0949bb681ed7342485a541c3738f7c7aceede1b6ea23b8c0"
EXPECTED_OUTPUT="d9b594bc869fee10dd2d2f7fadfb316f655fedc1316425e639ab437dd8c77afc"
PINNED_BLOBS={
 "Game.patch":"a20a1f2599af5ec9f62c5b05206b89886341906b",
 "H2FiveEggRules.patch":"92b04190d01483354a361e059559f7ac95fbef95",
}
PINNED_POLICY_BLOB="ef9b65bd6520231f299f21c5cfe2aa250798c8d0"

def sha(x):return hashlib.sha256(x).hexdigest()
def blob(x):return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def field(e,n):return e.find("./Properties/string[@name='%s']"%n)
def scan(root):
    sources={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        n,c=field(item,"Name"),field(item,"Source")
        if n is None or c is None:continue
        assert n.text not in sources,("DUPLICATE_SCRIPT",n.text)
        sources[n.text]=(item,c.text or "")
    return sources

def build(input_place,out):
    assert sha(input_place.read_bytes())==EXPECTED_BASE,"WRONG_OFFICIAL_RC55_PLACE"
    assert blob(POLICY.read_bytes())==PINNED_POLICY_BLOB
    for name,lock in PINNED_BLOBS.items():
        assert blob((PATCHES/name).read_bytes())==lock,("SOURCE_PATCH_DRIFT",name)
    tree=ET.parse(input_place)
    root=tree.getroot()
    before=scan(root)
    assert len(before)==55,("CURRENT_SOURCE_COUNT",len(before))
    assert before["Game"][0].get("class")=="Script"
    assert before["H2FiveEggRules"][0].get("class")=="ModuleScript"
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp)
        for name in ("Game","H2FiveEggRules"):
            target=d/(name+".luau")
            target.write_text(before[name][1],encoding="utf8")
            patch=(PATCHES/(name+".patch")).resolve()
            for extra in (["--dry-run"],[]):
                task=subprocess.run(["patch","-p1","--fuzz=0","--batch","--forward",
                    "--reject-file=-","-d",str(d),"-i",str(patch),*extra],
                    capture_output=True,text=True)
                assert task.returncode==0,("PATCH_REJECTED",name,extra,task.stdout,task.stderr)
            field(before[name][0],"Source").text=target.read_text("utf8")
    parent={child:par for par in root.iter() for child in par}[before["Game"][0]]
    item=ET.SubElement(parent,"Item",{
        "class":"ModuleScript","referent":"P0D_EGG_RELAY_V1_AUTHOR_RC55_CANDIDATE"})
    props=ET.SubElement(item,"Properties")
    ET.SubElement(props,"string",{"name":"Name"}).text="EggRelayPolicy"
    ET.SubElement(props,"string",{"name":"Source"}).text=POLICY.read_text("utf8")
    out.parent.mkdir(parents=True,exist_ok=True)
    tree.write(out,encoding="utf-8",xml_declaration=True)
    after=scan(ET.parse(out).getroot())
    assert len(after)==56
    assert set(after)==set(before)|{"EggRelayPolicy"}
    assert sorted(k for k in before if after[k][1]!=before[k][1])==["Game","H2FiveEggRules"]
    assert sum(after[k][1]==before[k][1] for k in before)==53
    assert after["SavedPveMasteryPolicy"][1]==before["SavedPveMasteryPolicy"][1]
    assert after["SixSkillAtomicProfile"][1]==before["SixSkillAtomicProfile"][1]
    assert after["Game"][1].count("remote.OnServerEvent:Connect(")==1
    assert after["Game"][1].count('remote.Name = "TrapRaidersS1Remote"')==1
    digest=sha(out.read_bytes())
    assert digest==EXPECTED_OUTPUT,("REBASE_OUTPUT_DRIFT",digest)
    print("P0D_EGG_RELAY_GENUINE_RC55_TO_ISOLATED_56_EXACT_PASS",digest)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-place",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    build(args.original_place,args.output)
