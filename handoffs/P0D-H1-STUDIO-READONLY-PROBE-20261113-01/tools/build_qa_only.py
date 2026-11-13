#!/usr/bin/env python3
"""Build a separate NO-PUBLISH 30-source H1 Studio QA clone with original vetted probes.

Input baseline: #255 fixed 28-source complete game builder.
Added (and ONLY added): two original #245 source-vetted Studio-only read-only
observers. True engine play, mobile and human FUN are never auto-certified.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = Path(__file__).resolve().parents[1]
BASE = REPO / "handoffs/P0D-H1-WOW-4WAY-20261113-01"
BASE_PROJECT = BASE / "dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY"
OUT = ROOT / "dist/H1_QA_ONLY_UNPUBLISHED"
CLIENT = "StudioPassiveClientProbe.client.luau"
SERVER = "StudioPassiveServerProbe.server.luau"
EXPECTED = {CLIENT: "c0fb0a8ff39ba02277bd4484604b80f3207d7756",
            SERVER: "6272cbd587c714046685aba82be775c6dad21057"}
ANCHOR_GAME = "1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b"
ANCHOR_PROBES = "e2662b540f2312c95af67a1761ea05842482919d"
DISALLOWED = (
    r":\s*FireServer\s*\(",
    r":\s*FireClient\s*\(",
    r":\s*FireAllClients\s*\(",
    r"\bDataStoreService\b",
    r"\bMarketplaceService\b",
    r"\bPublishAsync\b",
    r"Instance\.new\s*\(\s*['\"]RemoteEvent['\"]",
)

def git_blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def check_probe(data:bytes,expected_blob:str|None=None)->bool:
    if expected_blob is not None and git_blob(data)!=expected_blob:
        raise ValueError("ORIGINAL_VETTED_PROBE_BLOB_CHANGED")
    body=data.decode("utf-8")
    if 'if not RunService:IsStudio() then return end' not in body:
        raise ValueError("PROBE_MISSING_STUDIO_ONLY_GUARD")
    if "P0D_STUDIO_PROBE_V1" not in body:
        raise ValueError("PROBE_LOG_PREFIX_MISSING")
    if any(re.search(x,body) for x in DISALLOWED):
        raise ValueError("MUTATING_PASSIVE_PROBE_FORBIDDEN")
    return True

def negative_safety_tests():
    safe=(ROOT/"inputs"/CLIENT).read_bytes()
    assert check_probe(safe,EXPECTED[CLIENT])
    good=safe.decode("utf-8")
    mutants=[
        good.replace('RunService:IsStudio()', 'true',1),
        good.replace('P0D_STUDIO_PROBE_V1', 'IGNORED_PROBE'),
        good+'\nremote:FireServer({action="DAMAGE"})\n',
        good+'\nInstance.new("RemoteEvent")\n',
        good+'\nlocal s = game:GetService("DataStoreService")\n',
        good+'\nlocal s = game:GetService("MarketplaceService")\n',
        good+'\nPublishAsync()\n',
    ]
    rejected=0
    for text in mutants:
        try: check_probe(text.encode("utf-8"),None)
        except ValueError: rejected+=1
    if rejected!=len(mutants):
        raise ValueError(f"UNSAFE_PROBE_MUTATION_ACCEPTED_{rejected}/{len(mutants)}")
    print("H1_QA_ONLY_PASSIVE_SAFETY_MUTANTS_REJECTED",rejected)

def assemble():
    for name,sha in EXPECTED.items():
        check_probe((ROOT/"inputs"/name).read_bytes(),sha)
    negative_safety_tests()
    # The inherited author-side builder is unchanged and independently pinned
    # by the GitHub base commit. It produces one original 28-script private game.
    subprocess.run([sys.executable,str(BASE/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True,timeout=50)
    original=sorted((BASE_PROJECT/"src").rglob("*.luau"))
    if len(original)!=28:
        raise ValueError("ORIGINAL_28_SOURCE_MISSING")
    before={x.relative_to(BASE_PROJECT/"src").as_posix():x.read_bytes() for x in original}
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(BASE_PROJECT,OUT)
    for name in EXPECTED:
        target=OUT/"src"/("client" if name==CLIENT else "server")/name
        if target.exists(): raise ValueError("CANNOT_OVERWRITE_ORIGINAL_GAME_SOURCE")
        shutil.copyfile(ROOT/"inputs"/name,target)
        check_probe(target.read_bytes(),EXPECTED[name])
    after={x.relative_to(OUT/"src").as_posix():x.read_bytes()
           for x in sorted((OUT/"src").rglob("*.luau"))}
    if len(after)!=30:
        raise ValueError("QA_CLONE_SCRIPT_COUNT_NOT_30")
    if any(after.get(k)!=v for k,v in before.items()):
        raise ValueError("QA_CLONE_CHANGED_ORIGINAL_28_SOURCE_BYTES")
    if set(after)-set(before)!={"client/"+CLIENT,"server/"+SERVER}:
        raise ValueError("QA_CLONE_UNEXPECTED_NEW_SOURCE")
    project=json.loads((OUT/"default.project.json").read_text(encoding="utf-8"))
    project["name"]="P0D_H1_4WAY_QA_ONLY_DO_NOT_PUBLISH"
    children=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    if "P0D_QA_ONLY_ReadOnlyClientObserver" in children:
        raise ValueError("CLIENT_PROBE_ALREADY_MOUNTED")
    children["P0D_QA_ONLY_ReadOnlyClientObserver"]={"$path":"src/client/"+CLIENT}
    # The server's entire src/server directory is already mapped to a folder,
    # and Rojo automatically includes StudioPassiveServerProbe.server.luau.
    (OUT/"default.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    source_lock={
        "QA_ONLY_NO_PUBLISH":True,"game_id":"TRAP_RAIDERS",
        "adoption_id":"P0D-FUN-H1-001",
        "original_fourway_game_sha":ANCHOR_GAME,
        "original_vetted_probe_source_sha":ANCHOR_PROBES,
        "inherited_original_scripts_preserved":28,
        "added_source_vetted_passive_Studio_only_probes":2,
        "source_script_count":30,
        "probe_blobs":EXPECTED,
        "owner_2client_Studio_proof":"NOT_TESTED",
        "physical_mobile_proof":"NOT_TESTED",
        "human_fun_gate":"NO_GO_PENDING",
        "official_rc_adopted":False,
        "published":False,
        "do_not_publish_or_replace_existing_pc_Place":True
    }
    (OUT/"QA_ONLY_SOURCE_LOCK.json").write_text(
        json.dumps(source_lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("H1_QA_ONLY_PRESERVED_ORIGINAL_28_OF_28_PLUS_VETTED_TWO_PROBES")
    return before,after

def verify_xml(place:Path,receipt:Path):
    source_files=sorted((OUT/"src").rglob("*.luau"))
    if len(source_files)!=30:raise ValueError("SOURCE30_NOT_GENERATED")
    source_expected=collections.Counter(x.read_text(encoding="utf-8") for x in source_files)
    XML=ET.fromstring(place.read_bytes())
    actual=[]; classes=collections.Counter()
    for item in XML.iter("Item"):
        cls=item.attrib.get("class")
        if cls not in {"Script","LocalScript","ModuleScript"}:continue
        script=item.find("./Properties/string[@name='Source']")
        if script is None:continue
        actual.append(script.text or "")
        classes[cls]+=1
    if classes!={"Script":3,"LocalScript":5,"ModuleScript":22}:
        raise ValueError("QA_PROBE_ORIGINAL_ROJO_CLASSES_MISMATCH "+repr(classes))
    if collections.Counter(actual)!=source_expected:
        raise ValueError("QA_PROBE_ORIGINAL_XML_30_BYTE_EXACT_FAIL")
    for name,sha in EXPECTED.items():
        check_probe((OUT/"src"/("client" if name==CLIENT else "server")/name).read_bytes(),sha)
    # Authoritative original remains one game and one Remote. Two probes just observe.
    game=(OUT/"src/server/Game.server.luau").read_text(encoding="utf-8")
    if game.count('remote.Name = "TrapRaidersS1Remote"')!=1:
        raise ValueError("AUTHORITY_REMOTE_COUNT_UNEXPECTED")
    for f in (OUT/"src/server/StudioPassiveServerProbe.server.luau",
              OUT/"src/client/StudioPassiveClientProbe.client.luau"):
        if any(re.search(p,f.read_text(encoding="utf-8")) for p in DISALLOWED):
            raise ValueError("PROBE_WRITE_INTENT_DETECTED")
    lock=json.loads((OUT/"QA_ONLY_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    lock.update({
        "real_Rojo_XML_script_classes":dict(classes),
        "real_Rojo_XML_verified_exact_30":True,
        "actual_qa_place_bytes":place.stat().st_size,
        "actual_qa_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    })
    receipt.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("H1_QA_ONLY_REAL_ROJO_XML_PRESERVES_ALL_28_ORIGINAL_PLUS_2_PROBES_EXACT")
    print("H1_QA_ONLY_PLACE_SHA256",lock["actual_qa_place_sha256"])

if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--assemble",action="store_true")
    arg.add_argument("--verify-xml",type=Path)
    arg.add_argument("--receipt",type=Path)
    a=arg.parse_args()
    if a.assemble:
        assemble()
    elif a.verify_xml is not None:
        if a.receipt is None: raise ValueError("--receipt required")
        verify_xml(a.verify_xml,a.receipt)
    else:
        arg.error("Specify --assemble or --verify-xml")
