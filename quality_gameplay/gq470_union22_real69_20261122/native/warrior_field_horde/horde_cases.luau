do
local function equal(value,wanted,message)
 check(value==wanted,message.." actual="..tostring(value).." expected="..tostring(wanted))
end

local species={
 ACORN_IMP={"Part",Enum.Material.Wood},
 BABY_GOLEM={"WedgePart",Enum.Material.Slate},
 BANNER_KNIGHT={"WedgePart",Enum.Material.Slate},
 ICE_SLIME={"Part",Enum.Material.SmoothPlastic},
 SHY_WRAITH={"WedgePart",Enum.Material.Fabric},
 SPARK_GOBLIN={"WedgePart",Enum.Material.Slate},
 SPIKE_BOAR={"Part",Enum.Material.Slate},
 TINY_SHIELD={"WedgePart",Enum.Material.Slate},
}

local function roster(s)
 spawnCurrentNeutral(s)
 local field=s.world:FindFirstChild("TacticalBattlefield")
 local parking=field.Position+Vector3.new(2,field.Size.Y*.5+3,10)
 local horde=s.world:FindFirstChild("NeutralHorde")
 local rows={}
 local count=0
 for _=1,45 do
  for _,m in ipairs(horde:GetChildren()) do
   local id=m:GetAttribute("EGGRUMBLE_NeutralSpecies")
   if id and not rows[id] then
    local hp=m:FindFirstChildOfClass("Humanoid")
    if hp and hp.Health>0 then
     local at=m.PrimaryPart.Position
     rows[id]={model=m,speed=m:GetAttribute("EGGRUMBLE_NeutralSpeed"),
      headOffset=m:FindFirstChild("Head").Position-at,
      accentOffset=m:FindFirstChild("SpeciesAccent").Position-at}
     count+=1
     m:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
     m:PivotTo(CFrame.new(parking))
    end
   end
  end
  if count==8 then break end
  advanceTo(now+.27)
 end
 equal(count,8,"actual Swarm wave spawns every original species")
 return rows
end

local function vectorFingerprint(v)
 return string.format("%.4f,%.4f,%.4f",v.X,v.Y,v.Z)
end

local function inspect(isOn)
 local s=ready("PRIVATE_HORDE_951")
 local rows=roster(s)
 local rigRows={}
 local wedges=0
 for id,expected in pairs(species) do
  local row=rows[id]
  local m=row.model
  local humanoid=m:FindFirstChildOfClass("Humanoid")
  local root=m:FindFirstChild("HumanoidRootPart")
  local head=m:FindFirstChild("Head")
  local accent=m:FindFirstChild("SpeciesAccent")
  local profile=dependencies.EGGRUMBLE_NeutralFinisherPolicy.species(id)
  check(profile and row.speed>0 and m:GetAttribute("EGGRUMBLE_NeutralPersonality")==profile.personality
   and m:GetAttribute("EGGRUMBLE_NeutralReaction")==profile.motion,"actual AI identity "..id)
  equal(humanoid.Health,32,"same live HP "..id)
  equal(humanoid.MaxHealth,32,"same max HP "..id)
  equal(humanoid.NameDisplayDistance,0,"internal label hidden "..id)
  equal(humanoid.HealthDisplayDistance,16,"same near HP label "..id)
  equal(humanoid.DisplayDistanceType,Enum.HumanoidDisplayDistanceType.Subject,"NPC-owned HP label "..id)
  equal(m.PrimaryPart,root,"canonical movement and damage root "..id)
  local count=0
  for _,p in ipairs(m:GetChildren()) do
   if p:IsA("BasePart") then count+=1 end
  end
  equal(count,3,"three physical parts "..id)
  for _,p in ipairs({root,head,accent}) do
   check(p.Anchored and not p.CanCollide,"same anchored/noncollidable presentation "..id)
   if isOn then equal(p.CastShadow,false,"candidate part remains cheap "..id) end
  end
  equal(root.CanTouch,false,"root touch remains off "..id)
  equal(head.CanTouch,false,"head touch remains off "..id)
  equal(accent.ClassName,if isOn then expected[1] else "Part","exact authored accent "..id)
  equal(root.Material,if isOn then expected[2] else Enum.Material.SmoothPlastic,"original/accent material "..id)
  equal(head.Material,Enum.Material.SmoothPlastic,"same head material "..id)
  local fabric=id=="SHY_WRAITH" or id=="BANNER_KNIGHT"
  equal(accent.Material,if not isOn then Enum.Material.SmoothPlastic elseif fabric then Enum.Material.Fabric else Enum.Material.Slate,
   "exact authored accent material "..id)
  if accent:IsA("WedgePart") then wedges+=1 end
  table.insert(rigRows,table.concat({id,row.speed,profile.personality,profile.motion,
   vectorFingerprint(root.Size),vectorFingerprint(head.Size),vectorFingerprint(accent.Size),
   vectorFingerprint(row.headOffset),vectorFingerprint(row.accentOffset)},"/"))
 end
 equal(wedges,if isOn then 5 else 0,"new WedgeParts only replace previous accent Parts")
 table.sort(rigRows)
 return table.concat(rigRows,";")
