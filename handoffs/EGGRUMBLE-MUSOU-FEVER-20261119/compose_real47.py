#!/usr/bin/env python3
"""#824: exact #815 Real44 -> Real47 private source-selected integration.

Modify only original singleton Swarm and SevenRoleCombat, add three modules,
and NEVER create a second HP/KO/score or player Remote authority. Without actual
Real44 source/artifact this script fails closed rather than simulating gameplay.
"""
from pathlib import Path
import argparse,copy,hashlib,json,os,re,shutil

SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
POLICY=("ServerScriptService","EGGRUMBLE_MusouFeverPolicy")
VFX=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_MusouAuraClient")
OBSERVER=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_MusouAuraController")
NEW=(POLICY,VFX,OBSERVER)
FEATURE="GQ8_MUSOU_FEVER_CHAIN_20261119"

def sha256(x:bytes):return hashlib.sha256(x).hexdigest()
def flatten(path:Path):
 p=path.resolve(strict=True)
 doc=json.loads(p.read_text(encoding="utf8"))
 found={}
 def visit(node,route=()):
  for key,item in node.items():
   if key.startswith("$"):continue
   k=route+(key,)
   if "$path" in item:
    if k in found:raise ValueError("RED_DUPLICATE_SOURCE_ROUTE")
    f=(p.parent/item["$path"]).resolve(strict=True)
    if not f.is_file():raise ValueError("RED_MISSING_AUTHOR_SOURCE_"+"/".join(k))
    found[k]=f
   else:visit(item,k)
 visit(doc["tree"])
 return doc,found

def only(src:str,old:str,new:str,why:str):
 n=src.count(old)
 if n!=1:raise ValueError("RED_ANCHOR_"+why+"_"+str(n))
 return src.replace(old,new,1)

SERVER_MUSOU=r'''
 local musouRound=Musou.newRound(tostring(session.world),os.clock())
 local musouNotices:{[string]:number}={}
 local function musouContext(user:Player,now:number)
  local uid=tostring(user.UserId)
  local castle=session.rules.castles[uid]
  local ch=user.Character
  local hum=ch and ch:FindFirstChildOfClass("Humanoid")
  local realMember=false
  if type(session.isCurrentHuman)=="function" then
   local ok,accepted=pcall(session.isCurrentHuman,user)
   realMember=ok and accepted==true
  end
  -- Cargo is read from the one server CastleMatchRules owner, never client HUD.
  local carry=castle~=nil and type(castle.heldEggs)=="number" and castle.heldEggs>0
  local shield=ch~=nil and ch:FindFirstChildOfClass("ForceField")~=nil
  -- Future #823 invul bridge must supply its server-owned Boolean before adoption;
  -- current Core44 does not yet provide a live invulnerability state.
  local invul=ch~=nil and ch:GetAttribute("EGGRUMBLE_ServerInvulnerable")==true
  local ctx={
   epoch=tostring(session.world),playerId=uid,avatarEpoch=tostring(ch),
   now=now,mode=session.mode,phase=session.rules.phase,
   serverCurrent=realMember,roleVerified=user:GetAttribute("EGGRUMBLE_Role")~=nil,
   role=user:GetAttribute("EGGRUMBLE_Role"),characterAlive=hum~=nil and hum.Health>0,
   castleAlive=castle~=nil and castle.alive==true,
   downed=ch~=nil and ch:GetAttribute("EGGRUMBLE_Downed")==true,
   eliminated=user:GetAttribute("EGGRUMBLE_Eliminated")==true,
   carryingEgg=carry,shieldActive=shield,invulnerable=invul,
  }
  if carry or shield or invul or not ctx.characterAlive or not ctx.castleAlive
     or ctx.downed or ctx.eliminated or session.rules.phase~="ACTIVE" then
   Musou.cancel(musouRound,ctx)
  end
  return ctx
 end
 local function musouReflect(user:Player)
  local uid=tostring(user.UserId)
  local ctx=musouContext(user,os.clock())
  local snap=Musou.snapshot(musouRound,ctx)
  local phase=if snap.active then snap.phase else "OFF"
  user:SetAttribute("EGGRUMBLE_MusouPhase",phase)
  user:SetAttribute("EGGRUMBLE_MusouRole",ctx.role)
  user:SetAttribute("EGGRUMBLE_MusouRemaining",if snap.active then snap.remaining else 0)
  user:SetAttribute("EGGRUMBLE_MusouReadyIn",snap.readyIn)
  if snap.active then
   local count=(musouNotices[uid] or 0)+1
   musouNotices[uid]=count
   -- One bounded expiry task per phase/real KO; stale tasks are invalidated.
   task.delay(math.min(20.1,math.max(.05,snap.remaining+.04)),function()
    if musouNotices[uid]==count and session.rules.phase=="ACTIVE" then
     musouReflect(user)
    end
   end)
  end
 end
'''
# Luau's local-function declaration already supports recursion; keep it intact.

