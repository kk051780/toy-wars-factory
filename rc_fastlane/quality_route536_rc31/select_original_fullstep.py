#!/usr/bin/env python3
"""RC31: use the immutable ORIGINAL #536 one-line wall clearance author patch.
Only one existing BotPathRouter module changes; all 30 other author sources
remain EXACT after #541/#537/#540/#539/#489/#555. No extra AI or Game.
"""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json,os
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_HEAD="cdf4fe5f231c998532963c5c16d9525d20a69e7e"
AUTHOR_SCRIPT_BLOB="651d4c6e92bfe8595eeadb438b594797bd473e77"
PINNED_484_ROUTER_BLOB="d9841bb874659129cae6c930bce302ff6936ac4a"
ROUTER=("ServerScriptService","EGGRUMBLE_BotPathRouter")
BOT=("ServerScriptService","EGGRUMBLE_BotActors")
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
ITEM=("ServerScriptService","EGGRUMBLE_FieldItemPickups")
COUNT=31

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def flat(path:Path):
    path=path.resolve(strict=True)
    doc=json.loads(path.read_text(encoding="utf-8"))
    sources={}
    def visit(node,prefix=()):
        for name,v in node.items():
            if name.startswith("$"):continue
            if not isinstance(v,dict):raise ValueError("RED_GQ536_BAD_PROJECT_NODE")
            route=prefix+(name,)
            if "$path" in v:
                if set(v)!={"$path"} or route in sources:
                    raise ValueError("RED_GQ536_MULTIPLE_AUTHORITIES")
                sources[route]=(path.parent/v["$path"]).resolve(strict=True)
            else:visit(v,route)
    visit(doc["tree"])
    if len(sources)!=COUNT or len({x[-1] for x in sources})!=COUNT:
        raise ValueError("RED_GQ536_NOT_31_UNIQUE_SCRIPTS")
    for route in (ROUTER,BOT,HOST,SWARM,COMBAT,ITEM):
        if route not in sources:raise ValueError("RED_GQ536_MISSING_CANONICAL_SCRIPT_"+route[-1])
    return doc,sources

