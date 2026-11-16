#!/usr/bin/env python3
"""Read-only author-source reconciliation: #533 private29 + #528 budget + #531 host membership.

Source-selective only. Imports original authors' patch functions rather than
reimplementing their features. All output is PRIVATE, never canonical RC.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, os
from pathlib import Path
from compose_triple29 import flatten, digest, ORIGINAL, POLICY

HOST = ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
BOT = ("ServerScriptService","EGGRUMBLE_BotActors")
BUDGET = ("ServerScriptService","EGGRUMBLE_DualModeNeutralBudget")
OWNER528_COMPOSER_BLOB = "2ab5fe9fee8333fe1c8ec6cf811bb5053fccf227"
OWNER531_COMPOSER_BLOB = "7ea28c922debfa25e64a93401a643a9f1babd932"
ORIGINAL_GAME_HEAD="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"

def load_file(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def git_blob(path:Path)->str:
    content=path.read_bytes()
    return hashlib.sha1(f"blob {len(content)}\0".encode()+content).hexdigest()

def once(text:str, before:str, after:str, label:str)->str:
    amount=text.count(before)
    if amount!=1: raise ValueError(f"RED_{label}_ANCHOR {amount} expected1")
    return text.replace(before,after,1)

def compose(base29:Path, author528:Path,author531:Path,policy528:Path,out:Path)->dict:
    base29=base29.resolve(strict=True)
    author528=author528.resolve(strict=True)
    author531=author531.resolve(strict=True)
    policy528=policy528.resolve(strict=True)
    out=out.resolve()
    assert not out.exists() and not (out.parent/"GQ_ADMISSION30_SOURCE_RECEIPT.json").exists()
    assert git_blob(author528)==OWNER528_COMPOSER_BLOB, "RED original #528 source drift"
    assert git_blob(author531)==OWNER531_COMPOSER_BLOB, "RED original #531 source drift"
    a=load_file(author528,"original528")
    b=load_file(author531,"original531")
    assert a.LOCK["author_head"]==b.OWNER_HEAD==ORIGINAL_GAME_HEAD
    assert b.AI_BOT_BLOB=="832a26c9f713012b924234ce4cf8c1654a75654e"
    tree,sources=flatten(base29)
    assert len(sources)==29
    assert all(key in sources for key in (HOST,BOT,ORIGINAL,POLICY))
    assert BUDGET not in sources
    receipt=json.loads((base29.parent/"TRIPLE29_SOURCE_RECEIPT.json").read_text())
    assert receipt["total_count"]==29 and receipt["preserved28_sources_exact"]==27
    assert receipt["status"]=="PRIVATE_SOURCE_ONLY_NOT_OFFICIAL_RC"
    assert not receipt["official_rc_adopted"]
    for key,path in sources.items():
        assert receipt["mapped_sha256"]["/".join(key)]==digest(path),(key,"RED source drift")
    assert git_blob(sources[BOT])==b.AI_BOT_BLOB, "RED #484 real bot duel not preserved"
    host=sources[HOST].read_text(encoding="utf-8")
    bot=sources[BOT].read_text(encoding="utf-8")
    swarm=sources[ORIGINAL].read_text(encoding="utf-8")
    # Original #531 author function: one HOST callback and existing BOT hit guard.
    fenced_host,fenced_bot=b.compose(host,bot)
    assert "session.isCurrentHuman=function" in fenced_host
    assert fenced_bot.count("session.isCurrentHuman(player)")==1
    for must in ("for targetId,targetActor in pairs(bots)","targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)",
                 "tryHeroAttack(actor,me,session,lastHit,bots)"):
        assert must in fenced_bot,("RED bot AI duel lost",must)
    # Original #528 author: shared same-server TEAM+BR capacity, no new Swarm loop.
    bounded_host=a.patch_host(fenced_host)
    bounded_swarm=a.patch_swarm(swarm)
    # In #501 fair-target enumeration, an old castle record is NOT proof that
    # the human still belongs to this session. Reuse #531 host callback verbatim.
    bounded_swarm=once(
        bounded_swarm,
        'if root and hum and hum.Health>0 then',
        'if root and hum and hum.Health>0 and session.isCurrentHuman~=nil and session.isCurrentHuman(p) then',
        "neutral_spawn_human_membership"
    )
    # Same authoritative host callback for #533 melee hit victim eligibility.
    bounded_swarm=once(
        bounded_swarm,
        'p:GetAttribute("EGGRUMBLE_QueuedMode")==session.mode',
        'session.isCurrentHuman~=nil and session.isCurrentHuman(p)',
        "neutral_melee_human_membership"
    )
    assert bounded_swarm.count("session.isCurrentHuman(p)")==2
    for tok in ('SpawnPacing.step(','EncounterFair.chooseIndex(','nearest.humanoid:TakeDamage(Melee.DAMAGE)',
                'local function credit(','h.Died:Connect(','ImpactFeedback.ko(',
                'session.neutralBudget:acquire(','session.neutralBudget:release('):
        assert bounded_swarm.count(tok)==1 or (
            tok=='session.neutralBudget:release(' and bounded_swarm.count(tok)>=2
        ),("RED one Swarm authority",tok,bounded_swarm.count(tok))
    assert bounded_swarm.count('lastMeleeSwing[m]=nil')==1
    assert bounded_swarm.count('setmetatable({}, {__mode="k"}) :: any')==2
    assert 'local SPAWN_BATCH=5' not in bounded_swarm
    assert bounded_host.count("session.isCurrentHuman=function")==1
    assert bounded_host.count("gqDualBudget=GQDualBudget.new(")==1
    assert bounded_host.count("session.neutralBudgetEpoch=gqDualBudget:begin(mode)")==1
    assert bounded_host.count("gqDualBudget:retire(mode,session.neutralBudgetEpoch)")==1
    assert fenced_bot.count("for targetId,targetActor in pairs(bots)")==1
    assert fenced_bot.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)")==1
    project=copy.deepcopy(tree)
    project["name"]="GQ_V3_NONAUTHOR_494_501_528_531_533_PRIVATE30"
    def remap(node,prefix=()):
        for k,v in node.items():
            if k.startswith("$"):continue
            key=prefix+(k,)
            if "$path" in v:
                assert key in sources
                v["$path"]=os.path.relpath(sources[key],out.parent).replace(os.sep,"/")
            else:remap(v,key)
    remap(project["tree"])
    changes={HOST:(bounded_host,"EGGRUMBLE_LobbyCastleModesPreview.server.luau"),
             BOT:(fenced_bot,"EGGRUMBLE_BotActors.luau"),
             ORIGINAL:(bounded_swarm,"EGGRUMBLE_SwarmCombat.luau")}
    for key,(content,name) in changes.items():
        path=out.parent/("ADMISSION30_"+name)
        assert not path.exists(),("RED overwrite",name)
        path.write_text(content,encoding="utf-8")
        project["tree"]["ServerScriptService"][key[-1]]={"$path":path.name}
    project["tree"]["ServerScriptService"][BUDGET[-1]]={
        "$path":os.path.relpath(policy528,out.parent).replace(os.sep,"/")
    }
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,mapped=flatten(out)
    assert len(mapped)==30 and set(mapped)==set(sources)|{BUDGET}
    assert len(set(k[-1] for k in mapped))==len(mapped)
    for key in set(sources)-set(changes):
        assert mapped[key].read_bytes()==sources[key].read_bytes(),("RED nonowner drift",key)
    assert mapped[BUDGET].read_bytes()==policy528.read_bytes()
    assert sum(k[0]=="ServerScriptService" for k in mapped)==27
    assert sum(k[0]=="StarterPlayer" for k in mapped)==3
    receipt_out={
        "feature":"GQ-V3-SOURCE-ADMISSION30-20261116",
        "status":"SOURCE_PRIVATE_ONLY_NOT_RC",
        "base29_receipt_sha256":digest(base29.parent/"TRIPLE29_SOURCE_RECEIPT.json"),
        "original_author_heads":{"game482":ORIGINAL_GAME_HEAD,
          "budget528":"6b29c50b6cc0b25192a121b2957497ede8b07f37",
          "membership531":"e78bff41e70564d0b26578e3c3a85f4698e6110e"},
        "source_count":30,"previous_source_count":29,
        "previous_byte_exact_count":26,"original_source_selective_overlays":[k[-1] for k in changes],
        "new_modules":[BUDGET[-1]],"server_count":27,"client_count":3,
        "mapped_sha256":{"/".join(k):digest(v) for k,v in sorted(mapped.items())},
        "rc_adopted":False,"claim_granted":False,"original_author_ack":False,
        "studio_tested":False,"android_tested":False,"owner_accepted":False,
        "rollback":"exclude #528/#531 and #533 three overlays and budget; restore exact #533 private29"
    }
    (out.parent/"GQ_ADMISSION30_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt_out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ30_AUTHOR_ORIGINAL_528_531_SINGLE_SWARM_30_PASS")
    return receipt_out

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for name in ("base29","author528","author531","policy528","out"):
        parser.add_argument("--"+name,required=True,type=Path)
    a=parser.parse_args()
    compose(a.base29,a.author528,a.author531,a.policy528,a.out)
