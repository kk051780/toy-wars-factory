#!/usr/bin/env python3
"""Select ONE pinned original #551 carrier-avatar Died callback into latest 31-source RC.
Pure source composer; original #551 author owns fix; #220 CAS writer owns official RC.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.machinery, json, os
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_COMPOSER_BLOB = "a330cf72caa71444562bf973c96a47d3fd4ce679"
AUTHOR_COMMIT = "93d774bf3aaecd0e7714d64a7f970003698d69ef"
ORIGINAL_HOST_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
HOST = ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
SWARM = ("ServerScriptService","EGGRUMBLE_SwarmCombat")
ITEM = ("ServerScriptService","EGGRUMBLE_FieldItemPickups")
COMBAT = ("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
DIED = "humanoid.Died:Connect(function()\n"
STOP = "\n     end))"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode()+b"\0"+data).hexdigest()

def load_author(path: Path):
    path=path.resolve(strict=True)
    if blob(path.read_bytes()) != AUTHOR_COMPOSER_BLOB:
        raise ValueError("RED_GQ551_PINNED_AUTHOR_COMPOSER_DRIFT")
    return importlib.machinery.SourceFileLoader("gq551_pinned_author",str(path)).load_module()

def flatten(path: Path):
    doc=json.loads(path.read_text(encoding="utf-8"))
    result={}
    def walk(node,parents=()):
        for name,value in node.items():
            if name.startswith("$"): continue
            if not isinstance(value,dict): raise ValueError("RED_INVALID_PROJECT_NODE")
            key=parents+(name,)
            if "$path" in value:
                if set(value)!={"$path"} or key in result: raise ValueError("RED_DUPLICATE_SOURCE_ROUTE")
                result[key]=(path.parent/value["$path"]).resolve(strict=True)
            else:walk(value,key)
    walk(doc["tree"])
    if len(result)!=31 or len({k[-1] for k in result})!=31:
        raise ValueError("RED_NOT_EXACTLY_31_UNIQUE_SOURCES")
    for key in (HOST,SWARM,ITEM,COMBAT):
        if key not in result: raise ValueError("RED_MISSING_SINGLE_AUTHORITY")
    return doc,result

def body(source: str) -> str:
    if source.count(DIED)!=1: raise ValueError("RED_HUMANOID_DIED_CALLBACK_DRIFT")
    tail=source.split(DIED,1)[1]
    if tail.count(STOP)<1:raise ValueError("RED_UNCLOSED_DIED_CALLBACK")
    return tail.split(STOP,1)[0]

def guards(author) -> tuple[str,str]:
    original=author.SOURCE.read_bytes()
    if blob(original)!=ORIGINAL_HOST_BLOB:raise ValueError("RED_ORIGINAL_482_HOST_DRIFT")
    raw=original.decode("utf-8")
    patched=author.patch(raw)
    before=body(raw).split('      local rootPart=',1)[0].rstrip("\n")
    after=body(patched).split('      local rootPart=',1)[0].rstrip("\n")
    if before!='      if joined[player.UserId]~=mode then return end':
        raise ValueError("RED_551_UNEXPECTED_ORIGINAL_GUARD")
    if (after.count("player.Character~=character")!=1
        or after.count("sessions[mode]~=session")!=1
        or after.count('session.rules.phase~="ACTIVE"')!=1
        or after.count("joined[player.UserId]~=mode")!=1):
        raise ValueError("RED_AUTHOR_551_GUARD_NOT_UNIQUE")
    if body(patched).replace(after,before,1)!=body(raw):
        raise ValueError("RED_AUTHOR_551_CHANGED_MORE_THAN_ONE_GUARD")
    return before,after

def patch(current: str,author) -> tuple[str,str,str]:
    old,new=guards(author)
    callback=body(current)
    if new in callback: raise ValueError("RED_ALREADY_ADOPTED_DO_NOT_DUPLICATE")
    if callback.count(old)!=1: raise ValueError("RED_CURRENT_HOST_GUARD_DRIFT")
    # Preserve #537 egg refresh, #540 assassin new-avatar stealth, #539 lobby presentation.
    if current.count('p:SetAttribute("EGGRUMBLE_StealthUntil",nil)')!=1:
        raise ValueError("RED_540_RESPAWN_FIX_MISSING")
    if current.count("session.refresh=function()")!=1:
        raise ValueError("RED_CASTLE_REFRESH_STATE_LOST")
    if current.count("session.dropCarrierEggs(tostring(player.UserId),")!=1:
        raise ValueError("RED_CARRIER_EGG_AUTHORITY_DRIFT")
    # Do not replace a similar guard elsewhere in match/queue/AI.
    modified=current.replace(DIED+callback+STOP,DIED+callback.replace(old,new,1)+STOP,1)
    if modified.replace(new,old,1)!=current:
        raise ValueError("RED_NONEXACT_ROLLBACK")
    return modified,old,new

def prepare(base:Path,author_path:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.exists(): raise ValueError("RED_OUTPUT_PROJECT_ALREADY_EXISTS")
    # Rewrite all 30 untouched paths relative to the isolated output folder.
    author=load_author(author_path)
    project,old=flatten(base)
    existing=old[HOST].read_text(encoding="utf-8")
    selected,old_guard,new_guard=patch(existing,author)
    if blob(old[ITEM].read_bytes())!="107046cb0bf81fed9e3cba1699ada31571e44a22":
        raise ValueError("RED_489_AUTHOR_ITEM_SOURCE_MISSING")
    folder=out.parent
    host=folder/"GQ551_CARRIER_CURRENT31.server.luau"
    if host.exists():raise ValueError("RED_SELECTED_HOST_OVERWRITE")
    host.write_text(selected,encoding="utf-8",newline="")
    doc=copy.deepcopy(project)
    doc["name"]="EGGRUMBLE_RC31_GQ551_ORIGINAL_CARRIER_AFTER_541_537_540_539_489"
    def rewrite(node,parents=()):
        for name,v in node.items():
            if name.startswith("$"):continue
            key=parents+(name,)
            if "$path" in v:
                file=host if key==HOST else old[key]
                v["$path"]=os.path.relpath(file,folder).replace(os.sep,"/")
            else:rewrite(v,key)
    rewrite(doc["tree"])
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,new=flatten(out)
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if changed!=[HOST] or len(new)!=31: raise ValueError("RED_MUST_CHANGE_ONLY_EXISTING_HOST")
    if any(old[k].read_bytes()!=new[k].read_bytes() for k in old if k!=HOST):
        raise ValueError("RED_OTHER30_SOURCE_DRIFT")
    # Execute actual extracted Host callback in native Luau, no fake hand-written behavior.
    native=author.native_cases(selected)
    if native.count("local function actualDiedCallback()")!=1 or "PASS 7 CASES" not in native:
        raise ValueError("RED_551_NATIVE_SOURCE_EXTRACTION_FAILED")
    (folder/"GQ551_ACTUAL_CALLBACK_7_NATIVE.luau").write_text(native,encoding="utf-8")
    receipt={
      "feature":"GQ_V3_CARRIER_STALE_AVATAR_DIED_FENCE_551",
      "original_551_commit":AUTHOR_COMMIT,
      "author_551_compose_blob":AUTHOR_COMPOSER_BLOB,
      "original_482_host_blob":ORIGINAL_HOST_BLOB,
      "source_count":31,
      "changed_script":"/".join(HOST),
      "other_30_source_bytes_exact":True,
      "source_previous_host_sha256":sha(existing.encode()),
      "source_selected_host_sha256":sha(selected.encode()),
      "previous_item489_sha256":sha(old[ITEM].read_bytes()),
      "old_guard":old_guard,
      "new_guard":new_guard,
      "rollback":"Unselect 551 only; restore exact #489 31-source project",
      "primary_rich51_untouched":True,
      "formal_rc_adoption_before_cas":False,
      "studio_android_art_fun_owner":"NOT_TESTED"
    }
    (folder/"GQ551_RC31_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ551_EXACT_ORIGINAL_ONE_HOST_30_OF_31_OTHER_BYTES_UNCHANGED_PASS")
    return receipt

def verify(base:Path,selected:Path,place:Path,author_path:Path):
    author=load_author(author_path)
    _,old=flatten(base)
    _,new=flatten(selected)
    if set(new)!=set(old):raise ValueError("RED_CHANGED_31_ROUTES")
    if [k for k in old if new[k].read_bytes()!=old[k].read_bytes()]!=[HOST]:
        raise ValueError("RED_EXPECTED_SINGLE_HOST_DELTA")
    current=new[HOST].read_text(encoding="utf-8")
    expected,_,rev=patch(old[HOST].read_text(encoding="utf-8"),author)
    if current!=expected or current.replace(rev,guards(author)[0],1)!=old[HOST].read_text(encoding="utf-8"):
        raise ValueError("RED_ORIGINAL_GUARD_ROLLBACK")
    actual={}
    for item in ET.parse(place).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None: raise ValueError("RED_XML_MISSING_PROPS")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in actual:raise ValueError("RED_XML_DUPLICATE")
        actual[name]=(cls,source.replace("\r\n","\n"))
    if len(actual)!=31 or set(actual)!={k[-1] for k in new}:raise ValueError("RED_REAL_ROJO_SCRIPT_COUNT")
    for k,path in new.items():
        cls=("Script" if path.name.endswith(".server.luau") else
             "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if actual[k[-1]]!=(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_REAL_ROJO_SOURCE_CLASS "+k[-1])
    report={
      "status":"SOURCE_SELECTED_31_PRIVATE_NO_OFFICIAL_CAS",
      "native_real_callback_cases":7,
      "rojo_real_source_class_exact":"31/31",
      "unchanged_existing_sources":30,
      "exact_host_rollback":True,
      "place_bytes":place.stat().st_size,
      "place_sha256":sha(place.read_bytes()),
      "studio_android_owner":"NOT_TESTED",
      "main_publish_spend":False
    }
    (selected.parent/"GQ551_RC31_VERIFIED_PLACE_RECEIPT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ551_RC31_ORIGINAL_CARRIER_REAL_ROJO_SOURCE_CLASS_31_31_PASS",report["place_bytes"],report["place_sha256"])
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--author",required=True,type=Path)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="prepare":prepare(a.base,a.author,a.out)
    elif a.place:verify(a.base,a.out,a.place,a.author)
    else:p.error("--place needed for verify")

if __name__=="__main__":main()
