#!/usr/bin/env python3
"""Exact-source private WCS-F01+C01 from real official RC55 Actions ZIP.
This does NOT write the official #220 RC or prove engine play.
Usage: python3 tools/build_from_rc55.py P0D_OFFICIAL_RICH55.zip out.rbxlx
"""
from pathlib import Path
import copy,hashlib,sys,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"src/WCS_Integrated.server.luau"
ORIGINAL_ZIP_SHA="9fd0c0d388dc8d89e44cd32d97a935ab83b57c6f600623a2699a979a901c466c"
ORIGINAL_PLACE_SHA="e439aa5d7372e77b0949bb681ed7342485a541c3738f7c7aceede1b6ea23b8c0"
NEW_SOURCE_BLOB="5eb76749414c33c11eb70310b2d1c59c1f945c21"
ORIGINAL_AUTHOR_BLOB="c3cf119e26ab0241a7bd2b0b25acca75a4250e10"
EXPECTED_PRIVATE_SHA="adc667a507fc3f4e691140888300dc8926f7617e3ae1db148817492081788d0f"
def sha(x):return hashlib.sha256(x).hexdigest()
def blob(x):return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\x00"+x).hexdigest()
def scripts(root):
    items={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        n=item.find('./Properties/string[@name="Name"]')
        s=item.find('./Properties/string[@name="Source"]')
        if n is None or s is None or n.text in items:raise ValueError("SCRIPT_MISSING_OR_DUPLICATED")
        items[n.text]=(item.get("class"),s.text or "")
    return items
def build(zip_path,out_path):
    if sha(zip_path.read_bytes())!=ORIGINAL_ZIP_SHA:raise ValueError("WRONG_OFFICIAL_RC55_ARCHIVE")
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip():raise ValueError("BROKEN_ARCHIVE_CRC")
        b=z.read("P0D_CANONICAL_RC_rich51.rbxlx")
    if sha(b)!=ORIGINAL_PLACE_SHA:raise ValueError("WRONG_OFFICIAL_RC55_PLACE")
    added=SOURCE.read_bytes()
    if blob(added)!=NEW_SOURCE_BLOB:raise ValueError("WCS_INTEGRATED_SCRIPT_DRIFT")
    start=b"-- P0D World-Character Synergy F01+C01 (S2+ isolated candidate)\n"
    end=b'world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")\n'
    a=added.find(start);e=added.find(end,a)
    if a<0 or e<0:raise ValueError("ORIGINAL_WCS_AUTHOR_MARKERS_LOST")
    original=added[a:e+len(end)]
    if blob(original)!=ORIGINAL_AUTHOR_BLOB:raise ValueError("ORIGINAL_MOGURON_AUTHOR_SOURCE_CHANGED")
    tree=ET.fromstring(b);before=scripts(tree)
    if len(before)!=55:raise ValueError("EXPECTED_55_CANONICAL_SCRIPTS")
    parent={c:p for p in tree.iter() for c in p}
    host=None
    for item in tree.iter("Item"):
        n=item.find('./Properties/string[@name="Name"]')
        if n is not None and n.text=="RealmHunt":host=item;break
    if host is None or host.get("class")!="Script":raise ValueError("NO_SERVER_SCRIPT_TEMPLATE")
    holder=parent[host]
    name=holder.find('./Properties/string[@name="Name"]')
    if holder.get("class")!="Folder" or name is None or name.text!="TrapRaidersS1":raise ValueError("NOT_CANONICAL_GAME_FOLDER")
    add=copy.deepcopy(host)
    add.set("referent","P0D_WCS_F01_C01_56")
    add.find('./Properties/string[@name="Name"]').text="WCS_CrystalCanyon"
    add.find('./Properties/string[@name="Source"]').text=added.decode("utf8")
    holder.append(add)
    after=scripts(tree)
    if len(after)!=56 or set(after)-set(before)!={"WCS_CrystalCanyon"}:raise ValueError("WRONG_DELTA")
    if any(after[n]!=v for n,v in before.items()):raise ValueError("CANONICAL_55_SOURCE_CHANGED")
    if after["Game"][1].count("remote.OnServerEvent:Connect(")!=1:raise ValueError("DUPLICATE_REMOTE")
    for n in ("PersistentHatchStore","SixSkillAtomicProfile","SavedPveMasteryPolicy","RealmHunt","H1FunWorld","H2FiveEggRules"):
        if after[n]!=before[n]:raise ValueError("CANONICAL_AUTHORITY_CHANGED")
    got=ET.tostring(tree,encoding="utf8",xml_declaration=True)
    if sha(got)!=EXPECTED_PRIVATE_SHA:raise ValueError("PRIVATE_ROBLOX_XML_DRIFT")
    if scripts(ET.fromstring(got))!=after:raise ValueError("RBXLX_ROUNDTRIP_MISMATCH")
    out_path.write_bytes(got)
    print("P0D_GENUINE_RC55_PLUS_ORIGINAL_WCS_SOURCE_EXACT_PASS",len(after),sha(got))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: build_from_rc55.py official55.zip out.rbxlx")
    build(Path(sys.argv[1]),Path(sys.argv[2]))