def patch_swarm(s):
 s=only(s,
 'local NeutralFinisherPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralFinisherPolicy"))',
 'local NeutralFinisherPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralFinisherPolicy"))\nlocal Musou=require(script.Parent:WaitForChild("EGGRUMBLE_MusouFeverPolicy"))',
 "ONE_SERVER_MODULE")
 s=only(s,' local curseEpoch=tostring(session.world)',
   ' local curseEpoch=tostring(session.world)\n'+SERVER_MUSOU.rstrip("\n"),"MATCH_SCOPED_MUSOU")
 match=re.findall(r"(?m)^([ ]*)releaseCharmed\(m\)[ ]*$",s)
 if len(match)!=1:raise ValueError("RED_EXPECT_ONE_DEATH_CLEANUP")
 indent=match[0]
 s=only(s,indent+"releaseCharmed(m)",
  indent+"local wasCharmed=charmedByModel[m]~=nil\n"+indent+"releaseCharmed(m)",
  "ONE_DEATH_CONVERSION_FENCE")
 credit_matches=re.findall(r"(?m)^([ \t]*)credit\(id\)[ \t]*$",s)
 if len(credit_matches)!=1:raise ValueError("RED_KO_CREDIT_ANCHOR_"+str(len(credit_matches)))
 credit_indent=credit_matches[0]
 s=only(s,credit_indent+"credit(id)","""     credit(id)
     -- The genuine existing KoFence just accepted this single death and score.
     -- No synthetic KO or duplicate scoring; the neutralId is session-unique.
     if attacker and not wasCharmed then
      local context=musouContext(attacker,os.clock())
      local ok=Musou.onConfirmedKO(musouRound,context,{
       serverConfirmed=true,enemyConfirmed=true,creditVerified=true,
       scoreEligible=true,creditedPlayerId=id,
       victimId=neutralId,receiptId=curseEpoch..":"..neutralId,
       targetKind="NEUTRAL",isSummoned=false,isConverted=false,
      })
      if ok then musouReflect(attacker) end
     end""".replace("     credit(id)",credit_indent+"credit(id)",1),"KO_FENCE_AFTER_CREDIT")
 s=only(s,
  'return strike(tostring(player.UserId),at,radius,damage*bonus,',
  'local power=Musou.attackMultiplier(musouRound,musouContext(player,os.clock()),"NEUTRAL")\n   return strike(tostring(player.UserId),at,radius,damage*bonus*power,',
  "SINGLE_SWARM_PLAYER_DAMAGE")
 s=only(s,' local api={\n',''' local api={
  activateMusou=function(user:Player)
   local ctx=musouContext(user,os.clock())
   local ok,decision=Musou.activate(musouRound,ctx)
   musouReflect(user)
   return ok,decision
  end,
  musouMultiplier=function(user:Player,kind:string)
   return Musou.attackMultiplier(musouRound,musouContext(user,os.clock()),kind)
  end,
  musouActive=function(user:Player):boolean
   local snap=Musou.snapshot(musouRound,musouContext(user,os.clock()))
   return snap.active==true
  end,
''',"EXISTING_SWARM_API_ONLY")
 if s.count("function Swarm.start(session:any)")!=1 or s.count("h:TakeDamage(effectiveDamage)")!=1 or s.count("KoFence.mayCredit(")<1 or s.count("credit(id)")!=1:
  raise ValueError("RED_EXISTING_SINGLE_SWARM_DAMAGE_KO_FENCE_LOST")
 for t in ["neutralBudget:acquire","SpawnPacing.step","EncounterFair","CurseConversionPolicy.seal(","NeutralFinisherPolicy.select("]:
  if t not in s: raise ValueError("RED_LOST_REAL44_"+t)
 return s

