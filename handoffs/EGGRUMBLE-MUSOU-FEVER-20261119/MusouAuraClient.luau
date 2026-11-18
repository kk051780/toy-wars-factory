--!strict
-- GQ8 #824 OPTIONAL VFX MODULE. Cosmetic-only; never awards KO/damage/charges.
-- Must run in each observing client from the EXISTING server replicated Musou snapshot.
-- No client-owned network channel; cosmetics reflect only server-owned attributes.
local RunService=game:GetService("RunService")
local M={}
local FOLDER="EGGRUMBLE_MUSOU_OBSERVER_AURA"
local DESIGN={
 WARRIOR={color=Color3.fromRGB(255,214,66),edge=Color3.fromRGB(255,255,244),
  name="神威・黄金天輪",symbol="✦",spin=5},
 MAGE={color=Color3.fromRGB(71,223,255),edge=Color3.fromRGB(255,123,244),
  name="元素・虹彩星群",symbol="✧",spin=4},
 NINJA={color=Color3.fromRGB(245,56,88),edge=Color3.fromRGB(31,15,54),
  name="暗殺者・紅影連斬",symbol="✕",spin=7},
 TRAPPER={color=Color3.fromRGB(159,94,250),edge=Color3.fromRGB(104,231,247),
  name="超能力・重力六角陣",symbol="⬡",spin=4},
 BUILDER={color=Color3.fromRGB(255,160,55),edge=Color3.fromRGB(250,239,118),
  name="超機械・電磁歯車",symbol="⚙",spin=5},
 BEAST={color=Color3.fromRGB(59,237,149),edge=Color3.fromRGB(228,234,122),
  name="獣王・咆哮",symbol="◆",spin=5},
 ZOMBIE={color=Color3.fromRGB(151,59,243),edge=Color3.fromRGB(220,150,250),
  name="冥王・呪魂螺旋",symbol="☾",spin=4},
}
local function validSnapshot(s)
 return type(s)=="table" and s.active==true
  and DESIGN[s.role]~=nil
  and (s.phase=="MUSOU" or s.phase=="RUSH" or s.phase=="KAKUHEN")
  and type(s.remaining)=="number" and s.remaining==s.remaining and s.remaining>0
end
local function clean(character)
 local head=character:FindFirstChild("Head")
 if head then
  local origin=head:FindFirstChild("MusouAuraOrigin")
  if origin then origin:Destroy() end
 end
 local old=character:FindFirstChild(FOLDER)
 if old then old:Destroy() end
end
local function phaseText(p)
 if p=="KAKUHEN" then return "確変覚醒"
 elseif p=="RUSH" then return "連チャン無双" end
 return "無双覚醒"
end
local function localViewDist(head)
 local camera=workspace.CurrentCamera
 if not camera then return math.huge end
 return (camera.CFrame.Position-head.Position).Magnitude
end
function M.stop(character)
 if not RunService:IsClient() or not character then return end
 clean(character)
