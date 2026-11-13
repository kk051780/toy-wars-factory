--!strict
-- Server-only pure decision gates; no player movement or remote authority here.
local Rules={}
Rules.NET_RANGE=13
Rules.NET_COOLDOWN=14
Rules.NET_DURATION=1.2
Rules.NET_IMMUNITY=8
Rules.BREAK_DELAY=.45
Rules.RESCUE_RANGE=8
function Rules.canNet(x)
    if type(x)~="table" then return false end
    return x.phase=="ACTIVE" and x.role=="GUARDIAN" and x.alive==true
        and x.team~="NONE" and x.egg==false and x.bound==false
        and type(x.now)=="number" and type(x.last)=="number"
        and x.now-x.last>=Rules.NET_COOLDOWN
end
function Rules.canTarget(x)
    if type(x)~="table" then return false end
    return x.enemy==true and x.alive==true and x.bound==false
        and x.immune==false and x.invulnerable==false
        and type(x.distance)=="number" and x.distance<=Rules.NET_RANGE
        and type(x.facing)=="number" and x.facing>=.3
        and x.visible==true
end
function Rules.canBreak(record,now)
    return type(record)=="table" and record.kind=="NET"
        and type(record.startedAt)=="number" and type(now)=="number"
        and now-record.startedAt>=Rules.BREAK_DELAY
end
function Rules.canRescue(x)
    return type(x)=="table" and x.phase=="ACTIVE"
        and x.teammate==true and x.alive==true
        and x.targetBound==true and x.visible==true
        and type(x.distance)=="number" and x.distance<=Rules.RESCUE_RANGE
end
return Rules
