#!/usr/bin/env python3
"""One-author GQ582 zombie source-select AFTER final official31 Swarm/ITEM/Host.
No duplicated Game/Combat/Remote/Store, and 30/31 source bytes identical.
Private/premerge candidate until #220 sole-writer CAS and official sameHEAD CI.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_582_HEAD = "497ff09e7d148e591691f5b1e3f5c543d6794ee8"
COMPOSER_BLOB = "d9491a682e1d66ab45451ed74857faaf328b5e20"
POLICY_BLOB = "6aa47b0baf7580f41e0e25f44acff91c18c56a81"
RUNTIME_BLOB = "7cc135ebedd6f72a5e34955f64fca60edd53a946"
COMBAT = ("ServerScriptService", "EGGRUMBLE_SevenRoleCombat")
SELECTED_SOURCE = "GQ582_SINGLE_EXISTING_COMBAT.luau"
RECEIPT = "GQ582_RC31_SOURCE_EXACT_RECEIPT.json"

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def scan(project_path: Path):
    obj = json.loads(project_path.read_text(encoding="utf8"))
    files = {}
    def visit(node, parent=()):
        for k, v in node.items():
            if k.startswith("$"): continue
            assert isinstance(v, dict), "RED_BAD_ROJO_NODE"
            route = parent + (k,)
            if "$path" in v:
                assert set(v) == {"$path"} and route not in files, "RED_DUPLICATE_SCRIPT"
                files[route] = (project_path.parent / v["$path"]).resolve(strict=True)
            else:
                visit(v,route)
    visit(obj["tree"])
    assert len(files) == 31 and len({r[-1] for r in files}) == 31, "RED_WRONG_31"
    for singular in ("EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SevenRoleCombat",
                     "EGGRUMBLE_SwarmCombat","EGGRUMBLE_BotActors",
                     "EGGRUMBLE_FieldItemPickups","EGGRUMBLE_MatchResultService"):
        assert sum(r[-1] == singular for r in files) == 1, "RED_AUTHORITY_" + singular
    assert COMBAT in files
    return obj, files

def author(composer: Path, policy: Path, runtime: Path):
    for file, expected in ((composer,COMPOSER_BLOB),(policy,POLICY_BLOB),
                           (runtime,RUNTIME_BLOB)):
        if git_blob(file.read_bytes()) != expected:
            raise ValueError("RED_GQ582_IMMUTABLE_AUTHOR_SOURCE_"+file.name)
    spec=importlib.util.spec_from_file_location("original582",composer)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module,policy.read_text(encoding="utf8"),runtime.read_text(encoding="utf8")

def expected_changed(before: str, mod, policy: str, runtime: str) -> str:
    # Original #582 composer is the ONLY author logic; this is a packaging adapter.
    # Require original Zombie hunk exactly once in the *latest composed #530 Combat*.
    if before.count(mod.OLD_ZOMBIE) != 1 or before.count(mod.HERO_ANCHOR) != 1:
        raise ValueError("RED_COMBAT_GQ530_SOURCE_DRIFT_OR_ALREADY_SELECTED")
    candidate=mod.compose(before,policy,runtime)
    # OFF must restore current accepted RC31 Combat including #530/#529/#516
    # and leave everything except original ZOMBIE body untouched.
    inline=candidate.split(mod.HERO_ANCHOR,1)[1].split(
        mod.OLD_ZOMBIE.splitlines()[0],1)[0]
    if not candidate.startswith(before.split(mod.HERO_ANCHOR,1)[0]+mod.HERO_ANCHOR):
        raise ValueError("RED_MODIFIED_COMBAT_HEADER")
    # Compute exact unique insertion through a known original tail.
    prefix,rest=before.split(mod.HERO_ANCHOR,1)
    after_prefix=candidate[len(prefix+mod.HERO_ANCHOR):]
    if not after_prefix.endswith(rest.replace(mod.OLD_ZOMBIE,mod.NEW_ZOMBIE,1)):
        raise ValueError("RED_NON_ZOMBIE_COMBAT_CHANGED")
    inserted=after_prefix[:-len(rest.replace(mod.OLD_ZOMBIE,mod.NEW_ZOMBIE,1))]
    if candidate.count(inserted)!=1 or not inserted.startswith("local ZombieCommander="):
        raise ValueError("RED_ONE_INLINE_AUTHORITY_NOT_PROVEN")
    if candidate.replace(inserted,"",1).replace(mod.NEW_ZOMBIE,mod.OLD_ZOMBIE,1)!=before:
        raise ValueError("RED_OFF_RESTORE_NOT_BYTE_EXACT")
    return candidate

def prepare(base:Path, composer:Path, policy:Path, runtime:Path, out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.parent != base.parent or out==base or out.exists():
        raise ValueError("RED_OUTPUT_NOT_CLEAN_SIBLING")
    project,files=scan(base)
    mod,p,r=author(composer,policy,runtime)
    before=files[COMBAT].read_bytes()
    if b"local HeroCombat={}" not in before or b"ZOMBIE" not in before:
        raise ValueError("RED_LATEST_COMBAT_MISSING_ORIGINAL_OWNER")
    candidate=expected_changed(before.decode("utf8"),mod,p,r).encode("utf8")
    src=out.parent/SELECTED_SOURCE
    if src.exists():
        raise ValueError("RED_OUTPUT_EXISTS")
    src.write_bytes(candidate)
    selected=copy.deepcopy(project)
    selected["tree"][COMBAT[0]][COMBAT[1]]["$path"]=SELECTED_SOURCE
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,selected_files=scan(out)
    if set(files)!=set(selected_files): raise ValueError("RED_SCRIPT_LAYOUT_DRIFT")
    if sum(files[k].read_bytes()!=selected_files[k].read_bytes() for k in files)!=1:
        raise ValueError("RED_NOT_EXACT_ONE_COMBAT_DELTA")
    if any(files[k].read_bytes()!=selected_files[k].read_bytes() for k in files if k!=COMBAT):
        raise ValueError("RED_OTHER30_CHANGED")
    receipt={
       "schema":"GQ582_RC31_ONE_COMBAT_SOURCE_EXACT",
       "author_head":AUTHOR_582_HEAD,
       "author_composer_blob":COMPOSER_BLOB,
       "policy_blob":POLICY_BLOB,"runtime_blob":RUNTIME_BLOB,
       "base_project":base.name,"selected_project":out.name,
       "source_count":31,"new_scripts":0,"changed_single_script":"/".join(COMBAT),
       "unchanged_previous_scripts":30,
       "original_combat_sha256":digest(before),
       "selected_combat_sha256":digest(candidate),
       "original_off_rollback_byte_exact":True,
       "official_rc_adopted":False,
       "roblox_engine_tested":False,"android_tested":False
    }
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ582_LATEST_COMPOSED31_SINGLE_COMBAT_ONLY_AND_OFF_EXACT_PASS")
    return receipt

def verify(base:Path,out:Path,place:Path,composer:Path,policy:Path,runtime:Path):
    project,old=scan(base);_,new=scan(out)
    mod,p,r=author(composer,policy,runtime)
    candidate=expected_changed(old[COMBAT].read_text(),mod,p,r)
    if set(old)!=set(new) or new[COMBAT].read_text()!=candidate:
        raise ValueError("RED_SELECTED_COMBAT_NOT_EXACT")
    if sum(old[k].read_bytes()!=new[k].read_bytes() for k in old)!=1:
        raise ValueError("RED_CHANGED_NOT_EXACT_ONE")
    actual={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.attrib.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"): continue
        props=item.find("Properties")
        if props is None: raise ValueError("RED_MISSING_PROPS")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None: src=props.findtext("string[@name='Source']")
        if not name or src is None or name in actual: raise ValueError("RED_BAD_SCRIPT_XML")
        actual[name]=(kind,src.replace("\r\n","\n"))
    if len(actual)!=31 or {r[-1] for r in new}!=set(actual):
        raise ValueError("RED_PLACE_WRONG_SCRIPT_SET")
    for route,source in new.items():
        expected="Script" if source.name.endswith(".server.luau") else (
                 "LocalScript" if source.name.endswith(".client.luau") else "ModuleScript")
        if actual[route[-1]]!=(expected,source.read_text().replace("\r\n","\n")):
            raise ValueError("RED_SOURCE_CLASS_MISMATCH "+route[-1])
    receipt=json.loads((out.parent/RECEIPT).read_text())
    if digest(old[COMBAT].read_bytes())!=receipt["original_combat_sha256"]:
        raise ValueError("RED_OFF_COMBAT_DRIFT")
    receipt.update({"real_rojo_source_class_exact":"31/31",
                    "place_bytes":place.stat().st_size,
                    "place_sha256":digest(place.read_bytes()),
                    "source_lock_author_582":True,
                    "all_30_other_domains_byte_exact":True})
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ582_TRUE_RC31_ROJO31_SCRIPT_CLASS_SOURCE_EXACT_PASS",receipt["place_bytes"])

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["prepare","verify"])
    for name in ("base","out","composer","policy","runtime"):
        ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--place",type=Path)
    args=ap.parse_args()
    if args.action=="prepare":
        prepare(args.base,args.composer,args.policy,args.runtime,args.out)
    else:
        if args.place is None: ap.error("--place required for verify")
        verify(args.base,args.out,args.place,args.composer,args.policy,args.runtime)