end
function M.start(character,snapshot)
 if not RunService:IsClient() or not character or not validSnapshot(snapshot) then return false end
 local head=character:FindFirstChild("Head")
 if not head or not head:IsA("BasePart") then return false end
 clean(character)
 local d=DESIGN[snapshot.role]
 local folder=Instance.new("Folder")
 folder.Name=FOLDER
 folder.Parent=character
 -- Everyone sees a high-contrast state. No full screen FX / flash / chromatic pulsing.
 local h=Instance.new("Highlight")
 h.Name="MusouHeroOutline"
 h.Adornee=character
 h.DepthMode=Enum.HighlightDepthMode.Occluded
 h.FillColor=d.color
 h.OutlineColor=d.edge
 h.FillTransparency=.7
 h.OutlineTransparency=0
 h.Parent=folder
 local gui=Instance.new("BillboardGui")
 gui.Name="MusouEnemyVisibleNameplate"
 gui.Adornee=head
 gui.AlwaysOnTop=false
 gui.Size=UDim2.fromOffset(195,54)
 gui.StudsOffsetWorldSpace=Vector3.new(0,3.35,0)
 gui.MaxDistance=160
 gui.Parent=folder
 local label=Instance.new("TextLabel")
 label.Name="State"
 label.BackgroundTransparency=1
 label.TextScaled=true
 label.Font=Enum.Font.GothamBlack
 label.TextColor3=d.color
 label.TextStrokeColor3=Color3.new(0,0,0)
 label.TextStrokeTransparency=.1
 label.Text=d.symbol.." "..phaseText(snapshot.phase).." "..d.symbol
 label.Size=UDim2.fromScale(1,1)
 label.Parent=gui
 -- One low-cost particle fountain instead of 7 parallel emitters / screen shaders.
 local a=Instance.new("Attachment")
 a.Name="MusouAuraOrigin"
 a.Parent=head
 local particles=Instance.new("ParticleEmitter")
 particles.Name="RoleAura"
 particles.Texture="rbxasset://textures/particles/sparkles_main.dds"
 particles.Color=ColorSequence.new(d.color,d.edge)
 particles.LightEmission=.7
 particles.Rate=12
 particles.Speed=NumberRange.new(1.2,2.8)
 particles.Drag=2
 particles.SpreadAngle=Vector2.new(180,180)
 particles.Lifetime=NumberRange.new(.35,.7)
 particles.Size=NumberSequence.new({
  NumberSequenceKeypoint.new(0,.42),
  NumberSequenceKeypoint.new(.7,.25),
  NumberSequenceKeypoint.new(1,0)
 })
 particles.Enabled=true
 particles.Parent=a
 -- Particle emitter lives on the Head; retain its attachment pointer for cleanup.
 folder:SetAttribute("RoleId",snapshot.role)
 folder:SetAttribute("Mode",snapshot.phase)
 folder:SetAttribute("ClientCosmeticOnly",true)
 particles:Emit(snapshot.phase=="KAKUHEN" and 18 or 8)
 -- Manually destroy the Head attachment on stop (it is not a folder child).
 return true
end
function M.update(character,snapshot)
 if not RunService:IsClient() or not character then return end
 local folder=character:FindFirstChild(FOLDER)
 if not validSnapshot(snapshot) then
  if folder then clean(character) end
  return
 end
 if not folder or folder:GetAttribute("RoleId")~=snapshot.role then
  M.start(character,snapshot)
  folder=character:FindFirstChild(FOLDER)
 end
 if not folder then return end
 local d=DESIGN[snapshot.role]
 local h=folder:FindFirstChild("MusouHeroOutline")
 local gui=folder:FindFirstChild("MusouEnemyVisibleNameplate")
 if h then h.FillTransparency=snapshot.phase=="KAKUHEN" and .42 or .7 end
 if gui then
  local label=gui:FindFirstChild("State")
  if label then
   label.Text=d.symbol.." "..phaseText(snapshot.phase).." "..d.symbol
  end
 end
 local head=character:FindFirstChild("Head")
 if head then
  local a=head:FindFirstChild("MusouAuraOrigin")
  local particles=if a then a:FindFirstChild("RoleAura") else nil
  if particles then
   local previous=folder:GetAttribute("Mode")
   if previous~=snapshot.phase then
    particles:Emit(snapshot.phase=="KAKUHEN" and 28 or 12)
   end
   local dist=localViewDist(head)
   local rate=if snapshot.phase=="KAKUHEN" then 24 else 12
   particles.Rate=if dist<=85 then rate elseif dist<=140 then 5 else 0
  end
 end
 folder:SetAttribute("Mode",snapshot.phase)
end
-- Integration calls M.update(character, trustedServerSnapshot) for every observing player.
-- It must call M.stop on character removal and cleanup Head/MusouAuraOrigin.
return M