def load_author(path:Path):
    path=path.resolve(strict=True)
    if blob(path.read_bytes())!=AUTHOR_SCRIPT_BLOB:
        raise ValueError("RED_GQ536_AUTHOR_PATCH_FILE_CHANGED")
    spec=importlib.util.spec_from_file_location("pinned_author_gq536",path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.ORIGINAL_AUTHOR_HEAD!="6b52eaf1f2725496277998fe0c5532b7a8fcaab5" or mod.ORIGINAL_BLOB!=PINNED_484_ROUTER_BLOB:
        raise ValueError("RED_GQ536_AUTHOR_PARENT_PIN_CHANGED")
    return mod

def prepare(base:Path,author_path:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.exists() or out==base:raise ValueError("RED_GQ536_REFUSE_OVERWRITE")
    author=load_author(author_path)
    doc,old=flat(base)
    raw=old[ROUTER].read_bytes()
    if blob(raw)!=PINNED_484_ROUTER_BLOB:
        raise ValueError("RED_GQ536_LATEST_RC_ROUTER_NO_LONGER_484_SOURCE")
    fixed=author.overlay(raw,locked=True)
    if fixed==raw or fixed.decode().replace(author.AFTER,author.BEFORE,1)!=raw.decode():
        raise ValueError("RED_GQ536_NOT_EXACT_AUTHOR_SINGLE_LINE")
    if fixed.count(author.AFTER.encode("utf-8"))!=1:
        raise ValueError("RED_GQ536_RAY_PATCH_NOT_UNIQUE")
    # Ensure current official first layer includes previous authors; never source-select stale older BotActors.
    if "session.isCurrentHuman(player)" not in old[BOT].read_text(encoding="utf-8"):
        raise ValueError("RED_GQ531_HUMAN_FENCE_MISSING")
    if "candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)" not in old[SWARM].read_text(encoding="utf-8"):
        raise ValueError("RED_GQ541_NEUTRAL_FALLBACK_MISSING")
    if 'interactionGuard.allow(player,part,"拾う",part.Name)' not in old[ITEM].read_text(encoding="utf-8"):
        raise ValueError("RED_GQ489_ITEM_SOURCE_MISSING")
    out.parent.mkdir(parents=True,exist_ok=True)
    router=out.parent/"GQ536_EXISTING_BotPathRouter.luau"
    if router.exists():raise ValueError("RED_GQ536_EXISTING_PATCHED_ROUTER")
    router.write_bytes(fixed)
    new=copy.deepcopy(doc)
    new["name"]="EGGRUMBLE_GQ536_RC31_ACTUAL_AUTHOR_SINGLE_ROUTER_WALL_CLEAR"
    def visit(node,prefix=()):
        for name,v in node.items():
            if name.startswith("$"):continue
            route=prefix+(name,)
            if "$path" in v:
                target=router if route==ROUTER else old[route]
                v["$path"]=os.path.relpath(target,out.parent).replace(os.sep,"/")
            else:visit(v,route)
    visit(new["tree"])
    out.write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,mapped=flat(out)
    if set(mapped)!=set(old):
        raise ValueError("RED_GQ536_CHANGED_SCRIPT_TREE")
    changes=[k for k in mapped if old[k].read_bytes()!=mapped[k].read_bytes()]
    if changes!=[ROUTER]:
        raise ValueError("RED_GQ536_ONLY_BOTPATHROUTER_MAY_CHANGE "+repr(changes))
    if mapped[ROUTER].read_bytes()!=fixed:
        raise ValueError("RED_GQ536_GENERATED_SCRIPT_BYTES_CHANGED")
    receipt={
       "feature":"GQ536_BOT_NAV_FULL_REQUESTED_STEP_RAYCAST",
       "original_author_head":AUTHOR_HEAD,
       "original_author_script_git_blob":AUTHOR_SCRIPT_BLOB,
       "router_original_484_git_blob":PINNED_484_ROUTER_BLOB,
       "script_count":COUNT,
       "only_changed_script":"/".join(ROUTER),
       "other_thirty_selected_rc_sources_byte_exact":30,
       "one_original_7_role_combat":True,
       "one_swarm_541_preserved":True,
       "botactor_555_preserved":True,
       "original_489_item_preserved":True,
       "original_castle_lobby_host_preserved":True,
       "full_requested_step_raycast":True,
       "previous_router_source_sha256":sha(raw),
       "selected_router_source_sha256":sha(fixed),
       "source_sha256":{"/".join(k):sha(p.read_bytes()) for k,p in sorted(mapped.items())},
       "flag_off_base":str(base),
       "rollback_byte_exact":True,
       "formal_rc_attested":False,
       "studio_android_owner":"NOT_TESTED",
    }
    (out.parent/"GQ536_RC31_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ536_EXACT_ORIGINAL_AUTHOR_SINGLE_ROUTER_RC31_30_UNCHANGED_PASS")
    return receipt

def verify(base:Path,selected:Path,author_path:Path,place:Path):
    original=load_author(author_path)
    _,before=flat(base)
    _,after=flat(selected)
    if set(before)!=set(after):
        raise ValueError("RED_GQ536_SOURCE_MAP_CHANGED")
    changed=[k for k in before if before[k].read_bytes()!=after[k].read_bytes()]
    if changed!=[ROUTER]:
        raise ValueError("RED_GQ536_NOT_ONE_EXISTING_ROUTER")
    expected=original.overlay(before[ROUTER].read_bytes(),locked=True)
    if after[ROUTER].read_bytes()!=expected or expected.decode().replace(original.AFTER,original.BEFORE,1)!=before[ROUTER].read_text():
        raise ValueError("RED_GQ536_AUTHOR_ROUTE_PATCH_NOT_EXACT")
    actual={}
    for el in ET.fromstring(place.read_bytes()).iter("Item"):
        kind=el.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"):continue
        props=el.find("Properties")
        if props is None:raise ValueError("RED_GQ536_NO_SCRIPT_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in actual:
            raise ValueError("RED_GQ536_PLACE_DUPLICATE_OR_MISSING_SOURCE")
        actual[name]=(kind,source.replace("\r\n","\n"))
    exp={}
    for route,f in after.items():
        kind="Script" if f.name.endswith(".server.luau") else ("LocalScript" if f.name.endswith(".client.luau") else "ModuleScript")
        exp[route[-1]]=(kind,f.read_text(encoding="utf-8").replace("\r\n","\n"))
    if exp!=actual or len(actual)!=COUNT:
        raise ValueError("RED_GQ536_REAL_ROJO_SCRIPT_SOURCE_CLASS_MISMATCH")
    receiptfile=selected.parent/"GQ536_RC31_SOURCE_RECEIPT.json"
    receipt=json.loads(receiptfile.read_text())
    for k,f in after.items():
        if receipt["source_sha256"]["/".join(k)]!=sha(f.read_bytes()):
            raise ValueError("RED_GQ536_SOURCE_CHANGED_POST_COMPOSE "+str(k))
    receipt.update({
        "real_rojo_source_class_exact":"31/31",
        "rojo_place_bytes":place.stat().st_size,
        "rojo_place_sha256":sha(place.read_bytes())
    })
    receiptfile.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ536_REAL_ROJO_ONE_ROUTER_31_31_SOURCE_EXACT_PASS",place.stat().st_size,sha(place.read_bytes()))
    return receipt

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("action",choices=("prepare","verify"))
    cli.add_argument("--base",required=True,type=Path)
    cli.add_argument("--out",required=True,type=Path)
    cli.add_argument("--author",required=True,type=Path)
    cli.add_argument("--place",type=Path)
    a=cli.parse_args()
    if a.action=="prepare":prepare(a.base,a.author,a.out)
    else:
        if a.place is None:cli.error("--place required")
        verify(a.base,a.out,a.author,a.place)
if __name__=="__main__":main()
