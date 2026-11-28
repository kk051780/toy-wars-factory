do
local FLAG="P0D_ENABLE_PRIVATE_FOREST_BIOMES_421"
local FOLDER="EGGRUMBLE_FlagshipLandscape_VisualOnly"

local propertyChanges={}
function methods:GetPropertyChangedSignal(property)
 local byProperty=propertyChanges[self]
 if not byProperty then byProperty={};propertyChanges[self]=byProperty end
 if not byProperty[property] then byProperty[property]=signal() end
 return byProperty[property]
end
local previousWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,property,value)
 local before=self._props[property]
 previousWrite(self,property,value)
 local changes=propertyChanges[self]
 if before~=value and changes and changes[property] then changes[property]:Fire() end
end

local function artRuntime()
 local fromRGB=Color3.fromRGB
 local Color3={fromRGB=function(r,g,b)
  local result=fromRGB(r,g,b)
  result.Lerp=function(first,last,blend)
   return {R=first.R+(last.R-first.R)*blend,G=first.G+(last.G-first.G)*blend,
    B=first.B+(last.B-first.B)*blend}
  end
  return result
 end}
-- INSERT_SELECTED_FIELD_ART
end

local function paint(label,flag)
 if flag~=nil then workspace:SetAttribute(FLAG,flag) end
 local s=ready(label)
 s.world.Destroying.Once=function(event,callback)
  local connection
  connection=event:Connect(function(...)
   connection:Disconnect()
   callback(...)
  end)
  return connection
 end
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local gate=s.castleModels["42"].door
 local old={
  hp=s.rules.castles["42"].hp,eggs=s.rules.castles["42"].vaultEggs,phase=s.rules.phase,
  floor=floor.Size,gate=gate.CFrame,collide=gate.CanCollide,
 }
 artRuntime()
 advanceTo(now+.025)
 local art=s.world:FindFirstChild(FOLDER)
 check(art and art.Parent==s.world,"existing exact arena art source executed")
 check(s.rules.castles["42"].hp==old.hp and s.rules.castles["42"].vaultEggs==old.eggs
  and s.rules.phase==old.phase and floor.Size==old.floor and gate.CFrame==old.gate
  and gate.CanCollide==old.collide,"actual HP, real eggs, win phase and collision properties untouched")
 return s,art,floor
end

local function crest(color,red,green,blue)
 local expected=Color3.fromRGB(red,green,blue)
 return color.R==expected.R and color.G==expected.G and color.B==expected.B
end
local function measure(s,art)
 local artParts,wedgeParts,grassParts,slateParts={},0,0,0
 for _,p in ipairs(s.world:GetDescendants()) do
  if p:IsA("BasePart") and p.Name:sub(1,4)=="ART_"
   and (p:IsDescendantOf(art) or p.Parent.Name=="EGGRUMBLE_CastleArt_VisualOnly") then
   check(p.Anchored and not p.CanCollide and not p.CanQuery and not p.CanTouch and not p.CastShadow,
    "all actual decoration remains non-physical and shadowless")
   check(p.Transparency==0,"no new transparency draw in forest")
   table.insert(artParts,p)
   if p:IsA("WedgePart") then wedgeParts+=1 end
   if p.Material==Enum.Material.Grass then grassParts+=1 end
   if p.Material==Enum.Material.Slate then slateParts+=1 end
  end
 end
 local pathParts,canopies,rocks,gates={},0,0,{}
 for _,p in ipairs(art:GetChildren()) do
  if not p:IsA("BasePart") then continue end
  if p.Name:find("^ART_Canopy") then canopies+=1 end
  if p.Name:find("^ART_Boulder") then rocks+=1 end
  local id=p.Name:match("^ART_AncientForestGate_(%d+)_")
  if id then gates[id]=(gates[id] or 0)+1 end
  if p.Name:find("^ART_Waystone") or p.Name:find("^ART_LaneIdentity") or p.Name:find("^ART_RuinedArch") then
   table.insert(pathParts,p)
  end
 end
 local routeParts=#pathParts
 equal(canopies,60,"existing 20 trees retain 3 crowns apiece")
 equal(routeParts,40,"original road/waystones/central ruin shape count")
 check(#artParts<=320,"actual 320 per-arena global art cap")
 local function Vec(v)
  return ("%0.3f,%0.3f,%0.3f"):format(v.X,v.Y,v.Z)
 end
 local routeMap={}
 for _,piece in ipairs(pathParts) do
  table.insert(routeMap,piece.Name.."@"..Vec(piece.Position).."@"..Vec(piece.Size))
 end
 table.sort(routeMap)
 fixturePrint("ART_BUDGET\t"..#artParts.."\t"..wedgeParts.."\t"..grassParts.."\t"..slateParts)
 fixturePrint("ART_ROUTE\t"..table.concat(routeMap,"|"))
 return gates,rocks
end

function growthCases.forest421_on()
 local s,art,floor=paint("PRIVATE_FOREST_421",nil)
 local gates,rocks=measure(s,art)
 equal(rocks,4,"existing middle rocky cluster remains")
 local count=0;local north=0;local south=0
 for id,parts in pairs(gates) do
  equal(parts,4,"exact same primitive budget per new gate")
  local key=art:FindFirstChild("ART_AncientForestGate_"..id.."_Keystone")
  check(key and key:IsA("WedgePart") and key.Material==Enum.Material.Slate,
   "actual matte keystone uses the existing Slate primitive")
  check(math.abs(key.Position.X-floor.Position.X)>=315,"gates stay on existing outer flank")
  if key.Position.Z<floor.Position.Z then
   check(crest(key.Color,143,220,203),"author teal northern landmark");north+=1
  else
   check(crest(key.Color,230,180,218),"author opaque rose southern landmark");south+=1
  end
  count+=1
 end
 check(count==4 and north==2 and south==2,"two gateways in each real direction")
 local n=art:FindFirstChild("ART_Canopy1_3")
 local k=art:FindFirstChild("ART_Canopy10_3")
 check(n and k and crest(n.Color,166,201,185) and crest(k.Color,199,164,190)
  and n.Size.X<4.5 and k.Size.X<4.5,"existing named art crowns carry real pale two-biome tint")
 return "two exact biome palettes and four opaque ancient gate silhouettes replace old pieces on real same Host field"
end

local function unchanged(label,flag)
 local s,art=paint(label,flag)
 local gates,rocks=measure(s,art)
 check(next(gates)==nil and rocks==20,"legacy exact boulder groups present")
 local n=art:FindFirstChild("ART_Canopy1_3")
 local k=art:FindFirstChild("ART_Canopy10_3")
 check(crest(n.Color,91,134,94) and crest(k.Color,69,109,80)
  and math.abs(n.Size.X-4.5)<.001 and math.abs(k.Size.X-4.5)<.001,"legacy crown bodies and palette")
end
function growthCases.forest421_flag_off()
 unchanged("PRIVATE_FOREST_421_FLAG_OFF",false)
 return "runtime flag false on arena creation restores the original forest without changing source owners"
end
function growthCases.forest421_physical_off()
 unchanged("PRIVATE_FOREST_421_PHYSICAL_OFF",nil)
 return "byte exact prior FieldArt has original forest, same route marks and baseline scene allocation"
end
end
