--!nocheck
-- WORLD G9 S2+ STANDALONE private Studio-only egg tag game. No S1/H1 Game, Remote, persistence, paid or client authority.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local Workspace=game:GetService("Workspace")
local Rules=require(script.Parent:WaitForChild("G9EggRules",10))
local travelWorld=Workspace:WaitForChild("G8_PRIVATE_3LEVEL_TRAVEL",25)
if not travelWorld then
 warn("G9: expected original two-script G8 three-tier server travel world not available")
 return
end
if Workspace:FindFirstChild("G9_PRIVATE_EGG_TAG_RAID") then return end
local root=Instance.new("Folder")
root.Name="G9_PRIVATE_EGG_TAG_RAID"
root:SetAttribute("PrivateStudioOnly",true)
root:SetAttribute("NoH1GameAuthority",true)
root.Parent=Workspace
local RED=Color3.fromRGB(246,104,100)
local BLUE=Color3.fromRGB(92,181,255)
local WHITE=Color3.fromRGB(248,242,222)
local GOLD=Color3.fromRGB(249,215,99)
local INK=Color3.fromRGB(39,54,82)
local state=Rules.new()
local assigned={}
local teamSizes={RED=0,BLUE=0}
local eggParts={}
local eggPrompts={}
local eggLabels={}
local scorePrompts={}
local lastMessage="敵の卵を取って、自分の色の台へ！"
local clockBucket=0
local lookoutUntil=0
local lookoutText=""
local gameToken=0

local function makePart(name,size,pos,color,collidable,material,alpha)
 local p=Instance.new("Part")
 p.Name=name
 p.Size=size
 p.Position=pos
 p.Color=color
 p.Anchored=true
 p.CanCollide=collidable==true
 p.CanTouch=false
 p.CanQuery=collidable==true
 p.CastShadow=collidable==true
 p.Material=material or Enum.Material.SmoothPlastic
 p.Transparency=alpha or 0
 p.Parent=root
 return p
end
local function billboard(part,name,text,color)
 local g=Instance.new("BillboardGui")
 g.Name=name
 g.Size=UDim2.fromOffset(235,84)
 g.StudsOffsetWorldSpace=Vector3.new(0,4,0)
 g.AlwaysOnTop=false
 g.MaxDistance=90
 g.Parent=part
 local l=Instance.new("TextLabel")
 l.Name="Text"
 l.Size=UDim2.fromScale(1,1)
 l.Text=text
 l.TextColor3=color
 l.BackgroundColor3=INK
 l.BackgroundTransparency=.1
 l.Font=Enum.Font.GothamBold
 l.TextScaled=true
 l.TextWrapped=true
 l.Parent=g
 local corner=Instance.new("UICorner")
 corner.CornerRadius=UDim.new(0,11)
 corner.Parent=l
 return l
end
local function prompt(parent,name,action,colorName)
 local p=Instance.new("ProximityPrompt")
 p.Name=name
 p.ActionText=action
 p.ObjectText=colorName
 p.KeyboardKeyCode=Enum.KeyCode.E
 p.GamepadKeyCode=Enum.KeyCode.ButtonX
 p.HoldDuration=0
 p.RequiresLineOfSight=false
 p.MaxActivationDistance=10
 p.Parent=parent
 return p
end
local banner=makePart("G9_SEA_PUBLIC_SCOREBOARD_ANCHOR",Vector3.new(1,1,1),
 Vector3.new(0,-18,184),GOLD,false,Enum.Material.SmoothPlastic,1)
local scoreboard=billboard(banner,"G9TwoTeamScore","RED 0 / 3  |  BLUE 0 / 3",WHITE)
local lobby=makePart("G9_START_PORT_TUTORIAL_ANCHOR",Vector3.new(1,1,1),
 Vector3.new(0,7,-16),GOLD,false,Enum.Material.SmoothPlastic,1)
billboard(lobby,"G9KidsRules","1 敵の卵をタップ\n2 自分の色の台へ\n3 逃げる人をタップで救出",WHITE)

local function teamOf(player)
 return assigned[player]
end
local function avatar(player)
 if not player then return nil,nil,nil end
 local character=player.Character
 if not character or not character:IsDescendantOf(Workspace) then return nil,nil,nil end
 local hum=character:FindFirstChildOfClass("Humanoid")
 local hrp=character:FindFirstChild("HumanoidRootPart")
 if not hum or hum.Health<=0 or not hrp or not hrp:IsA("BasePart") then return nil,nil,nil end
 return character,hum,hrp
end
local function dist2(a,b)
 local d=a-b
 return d:Dot(d)
end
local function carrierForEgg(eggTeam)
 for player in pairs(assigned) do
  if player.UserId==state.carrier[eggTeam] then return player end
 end
 return nil
end
local function carrierEgg(player)
 if not player then return "" end
 for _,egg in ipairs(Rules.TEAMS) do
  if state.carrier[egg]==player.UserId then return egg end
 end
 return ""
