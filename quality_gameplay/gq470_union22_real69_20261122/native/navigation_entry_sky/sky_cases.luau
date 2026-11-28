do
local FLAG="P0D_ENABLE_PRIVATE_FAR_SKY_FACETS"
local REDUCED="EGGRUMBLE_ReducedEffects"
local NAME="EGGRUMBLE_FarSkyFacets_Local"

local function client(touch,at)
 local focusLost,focusGained=signal(),signal()
 local camera=Instance.new("Camera");camera.Name="NativeSkyCamera"
 camera.CFrame=CFrame.new(at+Vector3.new(0,7,-12));workspace.CurrentCamera=camera
 workspace._props.DescendantRemoving=signal()
 Players.LocalPlayer=player
 local service=game.GetService
 game.GetService=function(self,name)
  if name=="UserInputService" then return {TouchEnabled=touch,WindowFocusReleased=focusLost,WindowFocused=focusGained} end
  return service(self,name)
 end
 local script=Instance.new("LocalScript");script.Name="NativePhysicalSkyLOD"
 script.Parent=player:FindFirstChild("PlayerGui")
 local loaded=script
-- INSERT_PHYSICAL_ART_LOD
 return loaded,focusLost,focusGained
end

local function playing(label)
 local s=ready(label)
 local field=s.world:FindFirstChild("TacticalBattlefield")
 check(field and field.Size.X==890 and field.Size.Z==1050,"exact actual host field dimensions")
 local horizon=field.Position+Vector3.new(0,field.Size.Y*.5,0)
 local at=horizon+Vector3.new(13,3,11)
 rootPart.CFrame=CFrame.new(at)
 return s,field,horizon,at
end

local function sky()
 return workspace:FindFirstChild(NAME)
end

