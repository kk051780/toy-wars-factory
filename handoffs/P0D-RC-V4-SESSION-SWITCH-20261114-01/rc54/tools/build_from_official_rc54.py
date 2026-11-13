#!/usr/bin/env python3
"""Rebase RC54 four minimal source switches, never overwrite canonical RC.

Run: python tools/build_from_official_rc54.py OFFICIAL_ACTIONS_ARTIFACT.zip out.rbxlx
Original artifact ID 14068663217, Actions run 43491029567.
Studio source/static QA only, not real engine validation.
"""
import collections
import hashlib
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_ZIP_SHA="14b0a42089819f231473540355819494decff97c5e71cad893582f5490130469"
ORIGINAL_PLACE_SHA="1afdb2661b47eafa97985b27eaab5b0236d15f6f6e21863d089cebaf7e745758"
FINAL_PLACE_SHA="b534244c487060ce64fc47d4a8057b752086e0349859b559590745ea56e9d10c"
BASE_BLOBS={
 "H1FunWorld":"7a90affd4eb7eebcdfba39d833a2875ff665d5cf",
 "RealmHunt":"24f4813f50b97ccab7cbf7a89ef1be062b53d5f4",
 "V4TrainingBridge":"dbb7171add2b29e337171e547bc40101c2b0dce4",
 "V4TrialOverlay":"fd5f93f982e353b22eed1a5eb29ad965bb73da5b",
}
TARGET_BLOBS={
 "H1FunWorld":"c5294424e208b210ea84985bc2c07ce848da6930",
 "RealmHunt":"9d69c9c7e920b9994b950b370a11615fc61a9e72",
 "V4TrainingBridge":"13bfed72541debc6d3b86d906742dc53f998d444",
 "V4TrialOverlay":"8db6f1ff1c26f0dd5ec4d9b5916a02311d0deb22",
}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def once(s,a,b):
    if s.count(a)!=1:raise ValueError("ANCHOR_MISSING_OR_DUPLICATED: "+a[:70])
    return s.replace(a,b,1)
def patch_client(s):
    s=once(s,'''    baseWarning=if saved then "DEV保存確認済 / 対戦強化なし"
        else "保存状況:"..saveState.." / 体験XP"''',
'''    local previewAllowed=player:GetAttribute("P0D_V4_PreviewAllowed")~=false
    baseWarning=if saved then "DEV保存確認済 / 対戦強化なし"
        elseif not previewAllowed then "試作XPは停止・DEV保存は未確認"
        else "保存状況:"..saveState.." / 体験XP"''')
    s=once(s,'    local active=player:GetAttribute("P0D_V4_Active")==true',
'''    local active=previewAllowed and player:GetAttribute("P0D_V4_Active")==true''')
    s=once(s,'        rows[i].Text=string.format("%s   Lv%d   XP%d  次まで%d",display,lv,xp,nextXP)',
'''        if not saved and not previewAllowed then
            rows[i].Text=display.."  試作XP：停止中"
        else
            rows[i].Text=string.format("%s   Lv%d   XP%d  次まで%d",display,lv,xp,nextXP)
        end''')
    return s

def main(zip_path,out_path):
    zip_bytes=zip_path.read_bytes()
    if digest(zip_bytes)!=ORIGINAL_ZIP_SHA:raise ValueError("WRONG_OFFICIAL_RC54_ZIP")
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:raise ValueError("BAD_ZIP_CRC")
        original=z.read("P0D_CANONICAL_RC_rich51.rbxlx")
    if digest(original)!=ORIGINAL_PLACE_SHA:raise ValueError("WRONG_RC54_PLACE")
    tree=ET.fromstring(original)
    rows={}
    for item in tree.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        n=item.find('./Properties/string[@name="Name"]')
        src=item.find('./Properties/string[@name="Source"]')
        if n is not None and src is not None:
            if n.text in rows:raise ValueError("DUPLICATE_SCRIPT_NAME")
            rows[n.text]=(item.get("class"),src)
    if len(rows)!=54:raise ValueError("WRONG_SOURCE_COUNT")
    baseline={n:(el.text or "").encode("utf8") for n,(kind,el) in rows.items()}
    for name,old_blob in BASE_BLOBS.items():
        if blob(baseline[name])!=old_blob:raise ValueError("ORIGINAL_SOURCE_DRIFT: "+name)
    for name,new_blob in TARGET_BLOBS.items():
        if name=="V4TrialOverlay":
            new=patch_client(baseline[name].decode("utf8")).encode("utf8")
        else:
            new=(ROOT/"src"/(name+".luau")).read_bytes()
        if blob(new)!=new_blob:raise ValueError("PATCH_SOURCE_DRIFT: "+name)
        rows[name][1].text=new.decode("utf8")
    result={n:(el.text or "").encode("utf8") for n,(kind,el) in rows.items()}
    changed=sorted(n for n in result if result[n]!=baseline[n])
    if changed!=sorted(TARGET_BLOBS):raise ValueError("UNEXPECTED_MODIFIED_SOURCE")
    if len(result)!=54 or sum(result[n]==baseline[n] for n in baseline)!=50:raise ValueError("CHANGED_50_CORE_SOURCES")
    for name in ["Game","PersistentHatchStore","SixSkillAtomicProfile","RealmHuntHUD","DojoRules","MusouHorde"]:
        if result[name]!=baseline[name]:raise ValueError("CRITICAL_SOURCE_CHANGE: "+name)
    if result["Game"].decode("utf8").count("remote.OnServerEvent:Connect(")!=1:raise ValueError("DUPLICATE_GAME_REMOTE")
    if collections.Counter(x[0] for x in rows.values())!=collections.Counter({"Script":4,"LocalScript":9,"ModuleScript":41}):raise ValueError("SCRIPT_CLASS_DRIFT")
    if "P0D_V4_SaveStatus" not in result["V4TrialOverlay"].decode("utf8"):raise ValueError("REMOVED_SAVE_STATUS")
    if "SkyClueGroundFallback" not in result["RealmHunt"].decode("utf8"):raise ValueError("MISSING_REALM_FALLBACK")
    out=ET.tostring(tree,encoding="utf8",xml_declaration=True)
    if digest(out)!=FINAL_PLACE_SHA:raise ValueError("RBXLX_BYTE_DRIFT")
    out_path.write_bytes(out)
    print("PRIVATE_RC54_SOURCE_REBASE_EXACT_PASS","54/54","old50/54",digest(out))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: build_from_official_rc54.py original_actions.zip output.rbxlx")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