end

function growthCases.horde951_shapes()
 return "rig="..inspect(true)
end

function growthCases.horde951_physical_off()
 return "rig="..inspect(false)
end

function growthCases.horde951_reaction()
 local s=ready("PRIVATE_HORDE_951_REACTION")
 local m=roster(s).BANNER_KNIGHT.model
 local h=m:FindFirstChildOfClass("Humanoid")
 local accent=m:FindFirstChild("SpeciesAccent")
 equal(accent.ClassName,"WedgePart","reaction exercises the changed visual class")
 local start=accent.Size
 local from=clearNeutralApproach(m,m.PrimaryPart.Position)
 rootPart.CFrame=CFrame.new((from.Position+m.PrimaryPart.Position)*.5,m.PrimaryPart.Position)
 m:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
 local function strike(amount)
  return s.swarm.damageFromPlayer(player,m.PrimaryPart.Position,.1,amount,"CIRCLE",nil,m,
   rootPart.Position+Vector3.new(0,1,0))
 end
 local wall=Instance.new("Part")
 wall.Name="NativeHorde951Wall"
 wall.Anchored=true;wall.CanQuery=true;wall.CanCollide=true
 wall.Size=Vector3.new(5,8,5)
 wall.CFrame=CFrame.new((rootPart.Position+m.PrimaryPart.Position)*.5)
 wall.Parent=s.world
 equal(strike(5),0,"solid cover blocks the same authorized neutral")
 equal(h.Health,32,"blocked strike leaves real HP")
 check(not m:GetAttribute("EGGRUMBLE_NeutralHitSerial") and not m:GetAttribute("EGGRUMBLE_MotionSerial"),
  "blocked strike leaves no hit or reaction cue")
 wall:Destroy()
 equal(strike(5),1,"exact live Swarm hit")
 equal(h.Health,27,"real server HP 32 to 27")
 check(m:GetAttribute("EGGRUMBLE_NeutralHitSerial") and m:GetAttribute("EGGRUMBLE_MotionSerial")
  and accent.Size.Magnitude>start.Magnitude,"one hit animated original live accent")
 advanceTo(now+.21)
 check((accent.Size-start).Magnitude<.0001 and m:FindFirstChild("SpeciesAccent")==accent,
  "original reaction pulse returns to original dimensions without allocating a piece")
 local count=s.swarm.getTotal()
 equal(strike(40),1,"exact same living target has a single lethal strike")
 equal(s.swarm.getTotal(),count+1,"one actual KO")
 equal(strike(40),0,"dead target cannot be damaged or credited")
 equal(s.swarm.getTotal(),count+1,"dead target cannot produce a second KO")
 return "solid wall gives no HP/cue; real accepted strike 32→27 HP + existing accent pulse, one credited KO + rejected duplicate"
end

function growthCases.horde951_guardian_regression()
 local s=ready("PRIVATE_HORDE_951_GUARDIAN_READY")
 guardianHit(s,"PRIVATE_HORDE_951_GUARDIAN")
 return "real siege prompts start WARRIOR guard; MAGE Tool A changes actual guardian 110→80 HP"
end
end
