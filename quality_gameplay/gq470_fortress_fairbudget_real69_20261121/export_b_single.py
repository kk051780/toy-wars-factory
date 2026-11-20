#!/usr/bin/env python3
"""Verified one-existing-Source ONLY export for #220; NEVER formal RC adoption.

Input: official 69-source OFF and this patch's ON folder.
Emit exactly one selected FieldArt Luau byte stream + immutable audit manifest.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import tempfile

import patch_castle_fairbudget as p

PACKET = "B220_CASTLE_ONE_SELECTED_SOURCE_NOT_FORMAL"
MANIFEST = "SOURCE_SELECT_MANIFEST.json"

def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_B220_CASTLE_" + code)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def sha_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()

def prep(root: Path) -> tuple[dict, dict[str, bytes], dict[str, bytes], dict]:
    root = root.resolve()
    original_root = root / "OFF69_CASTLE_BUDGET"
    require(original_root.is_dir(), "MISSING_OFF")
    off_map, on_map = p.selected(original_root), p.selected(root)
    require(len(on_map) == len(off_map) == 69 and set(on_map) == set(off_map), "EXACT_69_ROUTES")
    current_meta = json.loads((root / p.RECEIPT).read_text(encoding="utf-8"))
    before_meta = json.loads((original_root / p.RECEIPT).read_text(encoding="utf-8"))
    require(before_meta["build_head"] == p.BASE, "ORIGINAL_HEAD")
    require(re.fullmatch(r"[0-9a-f]{40}", current_meta["build_head"]) and
            current_meta["build_head"] != p.BASE, "NOT_ACTUAL_PR_HEAD")
    require(current_meta["official_branch"] == "rc/p0d-s1-kids-rc01", "FORMAL_TARGET")
    require(current_meta["source_classes"] == before_meta["source_classes"], "SOURCE_CLASS_SET")
    require(current_meta["source_classes"].get(p.ROUTE) == "Script", "EXISTING_SCRIPT_CLASS")
    old = {r: src.read_bytes() for r, src in off_map.items()}
    new = {r: src.read_bytes() for r, src in on_map.items()}
    require({r for r in old if old[r] != new[r]} == {p.ROUTE}, "ONLY_ONE_CHANGED")
    require({r: digest(raw) for r, raw in old.items()} == before_meta["source_hashes"],
            "FORMAL_INPUT_LOCK")
    require({r: digest(raw) for r, raw in new.items()} == current_meta["source_hashes"],
            "CANDIDATE_RECEIPT_LOCK")
    require(digest(old[p.ROUTE]) == p.OLD_SHA, "FLAGSHIP_AUTHOR_PIN")
    require(new[p.ROUTE].count(p.FEATURE.encode()) == 1, "FEATURE_MARK")
    require((root / p.PLACE).stat().st_size ==
            current_meta["private_place_bytes"], "CANDIDATE_PLACE_SIZE")
    require(digest((root / p.PLACE).read_bytes()) ==
            current_meta["private_place_sha256"], "CANDIDATE_PLACE_SHA")
    require((original_root / p.PLACE).is_file(), "EXACT_ORIGINAL_PLACE_ABSENT")
    return current_meta,old,new,before_meta

def export(root: Path) -> Path:
    current,old,new,before = prep(root)
    output = root / PACKET
    require(not output.exists(), "EXISTING_PACKET")
    output.mkdir()
    only_source = output / "selected_sources" / (p.ROUTE + ".luau")
    only_source.parent.mkdir(parents=True)
    only_source.write_bytes(new[p.ROUTE])
    original_place = (root / "OFF69_CASTLE_BUDGET" / p.PLACE).read_bytes()
    candidate_place = (root / p.PLACE).read_bytes()
    manifest = {
      "schema": "GQ470_B220_CASTLE_SINGLE_SOURCE_SELECT_V1",
      "feature_id": p.FEATURE,
      "formal_branch": "rc/p0d-s1-kids-rc01",
      "formal_base_head": p.BASE,
      "candidate_exact_pr_head": current["build_head"],
      "only_selected_route": p.ROUTE,
      "source_class": before["source_classes"][p.ROUTE],
      "source_count": 69,
      "only_changed_source_count": 1,
      "other_68_exact": True,
      "before_sha256": digest(old[p.ROUTE]),
      "after_sha256": digest(new[p.ROUTE]),
      "before_git_blob": sha_blob(old[p.ROUTE]),
      "after_git_blob": sha_blob(new[p.ROUTE]),
      "selected_bytes": len(new[p.ROUTE]),
      "candidate_place_bytes": len(candidate_place),
      "candidate_place_sha256": digest(candidate_place),
      "formal_place_bytes": len(original_place),
      "formal_place_sha256": digest(original_place),
      "reverse_source_folder": "OFF69_CASTLE_BUDGET",
      "source_cas_writer": "ISSUE_220_AUTHENTICATED_B_ONLY",
      "formal_rc_modified": False,
      "new_game_authority": False,
      "source_gate": "PASS_SOURCE_ONLY",
      "studio": "NOT_TESTED",
      "android": "NOT_TESTED",
      "art": "ART_NO_GO",
      "fun": "FUN_NO_GO",
      "owner_accepted": False,
    }
    (output / MANIFEST).write_text(json.dumps(manifest,sort_keys=True,ensure_ascii=False,indent=2)+"\n",
                                    encoding="utf-8")
    validate(output)
    return output

def validate(packet: Path) -> dict:
    packet=packet.resolve()
    manifest=json.loads((packet / MANIFEST).read_text(encoding="utf-8"))
    target=p.ROUTE
    actual_files={f.relative_to(packet).as_posix() for f in packet.rglob("*") if f.is_file()}
    expected_files={MANIFEST,"selected_sources/"+target+".luau"}
    require(actual_files == expected_files, "NO_ADDITIONAL_GAME_SOURCES")
    raw=(packet / "selected_sources" / (target+".luau")).read_bytes()
    require(manifest.get("schema")=="GQ470_B220_CASTLE_SINGLE_SOURCE_SELECT_V1", "SCHEMA")
    require(manifest.get("only_selected_route")==target and manifest.get("source_class")=="Script",
            "ORIGINAL_OWNER")
    require(manifest.get("source_count")==69 and manifest.get("only_changed_source_count")==1
            and manifest.get("other_68_exact") is True,"ROUTES")
    require(manifest.get("formal_base_head")==p.BASE, "FORMAL_BASE")
    require(re.fullmatch(r"[0-9a-f]{40}",manifest.get("candidate_exact_pr_head","")) is not None,
            "ACTUAL_HEAD")
    require(manifest.get("after_sha256")==digest(raw) and
            manifest.get("after_git_blob")==sha_blob(raw) and
            manifest.get("selected_bytes")==len(raw),"PAYLOAD_HASH")
    require(raw.count(p.FEATURE.encode())==1,"FEATURE")
    require(manifest.get("formal_rc_modified") is False and
            manifest.get("new_game_authority") is False and
            manifest.get("owner_accepted") is False,"FAKE_AUTHORIZATION")
    require(manifest.get("studio")=="NOT_TESTED" and
            manifest.get("android")=="NOT_TESTED" and
            manifest.get("art")=="ART_NO_GO","FAKE_ART_PROOF")
    return manifest

def selftest(packet: Path) -> None:
    baseline=validate(packet)
    with tempfile.TemporaryDirectory() as path:
        test=Path(path)/PACKET
        shutil.copytree(packet,test)
        out=test/MANIFEST
        raw=json.loads(out.read_text(encoding="utf-8"))
        for name,changed in [
          ("FAKE_SOURCE",{"after_sha256":"0"*64}),
          ("FAKE_PR_HEAD",{"candidate_exact_pr_head":"BAD"}),
          ("FAKE_ART_PASS",{"art":"ART_GO"}),
          ("FAKE_RC_WRITE",{"formal_rc_modified":True}),
          ("SECOND_SOURCE",{"only_changed_source_count":2}),
          ("DIFFERENT_OWNER",{"only_selected_route":"ServerScriptService/EGGRUMBLE_GameHost"}),
        ]:
            tmp={**raw,**changed}
            out.write_text(json.dumps(tmp),encoding="utf-8")
            try:
                validate(test)
            except ValueError:
                pass
            else:
                raise AssertionError("RED_MUTANT_ACCEPTED_"+name)
        out.write_text(json.dumps(raw),encoding="utf-8")
        extra=test/"selected_sources"/"ServerScriptService"/"ROGUE_Game.luau"
        extra.write_text("-- forbidden duplicate owner",encoding="utf-8")
        try:
            validate(test)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_EXTRA_SOURCE_ACCEPTED")
        extra.unlink()
        selected=test/"selected_sources"/(p.ROUTE+".luau")
        selected.write_bytes(selected.read_bytes()+b"\n-- forged")
        try:
            validate(test)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_PAYLOAD_TAMPER_ACCEPTED")
    print("B220_CASTLE_ONE_SOURCE_PACKET_8_NEGATIVES_PASS",baseline["candidate_exact_pr_head"])

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",type=Path,required=True)
    args=parser.parse_args()
    output=export(args.base)
    selftest(output)
    print("B220_CASTLE_ONE_SOURCE_BYTES_ONLY_PASS",output)
