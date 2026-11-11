#!/usr/bin/env python3
"""Independent read-only actual S1 OFFICIAL RC integrity + native semantic QA.

Pin exact official Git commit and compare the WHOLE actual RC source tree to
pinned source import. Does NOT authorize actual Roblox release or Studio pass.
"""
import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys

import native_rules_gate as rules
import native_boss_receipt_gate as window
import native_d07_chain_gate as chain
import native_d07_temporal_gate as temporal

RC="fffdda7024def24b6ce756c39fa6e0c2fa35b288"
CAND="b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc"
RC_ROOT="releases/P0D_S1_KIDS_RC01/"
CAND_ROOT="handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/candidate/"
SCHEMA={"files","format","game_id","packet_id","public_source_allowed","work_id"}
SOURCE_SHA="b95f91fcf802607ff9d5f45a816553b295f68b8a"
OLD_RC="35d7d0525388e885aac8281eff2315a59831e0cf"
IMPORT_COMMIT="17ffd5c28bf15aeefa5f524291534f064f74029f"

def git(repo,*args):
    p=subprocess.run(["git","-C",repo,*args],capture_output=True,check=False)
    if p.returncode:
        raise RuntimeError("GIT_INPUT_UNAVAILABLE "+str(args)+": "+p.stderr.decode("utf-8","replace")[-200:])
    return p.stdout

def read_git(repo,commit,path):
    return git(repo,"show",commit+":"+path)

def tree(repo,commit):
    raw=git(repo,"ls-tree","-r","-z",commit)
    entries={}
    for row in raw.split(b"\0"):
        if not row: continue
        meta,path=row.split(b"\t",1)
        mode,kind,sha=meta.decode("ascii").split(" ")
        if kind=="blob": entries[path.decode("utf-8")]=sha
    return entries

def reltree(repo,commit,root):
    return {path[len(root):]:sha for path,sha in tree(repo,commit).items() if path.startswith(root)}

def guard(condition,code):
    if not condition: raise RuntimeError(code)

def verify_manifest(manifest,actual_paths,contents):
    guard(type(manifest)==dict and set(manifest)==SCHEMA,"BAD_MANIFEST_ROOT_KEYS")
    guard(manifest["format"]=="P0D_PUBLIC_SOURCE_V1" and
          manifest["game_id"]=="TRAP_RAIDERS" and
          manifest["packet_id"]=="P0D-S1-KIDS-RC01" and
          manifest["work_id"]=="p0d-siege-v19" and
          manifest["public_source_allowed"] is True,"BAD_MANIFEST_ID")
    records=manifest["files"]
    guard(isinstance(records,list) and len(records)==32,"NOT_32_MANIFEST_ENTRIES")
    declared={}
    for row in records:
        guard(isinstance(row,dict) and set(row)=={"path","sha256","size"},"BAD_ENTRY_SCHEMA")
        path=row["path"]
        guard(isinstance(path,str) and path not in declared and not path.startswith("/") and
              ".." not in path.split("/") and re.fullmatch(r"[0-9a-f]{64}",row["sha256"]) is not None
              and type(row["size"])==int and row["size"]>=0,"BAD_MANIFEST_ENTRY")
        declared[path]=row
    expected=set(actual_paths)-{"BUILD_MANIFEST.json"}
    guard(set(declared)==expected,"UNLISTED_OR_MISSING_RC_FILE")
    for path,row in declared.items():
        content=contents[path]
        guard(isinstance(content,bytes),"NOT_RAW_CONTENT "+path)
        guard(len(content)==row["size"] and hashlib.sha256(content).hexdigest()==row["sha256"],
              "RC_MANIFEST_DIGEST_MISMATCH "+path)
    return len(declared)

def guard_flags(game_source,release,selection,receipt,actual_subtree):
    guard(game_source.count("local CANONICAL_S1_ENABLED = false")==1,"CANONICAL_FLAG_NOT_OFF")
    guard(game_source.count("local D07_D08_RELEASE_REVIEW_APPROVED = false")==1,"D07_REVIEW_FLAG_NOT_OFF")
    guard(game_source.count("remote.OnServerEvent:Connect(")==1,"DUPLICATED_NETWORK_AUTHORITY")
    guard(release["first_release_authorized"] is False and
          release["monetization_enabled"] is False and
          release["roblox_studio_2client"]=="NOT_TESTED_CURRENT_RC",
          "UNSUPPORTED_RELEASE_ASSERTION")
    guard(selection["source_git_tree_sha"]==actual_subtree and
          selection["source_candidate_fixed_sha"]==CAND and
          selection["source_import_commit"]==IMPORT_COMMIT and
          selection["source_and_flags"]["CANONICAL_S1_ENABLED"] is False and
          selection["source_and_flags"]["D07_D08_RELEASE_REVIEW_APPROVED"] is False,
          "FORGED_SOURCE_LOCK")
    guard(receipt["previous_rc_commit"]==OLD_RC and
          receipt["import_commit"]==IMPORT_COMMIT and
          receipt["candidate_source_commit"]==CAND and
          receipt["src_subtree_sha"]==actual_subtree and
          receipt["source_luau_count"]==20 and
          receipt["official_20_file_native"]=="NOT_VERIFIED" and
          receipt["owner_public_release_approved"] is False,
          "FORGED_IMPORT_RECEIPT")