end
local function paint(message)
 if message then lastMessage=message end
 local label="RED "..state.scores.RED.." / 3   BLUE "..state.scores.BLUE.." / 3"
 if state.winner~="" then label=label.."\n"..state.winner.." の勝ち！つぎの勝負へ" end
 if state.winner=="" then
  label=label.."\n"..lastMessage
 end
 if os.clock()<lookoutUntil then label=label.."\n"..lookoutText end
 scoreboard.Text=label
 for _,egg in ipairs(Rules.TEAMS) do
  local atHome=state.home[egg]
  eggParts[egg].Transparency=if atHome then .04 else .93
  eggPrompts[egg].Enabled=atHome and state.winner==""
  eggLabels[egg].Text=if atHome then egg.." のたまご" else egg.." うばわれた！追いかけよう"
 end
 for player in pairs(assigned) do
  local carried=carrierEgg(player)
  player:SetAttribute("G9CarryingEgg",carried)
  player:SetAttribute("G9RoundWinner",state.winner)
  player:SetAttribute("G9ScoreRed",state.scores.RED)
  player:SetAttribute("G9ScoreBlue",state.scores.BLUE)
  local character=player.Character
  local hrp=character and character:FindFirstChild("HumanoidRootPart")
  if hrp then
   local tag=hrp:FindFirstChild("G9DefenderTagRescue")
   if tag and tag:IsA("ProximityPrompt") then tag.Enabled=carried~="" and state.winner=="" end
   local g=hrp:FindFirstChild("G9CarryingEggBubble")
   local l=g and g:FindFirstChild("Text")
   if l then
    l.Text=if carried~="" then "たまご運搬中！\n追いついて救出できるよ" else assigned[player].." チーム"
    l.TextColor3=if assigned[player]=="RED" then RED else BLUE
   end
  end
 end
end
local function afterAction(player,reason,team)
 if reason=="STOLEN" then
  paint(team.." が相手の卵を運んでる！")
 elseif reason=="RESCUED" then
  paint(team.." が自分の卵を救出！")
 elseif reason=="SCORED" or reason=="ROUND_WIN" then
  paint(team.." が得点！")
  if reason=="ROUND_WIN" then
   gameToken+=1
   local token=gameToken
   task.delay(6,function()
    if token~=gameToken or not root.Parent then return end
    state=Rules.new()
    lookoutUntil=0
    lookoutText=""
    paint("新しい勝負！敵の卵を取りに行こう")
   end)
  end
 end
 print("G9_REAL_STUDIO_EGG_ACTION",reason,team,player.UserId)
end
-- All egg pickups and scoring are server side, tied to its actual geometry.
for _,team in ipairs(Rules.TEAMS) do
 local x=if team=="RED" then -22 else 22
 local col=if team=="RED" then RED else BLUE
 local pedestal=makePart("G9_"..team.."_NEST",Vector3.new(12,2,12),
  Vector3.new(x,-27.1,168),col,true,Enum.Material.SmoothPlastic,.14)
 local egg=makePart("G9_"..team.."_REAL_EGG",Vector3.new(3.2,4.5,3.2),
  Vector3.new(x,-23.8,168),col,false,Enum.Material.Neon,.04)
 egg.Shape=Enum.PartType.Ball
 eggParts[team]=egg
 eggLabels[team]=billboard(egg,"G9EggName",team.." のたまご",WHITE)
 local pickup=prompt(egg,"G9EnemyEggPickup","敵の卵をとる",team.." のたまご")
 eggPrompts[team]=pickup
 pickup.Triggered:Connect(function(player)
  local actorTeam=teamOf(player)
  if not actorTeam then return end
  local _,_,hrp=avatar(player)
  if not hrp then return end
  local ok,reason=Rules.apply(state,"STEAL",actorTeam,player.UserId,team,
    dist2(hrp.Position,egg.Position),os.clock())
  if ok then afterAction(player,reason,actorTeam) end
 end)
 local pad=makePart("G9_"..team.."_SCORE_PAD",Vector3.new(15,1,12),
  Vector3.new(x,-27.4,136),col,true,Enum.Material.Neon,.18)
 billboard(pad,"G9ScoreName",team.." のゴール\n敵の卵を運ぶと得点",WHITE)
 local score=prompt(pad,"G9EggScore","自分の色の台へ",team.." のゴール")
 scorePrompts[team]=score
 score.Triggered:Connect(function(player)
  local actorTeam=teamOf(player)
  if not actorTeam then return end
  local _,_,hrp=avatar(player)
  if not hrp then return end
  local ok,reason=Rules.apply(state,"SCORE",actorTeam,player.UserId,team,
    dist2(hrp.Position,pad.Position),os.clock())
  if ok then afterAction(player,reason,actorTeam) end
 end)
end