def patch_combat(s):
 s=only(s,
  'enemyHum:TakeDamage(damage*duel*mark)',
  'local musou=if session.swarm and session.swarm.musouMultiplier then session.swarm.musouMultiplier(p,"HUMAN") else 1\n    enemyHum:TakeDamage(damage*duel*mark*musou)',
  "PVP_SINGLE_EXISTING_DAMAGE")
 s=only(s,
  'boss.damageFrom(p,math.min(100,amount*boost),true)',
  'boss.damageFrom(p,math.min(100,amount*boost*(if session.swarm and session.swarm.musouMultiplier then session.swarm.musouMultiplier(p,"BOSS") else 1)),true)',
  "BOSS_EXISTING_OWNER")
 s=only(s,
  'if instance:IsA("Tool") and string.sub(instance.Name,1,16)=="EGGRUMBLE_SKILL_" then instance:Destroy() end',
  'if instance:IsA("Tool") and (string.sub(instance.Name,1,16)=="EGGRUMBLE_SKILL_" or instance.Name=="EGGRUMBLE_MUSOU_AWAKEN") then instance:Destroy() end',
  "EQUIP_REPLACES_OLD_TOOLS")
 s=only(s,
  'if item:IsA("Tool") and string.sub(item.Name,1,16)=="EGGRUMBLE_SKILL_" then item:Destroy() end',
  'if item:IsA("Tool") and (string.sub(item.Name,1,16)=="EGGRUMBLE_SKILL_" or item.Name=="EGGRUMBLE_MUSOU_AWAKEN") then item:Destroy() end',
  "ROUND_CLEAR_TOOLS")
 marker="function HeroCombat.clear(p:Player)"
 if s.count(marker)!=1:raise ValueError("RED_CURRENT_CLEAR_ANCHOR")
 idx=s.index(marker)
 prefix=s[:idx]
 # The immediately preceding top-level "end" is the original equip() terminator.
 close=re.search(r"\nend[ \t]*\n[ \t]*$",prefix)
 if not close:raise ValueError("RED_CURRENT_EQUIP_CLOSURE")
 addon=r''' -- Real server-side Tool.Activated: no client Remote or damage parameter.
 -- This is a fourth selectable ability, distinct from the defensive #823 skill.
 local musouTool=Instance.new("Tool")
 musouTool.Name="EGGRUMBLE_MUSOU_AWAKEN"
 musouTool.ToolTip="無双覚醒｜大群連撃で連チャン・確変｜時間で回復"
 musouTool.RequiresHandle=false
 musouTool.CanBeDropped=false
 musouTool.Activated:Connect(function()
  if musouTool.Parent~=p.Character or not currentHumanMember(session,p) then return end
  if p:GetAttribute("EGGRUMBLE_Role")~=role then return end
  if session.swarm and session.swarm.activateMusou then
   session.swarm.activateMusou(p)
  end
 end)
 musouTool.Parent=backpack'''
 s=prefix[:close.start()]+"\n"+addon+prefix[close.start():]+s[idx:]
 for t in ["function HeroCombat.equip(", "function HeroCombat.clear(", "neutralAndBotHit(", "ImpactFeedback.hit(", "session.swarm.damageFromPlayer("]:
  if t not in s:raise ValueError("RED_EXISTING_COMBAT_LOST_"+t)
 if s.count("enemyHum:TakeDamage(")!=1:raise ValueError("RED_DOUBLE_PVP_DAMAGE")
 return s

