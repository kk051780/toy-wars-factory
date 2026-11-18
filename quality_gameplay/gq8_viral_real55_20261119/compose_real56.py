#!/usr/bin/env python3
"""GQ8 Real55 -> Real56: single preexisting V3 Host remains sole round/egg/castle owner.
Patches only factual *notification after* host-authorized state mutation.
No new ServerScript, RemoteEvent, trading, HP, damage or Store authority.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys, re
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten, klass

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
CLIENT=("StarterPlayer","StarterPlayerScripts","GQ8_ViralCapture")
FEATURE="GQ8_VIRAL_REAL56_20261119"

def exact(src, before, after, label):
    count=src.count(before)
    if count!=1: raise ValueError("RED_"+label+"_COUNT_"+str(count))
    return src.replace(before,after,1)

def regex_exact(src, pattern, replacement, label):
    amended,count=re.subn(pattern,replacement,src)
    if count!=1:raise ValueError("RED_"+label+"_COUNT_"+str(count))
    return amended

def patch_host(src):
    src=exact(src,"local function startSession(mode:string)",'''-- No extra gameplay owner: only this existing HOST emits factual capture hints.
local gq8ViralEpoch=0
local function gq8CaptureHint(player:Player,session:any,kind:string)
 if player.Parent~=Players then return end
 if session.rules.phase~="ACTIVE" and kind~="VICTORY" and kind~="COMEBACK" then return end
 local seq=player:GetAttribute("EGGRUMBLE_ViralSeq")
 if type(seq)~="number" or seq<0 or seq>100000000 then seq=0 end
 player:SetAttribute("EGGRUMBLE_ViralKind",kind)
 player:SetAttribute("EGGRUMBLE_ViralEpoch",session.gq8ViralEpoch)
 player:SetAttribute("EGGRUMBLE_ViralSeq",seq+1)
end

local function startSession(mode:string)''',"HOST_START")
    src=exact(src,'session.world.Name=mode.."_Arena";session.world.Parent=folder',
'''gq8ViralEpoch+=1
 session.gq8ViralEpoch=gq8ViralEpoch
 session.gq8ViralDanger={}
 session.gq8ViralResults=false
 session.world.Name=mode.."_Arena";session.world.Parent=folder''',"SESSION_EPOCH")
    src=regex_exact(src,
        r"if c\.alive and c\.heldEggs>0 then\n[ \t]+local ok=pcall\(function\(\) Rules\.depositEggs\(session\.rules,entry\.id,c\.heldEggs\) end\)\n[ \t]+if ok then session\.refresh\(\) end\n[ \t]+end",
        '''if c.alive and c.heldEggs>0 then
    local before=c.depositedEggs or 0
    local ok=pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end)
    if ok then
     if (c.depositedEggs or 0)>before then
      gq8CaptureHint(p,session,"EGG_DELIVER")
     end
     session.refresh()
    end
   end''',"EGG_DELIVER_EXACT_COMMIT")
    src=regex_exact(src,
        r"pcall\(function\(\) Rules\.takeEggs\(session\.rules,tostring\(p\.UserId\),1,entry\.id\) end\)\n[ \t]+session\.refresh\(\)",
'''local taker=session.rules.castles[tostring(p.UserId)]
   local before=taker and taker.heldEggs or 0
   local ok=pcall(function() Rules.takeEggs(session.rules,tostring(p.UserId),1,entry.id) end)
   if ok and taker and (taker.heldEggs or 0)>before then
    gq8CaptureHint(p,session,"EGG_STEAL")
   end
   session.refresh()''',"EGG_STEAL_EXACT_COMMIT")
    src=regex_exact(src,
        r"local c=session\.rules\.castles\[tostring\(player\.UserId\)\]\n[ \t]+if c and not c\.alive",
'''local c=session.rules.castles[tostring(player.UserId)]
     if c and c.alive and c.hp<=Rules.CASTLE_HP*.22
       and not session.gq8ViralDanger[player.UserId] then
      session.gq8ViralDanger[player.UserId]=true
      gq8CaptureHint(player,session,"CASTLE_DANGER")
     end
     if c and not c.alive''',"CASTLE_DANGER_ONLY_AUTHORIZED_STATE")
    src=regex_exact(src,
        r"if session\.rules\.winner~=nil then\n[ \t]+-- Short factual result shown exactly once",
'''if session.rules.winner~=nil then
    if not session.gq8ViralResults then
     session.gq8ViralResults=true
     for _,winnerPlayer in ipairs(queue) do
      if winnerPlayer.Parent==Players and joined[winnerPlayer.UserId]==mode then
       local id=tostring(winnerPlayer.UserId)
       local ownCastle=session.rules.castles[id]
       if ownCastle then
        local won=if mode=="TEAM" then session.rules.winner==ownCastle.team
         else session.rules.winner==id
        if won then
         local kind=if session.gq8ViralDanger[winnerPlayer.UserId] then "COMEBACK" else "VICTORY"
         gq8CaptureHint(winnerPlayer,session,kind)
        end
       end
      end
     end
    end
    -- Short factual result shown exactly once''',"TRUE_WINNER_ONLY")
    return src

def compose(parent55:Path, receipt55:Path, client:Path, out:Path):
    if out.exists():raise ValueError("RED_NO_OVERWRITE")
    original,old=flatten(parent55)
    assert len(old)==55 and HOST in old and CLIENT not in old,"RED_NOT_REAL55_PARENT"
    report=json.loads(receipt55.read_text(encoding="utf8"))
    assert report.get("selected_real55_count")==55 or report.get("selected_script_count")==55, "RED_RECEIPT_REAL55"
    expected={tuple(x["route"].split("/")):x for x in report["sources"]}
    assert set(old)==set(expected),"RED_PARENT_RECEIPT_ROUTES"
    for route,file in old.items():
        b=file.read_bytes();m=expected[route]
        assert hashlib.sha256(b).hexdigest()==m["sha256"] and len(b)==m["bytes"],"RED_PARENT_BYTES_"+"/".join(route)
    oldhost=old[HOST].read_text(encoding="utf8")
    host=patch_host(oldhost).encode("utf8")
    assert host!=old[HOST].read_bytes() and b"TakeDamage(" not in host[len(oldhost.encode("utf8")):],"RED_HOST_PATCH_NOT_PRESENT"
    child=client.read_bytes()
    assert b'EGGRUMBLE_ViralSeq' in child and b'FireServer(' not in child,"RED_BAD_CHILD"
    out.mkdir(parents=True)
    doc=copy.deepcopy(original)
    doc["name"]="GQ8_REAL56_VIRAL_TRUE_SERVER_EVENTS_CLIENT_CAPTURE_PRIVATE_ONLY"
    ledger=[]
    def put(route:tuple[str,...], b:bytes, suffix:str, owner:str):
        f=out.joinpath("sources",*route[:-1],route[-1]+suffix)
        f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        node=doc["tree"]
        for depth,name in enumerate(route[:-1]):
            if name not in node:node[name]={} if depth==0 else {"$className":"Folder"}
            node=node[name]
        node[route[-1]]={"$path":f.relative_to(out).as_posix()}
        ledger.append({"route":"/".join(route),"class":klass(f),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"origin":owner})
    for route,file in sorted(old.items()):
        cls=klass(file)
        suffix=".server.luau" if cls=="Script" else ".client.luau" if cls=="LocalScript" else ".luau"
        b=host if route==HOST else file.read_bytes()
        put(route,b,suffix,"one_host_notification_patch" if route==HOST else "exact_parent55")
    put(CLIENT,child,".client.luau","optional_client_first_party_capture")
    project=out/"EGGRUMBLE_REAL56.project.json"
    project.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    _,after=flatten(project)
    assert len(after)==56 and set(after)==set(old)|{CLIENT},"RED_REAL56_WIRING"
    for route,file in old.items():
        if route!=HOST: assert after[route].read_bytes()==file.read_bytes(),"RED_ORIGINAL_PRESERVATION_"+"/".join(route)
    assert klass(after[HOST])=="Script" and klass(after[CLIENT])=="LocalScript"
    result={"feature_id":FEATURE,"parent":55,"candidate":56,"modified_old_source":["/".join(HOST)],
        "unchanged_original_source_count":54,"new_client_source":["/".join(CLIENT)],
        "new_remote_owners":0,"new_store_owners":0,"publish_enabled":False,"filming_default_off":True,
        "private_studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NOT_TESTED",
        "rollback":"reselect exact immutable official Real55 original project",
        "sources":ledger}
    (out/"GQ8_VIRAL56_RECEIPT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ8_VIRAL56_ONE_HOST_ONLY_TRUE_EVENTS_54_PRESERVED_SOURCE_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent55",type=Path,required=True)
    p.add_argument("--receipt55",type=Path,required=True)
    p.add_argument("--client",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    compose(a.parent55,a.receipt55,a.client,a.out)
