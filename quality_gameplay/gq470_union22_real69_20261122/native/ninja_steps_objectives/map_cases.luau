do
local received={}
local function mapRuntime()
 local replicated=Instance.new("Folder")
 local service=game.GetService
 game.GetService=function(self,name)
  if name=="ReplicatedStorage" then return replicated end
  return service(self,name)
 end
 workspace.GetServerTimeNow=function() return now end
 function methods:FireClient(target,payload)
  check(self:IsA("RemoteEvent") and self.Name=="EGGRUMBLE_MapIntelUpdate_V1","actual existing MapIntel sender only")
  received[target]=payload
 end
 dependencies.EGGRUMBLE_MapVisibilityPolicy=(function()
-- INSERT_MAP_POLICY
 end)()
 local function activateMap()
-- INSERT_MAP_BRIDGE
 end
 activateMap()
end
local function actualMap(s,p,castle)
 local model=s.castleModels[tostring(p.UserId)].model
 local center=model:FindFirstChild("StandardFoundation")
 local deposit=model:FindFirstChild("OwnEggDeposit")
 check(deposit and center,"actual current Host created exact deposit/foundation")
 if castle~=nil then check(model==castle,"official same viewer castle") end
 local root=p.Character:FindFirstChild("HumanoidRootPart")
 root.CFrame=CFrame.new(center.Position+Vector3.new(3,5,2))
 return center,deposit
end
local function mapStep()
 RunService.Heartbeat:Fire(.91)
end
local function get(s,id)
 for _,m in ipairs(s.markers) do if m.id==id then return m end end
 return nil
