local basic=dependencies.EGGRUMBLE_BasicMobilityPolicy.SPECS.MAGE.basic
local session=ready("MAGE_CLOSE_ORIGINAL_HOST")
local tool=nil
for _,item in player:FindFirstChildOfClass("Backpack"):GetChildren() do
 if item:GetAttribute("EGGRUMBLE_InternalToolId")=="EGGRUMBLE_BASIC_ATTACK" then assert(not tool);tool=item end
end
assert(tool);tool.Parent=character
local neutral=spawnCurrentNeutral(session)
local h=neutral:FindFirstChildOfClass("Humanoid")
-- A clear, isolated lane in the Native fixture. Relative positions are controlled;
-- the actual Host-created tool, neutral, combat, Swarm and Died ledger are retained.
local testLane=session.world:FindFirstChild('TacticalBattlefield').Position+Vector3.new(105,250,42)
local function setPose(model,x,z,y)
 model:PivotTo(CFrame.new(testLane))
 local t=model.PrimaryPart.Position
 local pos=t-Vector3.new(x,y or 0,z)
 rootPart.CFrame=CFrame.new(pos,pos+Vector3.new(1,0,0))
 return pos,t
end
local function resumeClock()
 outsideField(session)
 advanceTo(now+.57)
end
local function shot(model,x,z,y,look)
 local h=model:FindFirstChildOfClass("Humanoid")
 local before=h.Health
 local pos,t=setPose(model,x,z,y)
 if look then rootPart.CFrame=CFrame.new(pos,pos+look) end
 local serial=player:GetAttribute("EGGRUMBLE_BasicCastSerial") or 0
 tool.Activated:Fire()
 equal(player:GetAttribute("EGGRUMBLE_BasicCastSerial"),serial+1,"actual accepted tool activation")
 tool.Activated:Fire()
 equal(player:GetAttribute("EGGRUMBLE_BasicCastSerial"),serial+1,"immediate repeat refused by original cooldown")
 return before-h.Health,pos,t
end
equal(shot(neutral,3,0,0),if patched then 9 else 0,"three-stud front fixed-ID HP")
print("CLOSE","ACTUAL_FRONT",neutral:GetAttribute("EGGRUMBLE_NeutralInstanceId"),if patched then "32->23" else "32->32")
resumeClock();equal(shot(neutral,-3,0,0),0,"rear rejected")
resumeClock();equal(shot(neutral,3,0,6),0,"height rejected")
resumeClock();equal(shot(neutral,16.05,0,0),0,"excess distance rejected")
resumeClock()
local wall=Instance.new("Part");wall.Name="NativeCloseBasicWall";wall.Anchored=true
local pos,t=setPose(neutral,3,0,0)
wall.Size=Vector3.new(.3,8,6);wall.CFrame=CFrame.new(pos+Vector3.new(1.5,1,0));wall.CanCollide=true;wall.Parent=workspace
equal(shot(neutral,3,0,0),0,"real Swarm LOS wall blocked")
wall:Destroy()
resumeClock();equal(shot(neutral,11,0,0),9,"old attack circle unchanged")
print("CLOSE","NEGATIVE_AND_LEGACY","blocked wall, rear, vertical, too far, original distance, immediate double-click")
local before=player:GetAttribute("EGGRUMBLE_NeutralKOs")
assert(before==0)
if patched then
 for goal=1,8 do
  if h.Health<=0 then neutral=spawnCurrentNeutral(session);h=neutral:FindFirstChildOfClass("Humanoid") end
  for j=1,5 do
   if h.Health<=0 then break end
   resumeClock()
   local hp=h.Health
   equal(shot(neutral,3,0,0),math.min(hp,9),"strikes against the same live neutral at KO "..goal.." / "..j)
  end
  assert(h.Health<=0)
  local id=tostring(player.UserId)
  equal(session.swarm.kills[id],goal,"exact existing ledger")
  equal(player:GetAttribute("EGGRUMBLE_NeutralKOs"),goal,"exact public KO")
  local value=session.swarm.getBattleGrowthSnapshot(id)
  equal(value.stage,if goal<4 then 2 else 3,"B stage")
  equal(value.xp,10*goal,"XP")
 end
 print("CLOSE","EIGHT_REAL_NEUTRALS","actual tool -> single Swarm damage -> Died/KO 1..8; B2/10, B3/40, B3/80")