local function budgets(field,horizon,count,touch)
 local folder=sky()
 check(folder and folder.Parent==workspace and #folder:GetChildren()==count,"actual single bounded local folder")
 check(folder:GetAttribute("PartBudgetActual")==count and folder:GetAttribute("PartBudgetMaximum")==12
  and folder:GetAttribute("TouchReduced")==touch,"exact authored count and reduced marker")
 local tops={{212,228,231},{226,223,216},{202,222,230},{231,220,208}}
 local shades={{158,187,198},{194,181,174},{157,190,201},{196,180,176}}
 local shapes={
  Base={Vector3.new(146,16,20),0,0,.52,math.rad(-2),shades},
  CrestA={Vector3.new(100,25,14),-39,12,.36,math.rad(5),tops},
  CrestB={Vector3.new(91,19,14),43,9,.42,math.rad(-5),tops},
 }
 local seen={}
 for _,part in ipairs(folder:GetChildren()) do
  local i,label=part.Name:match("^Cloud(%d+)_(%a+)$")
  i=tonumber(i)
  local row=shapes[label]
  check(i and i<=count/3 and row and not seen[part.Name],"one original Base/Crest pair per actual bank")
  seen[part.Name]=true
  check(part:IsA("WedgePart") and part.Anchored and not part.CanCollide and not part.CanTouch and not part.CanQuery
   and not part.CastShadow and part.Material==Enum.Material.SmoothPlastic,"matte flat-cost wedges only")
  local theta=((i-1)/4)*math.pi*2+math.rad(-18)
  local radius=625+(i%3)*55
  local altitude=158+(i%3)*12
  local tangent=Vector3.new(-math.sin(theta),0,math.cos(theta))
  local at=Vector3.new(math.cos(theta)*radius,altitude,math.sin(theta)*radius)+tangent*row[2]+Vector3.new(0,row[3],0)
  check((part.Position-(horizon+at)).Magnitude<.01 and (part.Size-row[1]).Magnitude<.01
   and part.Transparency==row[4],"author geometry matches physical world translation")
  local shade=row[6][i]
  local color=Color3.fromRGB(shade[1],shade[2],shade[3])
  check(part.Color.R==color.R and part.Color.G==color.G and part.Color.B==color.B,"author exact palette")
  local conservative=.5*math.sqrt(part.Size.X^2+part.Size.Y^2+part.Size.Z^2)
  check(math.abs(at.X)-conservative>field.Size.X*.5 or math.abs(at.Z)-conservative>field.Size.Z*.5,
   "authored world-visible facets are horizontally beyond existing playable ground")
  local vertical=.5*(part.Size.Y+part.Size.X*math.abs(math.sin(row[5])))
  check(at.Y-vertical>=145,"original upper sky clearance; no overlap with real sky travel floor")
 end
 return folder
end

function growthCases.sky959_desktop()
 local s,field,horizon,at=playing("FAR_SKY_959_DESKTOP")
 client(false,at)
 advanceTo(now+1.201)
 local folder=budgets(field,horizon,12,false)
 local mirror=Instance.new("Camera");mirror.CFrame=CFrame.new(at+Vector3.new(77,23,-14));workspace.CurrentCamera=mirror
 advanceTo(now+4.801)
 check(sky()==folder and #folder:GetChildren()==12 and s.rules.phase=="ACTIVE","same arena stays one immutable sky during camera changes")
 return "desktop exact author geometry and palette at twelve nonphysical matte wedges; camera swap preserves one bank group"
end

function growthCases.sky959_touch()
 local _,field,horizon,at=playing("FAR_SKY_959_TOUCH")
 client(true,at)
 advanceTo(now+1.202)
 budgets(field,horizon,9,true)
 return "touch keeps nine owned matte wedges in three original offsets beyond the playable field"
end

function growthCases.sky959_reduced_flag()
 local _,field,horizon,at=playing("FAR_SKY_959_REDUCED")
 player:SetAttribute(REDUCED,true)
 client(false,at)
 advanceTo(now+1.201)
 check(not sky(),"ReducedEffects starts with no geometry")
 player:SetAttribute(REDUCED,false);drainDeferred()
 advanceTo(now+1.202);budgets(field,horizon,12,false)
 player:SetAttribute(REDUCED,true);drainDeferred()
 check(not sky(),"live ReducedEffects immediately destroys the group")
 workspace:SetAttribute(FLAG,false);player:SetAttribute(REDUCED,false);drainDeferred()
 advanceTo(now+2.403);check(not sky(),"independent OFF remains zero")
 workspace:SetAttribute(FLAG,true);drainDeferred();advanceTo(now+1.203)
 budgets(field,horizon,12,false)
 workspace:SetAttribute(FLAG,false);drainDeferred()
 check(not sky(),"direct rollback removes its own parts immediately")
 return "reduced effects and runtime OFF independently prevent and retire all cloud geometry"
end

function growthCases.sky959_focus()
 local _,field,horizon,at=playing("FAR_SKY_959_FOCUS")
 local mounted,lost,gained=client(false,at)
 advanceTo(now+1.202)
 local initial=budgets(field,horizon,12,false)
 lost:Fire();drainDeferred()
 check(not sky() and not initial.Parent,"background tab/window loses the old owned geometry")
 advanceTo(now+3.603);check(not sky(),"no background reallocation")
 gained:Fire();drainDeferred()
 advanceTo(now+1.202)
 check(budgets(field,horizon,12,false)~=initial,"window returns to one newly owned group")
 mounted:Destroy();drainDeferred()
 check(not sky(),"destroying the existing client script releases all owned parts and listeners")
 lost:Fire();gained:Fire();advanceTo(now+2.401)
 check(not sky(),"stale focus signals cannot recreate effects")
 return "focus loss prevents background work; focus regain and script destruction own one group lifecycle"
end

function growthCases.sky959_expiry()
 local s,field,horizon,at=playing("FAR_SKY_959_EXPIRY")
 client(false,at)
 advanceTo(now+1.202)
 budgets(field,horizon,12,false)
 s.rules.phase="FINISHED";s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED");drainDeferred()
 check(not sky(),"actual arena phase change clears old horizon")
 advanceTo(now+2.403);check(not sky(),"result phase cannot respawn cloud geometry")
 return "real arena phase expiration removes local cloud silhouettes immediately"
end

function growthCases.sky959_physical_off()
 local _,_,_,at=playing("FAR_SKY_959_PHYSICAL_OFF")
 client(false,at)
 advanceTo(now+3.603)
 check(not sky(),"unchanged physical parent has no visual owner for sky banks")
 return "exact physical OFF retains original LOD without added sky geometry"
end
end
