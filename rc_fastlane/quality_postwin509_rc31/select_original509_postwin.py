#!/usr/bin/env python3
"""GQ509 proven original-author post-win late carrier-death egg freeze onto actual RC31.

Strict one function delta in one existing CastleMatchRules ModuleScript only.
No new Script/Game/Remote/Store/Score. Exact source-lock of #509 author, current
31 selected script inventory, native selected Rules, true Rojo Source/Class and
OFF rollback; formal RC admission only via #220 expected_sha nonforce CAS.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_zombie582_rc31"))
from select_original_zombie582 import scan, git_blob, digest

ROUTE=("ServerScriptService","EGGRUMBLE_CastleMatchRules")
AUTHOR_HEAD="a259e2d7a962f52061541276de3f2b1afbc9a7a4"
ORIGINAL_BLOB="27da5ca1e9e6d9a7afe0674030e387f094ee7492"
PATCHED_BLOB="ed87d70e7df94279af737871e8e439b9fc108d4f"
RECEIPT="GQ509_LATE_DEATH_RC31_SOURCE_EXACT_RECEIPT.json"
OUT_RULES="GQ509_CURRENT31_TERMINAL_EGG_RULES.luau"
NATIVE_SUFFIX="GQ509_CURRENT31_LATE_DEATH"

def author_patch(checker:Path,original:Path,patched:Path):
    spec=importlib.util.spec_from_file_location("original_gq509_author",checker)
    m=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    if git_blob(original.read_bytes())!=ORIGINAL_BLOB or git_blob(patched.read_bytes())!=PATCHED_BLOB:
        raise ValueError("RED_AUTHOR_GQ509_BLOB_DRIFT")
    # Executes immutable original #509's byte-exact one-function diff contract.
    selected=m.check_exact(original,patched)
    if selected!=original.read_text(encoding="utf8").replace(m.FIND,m.REPLACE):
        raise ValueError("RED_ORIGINAL_GQ509_AUTHOR_DIFF_NOT_EXACT")
    return m

def apply(current:str,m):
    if current.count(m.FIND)!=1 or current.count(m.REPLACE)!=0:
        raise ValueError("RED_CURRENT_RULES_ANCHOR_DRIFT_OR_ALREADY_APPLIED")
    if current.count("function M.onCarrierEliminated(")!=1 or not current.rstrip().endswith("return M"):
        raise ValueError("RED_CURRENT_RULES_AUTHORITY_OR_SHAPE_DRIFT")
    changed=current.replace(m.FIND,m.REPLACE,1)
    if changed.replace(m.REPLACE,m.FIND,1)!=current:
        raise ValueError("RED_GQ509_OFF_EXACT_ROLLBACK")
    if changed.count('if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end')!=1:
        raise ValueError("RED_TERMINAL_GUARD_DUPLICATE")
    return changed

def checked_files(base:Path,out:Path):
    oldproject,old=scan(base)
    newproject,new=scan(out)
    if len(old)!=31 or len(new)!=31:raise ValueError("RED_COUNT")
    if set(old)!=set(new) or ROUTE not in old or ROUTE not in new:
        raise ValueError("RED_RULES_LAYOUT_OR_31_CHANGED")
    if sum(old[x].read_bytes()!=new[x].read_bytes() for x in old)!=1:
        raise ValueError("RED_NOT_SINGLE_CHANGED_RULES_SOURCE")
    if any(old[x].read_bytes()!=new[x].read_bytes() for x in old if x!=ROUTE):
        raise ValueError("RED_OTHER30_NOT_BYTE_EXACT")
    return oldproject,old,new

def prepare(base:Path,out:Path,checker:Path,original:Path,patched:Path):
    if out.exists() or base.parent.resolve()!=out.parent.resolve() or out.name==base.name:
        raise ValueError("RED_NEW_SIBLING_OUTPUT_ONLY")
    m=author_patch(checker,original,patched)
    original_project,old=scan(base)
    if len(old)!=31 or ROUTE not in old:
        raise ValueError("RED_NO_RULES_OR_31_DRIFT")
    before=old[ROUTE].read_bytes()
    after=apply(before.decode("utf8"),m).encode("utf8")
    target=out.parent/OUT_RULES
    if target.exists():raise ValueError("RED_TARGET_ALREADY_EXISTS")
    target.write_bytes(after)
    project=copy.deepcopy(original_project)
    project["tree"][ROUTE[0]][ROUTE[1]]["$path"]=OUT_RULES
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,_,new=checked_files(base,out)
    assert new[ROUTE].read_bytes()==after
    receipt={
        "feature":"POSTWIN_LATE_CARRIER_DEATH_FREEZE_509",
        "source_author_head":AUTHOR_HEAD,
        "original_author_rules_blob":ORIGINAL_BLOB,
        "patched_author_rules_blob":PATCHED_BLOB,
        "new_game_or_remote_or_score_authority":False,
        "existing_rules_module_only":True,
        "previous_source_count":31,
        "source_count":31,
        "changed_scripts":1,
        "other30_byte_exact":True,
        "off_current_rules_byte_exact":True,
        "pre_rules_sha256":digest(before),
        "post_rules_sha256":digest(after),
        "native_current_rules":"NOT_RUN",
        "rojo_source_class":"NOT_RUN",
        "formal_rc_source_adoption":False,
        "studio_2client":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "owner":"NO_GO"
    }
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ509_ONE_EXISTING_RULES_OTHER30_EXACT_OFF_ROLLBACK_PASS")

def verify(base:Path,out:Path,place:Path,checker:Path,original:Path,patched:Path):
    m=author_patch(checker,original,patched)
    _,old,new=checked_files(base,out)
    expected=apply(old[ROUTE].read_text(encoding="utf8"),m)
    if new[ROUTE].read_text(encoding="utf8")!=expected:
        raise ValueError("RED_GQ509_SELECTED_ORIGINAL_HUNK_DRIFT")
    script_by_name={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("ModuleScript","Script","LocalScript"):continue
        prop=item.find("Properties")
        if prop is None:raise ValueError("RED_XML_NO_PROPERTIES")
        name=prop.findtext("string[@name='Name']")
        src=prop.findtext("ProtectedString[@name='Source']")
        if src is None:src=prop.findtext("string[@name='Source']")
        if not name or src is None or name in script_by_name:
            raise ValueError("RED_DUPLICATED_OR_BAD_XML_SCRIPT")
        script_by_name[name]=(cls,src.replace("\r\n","\n"))
    if len(script_by_name)!=31 or {k[-1] for k in new}!=set(script_by_name):
        raise ValueError("RED_REAL_ROJO_SCRIPT_COUNT")
    for route,path in new.items():
        cls=("Script" if path.name.endswith(".server.luau") else
             "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if script_by_name[route[-1]]!=(cls,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_REAL_SOURCE_CLASS_"+route[-1])
    rec=json.loads((out.parent/RECEIPT).read_text(encoding="utf8"))
    if (rec["pre_rules_sha256"]!=digest(old[ROUTE].read_bytes()) or
        rec["post_rules_sha256"]!=digest(new[ROUTE].read_bytes())):
        raise ValueError("RED_GQ509_SHA_RECEIPT_DRIFT")
    rec.update({
        "native_current_rules":"PASS_EXPECTED_IN_CI",
        "rojo_source_class":"31/31",
        "place_bytes":place.stat().st_size,
        "place_sha256":digest(place.read_bytes()),
        "verified_other30_exact":True,
        "verified_off_revert_exact":True
    })
    (out.parent/RECEIPT).write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ509_REAL_ROJO31_SOURCE_CLASS_AND_OFF_OTHER30_PASS",place.stat().st_size)

def harness(source:Path,test:Path,output:Path,mutant:bool=False):
    from importlib.util import spec_from_file_location,module_from_spec
    raw=source.read_text(encoding="utf8")
    if not raw.rstrip().endswith("return M"):raise ValueError("RED_NOT_LUAU_RULES")
    if mutant:
        guard=' if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end\n'
        if raw.count(guard)!=1:raise ValueError("RED_MUTANT_ANCHOR_DRIFT")
        raw=raw.replace(guard,"",1)
    last=raw.rstrip()
    last=last[:-len("return M")]
    if test.read_text(encoding="utf8").count("local Rules=M")!=1:
        raise ValueError("RED_ORIGINAL_NATIVE_SPEC_SHAPE")
    if output.exists():raise ValueError("RED_NATIVE_OUTPUT_EXISTS")
    output.write_text(last+test.read_text(encoding="utf8"),encoding="utf8")
    print("GQ509_NATIVE_SELECTED_CURRENT_RULES_EXACT_SOURCE_HARNESS_READY",("MUTANT" if mutant else "NORMAL"))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["prepare","verify","harness"])
    p.add_argument("--base",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checker",type=Path)
    p.add_argument("--original",type=Path)
    p.add_argument("--patched",type=Path)
    p.add_argument("--place",type=Path)
    p.add_argument("--source",type=Path)
    p.add_argument("--test",type=Path)
    p.add_argument("--mutant",action="store_true")
    a=p.parse_args()
    if a.mode=="harness":
        if not a.source or not a.test: p.error("harness requires --source and --test")
        harness(a.source,a.test,a.out,a.mutant)
    else:
        if not all((a.base,a.out,a.checker,a.original,a.patched)):p.error("missing source inputs")
        kw=dict(base=a.base,out=a.out,checker=a.checker,original=a.original,patched=a.patched)
        if a.mode=="prepare":prepare(**kw)
        else:
            if not a.place:p.error("verify needs place")
            verify(place=a.place,**kw)
