#!/usr/bin/env python3
"""SOURCE-SELECT existing original #551 stale-avatar egg-carrier Died guard into
the ONE current canonical V3 Host, after #541/#537/#540/#539/#489.
Do not reimplement the fix or overwrite any other author's 30 real scripts.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_HEAD="93d774bf3aaecd0e7714d64a7f970003698d69ef"
AUTHOR_COMPOSER_BLOB="a330cf72caa71444562bf973c96a47d3fd4ce679"
AUTHOR482_HOST_BLOB="7162b209bf67b74a71553217f3f744e072a0365d"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
BOT=("ServerScriptService","EGGRUMBLE_BotActors")
ITEM=("ServerScriptService","EGGRUMBLE_FieldItemPickups")
OLD='      if joined[player.UserId]~=mode then return end'
SIZE=31

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def flatten(project:Path):
    project=project.resolve(strict=True)
    doc=json.loads(project.read_text(encoding="utf-8"))
    result={}
    def visit(node,prefix=()):
        for name,v in node.items():
            if name.startswith("$"):continue
            if not isinstance(v,dict):raise ValueError("RED_NON_DICT_PROJECT_NODE")
            route=prefix+(name,)
            if "$path" in v:
                if set(v)!={"$path"} or route in result:raise ValueError("RED_MULTI_SOURCE_MAP")
                result[route]=(project.parent/v["$path"]).resolve(strict=True)
            else:visit(v,route)
    visit(doc["tree"])
    if len(result)!=SIZE or len({r[-1] for r in result})!=SIZE:
        raise ValueError("RED_SOURCE_31_COUNT_OR_DUPLICATE")
    for r in (HOST,SWARM,COMBAT,BOT,ITEM):
        if r not in result:raise ValueError("RED_GAME_AUTHORITY_ABSENT "+str(r))
    return doc,result

def author_import(path:Path):
    path=path.resolve(strict=True)
    if blob(path.read_bytes())!=AUTHOR_COMPOSER_BLOB:
        raise ValueError("RED_GQ551_EXISTING_AUTHOR_PATCH_SCRIPT_DRIFT")
    spec=importlib.util.spec_from_file_location("immutable_author_gq551",path)
    assert spec is not None and spec.loader is not None
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    if obj.AUTHOR_HEAD!= "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9" or obj.ORIGINAL_BLOB!=AUTHOR482_HOST_BLOB:
        raise ValueError("RED_GQ551_PARENT_SOURCE_PIN_DRIFT")
    if blob(obj.SOURCE.read_bytes())!=AUTHOR482_HOST_BLOB:
        raise ValueError("RED_GQ551_PARENT_ORIGINAL_HOST_DRIFT")
    return obj

def existing_author_delta(author):
    original=author.SOURCE.read_text(encoding="utf-8")
    patched=author.patch(original)
    if original.count(OLD)!=1:
        raise ValueError("RED_GQ551_ORIGINAL_INSERTION_NOT_UNIQUE")
    before, _, after=original.partition(OLD)
    if not patched.startswith(before) or not patched.endswith(after):
        raise ValueError("RED_GQ551_AUTHOR_CHANGED_ANOTHER_REGION")
    replacement=patched[len(before):len(patched)-len(after)]
    if not replacement or patched!=original.replace(OLD,replacement,1):
        raise ValueError("RED_GQ551_NOT_EXACT_ONE_AUTHORED_DELTA")
    if replacement.count("player.Character~=character")!=1 or replacement.count("sessions[mode]~=session")!=1 or 'session.rules.phase~="ACTIVE"' not in replacement:
        raise ValueError("RED_GQ551_GUARD_INCOMPLETE")
    if replacement.count("session.dropCarrierEggs")!=0:
        raise ValueError("RED_GQ551_DUPLICATE_CARRIER_AUTHORITY")
    return replacement

def prepare(base:Path,author_path:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.exists():raise ValueError("RED_OUTPUT_ALREADY_EXISTS")
    author=author_import(author_path)
    doc,oldfiles=flatten(base)
    previous=oldfiles[HOST].read_text(encoding="utf-8")
    # Exact original anchor still present AFTER genuine #537, #540 and #539 Host patches.
    if previous.count(OLD)!=1 or previous.count("humanoid.Died:Connect(function()")!=1:
        raise ValueError("RED_CURRENT_GQ551_CARRIER_DIED_ANCHOR_DRIFT")
    if previous.count("session.dropCarrierEggs(tostring(player.UserId),")!=1:
        raise ValueError("RED_CURRENT_EGG_CARRIER_AUTHORITY_DUPLICATE")
    for tok in ('session.isCurrentHuman=function', 'gqDualBudget=GQDualBudget.new('):
        if previous.count(tok)!=1:
            raise ValueError("RED_GQ531_528_HOST_DEPENDENCY_MISSING "+tok)
    replacement=existing_author_delta(author)
    patched=previous.replace(OLD,replacement,1)
    if patched.replace(replacement,OLD,1)!=previous:
        raise ValueError("RED_GQ551_OFF_ROLLBACK_NOT_EXACT")
    if patched.count(replacement)!=1:
        raise ValueError("RED_GQ551_SELECTED_CARRIER_GUARD_DUPLICATED")
    # Ensure original 30 source files are the *existing latest official selected* sources.
    if "SpawnPacing.step(" not in oldfiles[SWARM].read_text(encoding="utf-8") or "nearest.humanoid:TakeDamage(Melee.DAMAGE)" not in oldfiles[SWARM].read_text(encoding="utf-8"):
        raise ValueError("RED_GQ541_SWARM_LOST")
    item=oldfiles[ITEM].read_text(encoding="utf-8")
    if 'interactionGuard.allow(player,part,"拾う",part.Name)' not in item:
        raise ValueError("RED_GQ489_ITEM_SOURCE_LOST")
    out.parent.mkdir(parents=True,exist_ok=True)
    host=out.parent/"GQ551_SINGLE_EXISTING_HOST.server.luau"
    if host.exists():raise ValueError("RED_GQ551_HOST_ALREADY_PRESENT")
    host.write_text(patched,encoding="utf-8",newline="")
    new=copy.deepcopy(doc)
    new["name"]="EGGRUMBLE_V3_RC31_GQ551_EXISTING_AUTHOR_CARRIER_CURRENT_AVATAR"
    def remap(node,prefix=()):
        for name,v in node.items():
            if name.startswith("$"):continue
            key=prefix+(name,)
            if "$path" in v:
                src=host if key==HOST else oldfiles[key]
                v["$path"]=os.path.relpath(src,out.parent).replace(os.sep,"/")
            else:remap(v,key)
    remap(new["tree"])
    out.write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,now=flatten(out)
    if set(now)!=set(oldfiles):raise ValueError("RED_GQ551_SOURCE_KEYS_CHANGED")
    changed=[r for r in oldfiles if oldfiles[r].read_bytes()!=now[r].read_bytes()]
    if changed!=[HOST]:raise ValueError("RED_GQ551_NOT_ONLY_ONE_HOST "+str(changed))
    if now[HOST].read_text()!=patched:raise ValueError("RED_GQ551_HOST_SOURCE_SELECT_WRONG")
    for r in oldfiles:
        if r!=HOST and oldfiles[r].read_bytes()!=now[r].read_bytes():
            raise ValueError("RED_GQ551_UNAUTHORIZED_AUTHOR_REWRITE "+str(r))
    cases=out.parent/"GQ551_ACTUAL_HOST_DIED_NATIVE.luau"
    mutant=out.parent/"GQ551_OLD_GUARD_MUTANT.luau"
    cases.write_text(author.native_cases(patched),encoding="utf-8")
    mutant.write_text(author.native_cases(previous),encoding="utf-8")
    report={
       "feature":"GQ551_CARRIER_STALE_AVATAR_DIED_FENCE",
       "script_count":31,
       "original_author551_head":AUTHOR_HEAD,
       "original_author551_composer_blob":AUTHOR_COMPOSER_BLOB,
       "old_original_host_blob":AUTHOR482_HOST_BLOB,
       "existing_rc31_base_project_sha256":sha(base.read_bytes()),
       "selected_rc31_project_sha256":sha(out.read_bytes()),
       "previous_selected_host_sha256":sha(previous.encode("utf-8")),
       "new_selected_host_sha256":sha(patched.encode("utf-8")),
       "single_host_only_changed":True,
       "previous_other_30_sources_byte_exact":30,
       "original_current_541_swarm_preserved":True,
       "original_489_item_preserved":True,
       "original_537_540_539_host_preserved":True,
       "old_guard_mutant_must_fail":True,
       "rollback":base.name,
       "native_original_died_callback_case_count":7,
       "formal_rc_attested":False,
       "studio_android_owner":"NOT_TESTED",
       "source_sha256":{"/".join(k):sha(p.read_bytes()) for k,p in sorted(now.items())}
    }
    (out.parent/"GQ551_RC31_SOURCE_RECEIPT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("GQ551_ORIGINAL_AUTHOR_REAL_CURRENT_RC31_SINGLE_HOST_30_UNCHANGED_PASS")
    return report

def verify(base:Path,chosen:Path,place:Path,author_path:Path):
    author=author_import(author_path)
    _,old=flatten(base)
    _,now=flatten(chosen)
    if set(old)!=set(now):raise ValueError("RED_GQ551_PLACE_ROUTE_CHANGED")
    original=old[HOST].read_text(encoding="utf-8")
    replacement=existing_author_delta(author)
    if now[HOST].read_text(encoding="utf-8")!=original.replace(OLD,replacement,1):
        raise ValueError("RED_GQ551_AUTHOR_PATCH_NOT_EXACT")
    if now[HOST].read_text().replace(replacement,OLD,1)!=original:
        raise ValueError("RED_GQ551_ROLLBACK_NOT_BYTE_EXACT")
    changed=[k for k in old if old[k].read_bytes()!=now[k].read_bytes()]
    if changed!=[HOST]:
        raise ValueError("RED_GQ551_ONLY_HOST_MUST_CHANGE")
    expected={}
    for k,p in now.items():
        typ=("Script" if p.name.endswith(".server.luau") else "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
        expected[k[-1]]=(typ,p.read_text(encoding="utf-8").replace("\r\n","\n"))
    actual={}
    for it in ET.fromstring(place.read_bytes()).iter("Item"):
        typ=it.attrib.get("class")
        if typ not in {"Script","LocalScript","ModuleScript"}:continue
        props=it.find("Properties")
        if props is None:raise ValueError("RED_GQ551_PLACE_PROPERTIES_MISSING")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in actual:
            raise ValueError("RED_GQ551_PLACE_SOURCE_DUPLICATE_OR_ABSENT")
        actual[name]=(typ,source.replace("\r\n","\n"))
    if expected!=actual:
        raise ValueError("RED_GQ551_ROJO_SOURCE_CLASS_31_MISMATCH")
    recpath=chosen.parent/"GQ551_RC31_SOURCE_RECEIPT.json"
    receipt=json.loads(recpath.read_text())
    for k,p in now.items():
        if receipt["source_sha256"]["/".join(k)]!=sha(p.read_bytes()):
            raise ValueError("RED_GQ551_SOURCE_MOVED_SINCE_COMPOSE "+str(k))
    receipt["real_rojo_source_class_exact"]="31/31"
    receipt["place_bytes"]=place.stat().st_size
    receipt["place_sha256"]=sha(place.read_bytes())
    recpath.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ551_RC31_ON_ONLY_ONE_HOST_ROJO_EXACT_31_31_PASS",receipt["place_bytes"],receipt["place_sha256"])
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("prepare","verify"))
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--author",type=Path,required=True)
    ap.add_argument("--place",type=Path)
    args=ap.parse_args()
    if args.action=="prepare":
        prepare(args.base,args.author,args.out)
    else:
        if args.place is None:ap.error("--place is required for verify")
        verify(args.base,args.out,args.place,args.author)
if __name__=="__main__":main()
