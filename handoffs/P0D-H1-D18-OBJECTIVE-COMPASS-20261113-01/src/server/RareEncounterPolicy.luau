--!strict
-- S2+ original fantasy neutral-creature encounter preview.
-- Pure server-side contract: no client RNG, damage, tickets, datastore, drop,
-- inventory or paid manipulation. Rare percentage is a CONFIGURED TEST value,
-- never represented as a live game probability or observed economic result.
local P = {}
P.VERSION = "RARE_NEUTRAL_ENCOUNTER_PREVIEW_V1"
P.WINDOW_SECONDS = 45
P.SPAWN_CHANCE = 0.12
P.LIFETIME_SECONDS = 28
P.TELEGRAPH_SECONDS = 2
P.MAX_ACTIVE = 1
P.MIN_INTERACTION_DISTANCE = 14
P.ROUTE_ORDER = {"SPACE","CELESTIAL","EMBER","ECLIPSE"}
P.CREATURES = {
    SPACE={name="ほしくじら",world="SPACE",cue="✨ 星がふわふわ！",color="STAR",mode="ORBIT"},
    CELESTIAL={name="にじのペガサス",world="CELESTIAL",cue="☁ 雲がぴょん！",color="PEARL",mode="HOP"},
    EMBER={name="マグマモグラ",world="EMBER",cue="🔥 あかい もぐら",color="EMBER",mode="PEEK"},
    ECLIPSE={name="ふたつのかおのげんじゅう",world="ECLIPSE",cue="🌙 月と太陽",color="ECLIPSE",mode="SIDE"}
}
function P.newState()
    return {lastWindow=-1,activeId=nil,activeUntil=0,startedAt=0,serial=0}
end
local function finite(n)
    return type(n)=="number" and n==n and n>-math.huge and n<math.huge
end
function P.validNow(n)
    return finite(n) and n>=0
end
function P.worldForWindow(window)
    if not finite(window) or window<0 or window%1~=0 then return nil end
    return P.ROUTE_ORDER[(window%#P.ROUTE_ORDER)+1]
end
-- Observations: never mutate input state, never spawn twice for same window,
-- and no state except exactly one server-owned active instance at a time.
function P.step(s,now,draw)
    if not P.validNow(now) or not s or
       not finite(s.lastWindow) or not finite(s.activeUntil) then
        return s,{kind="INVALID"}
    end
    if s.activeId then
        if now < s.activeUntil then return s,{kind="NONE"} end
        return {lastWindow=s.lastWindow,activeId=nil,activeUntil=0,
                startedAt=0,serial=s.serial},{kind="DESPAWN",id=s.activeId}
    end
    local window=math.floor(now/P.WINDOW_SECONDS)
    if window<=s.lastWindow then return s,{kind="NONE"} end
    local nextState={lastWindow=window,activeId=nil,activeUntil=0,
                    startedAt=0,serial=s.serial}
    -- Invalid RNG must not silently become a guaranteed or paid spawn.
    if not finite(draw) or draw<0 or draw>=1 then
        return nextState,{kind="RNG_INVALID"}
    end
    if draw>=P.SPAWN_CHANCE then return nextState,{kind="MISSED"} end
    local id=P.worldForWindow(window)
    if not id then return nextState,{kind="INVALID"} end
    nextState.activeId=id
    nextState.startedAt=now
    nextState.activeUntil=now+P.LIFETIME_SECONDS
    nextState.serial=s.serial+1
    return nextState,{kind="SPAWN",id=id,serial=nextState.serial}
end
function P.motion(id,seconds)
    if not P.CREATURES[id] or not P.validNow(seconds) then
        return {x=0,y=0,z=0,alpha=1,description="INVALID"}
    end
    local a=seconds
    if id=="SPACE" then
        return {x=math.sin(a*0.28)*10,y=14+math.sin(a*0.6)*3,
                z=math.cos(a*0.28)*8,alpha=0,
                description="星くじらがゆっくり周回"}
    elseif id=="CELESTIAL" then
        return {x=math.sin(a*0.35)*7,y=8+math.abs(math.sin(a*1.2))*5,
                z=math.cos(a*0.35)*4,alpha=0,
                description="雲の上でやさしく跳ねる"}
    elseif id=="EMBER" then
        local peek=(math.floor(a/5)%2)==0
        return {x=math.sin(a*0.2)*4,y=4+(peek and 0 or -2),
                z=math.cos(a*0.2)*3,alpha=peek and 0 or 0.64,
                description=peek and "顔を出す" or "地面にかくれる"}
    else
        return {x=math.sin(a*0.4)*11,y=8+math.sin(a*0.7)*2,
                z=math.cos(a*0.25)*5,alpha=0,
                description=(math.floor(a/30)%2==0) and "太陽の側" or "月の側"}
    end
end
function P.validate()
    if #P.ROUTE_ORDER~=4 or P.MAX_ACTIVE~=1
       or P.SPAWN_CHANCE<=0 or P.SPAWN_CHANCE>=0.25
       or P.WINDOW_SECONDS<30 or P.LIFETIME_SECONDS>=P.WINDOW_SECONDS
       or P.TELEGRAPH_SECONDS<1 or P.MIN_INTERACTION_DISTANCE>16 then
        return false,"unsafe encounter limits"
    end
    local ids={}
    for _,id in ipairs(P.ROUTE_ORDER) do
        if ids[id] or not P.CREATURES[id] or
           #P.CREATURES[id].name<3 or #P.CREATURES[id].cue<3 then
            return false,"missing creature"
        end
        ids[id]=true
    end
    return true,"4 finite, non-reward rare visual encounters"
end
return P
