#!/usr/bin/env python3
"""RC57 -> isolated RC58 WCS-F01/C01 private Roblox XML; does NOT touch canonical RC.
Input is exact official Actions 43508562967 artifact, never a guessed or older RC.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/WCS_Integrated.server.luau"
OFFICIAL_RC_HEAD = "34d6d384d04ba1d4a394331a3e5c74f798e57a22"
OFFICIAL_RC_RUN = 43508562967
OFFICIAL_RC_ARTIFACT = 14076842489
OFFICIAL_ZIP_SHA256 = "552c506ef2812b220285f716562edfb17cdb285fc985b4cacec82996c88ecbdf"
OFFICIAL_PLACE_SHA256 = "15521b7dadbd96c0ef1ed12367b5fcf2f3738c4428ebf2fb8c43532b39b8a8"
SOURCE_GIT_BLOB = "331af98fec1b55c74eaa1febe8cb7bc6b580c607"
SAFE_AUTHOR_BLOB = "3edcb19d91de509afd3de227cbfbca5d75125ec2"
OUTPUT_MEMBER = "P0D_CANONICAL_RC_rich51.rbxlx"
ADD_NAME = "WCS_CrystalCanyon"
PRESERVE = (
    "Game", "PersistentHatchStore", "SixSkillAtomicProfile", "SavedPveMasteryPolicy",
    "SavedBeastEvolutionPolicy", "ScoutSpeciesPolicy", "RealmHunt", "H1FunWorld",
    "H2FiveEggRules", "WCS_Integrated"
)

def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()

def all_scripts(root):
    found = {}
    for item in root.iter("Item"):
        if item.get("class") not in {"Script", "LocalScript", "ModuleScript"}:
            continue
        name = item.find('./Properties/string[@name="Name"]')
        body = item.find('./Properties/string[@name="Source"]')
        if name is None or body is None or not name.text or name.text in found:
            raise ValueError("DUPLICATE_OR_MISSING_SCRIPT")
        found[name.text] = (item.get("class"), body.text or "")
    return found

def build(zip_path: Path, output: Path, receipt_path: Path):
    b = zip_path.read_bytes()
    if sha(b) != OFFICIAL_ZIP_SHA256: raise ValueError("OFFICIAL_RC57_ZIP_SHA_MISMATCH")
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None: raise ValueError("ZIP_CRC_FAILURE")
        before_bin = z.read(OUTPUT_MEMBER)
    if sha(before_bin) != OFFICIAL_PLACE_SHA256: raise ValueError("OFFICIAL_RC57_PLACE_SHA_MISMATCH")
    source = SOURCE.read_bytes()
    if blob(source) != SOURCE_GIT_BLOB: raise ValueError("WCS_RICH58_SOURCE_DRIFT")
    t = source.decode("utf8")
    assert "playerIsInGateClosureZone()" in t and "playerIsOnBridge()" not in t, "SAFETY_PATCH_MISSING"
    assert "nextOpenAllowed = os.clock() + REOPEN_COOLDOWN" in t, "SAFE_REAL_CLOSE_COOLDOWN"
    assert "if not RunService:IsStudio() then" in t, "STUDIO_ONLY"
    assert 'ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")==false' in t, "ROLLBACK_SWITCH"
    assert "localPoint.X) <= 3.5" in t and "localPoint.Z) <= 8" in t, "GATE_ZONE_MISSING"
    assert 'anchor.CFrame=CFrame.new(0,32,-23)' in t, "BOUNDS_SOURCE_DRIFT"
    assert t.count('world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")') == 1
    if any(x in t for x in ("OnServerEvent:Connect(", "GetDataStore(", "UpdateAsync(", "TakeDamage(")):
        raise ValueError("SECONDARY_GAME_AUTHORITY")

    root = ET.fromstring(before_bin)
    original = all_scripts(root)
    if len(original) != 57: raise ValueError("RC57_EXPECTED_57_SCRIPTS")
    if ADD_NAME in original or "WCS_Integrated" in original: raise ValueError("WCS_DUPLICATE")
    for needed in PRESERVE:
        if needed == "WCS_Integrated": continue
        if needed not in original: raise ValueError("RC57_MISSING_" + needed)
    if original["Game"][1].count('remote.OnServerEvent:Connect(') != 1:
        raise ValueError("NOT_ONE_REMOTE")
    if original["Game"][1].count('remote.Name = "TrapRaidersS1Remote"') != 1:
        raise ValueError("NOT_ONE_GAME_REMOTE")

    parent = {c:p for p in root.iter() for c in p}
    template = None
    for item in root.iter("Item"):
        n = item.find('./Properties/string[@name="Name"]')
        if item.get("class") == "Script" and n is not None and n.text == "RealmHunt":
            template = item
            break
    if template is None: raise ValueError("NO_SAFE_SERVER_TEMPLATE")
    holder = parent[template]
    holder_name = holder.find('./Properties/string[@name="Name"]')
    if holder.get("class") != "Folder" or holder_name is None or holder_name.text != "TrapRaidersS1":
        raise ValueError("NOT_SAME_GAME_FOLDER")
    ref = "P0D_WCS_RC58_20261114_01"
    if any(item.get("referent") == ref for item in root.iter("Item")):
        raise ValueError("REFERENT_COLLISION")
    new = copy.deepcopy(template)
    new.set("referent", ref)
    new.find('./Properties/string[@name="Name"]').text = ADD_NAME
    new.find('./Properties/string[@name="Source"]').text = t
    holder.append(new)

    final = all_scripts(root)
    if len(final) != 58 or set(final)-set(original) != {ADD_NAME}:
        raise ValueError("NOT_EXACTLY_ONE_SCRIPT_ADDED")
    if any(final[name] != value for name,value in original.items()):
        raise ValueError("OLD_57_CODE_MUTATED")
    if sum(1 for name in final if name == "Game") != 1 or final["Game"] != original["Game"]:
        raise ValueError("GAME_OWNER_CHANGED")
    output.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    result = ET.tostring(root, encoding="utf8", xml_declaration=True)
    if all_scripts(ET.fromstring(result)) != final: raise ValueError("RESULT_ROUNDTRIP_NOT_EXACT")
    receipt = {
        "schema":"P0D_WCS_RC57_PRIVATE_REBASE_V1",
        "status":"PRIVATE_RBXLX_BUILT_NOT_OFFICIAL_RC",
        "source_official_rc_head":OFFICIAL_RC_HEAD,
        "source_official_run":OFFICIAL_RC_RUN,
        "source_official_artifact":OFFICIAL_RC_ARTIFACT,
        "source_original_zip_sha256":OFFICIAL_ZIP_SHA256,
        "source_original_rbxlx_sha256":OFFICIAL_PLACE_SHA256,
        "original_luau_unchanged":57,
        "new_script_count":58,
        "added_script":ADD_NAME,
        "added_source_gitblob":SOURCE_GIT_BLOB,
        "source_original_author_safety_fix_gitblob":SAFE_AUTHOR_BLOB,
        "private_rbxlx_sha256":sha(result),
        "feature_switch":"ServerStorage attribute P0D_RC_ENABLE_WCS_F01_C01=false before Studio boot",
        "same_existing_game_store_remote":True,
        "native_luau_compile":"NOT_VERIFIED",
        "actual_studio_engine":"NOT_TESTED",
        "android":"NOT_TESTED","owner_fun":"NOT_TESTED",
        "official_rc_adopted":False,"main_merge":False,"published":False
    }
    output.write_bytes(result)
    receipt_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("P0D_WCS_PRIVATE_RC58_57_ORIGINAL_BYTE_EXACT_PASS",sha(result))
    return receipt

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("official_rc57_artifact_zip",type=Path)
    p.add_argument("output_rbxlx",type=Path)
    p.add_argument("receipt_json",type=Path)
    a=p.parse_args()
    build(a.official_rc57_artifact_zip,a.output_rbxlx,a.receipt_json)
