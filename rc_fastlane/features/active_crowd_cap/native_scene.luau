local UDim2={fromOffset=function(x,y) return {x,y} end,fromScale=function(x,y) return {x,y} end}

-- Native Horde scene
local floor={
    GrassArena={Position=Vector3.new(__GrassArena_POS__),Size=Vector3.new(__GrassArena_SIZE__),IsA=function() return true end},
    CenterRoad={Position=Vector3.new(__CenterRoad_POS__),Size=Vector3.new(__CenterRoad_SIZE__),IsA=function() return true end},
}
local world={FindFirstChild=function(_,name) return floor[name] end}
workspace={Raycast=function() return nil end}
local p1,p2={Name="left"},{Name="right"}
local roots={[p1]={Position=Vector3.new(-16,3,0)},[p2]={Position=Vector3.new(16,3,0)}}
local function healthy(player) return roots[player]~=nil,roots[player] end
local capped=__EXPECT_CAP__

local function count(impacts)
    local left,right,elite=0,0,0
    for _,impact in ipairs(impacts) do
        if impact.kind=="ELITE" then
            assert(impact.player==p1 and impact.damage==11)
            elite+=1
        elseif impact.player==p1 then
            assert(impact.kind=="MINION" and impact.damage==3)
            left+=1
        elseif impact.player==p2 then
            assert(impact.kind=="MINION" and impact.damage==3)
            right+=1
        else
            error("UNKNOWN_PLAYER_TARGET")
        end
    end
    return left,right,elite
end

local function prime(players)
    local horde=Horde.new(world)
    horde:reset(59,0)
    assert(#horde.mobs==9 and horde.mobs[1].home.X==-24 and horde.mobs[2].home.X==-8
        and horde.mobs[5].home.Z==18 and horde.mobs[9].elite)
    for frame=1,9 do horde:tick(frame*.5,players,healthy) end
    local elite=horde.mobs[9]
    elite.pos=Vector3.new(-16,2.65,4)
    elite.target=p1
    elite.tellUntil=5
    elite.attackAt=5
    return horde
end

do
    local players={p1}
    local horde=prime(players)
    local left,right,elite=count(horde:tick(5,players,healthy))
    print("t=5 solo",left,right,elite)
    assert(left==(if capped then 2 else 4) and right==0,"SOLO_PEAK_T5")
    assert(elite==1,"ELITE_INDEPENDENT_OF_NORMAL_CAP")
    left,right,elite=count(horde:tick(5.5,players,healthy))
    print("t=5.5 solo",left,right,elite)
    assert(left==(if capped then 2 else 0) and right==0 and elite==0,"NEXT_TICK_CAP_RESET")
end
do
    local players={p1,p2}
    local horde=prime(players)
    local left,right,elite=count(horde:tick(5,players,healthy))
    print("t=5 dual",left,right,elite)
    assert(left==(if capped then 2 else 4) and right==left,"DUAL_PLAYER_SEPARATE_LIMITS")
    assert(elite==1,"DUAL_PLAYER_ELITE")
    left,right,elite=count(horde:tick(5.5,players,healthy))
    print("t=5.5 dual",left,right,elite)
    assert(left==(if capped then 2 else 0) and right==left and elite==0,"DUAL_PLAYER_NEXT_TICK")
end
print("ACTIVE_FB008_ACTUAL_SELECTED_HORDE_PASS")
