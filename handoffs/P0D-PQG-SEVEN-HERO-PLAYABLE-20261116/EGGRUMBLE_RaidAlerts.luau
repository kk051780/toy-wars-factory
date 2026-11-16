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

-- Observe only original server-owned castle HP, with a per-session cooldown.
-- The host primes this after Rules.start, before combat begins.
function Alerts.siegeSignals(castles:{[string]:any},previousHP:{[string]:number},lastShownAt:{[string]:number},now:number):{Signal}
 assert(type(castles)=="table" and type(previousHP)=="table" and type(lastShownAt)=="table","invalid siege snapshot")
 assert(type(now)=="number" and now==now,"invalid clock")
 local out:{Signal}={}
 for id,castle in pairs(castles) do
  local hp=castle.hp
  if type(hp)=="number" and hp==hp then
   local previous=previousHP[id]
   previousHP[id]=hp
   if previous and hp<previous and hp>0 and castle.alive and
    (lastShownAt[id]==nil or now-lastShownAt[id]>=7) then
    lastShownAt[id]=now
    table.insert(out,{kind="SIEGE",castleId=tostring(id),duration=2.5})
   end
  end
 end
 return out
end

-- A castle can be under siege while eggs are stolen or banked.
-- Across refresh ticks, strategic objective alerts must beat routine HP chip damage.
-- No permanent HUD and no new damage/score authority.
local PRIORITY={SIEGE=1,DELIVER=2,RAID=3,FALL=4}
function Alerts.priority(kind:string):number
 return PRIORITY[kind] or 0
end

local function render(session:any,signal:Signal)
 local bits=session.castleModels and session.castleModels[signal.castleId]
 local castle=session.rules and session.rules.castles[signal.castleId]
 if not bits or not castle or not bits.banner or not bits.banner.Parent then return end
 if signal.kind~="FALL" and not castle.alive then return end
 local banner=bits.banner
 local priority=Alerts.priority(signal.kind)
 if priority==0 then return end
 local activePriority=banner:GetAttribute("EGGRUMBLE_AlertPriority")
 local expires=banner:GetAttribute("EGGRUMBLE_AlertUntil")
 if type(activePriority)=="number" and type(expires)=="number"
  and os.clock()<expires and priority<activePriority then
  return
 end
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
 local color=if signal.kind=="SIEGE" then Color3.fromRGB(245,163,63)
  elseif signal.kind=="RAID" then Color3.fromRGB(249,83,62)
  elseif signal.kind=="FALL" then Color3.fromRGB(104,91,91)
  else Color3.fromRGB(99,217,148)
 local copy=if signal.kind=="SIEGE" then "城が攻撃中！"
  elseif signal.kind=="RAID" then "卵強奪！防衛せよ"
  elseif signal.kind=="FALL" then "城が陥落！" else "卵を納入！"
 label.Text=copy
 notice.Enabled=true
 banner.Color=color
 local serial=(banner:GetAttribute("EGGRUMBLE_AlertSerial") or 0)+1
 banner:SetAttribute("EGGRUMBLE_AlertSerial",serial)
 banner:SetAttribute("EGGRUMBLE_AlertPriority",priority)
 banner:SetAttribute("EGGRUMBLE_AlertUntil",os.clock()+signal.duration)
 task.delay(signal.duration,function()
  if not banner.Parent or banner:GetAttribute("EGGRUMBLE_AlertSerial")~=serial then return end
  notice.Enabled=false
  local original=banner:GetAttribute("EGGRUMBLE_AlertBaseColor")
  -- A concurrent castle-decoration update must win over this cosmetic alert.
  if typeof(original)=="Color3" and banner.Color==color then banner.Color=original end
  banner:SetAttribute("EGGRUMBLE_AlertBaseColor",nil)
  banner:SetAttribute("EGGRUMBLE_AlertPriority",nil)
  banner:SetAttribute("EGGRUMBLE_AlertUntil",nil)
 end)
end

function Alerts.process(session:any)
 if not session or not session.rules or not session.rules.events then return end
 if session.alertSourceRules~=session.rules then
  session.alertSourceRules=session.rules
  session.alertCursor=0
  session.alertLastHP={}
  session.alertLastSiege={}
 end
 local siegeSignals=Alerts.siegeSignals(session.rules.castles,session.alertLastHP,session.alertLastSiege,os.clock())
 for _,signal in ipairs(siegeSignals) do render(session,signal) end
 -- Real egg theft/deposit/fall takes priority when simultaneous with siege.
 local signals,nextCursor=Alerts.collect(session.rules.events,session.alertCursor or 0)
 session.alertCursor=nextCursor
 for _,signal in ipairs(signals) do render(session,signal) end
end
return Alerts