def compose(src:Path,policy:Path,aura:Path,controller:Path,out:Path,receipt_path:Path):
 doc,orig=flatten(src)
 if len(orig)!=44 or not {SWARM,COMBAT}.issubset(orig) or set(NEW)&set(orig):
  raise ValueError("RED_BASE_MUST_BE_ACTUAL_REAL44")
 if any(not v.read_bytes() for v in orig.values()):raise ValueError("RED_EMPTY_AUTHOR")
 out.parent.mkdir(parents=True,exist_ok=True)
 dest=out.parent/"musou_overlay_sources"
 dest.mkdir(exist_ok=True)
 selected={
  SWARM:patch_swarm(orig[SWARM].read_text(encoding="utf8")),
  COMBAT:patch_combat(orig[COMBAT].read_text(encoding="utf8")),
  POLICY:policy.read_text(encoding="utf8"),
  VFX:aura.read_text(encoding="utf8"),
  OBSERVER:controller.read_text(encoding="utf8"),
 }
 for r,body in selected.items():
  ext=".client.luau" if r==OBSERVER else ".luau"
  target=dest/(r[-1]+ext)
  target.write_text(body,encoding="utf8",newline="\n")
  selected[r]=target
 next_doc=copy.deepcopy(doc)
 def relink(node,route=()):
  for key,item in node.items():
   if key.startswith("$"):continue
   k=route+(key,)
   if "$path" in item:
    chosen=selected.get(k,orig[k])
    item["$path"]=os.path.relpath(chosen,out.parent).replace(os.sep,"/")
   else:relink(item,k)
 relink(next_doc["tree"])
 next_doc["tree"]["ServerScriptService"][POLICY[-1]]={"$path":os.path.relpath(selected[POLICY],out.parent).replace(os.sep,"/")}
 scripts=next_doc["tree"]["StarterPlayer"]["StarterPlayerScripts"]
 for route in (VFX,OBSERVER):
  scripts[route[-1]]={"$path":os.path.relpath(selected[route],out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(next_doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 _,built=flatten(out)
 if len(built)!=47 or set(built)!=(set(orig)|set(NEW)):
  raise ValueError("RED_SELECTED_NOT_47_UNIQUE")
 for k,p in orig.items():
  if k not in (SWARM,COMBAT) and built[k].read_bytes()!=p.read_bytes():
   raise ValueError("RED_EXISTING_AUTHOR_BYTES_MODIFIED_"+"/".join(k))
 for p in (policy,aura,controller):
  if not p.read_bytes():raise ValueError("RED_MISSING_NEW_MODULE")
 receipt={
  "feature_id":FEATURE,"official_rc_adopted":False,
  "base_source_count":44,"selected_source_count":47,
  "modified_original":["/".join(SWARM),"/".join(COMBAT)],
  "unchanged_existing":42,
  "new_routes":["/".join(x) for x in NEW],
  "base_project_sha256":sha256(src.read_bytes()),
  "reversible_off44":"exact original project/source unchanged",
  "selected_sources":[{"route":"/".join(k),"sha256":sha256(v.read_bytes()),"bytes":v.stat().st_size,
   "origin":"new_module" if k in NEW else "modified_single_owner" if k in (SWARM,COMBAT) else "unchanged_real44"}
   for k,v in sorted(built.items())],
  "studio_2client":"NOT_TESTED","android15":"NOT_TESTED",
 }
 receipt_path.parent.mkdir(parents=True,exist_ok=True)
 receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("GQ8_REAL47_ACTUAL_SINGLE_OWNER_SOURCE_SELECTED",len(built),"EXACT_OFF44",len(orig))
 return built,orig

if __name__=="__main__":
 pa=argparse.ArgumentParser()
 pa.add_argument("--real44",type=Path,required=True)
 pa.add_argument("--policy",type=Path,required=True)
 pa.add_argument("--aura",type=Path,required=True)
 pa.add_argument("--controller",type=Path,required=True)
 pa.add_argument("--out",type=Path,required=True)
 pa.add_argument("--receipt",type=Path,required=True)
 a=pa.parse_args()
 compose(a.real44,a.policy,a.aura,a.controller,a.out,a.receipt)
