#!/usr/bin/env python3
"""Patch ONLY original #482 FIELD egg spawn Z rows; source-locked and reversible."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ORIGINAL_COMMIT="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_HOST_BLOB="7162b209bf67b74a71553217f3f744e072a0365d"
ORIGINAL_LINE="  local at=root+Vector3.new(worldX+(col-3.5)*93,3,290+row*200)\n"
REPLACEMENT_LINE="  local at=root+Vector3.new(worldX+(col-3.5)*93,3,rowZ[row+1])\n"
INSERT_AT=" -- Field eggs available in both modes, not single/multi mode toggles.\n"
ROWS_LINE=' local rowZ=if mode=="TEAM" then {338,506,610} else {338,448,676}\n'

def blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

def patch(source:str)->str:
    assert "local rowZ=" not in source, "already patched: never compose same fix twice"
    assert source.count(ORIGINAL_LINE)==1, "original field-egg positions moved; rebase required"
    assert source.count(INSERT_AT)==1, "original original field egg anchor moved"
    assert source.count('local eggId="FIELD_"..i')==1
    assert source.count("for i=1,24 do")==1
    assert 'function M.new' not in source, "this file must be existing sole Lobby host"
    new=source.replace(INSERT_AT,INSERT_AT+ROWS_LINE,1).replace(ORIGINAL_LINE,REPLACEMENT_LINE,1)
    assert new.replace(ROWS_LINE,"",1).replace(REPLACEMENT_LINE,ORIGINAL_LINE,1)==source
    assert new.count('local eggId="FIELD_"..i')==1
    assert new.count("for i=1,24 do")==1
    return new

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    original=args.source.read_bytes()
    assert blob_sha(original)==ORIGINAL_HOST_BLOB,"original #482 host has drifted; fail closed"
    assert args.source.resolve()!=args.out.resolve(),"NEVER edit original author"
    changed=patch(original.decode("utf-8"))
    assert args.out.name=="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(changed,encoding="utf-8")
    print("FIELD_EGGS_ONLY_HOST_PATCH_PASS",hashlib.sha256(changed.encode()).hexdigest())

if __name__=="__main__":
    main()
