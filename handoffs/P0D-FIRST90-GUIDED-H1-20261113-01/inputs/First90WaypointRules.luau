--!strict
-- Only a pure, view-only first-90-second waypoint selector. No movement/ownership authority.
local Nav={}
Nav.WINDOW=90
local function finite(x:any,lo:number,hi:number):boolean
    return type(x)=="number" and x==x and x>=lo and x<=hi
end
local function point(pos:any):boolean
    return type(pos)=="table"
        and finite(pos.x,-200,200) and finite(pos.y,-50,100)
        and finite(pos.z,-120,120)
end
function Nav.select(phase:any,elapsed:any,team:any,mode:any,step:any,
        origin:any,ownPad:any,eggs:any):any?
    if phase~="ACTIVE" or not finite(elapsed,0,Nav.WINDOW)
        or elapsed>=Nav.WINDOW or (team~="RED" and team~="BLUE")
        or (mode~="CLASSIC" and mode~="SCORE_5")
        or not point(origin) then return nil end
    if step=="RETURN" then
        if not point(ownPad) then return nil end
        return {kind="HOME",x=ownPad.x,y=ownPad.y,z=ownPad.z}
    end
    if step~="PICKUP" then return nil end
    if type(eggs)~="table" then return nil end
    local found=nil
    local best=math.huge
    local selectedId=""
    local opposite=if team=="RED" then "BLUE" else "RED"
    local count=0
    for _,egg in ipairs(eggs) do
        count+=1
        if count>5 then break end
        if type(egg)=="table" and type(egg.id)=="string" and #egg.id<=3
            and egg.available==true and point(egg) and
            (egg.owner=="RED" or egg.owner=="BLUE" or egg.owner=="NEUTRAL")
            and (mode=="SCORE_5" or egg.owner==opposite) then
            local dx=egg.x-origin.x
            local dz=egg.z-origin.z
            local dist2=dx*dx+dz*dz
            if dist2<best or (dist2==best and egg.id<selectedId) then
                best=dist2
                selectedId=egg.id
                found={kind="EGG",x=egg.x,y=egg.y,z=egg.z}
            end
        end
    end
    return found
end
return Nav
