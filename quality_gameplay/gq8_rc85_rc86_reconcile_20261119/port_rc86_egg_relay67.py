#!/usr/bin/env python3
"""RC86 EGG_RELAY_CLASSIC_V1 into one current V3 CastleMatchRules+Host.

Old ORIGINAL EggRelayPolicy policy: 8 horizontal / 4 vertical studs,
12-second interval, TEAM only, same living team, no stunned/eliminated
parties, client never supplies egg quantity/damage/state, server-only LOS and
one atomically transferred egg per accepted prompt.

Current V3 tracks aggregate 1..3 held eggs per castle, not individual carried
egg IDs, therefore this is a server-authoritative equivalent-one-egg relay,
not a dishonest byte-for-byte EggRelayPolicy Game import.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

RULES="ServerScriptService/EGGRUMBLE_CastleMatchRules"
HOST="ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
FEATURE="GQ8_RC86_EGG_RELAY_CLASSIC_SINGLE_CASTLE_AUTHORITY_REAL67_20261119"

RULES_M_OLD='''M.MAX_HOUSE_PIECES=48'''
RULES_M_NEW='''M.MAX_HOUSE_PIECES=48
-- GQ8_RC86_EGG_RELAY_CLASSIC_SINGLE_CASTLE_AUTHORITY_REAL67_20261119
M.RELAY_HORIZONTAL_STUDS=8
M.RELAY_VERTICAL_STUDS=4
M.RELAY_COOLDOWN_SECONDS=12'''

RULES_NEW_OLD='''  teamDeposits={RED=0,BLUE=0},teamSiegeTokens={RED=0,BLUE=0},'''
RULES_NEW_NEW='''  teamDeposits={RED=0,BLUE=0},teamSiegeTokens={RED=0,BLUE=0},
   eggRelayLastAt={},eggRelaySerial=0,'''

RULES_FN_OLD='''function M.auditEggConservation(m:any):any'''
RULES_FN_NEW='''-- Original RC86 EggRelayPolicy semantics adapted to the ONE V3 castle owner.
-- Called only by an existing server-owned ProximityPrompt. No client request,
-- remote, possession value, transfer sequence or Game/Store authority accepted.
-- Absolutely NO YIELD between validation and transfer; both inventory counts,
-- cooldown and the event receipt commit in this one server call.
function M.relayEgg(m:any,fromId:any,toId:any,nowSec:number,
 serverLOS:boolean,fromPos:Vector3,toPos:Vector3):any
 assertActive(m)
 assert(m.mode==M.MODE_TEAM,"classic egg relay is TEAM-only")
 local from=castleOf(m,fromId)
 local to=castleOf(m,toId)
 assert(from.id~=to.id and from.alive and to.alive
  and not from.isAI and not to.isAI
  and (from.team=="RED" or from.team=="BLUE") and from.team==to.team,
  "relay requires distinct living real teammates")
 assert(type(from.heldEggs)=="number" and from.heldEggs>=1 and from.heldEggs<=3
  and type(to.heldEggs)=="number" and to.heldEggs>=0 and to.heldEggs<3,
  "relay cannot invent eggs or exceed inventory cap")
 assert(type(nowSec)=="number" and nowSec==nowSec and nowSec>=0 and nowSec<1000000000,
  "server clock required")
 assert(typeof(fromPos)=="Vector3" and typeof(toPos)=="Vector3",
  "both positions must be trusted server Vector3")
 local dx=fromPos.X-toPos.X
 local dy=fromPos.Y-toPos.Y
 local dz=fromPos.Z-toPos.Z
 assert(math.abs(dy)<=M.RELAY_VERTICAL_STUDS
  and (dx*dx+dz*dz)<=M.RELAY_HORIZONTAL_STUDS*M.RELAY_HORIZONTAL_STUDS,
  "relay out of 8x4 studs range")
 assert(serverLOS==true,"relay cannot pass through wall")
 local previousFrom=m.eggRelayLastAt[from.id]
 local previousTo=m.eggRelayLastAt[to.id]
 assert((previousFrom==nil or (nowSec>=previousFrom
   and nowSec-previousFrom>=M.RELAY_COOLDOWN_SECONDS))
  and (previousTo==nil or (nowSec>=previousTo
   and nowSec-previousTo>=M.RELAY_COOLDOWN_SECONDS)),
  "relay cooldown or invalid clock")
 -- Avoid egg duplication by moving exactly ONE from existing source stock
 -- to existing target stock. Stock/field token total is unchanged.
 from.heldEggs-=1
 to.heldEggs+=1
 m.eggRelayLastAt[from.id]=nowSec
 m.eggRelayLastAt[to.id]=nowSec
 m.eggRelaySerial+=1
 local receipt={from=from.id,to=to.id,quantity=1,seq=m.eggRelaySerial,
  team=from.team,serverAt=nowSec}
 table.insert(m.events,{type="EGG_RELAY",from=receipt.from,to=receipt.to,
  quantity=1,seq=receipt.seq})
 return receipt
end

function M.auditEggConservation(m:any):any'''

HOST_STOP_OLD='''  if session.guardians then session.guardians.shutdown() end'''
HOST_STOP_NEW='''  if session.guardians then session.guardians.shutdown() end
  -- Original RC86 relay lives in this session only; no prompt survives teardown.
  if session.eggRelayStop then session.eggRelayStop() end'''

HOST_INSERT_OLD=''' -- Actual anchored 3D bot actors roam between castles and must reach their goal'''
HOST_INSERT_NEW='''  -- GQ8_RC86_EGG_RELAY_CLASSIC_SINGLE_CASTLE_AUTHORITY_REAL67_20261119
  -- Reuse this ONE Host, its real players and the ONE CastleMatchRules owner.
  -- Each recipient triggers a server-only prompt on the current egg carrier.
  -- No Remote, Tool, client-side quantity, second Game, Store, HUD or score.
  session.eggRelayPrompts={}
  session.eggRelayStop=function()
   for _,relayPrompt in ipairs(session.eggRelayPrompts) do
    relayPrompt.Enabled=false
    if relayPrompt.Parent then relayPrompt:Destroy() end
   end
   table.clear(session.eggRelayPrompts)
  end
  if mode=="TEAM" then
   local function mountRelayPrompt(carrierPlayer:Player,character:Model)
    local carrierRoot=character:FindFirstChild("HumanoidRootPart")
     or character:WaitForChild("HumanoidRootPart",5)
    if not carrierRoot or not carrierRoot:IsA("BasePart") or
     sessions[mode]~=session or carrierPlayer.Character~=character
     or session.rules.phase~="ACTIVE" then return end
    local prior=carrierRoot:FindFirstChild("EGGRUMBLE_ClassicEggRelay")
    if prior then return end
    local relayPrompt=Instance.new("ProximityPrompt")
    relayPrompt.Name="EGGRUMBLE_ClassicEggRelay"
    relayPrompt.ActionText="卵を受け取る"
    relayPrompt.ObjectText="味方の卵リレー"
    relayPrompt.HoldDuration=.35
    relayPrompt.MaxActivationDistance=Rules.RELAY_HORIZONTAL_STUDS
    relayPrompt.RequiresLineOfSight=true
    relayPrompt.Enabled=false
    relayPrompt.Parent=carrierRoot
    table.insert(session.eggRelayPrompts,relayPrompt)
    table.insert(session.lifeConnections,relayPrompt.Triggered:Connect(function(receiver:Player)
     if receiver==carrierPlayer or sessions[mode]~=session or
      session.rules.phase~="ACTIVE" or session.rules.winner~=nil
      or not relayPrompt.Enabled or relayPrompt.Parent~=carrierRoot
      or carrierPlayer.Character~=character
      or joined[carrierPlayer.UserId]~=mode or joined[receiver.UserId]~=mode
      or not session.isCurrentHuman(carrierPlayer)
      or not session.isCurrentHuman(receiver)
      or receiver:GetAttribute("EGGRUMBLE_Eliminated")==true
      or carrierPlayer:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
     local receiverCharacter=receiver.Character
     local receiverRoot=receiverCharacter and receiverCharacter:FindFirstChild("HumanoidRootPart")
     local carrierHuman=character:FindFirstChildOfClass("Humanoid")
     local receiverHuman=receiverCharacter and receiverCharacter:FindFirstChildOfClass("Humanoid")
     if not receiverRoot or not receiverRoot:IsA("BasePart")
      or not carrierHuman or carrierHuman.Health<=0
      or not receiverHuman or receiverHuman.Health<=0
      or receiverHuman:GetState()==Enum.HumanoidStateType.Dead
      or carrierHuman:GetState()==Enum.HumanoidStateType.Dead then return end
     -- No stun/restrain relay. No player-supplied positions, IDs or egg count.
     local now=os.clock()
     local function disabled(p:Player):boolean
      return p:GetAttribute("EGGRUMBLE_Stunned")==true
       or p:GetAttribute("EGGRUMBLE_Restrained")==true
       or (p:GetAttribute("EGGRUMBLE_StunUntil") or 0)>now
     end
     if disabled(receiver) or disabled(carrierPlayer) then return end
     local start=receiverRoot.Position+Vector3.new(0,1,0)
     local finish=carrierRoot.Position+Vector3.new(0,1,0)
     local delta=finish-start
     if math.abs(delta.Y)>Rules.RELAY_VERTICAL_STUDS
      or Vector3.new(delta.X,0,delta.Z).Magnitude>Rules.RELAY_HORIZONTAL_STUDS then return end
     local rp=RaycastParams.new()
     rp.FilterType=Enum.RaycastFilterType.Exclude
     rp.FilterDescendantsInstances={receiverCharacter,character}
     rp.RespectCanCollide=true
     local wall=workspace:Raycast(start,delta,rp)
     if wall and wall.Instance and wall.Instance.CanCollide then return end
     -- A trusted no-yield transaction atomically moves one egg between the
     -- existing castle inventories. Rule layer checks same team/capacity/12s.
     local ok=pcall(function()
      Rules.relayEgg(session.rules,tostring(carrierPlayer.UserId),
       tostring(receiver.UserId),now,true,carrierRoot.Position,receiverRoot.Position)
     end)
     if ok then
      local conservation=Rules.auditEggConservation(session.rules)
      if not conservation.valid then
       warn("[GQ8 RC86 EGG RELAY] conservation violation, check receipt immediately")
      end
      session.refresh()
     end
    end))
    task.spawn(function()
     while sessions[mode]==session and session.rules.phase=="ACTIVE"
      and character.Parent and carrierPlayer.Character==character
      and relayPrompt.Parent==carrierRoot do
      local c=session.rules.castles[tostring(carrierPlayer.UserId)]
      local hum=character:FindFirstChildOfClass("Humanoid")
      relayPrompt.Enabled=c~=nil and c.isAI~=true and c.alive
       and c.heldEggs>0 and hum~=nil and hum.Health>0
       and joined[carrierPlayer.UserId]==mode
       and carrierPlayer:GetAttribute("EGGRUMBLE_Eliminated")~=true
      task.wait(.35)
     end
     relayPrompt.Enabled=false
    end)
   end
   for _,relayOwner in ipairs(queue) do
    if relayOwner.Parent==Players and joined[relayOwner.UserId]==mode then
     table.insert(session.lifeConnections,relayOwner.CharacterAdded:Connect(function(ch)
      task.spawn(mountRelayPrompt,relayOwner,ch)
     end))
     if relayOwner.Character then
      task.spawn(mountRelayPrompt,relayOwner,relayOwner.Character)
     end
    end
   end
  end
  -- Actual anchored 3D bot actors roam between castles and must reach their goal'''

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def change(src:str,old:str,new:str,what:str)->str:
    if src.count(old)!=1 or new in src:
        raise ValueError("RED_RC86_RELAY_"+what+"_PARENT_DRIFT")
    changed=src.replace(old,new,1)
    if changed.replace(new,old,1)!=src:
        raise ValueError("RED_RC86_RELAY_"+what+"_UNRELATED_MUTATION")
    return changed

def patch_rules(src:str)->str:
    original=src
    src=change(src,RULES_M_OLD,RULES_M_NEW,"RULES_POLICY")
    src=change(src,RULES_NEW_OLD,RULES_NEW_NEW,"RULES_ROUND_STATE")
    src=change(src,RULES_FN_OLD,RULES_FN_NEW,"RULES_ATOMIC_TRANSFER")
    for token in ('RemoteEvent','DataStoreService','ProcessReceipt',':TakeDamage('):
        if src.count(token)!=original.count(token):
            raise ValueError("RED_RELAY_RULES_SECOND_OWNER")
    return src

def patch_host(src:str)->str:
    if 'local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))' not in src:
        raise ValueError("RED_RELAY_HOST_NOT_ORIGINAL_RULES_AUTHORITY")
    original=src
    src=change(src,HOST_STOP_OLD,HOST_STOP_NEW,"HOST_CLOSE_ROUND")
    src=change(src,HOST_INSERT_OLD,HOST_INSERT_NEW,"HOST_REAL_SESSION")
    for token in ('Instance.new("RemoteEvent")','ProcessReceipt','DataStoreService','MarketplaceService'):
        if src.count(token)!=original.count(token):
            raise ValueError("RED_RELAY_HOST_NEW_AUTHORITY")
    return src

def self_test():
    fixture="\\n".join((RULES_M_OLD,RULES_NEW_OLD,RULES_FN_OLD))
    rules=patch_rules(fixture)
    assert 'M.RELAY_HORIZONTAL_STUDS=8' in rules
    assert 'M.RELAY_VERTICAL_STUDS=4' in rules
    assert 'M.RELAY_COOLDOWN_SECONDS=12' in rules
    assert "from.heldEggs-=1" in rules and "to.heldEggs+=1" in rules
    assert 'serverLOS==true' in rules and 'm.eggRelaySerial+=1' in rules
    hostFixture="\\n".join(('local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))',HOST_STOP_OLD,HOST_INSERT_OLD))
    host=patch_host(hostFixture)
    for key in ("CharacterAdded:Connect", "relayPrompt.Triggered:Connect",
                "workspace:Raycast(start,delta,rp)",
                "Rules.relayEgg(session.rules,",
                "session.eggRelayStop=function()",
                'if mode=="TEAM" then'):
        assert key in host,key
    for fn,mutant in ((patch_rules,rules),(patch_host,host),
                      (patch_host,hostFixture.replace(HOST_STOP_OLD,"")),
                      (patch_rules,fixture.replace(RULES_M_OLD,"M.MAX_HOUSE_PIECES=49"))):
        try:fn(mutant)
        except ValueError:pass
        else:raise AssertionError("RED_RELAY_MUTANT_ACCEPTED")
    print("GQ8_RC86_RELAY_OLD_8_4_12_ATOMIC_TEAM_ONLY_NEGATIVE_MUTATIONS_PASS")

def apply(project_path:Path,receipt_path:Path):
    project=json.loads(project_path.read_text(encoding="utf8"))
    receipt=json.loads(receipt_path.read_text(encoding="utf8"))
    rows={row["route"]:row for row in receipt["sources"]}
    if project.get("name")!="EGGRUMBLE_REAL65_PRIVATE_STUDIO" or len(rows)!=65 or len(receipt["sources"])!=65:
        raise ValueError("RED_RC86_RELAY_NOT_SINGLE_ORIGINAL65_PARENT")
    for flag in ("rc86_meteor_shortcut","rc86_starry_path","rc86_three_undead_command",
                 "rc85_dojo_lobby_training","legacy_rc86_wind",
                 "stage_weapon_reach_balance","pickup_prompt_alias","rc86_trapper_pair_warp"):
        if not receipt.get(flag):
            raise ValueError("RED_RC86_RELAY_MISSING_PREVIOUS_LINEAGE_"+flag)
    if "rc86_egg_relay" in receipt:
        raise ValueError("RED_RC86_RELAY_DOUBLE_PORT")
    if (RULES not in rows or HOST not in rows or
        rows[RULES]["class"]!="ModuleScript" or rows[HOST]["class"]!="Script"):
        raise ValueError("RED_RC86_RELAY_ORIGINAL_HOST_RULES_OWNER_MISSING")
    before={}
    for route,row in rows.items():
        node=project["tree"]
        for segment in route.split("/"):node=node[segment]
        path=project_path.parent/node["$path"]
        data=path.read_bytes()
        if digest(data)!=row["sha256"] or len(data)!=row["bytes"]:
            raise ValueError("RED_RC86_RELAY_PARENT_SOURCE_HASH_"+route)
        before[route]=(path,data)
    for route,patch in ((RULES,patch_rules),(HOST,patch_host)):
        path,original=before[route]
        modified=patch(original.decode("utf8")).encode("utf8")
        path.write_bytes(modified)
        rows[route]["sha256"]=digest(modified)
        rows[route]["bytes"]=len(modified)
    if sum(path.read_bytes()!=data for path,data in before.values())!=2:
        raise ValueError("RED_RC86_RELAY_WRONG_SOURCE_MUTATION_COUNT")
    if HOST not in receipt["patched_existing_routes"] or RULES in receipt["patched_existing_routes"]:
        raise ValueError("RED_RC86_RELAY_UNEXPECTED_ORIGINAL_OWNER")
    receipt["patched_existing_routes"].append(RULES)
    receipt["original_real63_byte_unchanged"]-=1
    receipt["rc86_egg_relay"]={
        "feature_id":FEATURE,
        "original_rc86_flag":"EGG_RELAY_CLASSIC_V1",
        "original_rc86_source":"ServerScriptService/TrapRaidersS1/EggRelayPolicy",
        "original_rc86_artifact":14161823401,
        "ported_to_existing":[RULES,HOST],
        "server_auth_transport":"original Host character ProximityPrompt, no client-created remote",
        "one_egg_atomic_existing_inventory":True,
        "team_only":True,"original_horizontal_studs":8,
        "original_vertical_studs":4,"original_cooldown_seconds":12,
        "server_raycast_los":True,
        "server_authoritative_both_positions":True,
        "stale_avatar_mode_round_elimination_fenced":True,
        "max_carry":3,"egg_conservation":"count-preserving one to one",
        "historic_egg_id_transfer_seq":"NOT_APPLICABLE_V3_HAS_AGGREGATE_CARRIER_STOCK",
        "new_Game_Store_Remote_damage_writers":0,
        "selected_existing_scripts":65,
        "new_scripts":0,"unchanged_existing_scripts":63,
        "existing66_explorer67_canyon_preserved":True,
        "studio_solo_two_client":"NOT_TESTED",
        "android15":"NOT_TESTED","fun":"NO_GO",
        "rollback":"remove only Host and CastleMatchRules egg relay overlay; preserve original REAL67 Starfall/Meteor/Undead/Dojo/Trapper"}
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    for route,row in rows.items():
        data=before[route][0].read_bytes()
        if digest(data)!=row["sha256"] or len(data)!=row["bytes"]:
            raise ValueError("RED_RC86_RELAY_FINAL_SELECTED_SOURCE_"+route)
    print("GQ8_RC86_CLASSIC_EGG_RELAY_REAL67_8_4_12_SERVER_ONLY_SOURCE_LOCK_65_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--project",type=Path)
    parser.add_argument("--receipt",type=Path)
    a=parser.parse_args()
    if a.self_test:self_test()
    else:
        if not a.project or not a.receipt:parser.error("--project and --receipt required")
        apply(a.project,a.receipt)
