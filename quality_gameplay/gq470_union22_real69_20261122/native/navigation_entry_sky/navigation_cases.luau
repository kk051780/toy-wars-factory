do
local flag="P0D_ENABLE_PRIVATE_COMMON_ROUTE_GUIDE"
local ids={"COMMON-011","COMMON-020"}
local received={}
local function mapRuntime()
 local replicated=Instance.new("Folder")
 local service=game.GetService
 game.GetService=function(self,name)
  if name=="ReplicatedStorage" then return replicated end
  return service(self,name)
 end
 workspace.GetServerTimeNow=function() return now end
 function methods:FireClient(p,snapshot)
  check(self:IsA("RemoteEvent") and self.Name=="EGGRUMBLE_MapIntelUpdate_V1","same private MapIntel channel")
  received[p]=snapshot
 end
 dependencies.EGGRUMBLE_MapVisibilityPolicy=(function()
-- MAP_POLICY_SOURCE
 end)()
 do
-- MAP_BRIDGE_SOURCE
 end
end
local function publish()
 RunService.Heartbeat:Fire(.91)
end
local function tool(p,id)
 for _,container in ipairs({p:FindFirstChildOfClass("Backpack"),p.Character}) do
  for _,t in ipairs(container:GetChildren()) do
   if t:IsA("Tool") and t:GetAttribute("EGGRUMBLE_FixedAbilityId")==id then return t end
  end
 end
 return nil
end
local function cast(id,p)
 p=p or player
 local t=assert(tool(p,id))
 t.Parent=p.Character;t.Activated:Fire()
 return t
end
local function row(p,id)
 local sent=received[p]
 for _,r in ipairs(sent and sent.guides or {}) do if r.id==id then return r end end
 return nil
end
local function anchor(s,p)
 local model=s.castleModels[tostring(p.UserId)].model
 return model:FindFirstChild("StandardFoundation").Position,model:FindFirstChild("OwnEggDeposit").Position
end
local function park(s,point)
 for _,m in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  if m.PrimaryPart then
   m:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
   m:PivotTo(CFrame.new(point+Vector3.new(80,3,50)))
  end
 end
end
local function begin(opted,footing)
 trigger(player,scenes:FindFirstChild("ROLE_MAGE"),"職業選択")
 local stand=scenes:FindFirstChild("ROLE_FOOTING")
 if opted then trigger(player,stand,"装備する") end
 if footing then trigger(player,stand,"空中足場を装備") end
 local s=ready("PRIVATE_COMMON_GUIDE","MAGE")
 local field=s.world:FindFirstChild("TacticalBattlefield")
 local point=field.Position+Vector3.new(170,field.Size.Y*.5+3,-115)
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 rootPart.AssemblyLinearVelocity=Vector3.zero
 mapRuntime()
 local a=anchor(s,player)
 local b=anchor(s,second)
 secondRoot.CFrame=CFrame.new(b+Vector3.new(0,5,0))
 local flat=Vector3.new(a.X,point.Y,a.Z)
 for i=0,6 do
  rootPart.CFrame=CFrame.new(flat+(point-flat)*(i/6))
  publish()
 end
 park(s,point)
 advanceTo(now+.78)
 check(received[player] and received[second] and received[player].mode=="TEAM","actual same-round private sender for both owners")
 if opted then
  check(tool(player,ids[1]).Name=="方位光" and tool(player,ids[2]).Name=="帰還標","two actual opted-in inventory tools")
  check(not tool(second,ids[1]) and not tool(second,ids[2]),"other role did not opt in")
 else check(not tool(player,ids[1]) and not tool(player,ids[2]),"opt-in is explicit") end
 if footing then check(tool(player,"COMMON-025"),"original real Footing Tool retained") end
 return s,point
end
local function flat(at)
 return Vector3.new(at.X,0,at.Z)
end
local function position(receipt)
 return Vector3.new(receipt.x,receipt.y,receipt.z)
end
local function energy(s)
 return s.swarm.getRoleGrowthSnapshot(player).energy
end
local function wall(s,x,wide)
 local p=Instance.new("Part")
 p.Name="NativeCommonRouteWall";p.Size=Vector3.new(.4,10,wide or 6);p.CFrame=CFrame.new(x)
 p.Anchored=true;p.CanQuery=true;p.CanCollide=true;p.Parent=s.world
 return p
end
local function walk(s,start,distance)
 rootPart.CFrame=CFrame.new(start)
 park(s,start);advanceTo(now+.78)
 local moved=start+Vector3.new(distance,0,0)
 rootPart.CFrame=CFrame.new(moved)
 advanceTo(now+.39)
 return moved
end