end
local function tally(s)
 local ids={};local n=0
 for _,m in ipairs(s.markers) do
  check(not ids[m.id] and not m.rayFrom and not m.rayTo and not m.sourceModel,"existing public IDs are unique and ray/host inputs private")
  ids[m.id]=true;n+=1
 end
 check(n<=30 and #s.explored<=500,"existing marker and exploration payload budgets")
 return n
end
local function sameXZ(m,point)
 return m and math.abs(m.x-point.Position.X)<.001 and math.abs(m.z-point.Position.Z)<.001
end
local function rgb(c,r,g,b)
 local expected=Color3.fromRGB(r,g,b)
 return c.R==expected.R and c.G==expected.G and c.B==expected.B
end
local function clientSurface(expanded)
 local mapExpanded=expanded
 local canvas=Instance.new("Frame");canvas.AbsoluteSize=Vector2.new(160,115)
 local mapTitle=Instance.new("TextLabel")
 local layerButton=Instance.new("TextButton")
 local function rounded() end -- no effect on measured existing label shape/position
 local function closeDrawer() end
 local function refreshMapLayout() end
 local remote={OnClientEvent=signal()}
-- INSERT_MAP_REDRAW
-- INSERT_MAP_EVENT
 return {publish=function(payload) remote.OnClientEvent:Fire(payload) end,
  markers=markerPool,title=mapTitle}
end
local function label(view,text)
 for _,pin in ipairs(view.markers) do if pin.Visible and pin.Text==text then return pin end end
 return nil
end

function growthCases.minimap_team()
 local round=ready("PRIVATE_MINIMAP_TEAM")
 local a,d=actualMap(round,player)
 local b,e=actualMap(round,second)
 check(a.Position.X~=d.Position.X and b.Position.X~=e.Position.X,"deposit is separate from original castle center")
 mapRuntime();mapStep()
 local first,other=received[player],received[second]
 check(first and other and first.ownDeposit and other.ownDeposit and first.ownCastle~=other.ownCastle,"both exact own destinations server confirmed")
 check(sameXZ(get(first,first.ownCastle),d) and sameXZ(get(other,other.ownCastle),e),"each published own pin on actual contact")
 check(sameXZ(get(first,other.ownCastle),b) and sameXZ(get(other,first.ownCastle),a),"peer castle markers stay at public center")
 tally(first);tally(other)
 local view=clientSurface(false)
 view.publish(first)
 local owned=label(view,"納")
 check(owned and rgb(owned.BackgroundColor3,37,101,82) and owned.ZIndex==8 and owned.TextSize==11,
  "actual narrow existing renderer tells gold egg from own jade deposit")
 check(owned.Size.X.Offset==20 and owned.BackgroundTransparency==.02,"same narrow button footprint and opaque color")
 check(view.title.Text=="地図・陸","exact author localized compact map title")
 local expanded=clientSurface(true);expanded.publish(first)
 check(label(expanded,"納入")~=nil,"existing larger map shows full deposit label")
 return "actual TEAM per-recipient map sends each own deposit coordinates and no other deposit; same client pin rendered"
end

function growthCases.minimap_missing()
 local round=ready("PRIVATE_MINIMAP_MISSING")
 local center,deposit=actualMap(round,player)
 actualMap(round,second)
 local prompt=deposit:FindFirstChildOfClass("ProximityPrompt")
 mapRuntime();mapStep()
 check(received[player] and received[player].ownDeposit,"existing actionable destination before OFF")
 prompt.Enabled=false
 mapStep()
 local snapshot=received[player]
 check(snapshot and snapshot.ownDeposit==false and sameXZ(get(snapshot,snapshot.ownCastle),center),
  "no valid deposit prompt falls back to actual public castle center")
 local surface=clientSurface(false);surface.publish(snapshot)
 check(not label(surface,"納") and label(surface,"城"),"new label is never fabricated")
 player:SetAttribute("EGGRUMBLE_Eliminated",true)
 mapStep()
 local reset=received[player]
 check(reset.kind=="MAP_RESET","same existing invalid-player reset")
 surface.publish(reset)
 for _,pin in ipairs(surface.markers) do check(not pin.Visible,"existing reset hides all stale locations") end
 return "disabled real destination remains ordinary castle and elimination cleared all stale markers"
end

function growthCases.minimap_egg_visibility()
 local round=ready("PRIVATE_MINIMAP_FIELD_EGG")
 actualMap(round,player)
 actualMap(round,second)
 mapRuntime();mapStep()
 local first=received[player]
 check(first and first.ownDeposit,"actual initial map anchor")
 local origin=rootPart.Position
 local nearest=nil
 local best=math.huge
 for _,child in ipairs(round.world:GetChildren()) do
  if child:IsA("BasePart") and child.Name:match("^FieldEgg_%d+$") and not get(first,child.Name) then
   local dist=(child.Position-origin).Magnitude
   if dist<best then nearest=child;best=dist end
  end
 end
 check(nearest,"actual Host spawned an undisclosed egg, not a synthetic marker")
 local at=nearest.Position+Vector3.new(0,2,0)
 local steps=math.ceil((at-origin).Magnitude/100)
 for step=1,steps do
  rootPart.CFrame=CFrame.new(origin+(at-origin)*(step/steps))
  mapStep()
 end
 local real=received[player]
 check(real and real.ownDeposit and get(real,nearest.Name) and get(real,nearest.Name).kind=="EGG",
  "existing server fog independently published after physical exploration")
 tally(real)
 local view=clientSurface(true);view.publish(real)
 local egg=label(view,"卵")
 local home=label(view,"納入")
 check(egg and home and rgb(egg.BackgroundColor3,136,100,40) and egg.ZIndex==8
   and egg.Text~=home.Text,"egg has actual distinct gold glyph fill")
 return "current Host remote filters a real unexplored egg, then publishes gold only after real explored positions"
end

function growthCases.minimap_br()
 local round=growthCases.readySoloBR()
 local _,deposit=actualMap(round,player)
 mapRuntime();mapStep()
 local s=received[player]
 check(s and s.mode=="BATTLE_ROYALE" and s.ownDeposit and sameXZ(get(s,s.ownCastle),deposit),
  "actual one-player BR own contact")
 check(received[second]==nil,"none sent to nonmember peer")
 return "same authenticated current solo BR owned deposit and no client payload to nonmember"
end

function growthCases.minimap_physical_off()
 local round=ready("PRIVATE_MINIMAP_ANCESTOR")
 local center=actualMap(round,player)
 actualMap(round,second)
 mapRuntime();mapStep()
 local first=received[player]
 check(first and first.ownDeposit==nil and sameXZ(get(first,first.ownCastle),center),"exact physical ancestor still sends castle center")
 local old=clientSurface(false);old.publish(first)
 check(label(old,"城") and not label(old,"納"),"exact old client body untouched")
 return "physical parent preserved same public castle format, old color, and no deposit marker"
end
end
