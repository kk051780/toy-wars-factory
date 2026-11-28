do
local FLAG="P0D_ENABLE_PRIVATE_CASTLE_APPROACH_MATTE"
local FOLDER="EGGRUMBLE_CastleApproachMatte_VisualOnly"

local function client(mobile,at)
 local camera=Instance.new("Camera");camera.Name="NativeArtCamera"
 camera.CFrame=CFrame.new(at+Vector3.new(0,7,-12));workspace.CurrentCamera=camera
 workspace._props.DescendantRemoving=signal()
 Players.LocalPlayer=player
 local service=game.GetService
 game.GetService=function(self,name)
  if name=="UserInputService" then return {TouchEnabled=mobile} end
  return service(self,name)
 end
 local script=Instance.new("LocalScript");script.Name="NativePhysicalArtDistanceLOD"
 script.Parent=player:FindFirstChild("PlayerGui")
 local loaded=script
-- INSERT_PHYSICAL_ART_LOD
 return loaded
end

local function markCount(s)
 local pieces={}
 for _,item in ipairs(s.world:GetDescendants()) do
  if item:IsA("WedgePart") and item.Parent and item.Parent.Name==FOLDER then table.insert(pieces,item) end
 end
 return pieces
end
local function active(s)
 local area=s.world:FindFirstChild("TacticalBattlefield")
 local x=area.Size.X
 check(x==890,"actual current PRIVATE tactical terrain")
 local model=s.castleModels["42"].model
 local ramp=model:FindFirstChild("CastleAccessRamp")
 local position=ramp.Position+Vector3.new(62,4,65)
 rootPart.CFrame=CFrame.new(position)
 humanoid.Health=100
 return model,ramp,area,position
end
local function wetOrOther(s,position)
 local object=Instance.new("Part")
 object.Name="NativeNonWalkableLandmark";object.Color=Color3.fromRGB(170,170,172)
 object.Size=Vector3.new(2,1,2);object.Anchored=true;object.CanCollide=true;object.CanQuery=true
 object.CFrame=CFrame.new(position);object.Parent=s.world
 return object
end