function growthCases.guide_home()
 local s,current=begin(true,true)
 local _,home=anchor(s,player)
 local _,foreign=anchor(s,second)
 local life=now
 check(energy(s)==100,"real stage-zero energy")
 cast(ids[1]);publish()
 local mark=row(player,ids[1])
 check(mark and mark.stage==0,"actual server receipt reaches the current owner")
 local direction=flat(position(mark)-current)
 check(math.abs(direction.Magnitude-12)<.01 and direction.Unit:Dot(flat(home-current).Unit)>.999,
  "own real deposit determines exact S0 12-stud arrow")
 check(direction.Unit:Dot(flat(foreign-current).Unit)<.998 or (position(mark)-foreign).Magnitude>12,
  "never yields foreign-home position")
 equal(mark.expires-life,2,"exact S0 display lifetime")
 equal(energy(s),80,"one E20 after the physical cast")
 check(received[player].guideAvatar==character and received[player].guideArena==s.world and not row(second,ids[1]),
  "existing recipient is exact current avatar in this arena, no peer reveal")
 check(#received[player].markers<=30 and not mark.floor and not mark.world and not mark.actor,"no private internal context leaked")
 cast(ids[1]);equal(energy(s),80,"duplicate blocked by real shared CD")
 advanceTo(life+2.01);publish()
 check(not row(player,ids[1]),"exact expiry removes private route")
 return "real selected Tool A-style item to current own deposit direction at 12 studs, 2 seconds, E20/CD14; peer and ordinary map unchanged"
end

function growthCases.guide_return()
 local s,past=begin(true,false)
 cast(ids[2]);publish()
 check(not row(player,ids[2]) and energy(s)==100,"no distinct prior point, no payment")
 local current=walk(s,past,4.5)
 local castle=s.rules.castles[tostring(player.UserId)]
 local hp=humanoid.Health
 local life=now
 local castleHP=castle.hp
 cast(ids[2]);publish()
 local mark=row(player,ids[2])
 check(mark and mark.stage==0 and (flat(position(mark)-past)).Magnitude<.01,
  "viewer is sent exact legal prior point")
 equal(mark.expires-life,2,"S0 true lifetime")
 equal(energy(s),75,"E25 after real accepted route sample")
 check((rootPart.Position-current).Magnitude<.01 and hp==humanoid.Health and castleHP==castle.hp
  and castle.heldEggs==0 and s.swarm.getTotal()==0 and not row(second,ids[2]),
  "display only leaves own HP, pose, egg, castle, KO and other viewer unchanged")
 check(s.swarm.tryRoleGrowthCast(player,"MAGE",1,1,{[ids[2]]=1})==nil,"same canonical CD18");
 cast(ids[1]);publish()
 check(row(player,ids[1]) and row(player,ids[2]) and energy(s)==55,"independent receipts and charge clocks")
 local p=wall(s,(current+past)*.5)
 publish()
 check(not row(player,ids[2]),"late wall retires the previously visible safe return mark")
 p:Destroy()
 return "real owner-only prior sample is public to actor alone, no movement or HP rollback, second utility may coexist; late wall clears"
end

function growthCases.guide_return_denied()
 local s,past=begin(true,false)
 local current=walk(s,past,5)
 local p=wall(s,(current+past)*.5)
 cast(ids[2]);publish()
 check(not row(player,ids[2]) and energy(s)==100,"solid wall denies without consuming enemy or owner data")
 p:Destroy()
 humanoid.FloorMaterial=Enum.Material.Air
 cast(ids[1]);cast(ids[2]);publish()
 check(not row(player,ids[1]) and not row(player,ids[2]) and energy(s)==100,"airborne actor cannot invent safe point")
 humanoid.FloorMaterial=Enum.Material.Grass
 advanceTo(now+.39)
 rootPart.CFrame=CFrame.new(current+Vector3.new(25,0,0))
 advanceTo(now+.39)
 cast(ids[2]);publish()
 check(not row(player,ids[2]) and energy(s)==100,"discontinuous prior travel poisons history")
 local castle=s.rules.castles[tostring(player.UserId)]
 castle.heldEggs=1
 cast(ids[1]);publish()
 check(not row(player,ids[1]),"egg-carrier cannot acquire a guide")
 castle.heldEggs=0
 return "bounds, physical obstruction, an untraversed step, air and carrying fail shut without new disclosures"
end

function growthCases.guide_live_off()
 local s,past=begin(true,true)
 local current=walk(s,past,5)
 local old=cast(ids[1]);publish()
 check(row(player,ids[1]),"actual receipt present before disable")
 workspace:SetAttribute(flag,false)
 publish()
 check(not row(player,ids[1]) and not tool(player,ids[1]) and not tool(player,ids[2]),
  "OFF retires both approved utility tools and route instantly on observation")
 check(tool(player,"COMMON-025"),"OFF preserves Footing")
 old.Activated:Fire()
 publish()
 check(not row(player,ids[1]) and (rootPart.Position-current).Magnitude<.01,"stale utility cannot fire after OFF")
 workspace:SetAttribute(flag,true)
 check(not tool(player,ids[1]) and not s.commonGuideLoadouts[player.UserId],"explicit future choice required")
 return "existing live flag retires owners' utility state without touching the selected Footing equipment"
end

function growthCases.guide_physical_off()
 local s=begin(false,true)
 check(not tool(player,ids[1]) and not tool(player,ids[2]) and tool(player,"COMMON-025"),"exact OFF is prior equipment")
 local old=received[player]
 check(old and old.ownDeposit and not old.guides and not old.guideArena,"physical old MapIntel stays intact")
 return "exact old 69-source profile retains original map recipient, original Footing, no utility guides"
end

function growthCases.guide_stage_four()
 local s,base=begin(true,false)
 local moves={Vector3.zero,Vector3.new(1.2,0,0),Vector3.new(1.2,0,1.2),Vector3.new(0,0,1.2)}
 for i=1,600 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==4 then break end
  rootPart.CFrame=CFrame.new(base+moves[(i-1)%4+1]);park(s,base)
  advanceTo(now+.39)
 end
 check(s.swarm.getRoleGrowthSnapshot(player).stage==4,"actual active movement reaches S4")
 local present=walk(s,base,20)
 -- The continuous proof rule should reject the artificial 20 stud hop.
 cast(ids[2]);publish()
 check(not row(player,ids[2]),"history refuses 20 stud discontinuity even within S4")
 rootPart.CFrame=CFrame.new(base)
 advanceTo(now+.8)
 for i=1,4 do
  rootPart.CFrame=CFrame.new(base+Vector3.new(i*5,0,0))
  advanceTo(now+.39)
 end
 local life=now
 cast(ids[1]);cast(ids[2]);publish()
 local home=row(player,ids[1])
 local back=row(player,ids[2])
 check(home and back and home.stage==4 and back.stage==4,"both real Tools and S4 receipts")
 check(math.abs(flat(position(home)-present).Magnitude-28)<.01,"fixed S4 direction range28")
 check(math.abs(flat(position(back)-present).Magnitude-20)<.01 and back.expires-life==6 and home.expires-life==6,
  "S4 covers the oldest proven 20-stud segment under range24 and shows both for six seconds")
 equal(energy(s),55,"same shared E45 total")
 return "authentic S4 samples, 28-stud own direction, 20-stud proven walkback under 24, six-second duration"
end

local function surface()
 local gui=Instance.new("Frame")
 gui.AbsolutePosition=Vector2.new(0,0)
 local mapBox=Instance.new("Frame");mapBox.Parent=gui
 local function rounded() end
 local function label(n,parent,text,size)
  local p=Instance.new("TextLabel");p.Name=n;p.Parent=parent;p.Text=text;p.TextSize=size
  return p
 end
-- GUIDE_HUD_SOURCE
 return CommonGuideView,gui,mapBox
end

function growthCases.guide_hud()
 local s,past=begin(true,false)
 local current=walk(s,past,5)
 cast(ids[1]);cast(ids[2]);publish()
 local packet=received[player]
 check(#packet.guides==2,"actual network-shaped viewer snapshot")
 workspace.CurrentCamera={
  CFrame=CFrame.new(current,current+Vector3.new(1,0,0)),
  WorldToViewportPoint=function(self,v) return Vector3.new(160,v.Z>=current.Z and 280 or 300,3),true end,
 }
 local bank=Instance.new("Folder")
 local group=Instance.new("Folder");group.Name="EGGRUMBLE_GQ_ConfirmedHitAudio";group.Parent=bank
 local voice=Instance.new("Sound");voice.Name="ConfirmedHit_4";voice.Parent=group;voice.IsPlaying=false
 local heard={}
 function methods:Play()
  check(self==voice,"only original idle fourth voice")
  table.insert(heard,self.SoundId)
 end
 local other=game.GetService
 game.GetService=function(self,name) if name=="SoundService" then return bank end;return other(self,name) end
 local render,gui,map=surface()
 render.render(packet,character,s.world)
 local ribbon=map:FindFirstChild("CommonRouteDirection")
 check(ribbon and ribbon.Visible and ribbon.Text:find("自城",1,true) and ribbon.Text:find("帰路",1,true),
  "actual HUD distinguishes home direction and own return")
 local markers=0
 for _,m in ipairs(gui:GetChildren()) do
  if m.Name=="CommonRouteGround" and m.Visible then markers+=1 end
 end
 check(markers==2,"projected floor labels distinct and bounded")
 check(#heard==2 and heard[1]~=heard[2],"two distinct original sound assets")
 render.render(packet,character,s.world)
 check(#heard==2,"refresh never repeats a cast audio")
 local blocker=wall(s,(past+current)*.5)
 render.render(packet,character,s.world)
 local visible=0
 for _,m in ipairs(gui:GetChildren()) do
  if m.Name=="CommonRouteGround" and m.Visible then visible+=1 end
 end
 check(visible<2 and ribbon.Visible,"actual client hides floor tooltip behind cover pending server retirement")
 blocker:Destroy()
 render.render(packet,second.Character,s.world)
 check(not ribbon.Visible,"mismatched avatar safely hides")
 advanceTo(now+2.03)
 render.render(packet,character,s.world)
 check(not ribbon.Visible and #heard==2,"expired receipt cannot show or play")
 return "actual HUD projects at most two labels and a localized direction row, distinct original cues, suppresses foreign and expired payload"
end
end