-- Actual defender counterplay: ProximityPrompt attached to the carrier's real HumanoidRootPart.
local function installCharacter(player,character)
 task.defer(function()
  local hrp=character:WaitForChild("HumanoidRootPart",10)
  local hum=character:FindFirstChildOfClass("Humanoid") or character:WaitForChild("Humanoid",10)
  if not hrp or not hum or player.Character~=character or not root.Parent then return end
  local tag=prompt(hrp,"G9DefenderTagRescue","たまごを救出","近づいてタップ")
  tag.MaxActivationDistance=10
  tag.Enabled=false
  local label=billboard(hrp,"G9CarryingEggBubble","",WHITE)
  label.Parent.Parent.Name="G9CarryingEggBubble"
  tag.Triggered:Connect(function(rescuer)
   if rescuer==player or not teamOf(rescuer) then return end
   local egg=carrierEgg(player)
   if egg=="" or teamOf(rescuer)~=egg then return end
   local _,_,rescueRoot=avatar(rescuer)
   local _,_,carrierRoot=avatar(player)
   if not rescueRoot or not carrierRoot then return end
   local ok,reason=Rules.apply(state,"RESCUE",egg,rescuer.UserId,egg,
      dist2(rescueRoot.Position,carrierRoot.Position),os.clock())
   if ok then afterAction(rescuer,reason,egg) end
  end)
  hum.Died:Connect(function()
   local count=Rules.release(state,player.UserId)
   if count>0 then paint("たまごが元の城に戻った！") end
  end)
  paint()
 end)
end
local function assignPlayer(player)
 if assigned[player] then return end
 local team=if teamSizes.RED<=teamSizes.BLUE then "RED" else "BLUE"
 assigned[player]=team
 teamSizes[team]+=1
 player:SetAttribute("G9Team",team)
 player:SetAttribute("G9CarryingEgg","")
 player.CharacterAdded:Connect(function(character)
  local dropped=Rules.release(state,player.UserId)
  if dropped>0 then paint("たまごが城に戻った！") end
  installCharacter(player,character)
 end)
 if player.Character then installCharacter(player,player.Character) end
 paint()
 print("G9_STUDIO_TEAM_ASSIGNMENT",team,player.UserId)
end
Players.PlayerAdded:Connect(assignPlayer)
for _,player in ipairs(Players:GetPlayers()) do assignPlayer(player) end
Players.PlayerRemoving:Connect(function(player)
 local team=assigned[player]
 if not team then return end
 teamSizes[team]=math.max(0,teamSizes[team]-1)
 assigned[player]=nil
 local count=Rules.release(state,player.UserId)
 if count>0 then paint("たまごが城に戻った！") end
end)

-- A neutral lookout in SKY adds genuine useful information without speed/damage/loot.
local tower=makePart("G9_SKY_PUBLIC_LOOKOUT",Vector3.new(7,1,7),
 Vector3.new(0,49,313),GOLD,true,Enum.Material.Neon,.1)
billboard(tower,"G9SkyLookoutName","天空のみはり台\n卵を持つ人のいる階を調べる",WHITE)
local scout=prompt(tower,"G9SkyScout","だれがどの階？","全員に見える")
local lastScout=-100
scout.Triggered:Connect(function(player)
 local _,_,hrp=avatar(player)
 if not hrp then return end
 local now=os.clock()
 if now-lastScout<10 then return end
 if dist2(hrp.Position,tower.Position)>Rules.MAX_DISTANCE_SQUARED then return end
 local parts={}
 for _,egg in ipairs(Rules.TEAMS) do
  local carrier=carrierForEgg(egg)
  if carrier then
   local _,_,carryRoot=avatar(carrier)
   local zone=if not carryRoot then "みつからない"
    elseif carryRoot.Position.Z<65 then "港"
    elseif carryRoot.Position.Z<230 then "海底"
    else "天空"
   table.insert(parts,egg.." の卵→"..zone)
  end
 end
 lookoutText=if #parts==0 then "すべての卵が城にあるよ" else table.concat(parts,"  ")
 lookoutUntil=now+7
 lastScout=now
 paint()
 print("G9_SKY_SCOUT_SERVER_ONLY_USED",player.UserId)
end)
local beat=RunService.Heartbeat:Connect(function(dt)
 if not root.Parent then return end
 if type(dt)~="number" or dt<=0 or dt>.5 then return end
 clockBucket+=dt
 if clockBucket<.5 then return end
 clockBucket=0
 if Rules.expire(state,os.clock())>0 then paint("45秒！たまごは城に戻ったよ") end
 if lookoutUntil>0 and os.clock()>=lookoutUntil then
  lookoutUntil=0
  lookoutText=""
  paint()
 end
end)
script.Destroying:Connect(function()
 beat:Disconnect()
 root:Destroy()
end)
paint("敵の卵を取って、自分の台へ！")
print("G9_PRIVATE_STUDIO_2TEAM_EGG_TAG_READY", "PORT SEA SKY, win3, tag rescue, carrier ttl45")
