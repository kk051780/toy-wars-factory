#!/usr/bin/env python3
"""Source-exact original #508 neutral death credit inline policy on ONE current V3 RC31 Swarm.
No new score, Swarm, Game, Remote, Store or extra script. Not Studio proof.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path
import xml.etree.ElementTree as ET

OWNER508_HEAD="101a77b2f7dd041fe4f17d31f67cf7232ba4cda1"
OWNER508_POLICY_BLOB="00eed6aa306656eded1e3c9fc62acdf1a86ce248"
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
N=31
INSERT_AFTER='local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))\n'
BEFORE=('   if type(id)=="string" and session.rules.phase=="ACTIVE"\n'
        '    and session.rules.castles[id] and session.rules.castles[id].alive then\n')
AFTER=('   if type(id)=="string" and session.rules.phase=="ACTIVE"\n'
       '    and session.rules.castles[id] and session.rules.castles[id].alive\n'
       '    and KoFence.mayCredit(session,id,m,all) then\n')


def git_blob(data: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()


def sha(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()


def mapping(project: Path):
    doc=json.loads(project.read_text(encoding="utf-8"))
    found={}
    def walk(node,chain=()):
        for key,value in node.items():
            if key.startswith("$"):continue
            if not isinstance(value,dict):raise ValueError("RED_NOT_SCRIPT_MAP")
            path=chain+(key,)
            if "$path" in value:
                if set(value)!={"$path"} or path in found:
                    raise ValueError("RED_DUPLICATE_SCRIPT_AUTHORITY")
                found[path]=(project.parent/value["$path"]).resolve(strict=True)
            else:walk(value,path)
    walk(doc["tree"])
    if len(found)!=N or len({k[-1] for k in found})!=N or SWARM not in found:
        raise ValueError("RED_NOT_EXACT_SINGLE_SWARM_31")
    return doc,found


def author_policy(file: Path):
    original=file.read_bytes()
    if git_blob(original)!=OWNER508_POLICY_BLOB:
        raise ValueError("RED_ORIGINAL508_GIT_BLOB_DRIFT")
    text=original.decode("utf-8")
    for token in ("local Fence = {}","function Fence.decide(","function Fence.mayCredit("):
        if text.count(token)!=1:raise ValueError("RED_ORIGINAL508_POLICY_DRIFT "+token)
    if text.count("\nreturn Fence")==0 or not text.rstrip().endswith("return Fence"):
        raise ValueError("RED_AUTHOR508_MODULE_TRAILER_DRIFT")
    # Embed original author's full unchanged policy body, NOT rewrite or fork its logic.
    inner=text.replace("--!strict\n","",1)
    return 'local KoFence=(function()\n'+inner.rsplit("return Fence",1)[0]+'return Fence\nend)()\n'


def overlay(current: str, policy: str)->str:
    if "KoFence.mayCredit(" in current or "local KoFence=(function()" in current:
        raise ValueError("RED_ALREADY_SELECTED_OR_DOUBLE_NEUTRAL_KO_OWNER")
    if current.count(INSERT_AFTER)!=1 or current.count(BEFORE)!=1:
        raise ValueError("RED_NEUTRAL_ORIGINAL_AUTHOR_HOOK_DRIFT")
    for check in ("h.Died:Connect(", "local function credit(", "ImpactFeedback.ko(",
                  "SpawnPacing.step(", "EncounterFair.chooseIndex(",
                  "session.neutralBudget:acquire(", "candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"):
        if current.count(check)!=1:raise ValueError("RED_UPSTREAM_NEUTRAL_AUTHORITY_DRIFT "+check)
    selected=current.replace(INSERT_AFTER,INSERT_AFTER+policy,1).replace(BEFORE,AFTER,1)
    if selected.replace(INSERT_AFTER+policy,INSERT_AFTER,1).replace(AFTER,BEFORE,1)!=current:
        raise ValueError("RED_NOT_REVERSIBLE_ORIGINAL508_INLINE")
    if selected.count("h.Died:Connect(")!=1 or selected.count("local function credit(")!=1:
        raise ValueError("RED_DUPLICATE_KO_HANDLER")
    return selected


def prepare(base: Path, policy_file: Path, out: Path):
    base=base.resolve(strict=True)
    policy_file=policy_file.resolve(strict=True)
    if out.resolve()==base or out.parent.resolve()!=base.parent:
        raise ValueError("RED_SELECT_MUST_BE_SIBLING_NOT_INPLACE")
    data,original=mapping(base)
    source=original[SWARM].read_text(encoding="utf-8")
    policy=author_policy(policy_file)
    changed=overlay(source,policy)
    host=out.parent/"GQ508_ORIGINAL_NEUTRAL_SWARM.luau"
    if host.exists() and host.read_text(encoding="utf-8")!=changed:
        raise ValueError("RED_PREEXISTING_SELECTED_SWARM_MISMATCH")
    host.write_text(changed,encoding="utf-8")
    selected=copy.deepcopy(data)
    selected["tree"]["ServerScriptService"][SWARM[-1]]["$path"]=host.name
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,files=mapping(out)
    if set(original)!=set(files) or [k for k in files if original[k].read_bytes()!=files[k].read_bytes()]!=[SWARM]:
        raise ValueError("RED_OTHER_CURRENT_SOURCE_MODIFIED")
    proof={
        "script_count":31,"original_author508_head":OWNER508_HEAD,
        "original_author508_policy_git_blob":OWNER508_POLICY_BLOB,
        "source_changed":"/".join(SWARM),"other_30_byte_identical":True,
        "original_single_died_callback":True,"original_single_credit_function":True,
        "off_project":base.name,"on_project":out.name,
        "off_rollback_byte_exact":True,
        "source_sha256_before":sha(source.encode()),"source_sha256_after":sha(changed.encode()),
        "policy_exact_inner_embedded":True,
        "no_extra_script_or_score_authority":True,
        "studio_android_owner":"NOT_TESTED","official_rc_adopted":False,
    }
    (out.parent/"GQ508_NEUTRAL_KO_RC31_RECEIPT.json").write_text(
        json.dumps(proof,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ508_ORIGINAL_508_SERVER_KO_DEATH_GATE_INLINE_CURRENT31_OTHER30_EXACT")


def verify(base: Path, policy_file: Path, selected: Path, place: Path):
    _,old=mapping(base.resolve(strict=True))
    _,now=mapping(selected.resolve(strict=True))
    if set(old)!=set(now) or [k for k in old if old[k].read_bytes()!=now[k].read_bytes()]!=[SWARM]:
        raise ValueError("RED_NEUTRAL_SOURCE_NOT_ONLY_ONE")
    expected=overlay(old[SWARM].read_text(encoding="utf-8"),author_policy(policy_file.resolve(strict=True)))
    if now[SWARM].read_text(encoding="utf-8")!=expected:
        raise ValueError("RED_ORIGINAL_AUTHOR_POLICY_SOURCE_NOT_EXACT")
    found={}
    for entry in ET.parse(place).iter("Item"):
        kind=entry.attrib.get("class")
        if kind not in {"Script","ModuleScript","LocalScript"}:continue
        props=entry.find("Properties")
        if props is None:raise ValueError("RED_SCRIPT_PROPS_MISSING")
        name=props.findtext("string[@name='Name']")
        content=props.findtext("ProtectedString[@name='Source']")
        if content is None:content=props.findtext("string[@name='Source']")
        if not name or content is None or name in found:raise ValueError("RED_SCRIPT_DUPLICATE")
        found[name]=(kind,content.replace("\r\n","\n"))
    if set(found)!={k[-1] for k in now}:raise ValueError("RED_EMBEDDED_SOURCE_NAMES_NOT31")
    for key,path in now.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]]!=(kind,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_EMBEDDED_ROJO_SOURCE_CLASS_MISMATCH "+key[-1])
    receipt=selected.parent/"GQ508_NEUTRAL_KO_RC31_RECEIPT.json"
    data=json.loads(receipt.read_text(encoding="utf-8"))
    if not data["other_30_byte_identical"] or not data["off_rollback_byte_exact"]:
        raise ValueError("RED_RECEIPT_UNSAFE")
    data.update({"real_rojo_source_class_exact":"31/31","place_bytes":place.stat().st_size,
                 "place_sha256":sha(place.read_bytes())})
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ508_NEUTRAL_KO_FINAL31_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",data["place_bytes"],data["place_sha256"])


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("action",choices=("prepare","verify"))
    cli.add_argument("--base",type=Path,required=True)
    cli.add_argument("--author",type=Path,required=True)
    cli.add_argument("--out",type=Path,required=True)
    cli.add_argument("--place",type=Path)
    args=cli.parse_args()
    if args.action=="prepare":
        prepare(args.base,args.author,args.out)
    else:
        if not args.place:cli.error("verify needs --place")
        verify(args.base,args.author,args.out,args.place)


if __name__=="__main__":main()
