--!strict
-- #765 lane2: additive, local-only, no network emitters or damage/HP/score writers.
-- No permanent HUD panels. The only trigger is the server's optional visual cue.
local Players=game:GetService("Players")
local UserInputService=game:GetService("UserInputService")
local TweenService=game:GetService("TweenService")
local Debris=game:GetService("Debris")
local Cue=require(script.Parent:WaitForChild("EGGRUMBLE_ElementCueSpec"))
local LOW=UserInputService.TouchEnabled
local ATTRIBUTE="EGGRUMBLE_VisualCue"
local LIMIT=6
local active=0
local lastSeq:{[Player]:number}={}
local lastAt:{[Player]:number}={}
local listeners:{[Player]:RBXScriptConnection}={}
local function render(p:Player)
 local cue=Cue.parse(p:GetAttribute(ATTRIBUTE),LOW)
 if not cue or cue.sequence<=(lastSeq[p] or 0) then return end
 -- Never replay a stale sequence after an avatar dies or a packet is duplicated.
 lastSeq[p]=cue.sequence
 local now=os.clock()
 if now-(lastAt[p] or -100)<.10 or active>=LIMIT then return end
 local char=p.Character
 local root=char and char:FindFirstChild("HumanoidRootPart")
 local hum=char and char:FindFirstChildOfClass("Humanoid")
 local camera=workspace.CurrentCamera
 if not root or not root:IsA("BasePart") or not hum or hum.Health<=0
  or not camera or (camera.CFrame.Position-root.Position).Magnitude>cue.range then return end
 lastAt[p]=now
 active+=1
 task.delay(cue.lifetime,function() active=math.max(0,active-1) end)
 local center=root.CFrame*CFrame.new(0,2.1,-2.7)
 local tint=Color3.fromRGB(cue.rgb[1],cue.rgb[2],cue.rgb[3])
 for i=1,cue.parts do
  local piece:BasePart
  if cue.shape=="FORK" or cue.shape=="SHARD" or cue.shape=="CRYSTAL"
   or cue.shape=="PINWHEEL" then
   piece=Instance.new("WedgePart")
  else
   piece=Instance.new("Part")
  end
  piece.Name="EGGRUMBLE_TemporaryElementCue"
  piece.Anchored=true
  piece.CanCollide=false
  piece.CanTouch=false
  piece.CanQuery=false
  piece.CastShadow=false
  piece.Material=Enum.Material.SmoothPlastic
  piece.Color=tint
  piece.Transparency=.18
  local angle=(i-1)*math.pi*2/cue.parts
  local radial=cue.shape=="HALO" and .9 or .48
  local offset=CFrame.new(math.cos(angle)*radial,math.sin(angle)*.4,math.sin(angle)*radial)
  if cue.shape=="RINGS" or cue.shape=="HALO" then
   (piece::Part).Shape=Enum.PartType.Cylinder
   piece.Size=Vector3.new(.16,1.12,1.12)
   piece.CFrame=center*offset*CFrame.Angles(0,0,math.pi/2)
  elseif cue.shape=="BOLT" or cue.shape=="CHAIN" then
   piece.Size=Vector3.new(.24,1.35,.24)
   piece.CFrame=center*offset*CFrame.Angles(0,0,angle+.55)
  elseif cue.shape=="FORK" then
   piece.Size=Vector3.new(.34,1.35,.35)
   piece.CFrame=center*offset*CFrame.Angles(0,angle,.30)
  elseif cue.shape=="PINWHEEL" then
   piece.Size=Vector3.new(.35,.8,.2)
   piece.CFrame=center*offset*CFrame.Angles(.4,angle,.6)
  elseif cue.shape=="SHARD" then
   piece.Size=Vector3.new(.65,.9,.55)
   piece.CFrame=center*offset*CFrame.Angles(.35,angle,.32)
  else
   piece.Size=Vector3.new(.38,1.06,.38)
   piece.CFrame=center*offset*CFrame.Angles(.75,angle,.6)
  end
  piece.Parent=workspace
  TweenService:Create(piece,TweenInfo.new(cue.lifetime,Enum.EasingStyle.Quad,
   Enum.EasingDirection.Out),{Transparency=1,Size=piece.Size*.22,
   CFrame=piece.CFrame*CFrame.new(0,.4,0)}):Play()
  Debris:AddItem(piece,cue.lifetime+.08)
 end
 -- Brief, distance-limited, readable text: no permanent screen overlay.
 local anchor=Instance.new("Part")
 anchor.Name="EGGRUMBLE_TemporaryCueLabelAnchor"
 anchor.Anchored=true
 anchor.Transparency=1
 anchor.CanCollide=false
 anchor.CanTouch=false
 anchor.CanQuery=false
 anchor.Size=Vector3.new(.1,.1,.1)
 anchor.CFrame=center*CFrame.new(0,1.3,0)
 anchor.Parent=workspace
 local bb=Instance.new("BillboardGui")
 bb.Name="EGGRUMBLE_TemporaryOutcome"
 bb.Size=UDim2.fromOffset(112,28)
 bb.AlwaysOnTop=false
 bb.MaxDistance=cue.range
 bb.Adornee=anchor
 bb.Parent=anchor
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1)
 label.BackgroundTransparency=1
 label.Font=Enum.Font.GothamBold
 label.TextScaled=true
 label.TextColor3=tint
 label.TextStrokeTransparency=.25
 label.Text=cue.text.." "..cue.outcomeSymbol
 label.Parent=bb
 Debris:AddItem(anchor,cue.lifetime+.1)
end
local function bind(p:Player)
 if listeners[p] then return end
 listeners[p]=p:GetAttributeChangedSignal(ATTRIBUTE):Connect(function() render(p) end)
end
Players.PlayerAdded:Connect(bind)
Players.PlayerRemoving:Connect(function(p)
 if listeners[p] then listeners[p]:Disconnect();listeners[p]=nil end
 lastSeq[p]=nil
 lastAt[p]=nil
end)
for _,p in ipairs(Players:GetPlayers()) do bind(p) end