else
 print("CLOSE","CONTROL_FINISH","normal attacks at range remained eligible; no invented KO")
end
local enemy=spawnCurrentNeutral(session)
local enemyHum=enemy:FindFirstChildOfClass("Humanoid")
local hp=enemyHum.Health
local count=player:GetAttribute("EGGRUMBLE_NeutralKOs")
setPose(enemy,3,0,0)
local beforeGU=#guardianCalls
activate(player,"A")
assert(player:GetAttribute("EGGRUMBLE_SkillCastSignature")=="MAGE:A:1")
equal(enemyHum.Health,hp,"MAGE A still excludes near zone for neutrals")
assert(#guardianCalls==beforeGU+1 and guardianCalls[#guardianCalls].shape=="CRYSTAL")
resumeClock();setPose(enemy,3,0,0)
secondRoot.CFrame=CFrame.new(enemy.PrimaryPart.Position+Vector3.new(0,0,1))
local secondHP=secondHumanoid.Health
local beforeBasic=#guardianCalls
shot(enemy,3,0,0)
equal(secondHumanoid.Health,secondHP,"nearby opposing player retains original wand shape")
assert(#guardianCalls==beforeBasic+1 and guardianCalls[#guardianCalls].shape=="CRYSTAL")
equal(player:GetAttribute("EGGRUMBLE_NeutralKOs"),count,"nonlethal hit never adds reward")
print("CLOSE","BASIC_VS_OTHER_TARGETS","skill A near still misses; Guardian received CRYSTAL for skill and basic; nearby opposing human HP unchanged")

local function pitched(label,angle,x,z,y,hit,blocked,reverse)
 resumeClock()
 local subject=spawnCurrentNeutral(session)
 local health=subject:FindFirstChildOfClass("Humanoid")
 -- A single selected real spawned neutral in a clear, controlled Native test lane.
 for _,other in subject.Parent:GetChildren() do
  if other~=subject and other:IsA("Model") and other.PrimaryPart
   and (other.PrimaryPart.Position-testLane).Magnitude<26 then
   other:PivotTo(CFrame.new(testLane+Vector3.new(45,0,45)))
  end
 end
 local pos,target=setPose(subject,x,z,y)
 local barrier=nil
 if blocked then
  barrier=Instance.new("Part");barrier.Anchored=true;barrier.CanCollide=true
  barrier.Size=Vector3.new(.25,16,8);barrier.CFrame=CFrame.new((pos+target)*.5+Vector3.new(0,1,0))
  barrier.Parent=workspace
 end
 local sign=if reverse then -1 else 1
 local aim=Vector3.new(sign*math.cos(math.rad(angle)),math.sin(math.rad(angle)),0)
 local before=health.Health
 local damage=shot(subject,x,z,y,aim)
 if barrier then barrier:Destroy() end
 equal(damage,if hit then math.min(before,9) else 0,label)
 print("CLOSE","PITCH",label,angle,x,z,y,damage)
end
for _,sign in {-1,1} do
 local angle=sign*30
 pitched("new horizontal contact",angle,3,0,0,patched)
 pitched("V1 false positive at torso delta 10.4",angle,3,0,10.4*sign,false)
 pitched("torso-height inclusive",angle,3,0,5*sign,patched)
 pitched("torso-height exclusive",angle,3,0,5.01*sign,false)
 pitched("original far projected circle",angle,11*math.cos(math.rad(angle)),0,10.4*sign,true)
 pitched("collidable wall on contact",angle,3,0,0,false,true)
 pitched("near approach remains narrow",angle,3,1.51,0,false)
 pitched("rear contact rejected",angle,-3,0,0,false)
 pitched("reverse horizontal facing",angle,-3,0,0,patched,false,true)
end
pitched("no invented heading for vertical pose",90,3,0,0,false)
pitched("steep pitch avoids artificially long horizontal band",75,8,0,0,false)

print("CLOSE","DONE",patched)