local function checkPieces(pieces,expected)
 equal(#pieces,expected,"bounded live local visual wedge allocation")
 local shown=0
 local counts={}
 for _,part in ipairs(pieces) do
  local ramp=part.Parent.Parent:FindFirstChild("CastleAccessRamp")
  check(part.Anchored and not part.CanCollide and not part.CanTouch and not part.CanQuery and not part.CastShadow,
   "source client wedge is nonphysical and shadowless")
  check(part.Material==Enum.Material.Slate and part.Reflectance==0,"author matte material")
  if part.Transparency<.01 then
   shown+=1
   check(math.abs(part.Position.X-ramp.Position.X)>ramp.Size.X*.5+1.7,
    "readable geometry remains outside existing access route")
  end
  counts[ramp]=(counts[ramp] or 0)+1
 end
 for _,count in pairs(counts) do equal(count,8,"exact two four-mark edges per selected ramp") end
 check(shown>=8,"actual floor rays admit visible wedges")
end

function growthCases.approach_touch()
 local s=ready("PRIVATE_ART_CASTLE_APPROACH_TOUCH")
 local model,ramp,arena,position=active(s)
 local gate=s.castleModels["42"].door
 local oldGate,oldRamp,oldFloor=gate.Position,ramp.Size,arena.Size
 local before=s.rules.castles["42"].hp
 local script=client(true,position)
 advanceTo(now+.19)
 checkPieces(markCount(s),16)
 check(gate.Position==oldGate and ramp.Size==oldRamp and arena.Size==oldFloor
  and gate.CanCollide==false and ramp.CanCollide and s.rules.castles["42"].hp==before,
  "actual gate and route physical sources left intact")
 check(model:FindFirstChild(FOLDER),"visible route belongs to actual same-arena castle, not fake ancestor lookup")
 script:Destroy()
 equal(#markCount(s),0,"real local script destruction disposes all wedges immediately")
 return "existing current Host CastleAccessRamp receives at most 16 touch matte marks; physical door, ramp and HP preserved"
end

function growthCases.approach_desktop()
 local s=ready("PRIVATE_ART_CASTLE_APPROACH_DESKTOP")
 local _,_,_,position=active(s)
 local script=client(false,position)
 advanceTo(now+.18)
 checkPieces(markCount(s),24)
 script:Destroy()
 return "actual opted-in desktop scene shows three nearest current castle ramp pairs, 24 max"
end

function growthCases.approach_clip_fade()
 local s=ready("PRIVATE_ART_CASTLE_APPROACH_FADE")
 local model,ramp,arena,position=active(s)
 local ground=arena.Position.Y+arena.Size.Y*.5
 local blockedPosition=Vector3.new(ramp.Position.X-7.35,ground+.45,ramp.Position.Z-9)
 local temporary=wetOrOther(s,blockedPosition)
 local script=client(true,position)
 advanceTo(now+.19)
 local folder=model:FindFirstChild(FOLDER)
 local blocked=folder and folder:FindFirstChild("ApproachEdge_-1_1")
 local visible=folder and folder:FindFirstChild("ApproachEdge_1_1")
 check(blocked and blocked.Transparency==1 and visible and visible.Transparency<.01,
  "prop cannot become accepted ground; identical clear edge remains visible")
 temporary:Destroy()
 advanceTo(now+2.62)
 check(blocked.Transparency==0,"restored exact arena floor reuses existing shape")
 local move=ramp.Position+Vector3.new(140,4,0)
 rootPart.CFrame=CFrame.new(move)
 advanceTo(now+.19)
 check(visible.Transparency>.42 and visible.Transparency<.60,"exact 125 to 155 stud alpha band")
 rootPart.CFrame=CFrame.new(ramp.Position+Vector3.new(160,4,0))
 advanceTo(now+.19)
 check(visible.Transparency==1,"visible range ends before prefetch limit")
 script:Destroy()
 return "actual floor obstruction rejects one mark, restores on requery, and applies author 125–155 stud fade"
end

function growthCases.approach_wrong_arena()
 local s=ready("PRIVATE_ART_CASTLE_APPROACH_SCOPE")
 local model,_,_,position=active(s)
 local script=client(true,position)
 local other=Instance.new("Folder");other.Name="Castle_OutsideField";other.Parent=workspace
 advanceTo(now+.19)
 check(#markCount(s)>0 and not other:FindFirstChild(FOLDER),"only exact current Host arena children")
 s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED")
 advanceTo(now+.17)
 equal(#markCount(s),0,"non-ACTIVE immediately clears local arena scenery")
 check(not model:FindFirstChild(FOLDER),"no stale result or lobby marks")
 script:Destroy()
 return "wrong/past arena and non-active result phase cannot own visible decorations"
end

function growthCases.approach_live_off()
 local s=ready("PRIVATE_ART_CASTLE_APPROACH_OFF")
 local _,_,_,position=active(s)
 local script=client(true,position)
 advanceTo(now+.19)
 check(#markCount(s)==16,"one actual current deck can roll back")
 workspace:SetAttribute(FLAG,false)
 equal(#markCount(s),0,"live flag clears created pieces synchronously")
 advanceTo(now+2.7)
 equal(#markCount(s),0,"flag OFF cannot repaint")
 script:Destroy()
 return "runtime OFF immediately clears and does not recreate wedges"
end

function growthCases.approach_physical_off()
 local s=ready("PRIVATE_ART_CASTLE_APPROACH_ANCESTOR")
 local _,_,_,position=active(s)
 local script=client(true,position)
 advanceTo(now+2.7)
 equal(#markCount(s),0,"unchanged actual predecessor contains no route decoration")
 script:Destroy()
 return "physical ancestor untouched; no new wedge state"
end
end
