#!/usr/bin/env python3
"""GQ800: real, bounded curse conversion inside the ONE original neutral Swarm.
Source-select verified #815 Real43, original #801 policy, and patch Swarm only.
No independent spawner/Remote/Store/Game/score/HP authority, official write or publish.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re
from pathlib import Path

SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
CURSE=("ServerScriptService","EGGRUMBLE_CurseConversionPolicy")
POLICY_BLOB="0bd81a807ff6a935642a660b9fe9e0fd05ef484c"

def git_blob(data:bytes)->str:
    return hashlib.sha1(("blob %d"%len(data)).encode()+b"\0"+data).hexdigest()

def flatten(project:Path):
    project=Path(project).resolve(strict=True)
    doc=json.loads(project.read_text())
    files={}
    def walk(node,route=()):
        for name,value in node.items():
            if name.startswith("$"):continue
            key=route+(name,)
            if "$path" in value:
                if key in files:raise ValueError("RED_DUPLICATE_ROUTE")
                files[key]=(project.parent/value["$path"]).resolve(strict=True)
            else:walk(value,key)
    walk(doc["tree"])
    return doc,files

def replace_once(source:str,old:str,new:str,label:str)->str:
    n=source.count(old)
    if n!=1:raise ValueError(f"RED_{label}_ANCHOR_COUNT_{n}")
    return source.replace(old,new,1)

HELPERS=r'''
  -- All charm receipts are issued inside the original server-confirmed Swarm hit loop.
  -- One charm slot per owner is conservative: existing ZOMBIE may already summon 3.
  -- Do not allow clients to set a new trust-bearing Remote or owner attribution.
  local function releaseCharm(model:Model)
    local info=charmed[model]
    if not info then return end
    charmed[model]=nil
    model:SetAttribute("EGGRUMBLE_CharmedOwnerId",nil)
    model:SetAttribute("EGGRUMBLE_CurseSigil",nil)
    local accent=model:FindFirstChild("SpeciesAccent")
    if accent and accent:IsA("BasePart") then
      accent.Color=info.originalColor
    end
    local state=curseStates[info.ownerId]
    if state then state.members[info.targetId]=nil;state.stacks[info.targetId]=nil end
  end
  local function expireCharms()
    local now=os.clock()
    for model,info in pairs(charmed) do
      local p=Players:GetPlayerByUserId(tonumber(info.ownerId) or -1)
      local char=p and p.Character
      local h=char and char:FindFirstChildOfClass("Humanoid")
      local castle=session.rules.castles[info.ownerId]
      if not model.Parent or now>=info.expires or not h or h.Health<=0
          or not castle or not castle.alive or session.rules.phase~="ACTIVE"
          or (p and p:GetAttribute("EGGRUMBLE_Role")~="ZOMBIE") then
        releaseCharm(model)
      end
    end
  end
  local function charmOwnerPosition(model:Model):Vector3?
    local info=charmed[model]
    if not info then return nil end
    local p=Players:GetPlayerByUserId(tonumber(info.ownerId) or -1)
    local c=p and p.Character
    local root=c and c:FindFirstChild("HumanoidRootPart")
    if root and root:IsA("BasePart") then return root.Position end
    return nil
  end
  local function applyCurseOnVerifiedHit(user:Player?,model:Model,h:Humanoid,receipt:number,origin:Vector3,role:string)
    if not user or role~="ZOMBIE" or h.Health<=0 or not model.PrimaryPart then return end
    local ownerId=tostring(user.UserId)
    local castle=session.rules.castles[ownerId]
    local char=user.Character
    local userHumanoid=char and char:FindFirstChildOfClass("Humanoid")
    local root=char and char:FindFirstChild("HumanoidRootPart")
    if not castle or not castle.alive or not userHumanoid or userHumanoid.Health<=0
       or not root or not root:IsA("BasePart") or session.rules.phase~="ACTIVE" then return end
    local targetId=model:GetAttribute("EGGRUMBLE_NeutralUID")
    if type(targetId)~="string" then return end
    local state=curseStates[ownerId]
    if not state or not state.active then
      state=CurseConversionPolicy.new(tostring(session),ownerId)
      curseStates[ownerId]=state
    end
    local action=CurseConversionPolicy.seal(state,os.clock(),{
      serverConfirmedHit=true,role=role,epoch=tostring(session),ownerId=ownerId,
      phase=session.rules.phase,ownerAlive=true,avatarCurrent=true,
      targetKind="NEUTRAL",targetAlive=h.Health>0,targetFriendly=charmed[model]~=nil,
      isBoss=false,isPlayer=false,sameTeam=false,inLineOfSight=true,
      distance=(model.PrimaryPart.Position-origin).Magnitude,
      targetId=targetId,species=model:GetAttribute("EGGRUMBLE_NeutralSpecies"),
      hpFraction=h.Health/math.max(h.MaxHealth,1),
      uniqueHitId="verified-"..tostring(receipt),
      -- Guaranteed conservative upper bound, until a trusted summon counter is wired.
      -- This prevents original 3 summons + converted neutrals exceeding the shared 4 budget.
      existingSummoned=3,
    })
    if not action then return end
    if action.kind=="SEAL" then
      model:SetAttribute("EGGRUMBLE_CurseSigil",action.stacks)
    elseif action.kind=="CHARM" then
      local accent=model:FindFirstChild("SpeciesAccent")
      local previous=if accent and accent:IsA("BasePart") then accent.Color else Color3.new(1,1,1)
      charmed[model]={ownerId=ownerId,targetId=targetId,
        expires=action.expires,originalColor=previous}
      model:SetAttribute("EGGRUMBLE_CharmedOwnerId",ownerId)
      model:SetAttribute("EGGRUMBLE_CurseSigil",nil)
      if accent and accent:IsA("BasePart") then accent.Color=Color3.fromRGB(92,235,164) end
    end
  end
  local function charmedNeutralAttack(model:Model)
    local info=charmed[model]
    if not info or not model.PrimaryPart then return end
    local now=os.clock()
    if now-(lastCharmAttack[model] or -100)<1.3 then return end
    local origin=model.PrimaryPart.Position
    local nearest=nil
    local best=7
    for victim,h in pairs(live) do
      if victim~=model and not charmed[victim] and victim.Parent and h.Health>0
         and victim.PrimaryPart then
        local d=(victim.PrimaryPart.Position-origin).Magnitude
        if d<best and lineOfSightToNeutral(origin,model,victim) then
          nearest=h;best=d
        end
      end
    end
    if nearest then
      lastCharmAttack[model]=now
      nearest:SetAttribute("LastAttackerId",info.ownerId)
      nearest:TakeDamage(6) -- same existing Swarm HP authority, never human/castle damage
    end
  end
'''
def patch_swarm(source:str)->str:
    if "GQ800_CurseConversionPolicy" in source or "EGGRUMBLE_CurseConversionPolicy" in source:
        raise ValueError("RED_CHARM_ALREADY_INTEGRATED_REBASE")
    if "function Swarm.start(session:any)" not in source or source.count("NeutralFinisherPolicy.select(")!=1:
        raise ValueError("RED_NOT_VERIFIED_SINGLE_SWARM")
    source=replace_once(source,
        'local NeutralFinisherPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralFinisherPolicy"))',
        'local NeutralFinisherPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralFinisherPolicy"))\nlocal CurseConversionPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_CurseConversionPolicy"))',
        "POLICY_REQUIRE")
    source=replace_once(source,
        'm:SetAttribute("EGGRUMBLE_NeutralSpecies",speciesId)',
        'm:SetAttribute("EGGRUMBLE_NeutralSpecies",speciesId)\n m:SetAttribute("EGGRUMBLE_NeutralUID",tostring(serial))',
        "SERVER_UID")
    source=replace_once(source,
        "local hitSerial=0",
        "local hitSerial=0\n  local charmed:{}={}\n  local curseStates:{}={}\n  local lastCharmAttack:{}={}",
        "CHARM_MEMORY")
    source=replace_once(source,
        "local function strike(id:string,",
        HELPERS+"\n  local function strike(id:string,",
        "HELPERS")
    source=replace_once(source,
        'local role=user and (user:GetAttribute("EGGRUMBLE_Role") or "WARRIOR") or "WARRIOR"',
        'local role=user and (user:GetAttribute("EGGRUMBLE_Role") or "WARRIOR") or "WARRIOR"\n      applyCurseOnVerifiedHit(user,model,h,hitSerial,origin,role)',
        "ACTUAL_HIT_HOOK")
    # Only hostile neutrals may be struck; charmed actors still stay in the sole live set.
    source=replace_once(source,
        'if m.Parent and h.Health>0 and m.PrimaryPart then\n     local delta=m.PrimaryPart.Position-at',
        'if m.Parent and h.Health>0 and m.PrimaryPart and not charmed[m] then\n     local delta=m.PrimaryPart.Position-at',
        "FRIENDLY_FIRE")
    # Physical follow is in the already-owned neutral movement loop, not a second controller.
    old='''       for _,target in ipairs(candidates) do
        local delta=Vector3.new(target.X-at.X,0,target.Z-at.Z)
        if delta.Magnitude<best then near=delta;best=delta.Magnitude end
       end'''
    new='''       local ownerTarget=charmOwnerPosition(m)
       if ownerTarget then
        local delta=Vector3.new(ownerTarget.X-at.X,0,ownerTarget.Z-at.Z)
        near=delta;best=delta.Magnitude
        charmedNeutralAttack(m)
       else
        for _,target in ipairs(candidates) do
         local delta=Vector3.new(target.X-at.X,0,target.Z-at.Z)
         if delta.Magnitude<best then near=delta;best=delta.Magnitude end
        end
       end'''
    source=replace_once(source,old,new,"FOLLOW_OWNER")
    # Explicit expiry, death or role loss cleanup every native Swarm movement tick.
    needle='while all.Parent and session.rules.phase=="ACTIVE" do\n    local candidates=aliveTargets()'
    if source.count(needle)!=2:
        raise ValueError("RED_EXPECT_TWO_ORIGINAL_SWARM_LOOPS")
    pos=source.find(needle,source.find(needle)+len(needle))
    source=source[:pos]+needle.replace("    local candidates=aliveTargets()",
        "    expireCharms()\n    local candidates=aliveTargets()")+source[pos+len(needle):]
    if source.count("function Swarm.start(session:any)")!=1 or source.count("local function charmedNeutralAttack(")!=1:
        raise ValueError("RED_DUPLICATE_CONTROLLER")
    if any(v in source for v in ("DataStoreService","MarketplaceService","RemoteEvent")):
        raise ValueError("RED_UNTRUSTED_STORE_REMOTE")
    return source

def compose(before:Path,policy:Path,out:Path):
    before=Path(before).resolve(strict=True)
    policy=Path(policy).resolve(strict=True)
    out=Path(out).resolve()
    if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
    doc,original=flatten(before)
    if len(original)!=43 or SWARM not in original or CURSE in original:
        raise ValueError("RED_NOT_VERIFIED_REAL43")
    if git_blob(policy.read_bytes())!=POLICY_BLOB:
        raise ValueError("RED_NOT_IMMUTABLE_ORIGINAL_801_POLICY")
    swarm=original[SWARM].read_text()
    changed=patch_swarm(swarm)
    out.parent.mkdir(parents=True,exist_ok=True)
    patch=out.parent/"EGGRUMBLE_SwarmCombat_Real44.luau"
    patch.write_text(changed)
    new=copy.deepcopy(doc)
    def relink(node,route=()):
        for k,v in node.items():
            if k.startswith("$"):continue
            r=route+(k,)
            if "$path" in v:
                v["$path"]=os.path.relpath(patch if r==SWARM else original[r],out.parent).replace(os.sep,"/")
            else:relink(v,r)
    relink(new["tree"])
    new["tree"]["ServerScriptService"][CURSE[-1]]={
       "$path":os.path.relpath(policy,out.parent).replace(os.sep,"/")}
    new["name"]="GQ800_REAL44_SINGLE_SWARM_CURSE_LIVE_PREP_NOT_OFFICIAL"
    out.write_text(json.dumps(new,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    _,latest=flatten(out)
    if set(latest)!=set(original)|{CURSE} or len(latest)!=44:
        raise ValueError("RED_BAD_SOURCE_COUNT")
    for route,src in original.items():
        if route!=SWARM and latest[route].read_bytes()!=src.read_bytes():
            raise ValueError("RED_MODIFIED_EXISTING_OWNER_"+"/".join(route))
    receipt={"profile":"REAL44_CHARM_LIVE","old_count":43,"new_count":44,
             "exact_existing_sources":42,"modified_existing":["/".join(SWARM)],
             "new_unchanged_original_policy":["/".join(CURSE)],
             "original_policy_blob":POLICY_BLOB,
             "old_swarm_blob":git_blob(original[SWARM].read_bytes()),
             "new_swarm_blob":git_blob(changed.encode()),
             "limit":"One real charmed actor per owner; existing 3 summoned + 1 charmed <= 4",
             "rollback":"Select original, complete Real43 packet (one Swarm); exclude Curse policy",
             "official_rc":False,"studio_2client":"NOT_TESTED","android15":"NOT_TESTED",
             "owner_fun":"NOT_TESTED"}
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("GQ800_REAL43_TO_REAL44_SINGLE_SWARM_REUSE_POLICY_READY")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original43",type=Path,required=True)
    p.add_argument("--original-policy",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    compose(a.original43,a.original_policy,a.out)
