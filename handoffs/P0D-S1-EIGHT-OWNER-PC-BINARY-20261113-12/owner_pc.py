#!/usr/bin/env python3
"""Keyless OFFLINE exact 8-safe binary verification; optional no-overwrite staging.

Never opens Roblox Studio, does not publish, make network calls, edit game code,
or label any real PC/mobile test as complete.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import zipfile

PLACE = "TRAP_RAIDERS_S1_EIGHT_SAFE_HUD_REVIEW.rbxlx"
RECEIPT = "EIGHT_SAFE_HUD_REVIEW_ONLY_RECEIPT.json"
LOCK = "SOURCE_LOCK.json"
CASES = "SCENARIOS_NOT_TESTED.json"
MANIFEST = "TRANSFER_MANIFEST.json"
FILES = (PLACE, RECEIPT, LOCK, CASES, "STUDIO_QA_CARDS.md", "README.md", "owner_pc.py")
ORIGINAL_SHA256 = "b27f401cd6aed7242665098a4cf323184fe13f2ef964b59a3c97b82daf998d04"
ORIGINAL_BYTES = 159080
SOURCE_SHA = "7b4f95a3f424741bbe8ff1c555c5f5a2ed64d4bd"
OFFICIAL_RC = "1263a03701211a652b99b91d2339575dc8104eff"
CI_RUN = 43257388055
CI_ARTIFACT = 13961872174
STAGE = "P0D_S1_EIGHT_OWNER_STUDIO_QA_b27f401cd6ae"
MANIFEST_FORMAT = "P0D_S1_EIGHT_OWNER_TRANSFER_V1"
EXPECTED_SECTIONS = {"Script":1,"LocalScript":3,"ModuleScript":17}

class Blocked(Exception):
    pass

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def parse_json(data: bytes, where: str):
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise Blocked(where+"_INVALID_JSON") from exc

def verify_files(files: dict[str,bytes]) -> dict:
    if set(files) != set(FILES) | {MANIFEST}:
        raise Blocked("EXACT_FILE_SET_WRONG")
    m=parse_json(files[MANIFEST],"TRANSFER_MANIFEST")
    if set(m) != {"format","files","place_sha256","studio_tested","owner_publish_approved"}:
        raise Blocked("TRANSFER_MANIFEST_FIELDS")
    if m["format"] != MANIFEST_FORMAT or m["place_sha256"] != ORIGINAL_SHA256:
        raise Blocked("TRANSFER_MANIFEST_VERSION_OR_PLACE_PIN")
    if m["studio_tested"] is not False or m["owner_publish_approved"] is not False:
        raise Blocked("FORGED_TEST_OR_PUBLISH_STATUS")
    hashes=m["files"]
    if not isinstance(hashes,dict) or set(hashes)!=set(FILES):
        raise Blocked("MANIFEST_FILE_SET_MISMATCH")
    for name in FILES:
        content=files[name]
        item=hashes[name]
        if (not isinstance(item,dict) or set(item)!={"size","sha256"}
                or type(item["size"]) is not int or item["size"] != len(content)
                or item["sha256"] != sha(content)):
            raise Blocked("BUNDLE_FILE_HASH_MISMATCH:"+name)
    if len(files[PLACE]) != ORIGINAL_BYTES or sha(files[PLACE]) != ORIGINAL_SHA256:
        raise Blocked("WRONG_GAME_BINARY_SOURCE")
    if b"<roblox" not in files[PLACE][:512]:
        raise Blocked("GAME_NOT_XML_ROBLOX_PLACE")
    lock=parse_json(files[LOCK],"SOURCE_LOCK")
    required = {
        "format":"P0D_S1_EIGHT_SAFE_OWNER_PC_BINARY_LOCK_V1",
        "preview_commit":SOURCE_SHA,
        "original_CI_head":SOURCE_SHA,
        "original_native_Rojo_CI_run_id":CI_RUN,
        "original_CI_gh_artifact_id":CI_ARTIFACT,
        "original_place_sha256":ORIGINAL_SHA256,
        "original_place_size":ORIGINAL_BYTES,
        "original_place_filename":PLACE,
        "official_RC_base":OFFICIAL_RC,
        "original_source_37_entries":37,
        "actual_embedded_scripts":21,
        "original_rojo_bad_XML_mutations_rejected":12,
        "genuine_luau_compiler_scripts_passed":21,
        "scenario_count":30,
        "expected_script_classes":EXPECTED_SECTIONS,
        "boss_D07_D08_enabled":False,
        "studio_actual_2client_tested":False,
        "studio_actual_mobile_tested":False,
        "human_child_playtest_tested":False,
        "owner_published":False,
        "owner_release_authorized":False,
        "stage":"PRELAUNCH",
    }
    if any(lock.get(k)!=v or type(lock.get(k)) is not type(v) for k,v in required.items()):
        raise Blocked("SOURCE_LOCK_INVALID_OR_FALSE_STUDIO_RESULT")
    receipt=parse_json(files[RECEIPT],"ORIGINAL_CI_RECEIPT")
    must={
        "format":"P0D_EIGHT_CHANGE_S1_RBXLX_REVIEW_ONLY_V1",
        "source_scripts_verified":21,
        "server_scripts":1,
        "local_scripts":3,
        "module_scripts":17,
        "rojo_xml_mutations_rejected":12,
        "place_sha256":ORIGINAL_SHA256,
        "place_bytes":ORIGINAL_BYTES,
        "studio_tested":False,
        "two_real_clients_tested":False,
        "mobile_tested":False,
        "owner_approved_public_release":False,
        "published":False,
    }
    if any(receipt.get(k)!=v or type(receipt.get(k)) is not type(v) for k,v in must.items()):
        raise Blocked("ORIGINAL_RECEIPT_FALSE_OR_UNPINNED")
    qa=parse_json(files[CASES],"REAL_STUDIO_CASES")
    if (qa.get("format")!="P0D_S1_EIGHT_REAL_STUDIO_QA_NOT_TESTED_V1"
        or qa.get("source_place_sha256")!=ORIGINAL_SHA256
        or qa.get("studio_tested") is not False
        or qa.get("owner_publish_approval") is not False
        or qa.get("qa_release_authorized") is not False):
        raise Blocked("STUDIO_QA_CLAIM_NOT_SAFELY_UNTESTED")
    rows=qa.get("scenarios")
    if not isinstance(rows,list) or len(rows)!=30:
        raise Blocked("NOT_EXACTLY_30_STUDIO_CASES")
    ids=[r.get("id") for r in rows if isinstance(r,dict)]
    if (len(ids)!=30 or len(set(ids))!=30
        or any(not isinstance(i,str) or not i for i in ids)
        or any(r.get("status")!="NOT_TESTED" or r.get("evidence")!=[]
               or r.get("owner_reviewed") is not False
               or r.get("actual_observation") is not None for r in rows)):
        raise Blocked("FORGED_OR_DUPLICATE_STUDIO_EVIDENCE")
    return {
        "status":"SOURCE_BINARY_VERIFIED_NOT_STUDIO",
        "source_SHA":SOURCE_SHA,
        "place_sha256":ORIGINAL_SHA256,
        "place_bytes":ORIGINAL_BYTES,
        "files":len(FILES),
        "studio_cases_NOT_TESTED":30,
        "studio_tested":False,
        "two_clients_tested":False,
        "mobile_tested":False,
        "public_release_authorized":False,
    }

def verify_folder(folder: Path):
    if not folder.is_dir() or folder.is_symlink():
        raise Blocked("BUNDLE_MUST_BE_REAL_DIRECTORY")
    expected=set(FILES)|{MANIFEST}
    if set(p.name for p in folder.iterdir())!=expected:
        raise Blocked("UNKNOWN_MISSING_OR_EXTRA_BUNDLE_FILE")
    data={}
    for name in expected:
        p=folder/name
        if p.is_symlink() or not p.is_file():
            raise Blocked("BUNDLE_SYMLINK_OR_NOT_FILE:"+name)
        if p.stat().st_size>500000:
            raise Blocked("OVERSIZED_BUNDLE_FILE")
        data[name]=p.read_bytes()
    return data

def verify_zip(path: Path):
    if not path.is_file() or path.is_symlink():
        raise Blocked("ZIP_MISSING_OR_SYMLINK")
    if path.stat().st_size>1000000:
        raise Blocked("ARCHIVE_OVERSIZE")
    result={}
    try:
        with zipfile.ZipFile(path,"r") as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or set(names)!=set(FILES)|{MANIFEST}:
                raise Blocked("ZIP_EXTRA_DUPLICATE_OR_TRAVERSAL_NAME")
            for entry in z.infolist():
                if (entry.filename!=Path(entry.filename).name or
                    entry.filename.startswith(".") or
                    not entry.is_file() or entry.flag_bits&1 or
                    stat.S_IFMT(entry.external_attr>>16)==stat.S_IFLNK or
                    entry.file_size>500000):
                    raise Blocked("ZIP_UNSAFE_ENTRY")
            if sum(x.file_size for x in z.infolist())>900000:
                raise Blocked("ZIP_UNCOMPRESSED_SIZE_LIMIT")
            if z.testzip() is not None:
                raise Blocked("ZIP_CRC_FAILURE")
            for name in names:
                result[name]=z.read(name)
    except (zipfile.BadZipFile,ValueError,EOFError,RuntimeError) as exc:
        raise Blocked("INVALID_ZIP_CONTENT") from exc
    verify_files(result)
    return result

def prepare(data: dict[str,bytes], destination: Path) -> dict:
    verify_files(data)
    if not destination.is_absolute() or not destination.is_dir():
        raise Blocked("EXISTING_ABSOLUTE_DESTINATION_REQUIRED")
    node=destination
    while True:
        if node.is_symlink():
            raise Blocked("DESTINATION_SYMLINK_FORBIDDEN")
        if node==node.parent: break
        node=node.parent
    target=destination/STAGE
    if target.exists() or target.is_symlink():
        raise Blocked("NO_OVERWRITE_TARGET_ALREADY_EXISTS")
    try:
        target.mkdir(mode=0o700,exist_ok=False)
    except FileExistsError as exc:
        raise Blocked("NO_OVERWRITE_TARGET_ALREADY_EXISTS") from exc
    for name in FILES+(MANIFEST,):
        with (target/name).open("xb") as output:
            output.write(data[name])
    verify_files(verify_folder(target))
    return {"status":"ISOLATED_PC_QA_COPY_CREATED_NO_STUDIO","path":str(target),
            "place_file":str(target/PLACE),"no_files_overwritten":True,
            "real_roblox_studio":"NOT_TESTED","public_release_authorized":False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group()
    g.add_argument("--bundle",type=Path)
    g.add_argument("--zip",dest="zip_path",type=Path)
    p.add_argument("--prepare",action="store_true")
    p.add_argument("--destination",type=Path)
    args=p.parse_args(argv)
    try:
        if args.zip_path:
            files=verify_zip(args.zip_path)
        else:
            files=verify_folder(args.bundle or Path(__file__).resolve().parent)
        if args.prepare:
            if args.destination is None:
                raise Blocked("DESTINATION_REQUIRED_WITH_PREPARE")
            result=prepare(files,args.destination)
        else:
            result=verify_files(files)
    except (Blocked,OSError,TypeError,ValueError,UnicodeError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc),
                          "studio_tested":False,"published":False},ensure_ascii=False))
        return 2
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    sys.exit(main())
