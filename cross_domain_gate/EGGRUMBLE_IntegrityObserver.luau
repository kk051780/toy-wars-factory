--!strict
-- PRIVATE / Studio-only. Read-only 7-domain runtime integrity observer.
-- It never changes CastleMatchRules, damage, scores, eggs, items or player state.
-- Integration is source-selective in private 27-script composer; NOT official RC.
local Players=if game then game:GetService("Players") else nil
local Observer={}
local ROLES={
 WARRIOR=true,MAGE=true,NINJA=true,TRAPPER=true,BUILDER=true,BEAST=true,ZOMBIE=true,
}

local function append(list:{string},code:string)
 table.insert(list,code)
end

function Observer.inspect(session:any,rulesModule:any,playersOverride:any?):any
 local playerService=playersOverride or Players
 local report={red={},yellow={},checked={
  character=false,field=false,battle=false,castle=false,neutral=false,item=false,lobby=false,
 }}
 if not session or not session.rules or not session.roster then
  append(report.red,"SESSION_MISSING");return report
 end
 local state=session.rules
 if session.mode~="TEAM" and session.mode~="BATTLE_ROYALE" then
  append(report.red,"MODE_INVALID")
 end
 if state.phase~="ACTIVE" and state.phase~="FINISHED" then
  append(report.yellow,"SESSION_NOT_ACTIVE")
 end
 if type(state.castles)~="table" or type(state.ids)~="table" then
  append(report.red,"CASTLE_ROSTER_MISSING");return report
 end

 -- CASTLES / EGG STOCK. The game's own server rules are authoritative.
 local conservationOk,audit=pcall(function()
  return rulesModule.auditEggConservation(state)
 end)
 if not conservationOk or type(audit)~="table" or audit.valid~=true then
  append(report.red,"EGG_CONSERVATION_OR_AUDIT_FAILED")
 end
 report.checked.castle=true
 local rosterCount=0
 for _,entry in ipairs(session.roster) do
  rosterCount+=1
  local castle=state.castles[tostring(entry.id)]
  if not castle then
   append(report.red,"ROSTER_CASTLE_MISSING")
  else
   if type(castle.hp)~="number" or castle.hp~=castle.hp
    or castle.hp<0 or castle.hp>rulesModule.CASTLE_HP then
    append(report.red,"CASTLE_HP_RANGE")
   end
   if castle.alive and castle.hp<=0 then append(report.red,"LIVING_CASTLE_NO_HP") end
   if not castle.alive and castle.hp>0 then append(report.red,"FALLEN_CASTLE_HAS_HP") end
   if type(castle.heldEggs)~="number" or castle.heldEggs<0
    or castle.heldEggs>3 or castle.heldEggs%1~=0 then
    append(report.red,"EGG_CARRY_RANGE")
   end
  end
 end
 if rosterCount~=#state.ids then append(report.red,"ROSTER_COUNT_MISMATCH") end
 if state.phase=="ACTIVE" and state.winner~=nil then
  append(report.red,"ACTIVE_MATCH_HAS_WINNER")
 end

 -- FIELD / ROUTES: do not confuse optional art with required traversable ground.
 report.checked.field=true
 local world=session.world
 if not world or world.Parent==nil then
  append(report.red,"FIELD_WORLD_MISSING")
 else
  if not world:FindFirstChild("TacticalBattlefield") then
   append(report.red,"TACTICAL_GROUND_MISSING")
  end
  for i=1,3 do
   if not world:FindFirstChild("TacticalRoute_"..tostring(i)) then
    append(report.yellow,"TACTICAL_ROUTE_MISSING")
   end
  end
 end

 -- BATTLE / NEUTRAL NPC. Reports missing server state, never invents KO evidence.
 report.checked.battle=true
 report.checked.neutral=true
 if type(session.swarm)~="table" or type(session.swarm.kills)~="table" then
  append(report.red,"NEUTRAL_HORDE_STATE_MISSING")
 else
  for _,ko in pairs(session.swarm.kills) do
   if type(ko)~="number" or ko<0 or ko~=ko or ko%1~=0 then
    append(report.red,"INVALID_SERVER_KO_COUNTER")
    break
   end
  end
 end
 if session.bossStatus=="YELLOW_BOSS_OPTIONAL" then
  append(report.yellow,"OPTIONAL_BOSS_FAILED")
 elseif session.bossStatus~="READY" then
  append(report.yellow,"BOSS_UNVERIFIED")
 end

 -- ITEMS: item failure may be YELLOW under OWNER fast-iteration rule.
 report.checked.item=true
 if session.itemIntakeStatus=="READY" then
  if type(session.fieldItemCount)~="number" or session.fieldItemCount<1 then
   append(report.red,"ITEM_READY_WITHOUT_SPAWNS")
  end
 elseif session.itemIntakeStatus=="YELLOW_ITEM_OPTIONAL" then
  append(report.yellow,"OPTIONAL_ITEM_INTAKE_FAILED")
 else
  append(report.yellow,"ITEM_STATUS_UNVERIFIED")
 end

 -- CHARACTER / LOBBY ownership: verify actual server-selected role, not HUD text.
 report.checked.character=true
 report.checked.lobby=true
 for _,entry in ipairs(session.roster) do
  if not entry.isAI then
   local player=playerService and playerService:GetPlayerByUserId(tonumber(entry.id) or -1)
   if player and player.Parent==playerService then
    local role=player:GetAttribute("EGGRUMBLE_Role")
    if not ROLES[role] then append(report.yellow,"HUMAN_ROLE_NOT_ACKNOWLEDGED") end
   end
  end
 end
 return report
end

-- Read-only, bounded warning fingerprint for mobile/Studio log-flood avoidance.
-- No player IDs, positions or action contents are logged. Order-independent.
function Observer.warningSignature(report:any):string
 if type(report)~="table" then return "INVALID_REPORT" end
 local tokens={}
 for _,severity in ipairs({"red","yellow"}) do
  local entries=report[severity]
  if type(entries)~="table" then
   table.insert(tokens,severity..":INVALID")
  else
   local unique={}
   for _,code in ipairs(entries) do
    if type(code)=="string" and #code>0 and #code<=96 then
     unique[code]=true
    end
   end
   local keys={}
   for code in pairs(unique) do table.insert(keys,code) end
   table.sort(keys)
   for _,code in ipairs(keys) do table.insert(tokens,severity..":"..code) end
  end
 end
 return table.concat(tokens,"|")
end

function Observer.warningDelta(previous:string?,report:any):(string,boolean,boolean)
 local current=Observer.warningSignature(report)
 local changed=current~=previous
 -- No initial clean health ping; log recovery once after a previous error.
 local emit=changed and (current~="" or (previous~=nil and previous~=""))
 return current,emit,(current=="" and emit)
end

return Observer