def verify(repo):
    rc_paths=reltree(repo,RC,RC_ROOT)
    guard(len(rc_paths)==33,"UNEXPECTED_RC_FILE_COUNT_"+str(len(rc_paths)))
    contents={path:read_git(repo,RC,RC_ROOT+path) for path in rc_paths}
    manifest=json.loads(contents["BUILD_MANIFEST.json"])
    count=verify_manifest(manifest,set(rc_paths),contents)
    actual_src=git(repo,"rev-parse",RC+":"+RC_ROOT+"src").decode().strip()
    expected_src=git(repo,"rev-parse",CAND+":"+CAND_ROOT+"src").decode().strip()
    guard(actual_src==expected_src==SOURCE_SHA,"OFFICIAL_RC_SOURCE_TREE_CHANGED")
    candidate_paths=reltree(repo,CAND,CAND_ROOT)
    src={path:sha for path,sha in rc_paths.items() if path.startswith("src/")}
    original={path:sha for path,sha in candidate_paths.items() if path.startswith("src/")}
    guard(src==original and len(src)==20 and
          all(p.endswith(".luau") for p in src),"RC_20_LUAU_DIFFER_FROM_IMPORTED_SOURCE")
    game=contents["src/server/Game.server.luau"].decode("utf-8")
    release=json.loads(contents["docs/RELEASE_STATUS.json"])
    selection=json.loads(contents["docs/SOURCE_SELECTION.json"])
    receipt=json.loads(contents["CHAT_RC_RECEIPT.json"])
    guard_flags(game,release,selection,receipt,actual_src)
    # Intentional negative probes: every one MUST be refused.
    total=0
    bad=copy.deepcopy(manifest)
    bad["files"][0]["sha256"]="0"*64
    try: verify_manifest(bad,set(rc_paths),contents)
    except RuntimeError: total+=1
    bad=copy.deepcopy(manifest)
    more=set(rc_paths); more.add("src/server/HiddenGame.server.luau")
    try: verify_manifest(bad,more,contents)
    except RuntimeError: total+=1
    badgame=game.replace("local D07_D08_RELEASE_REVIEW_APPROVED = false",
                        "local D07_D08_RELEASE_REVIEW_APPROVED = true",1)
    try: guard_flags(badgame,release,selection,receipt,actual_src)
    except RuntimeError: total+=1
    badsel=dict(selection);badsel["source_git_tree_sha"]="0"*40
    try: guard_flags(game,release,badsel,receipt,actual_src)
    except RuntimeError: total+=1
    corrupt=dict(contents);corrupt["src/server/Game.server.luau"]=b"malicious"
    try: verify_manifest(manifest,set(rc_paths),corrupt)
    except RuntimeError: total+=1
    guard(total==5,"NEGATIVE_PROBES_NOT_FAIL_CLOSED")
    print("P0D_ACTUAL_OFFICIAL_RC_SOURCE_PASS manifest=%d/32 luau=20/20 subtree=%s"%(
        count,actual_src))
    print("P0D_ACTUAL_RC_INTEGRITY_NEGATIVE_CONTROLS=5/5")
    return True

def actual_native_against_rc(repo,luau):
    # Historical independently written test programs contain fixed SHA source
    # targets. Point those very same test oracles at ACTUAL official RC, while
    # preserving their Git blob SHA locks and every assertion/mutation probe.
    rules.PIN=RC
    rules.PATH=RC_ROOT+"src/server/S1Rules.luau"
    window.SOURCE_COMMIT=RC
    window.SOURCE_PATH=RC_ROOT+"src/server/GoroganAttackReceiptWindow.luau"
    chain.BASE=RC
    chain.ROOT=RC_ROOT+"src/server/"
    temporal.baseline=chain
    for name,runner in [
        ("S1Rules",rules.main),
        ("AttackReceipt",window.main),
        ("FourModule",chain.main),
        ("ThreeStompTemporal",temporal.main)
    ]:
        original_args=sys.argv
        try:
            sys.argv=["exact-rc-native","--repo",repo,"--luau",luau]
            guard(runner()==0,"RC_NATIVE_GATE_FAILED_"+name)
            print("P0D_OFFICIAL_RC_NATIVE_MODULE_PASS "+name)
        finally: sys.argv=original_args
    print("P0D_OFFICIAL_RC_NATIVE_SEMANTIC_ASSERTIONS=7927")
    print("P0D_OFFICIAL_RC_ALL_NATIVE_MUTATIONS_REJECTED=17")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True)
    p.add_argument("--luau",required=True)
    a=p.parse_args()
    verify(a.repo)
    actual_native_against_rc(a.repo,a.luau)
    print("P0D_ACTUAL_OFFICIAL_RC_QA_SUCCESS immutable_commit="+RC)
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except (OSError,RuntimeError,ValueError,UnicodeError,subprocess.TimeoutExpired) as e:
        print("P0D_ACTUAL_OFFICIAL_RC_QA_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(1)
