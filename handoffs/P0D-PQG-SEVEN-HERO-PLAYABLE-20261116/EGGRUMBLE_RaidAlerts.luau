--!strict
-- P0D #470 independent GQ RAID-ALERT lane (isolated private V3 only).
-- Reuses CastleMatchRules.events and existing castle banners: NO new egg, score,
-- AI, HUD, hitboxes, monetization, remote events, or parallel match host.
-- Source-only candidate; Studio/Android and official RC acceptance remain required.
local Alerts = {}

export type Signal = {kind:string,castleId:string,duration:number}

function Alerts.intent(event:any):Signal?
 if type(event)~="table" then return nil end
 if event.type=="EGG_TAKEN" then
  if event.source==nil or event.source=="FIELD" or (tonumber(event.quantity) or 0)<=0 then return nil end
  return {kind="RAID",castleId=tostring(event.source),duration=4}
 elseif event.type=="EGG_DEPOSIT" then
  if event.owner==nil or (tonumber(event.quantity) or 0)<=0 then return nil end
  return {kind="DELIVER",castleId=tostring(event.owner),duration=2}
 elseif event.type=="CASTLE_FALL" then
  if event.owner==nil then return nil end
  return {kind="FALL",castleId=tostring(event.owner),duration=6}
 end
 return nil
end

-- Pure cursor-based ingestion: repeated refreshes must never re-announce
-- old events. Each TEAM or BR session owns an independent cursor.
function Alerts.collect(events:{any},lastIndex:number):({Signal},number)
 assert(type(events)=="table","events must come from authoritative rules")
 assert(type(lastIndex)=="number" and lastIndex>=0,"invalid event cursor")
 local out:{Signal}={}
 for idx=math.floor(lastIndex)+1,#events do
  local signal=Alerts.intent(events[idx])
  if signal then table.insert(out,signal) end
 end
 return out,#events
end

local function render(session:any,signal:Signal)
 local bits=session.castleModels and session.castleModels[signal.castleId]
 local castle=session.rules and session.rules.castles[signal.castleId]
 if not bits or not castle or not bits.banner or not bits.banner.Parent then return end
 if signal.kind~="FALL" and not castle.alive then return end
 local banner=bits.banner
 local notice=banner:FindFirstChild("EGGRUMBLE_RaidNotice")
 if not notice then
  notice=Instance.new("BillboardGui")
  notice.Name="EGGRUMBLE_RaidNotice"
  notice.Size=UDim2.fromOffset(158,45)
  notice.StudsOffsetWorldSpace=Vector3.new(0,6,0)
  notice.MaxDistance=190
  notice.AlwaysOnTop=false
  notice.Parent=banner
  local label=Instance.new("TextLabel")
  label.Name="Text"
  label.Size=UDim2.fromScale(1,1)
  label.BackgroundColor3=Color3.fromRGB(34,27,29)
  label.BackgroundTransparency=.18
  label.TextColor3=Color3.fromRGB(255,245,229)
  label.Font=Enum.Font.GothamBold
  label.TextScaled=true
  label.TextWrapped=true
  label.Parent=notice
 end
 local label=notice:FindFirstChild("Text")::TextLabel?
 if not label then return end
 local oldColor=banner:GetAttribute("EGGRUMBLE_AlertBaseColor")
 if typeof(oldColor)~="Color3" then banner:SetAttribute("EGGRUMBLE_AlertBaseColor",banner.Color) end
 local color=if signal.kind=="RAID" then Color3.fromRGB(249,83,62)
  elseif signal.kind=="FALL" then Color3.fromRGB(104,91,91)
  else Color3.fromRGB(99,217,148)
 local copy=if signal.kind=="RAID" then "卵強奪！防衛せよ"
  elseif signal.kind=="FALL" then "城が陥落！" else "卵を納入！"
 label.Text=copy
 notice.Enabled=true
 banner.Color=color
 local serial=(banner:GetAttribute("EGGRUMBLE_AlertSerial") or 0)+1
 banner:SetAttribute("EGGRUMBLE_AlertSerial",serial)
 task.delay(signal.duration,function()
  if not banner.Parent or banner:GetAttribute("EGGRUMBLE_AlertSerial")~=serial then return end
  notice.Enabled=false
  local original=banner:GetAttribute("EGGRUMBLE_AlertBaseColor")
  -- A concurrent castle-decoration update must win over this cosmetic alert.
  if typeof(original)=="Color3" and banner.Color==color then banner.Color=original end
  banner:SetAttribute("EGGRUMBLE_AlertBaseColor",nil)
 end)
end

function Alerts.process(session:any)
 if not session or not session.rules or not session.rules.events then return end
 if session.alertSourceRules~=session.rules then
  session.alertSourceRules=session.rules
  session.alertCursor=0
 end
 local signals,nextCursor=Alerts.collect(session.rules.events,session.alertCursor or 0)
 session.alertCursor=nextCursor
 for _,signal in ipairs(signals) do render(session,signal) end
end
return Alerts
