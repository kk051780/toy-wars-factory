-- Candidate: immutable ability selection and stage data. No effect, ownership or cast authority.
local normal, premium
if script then
    normal = require(script.Parent.AbilityNormalData)
    premium = require(script.Parent.AbilityPremiumData)
else
    normal = require("./AbilityNormalData")
    premium = require("./AbilityPremiumData")
end
local function freeze(t)
    for _, v in pairs(t) do
        if type(v) == "table" and not table.isfrozen(v) then freeze(v) end
    end
    return table.freeze(t)
end
local byRole, premiumIds = {}, {}
for _, r in ipairs({"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}) do byRole[r] = {} end
for id,e in pairs(normal) do
    for _,r in ipairs(e.roles) do table.insert(byRole[r],id) end
end
for _,ids in pairs(byRole) do table.sort(ids) end
for id in pairs(premium) do table.insert(premiumIds,id) end
table.sort(premiumIds)
freeze(normal); freeze(premium); freeze(byRole); freeze(premiumIds)
local empty = table.freeze({})
local M = {}
function M.getNormal(id) return type(id)=="string" and normal[id] or nil end
function M.getPremium(id) return type(id)=="string" and premium[id] or nil end
function M.normalForRole(r) return type(r)=="string" and byRole[r] or empty end
function M.premiumForRole(r) return type(r)=="string" and byRole[r] and premiumIds or empty end
function M.eligibleNormal(r,id)
    local e=M.getNormal(id)
    return e~=nil and type(r)=="string" and table.find(e.roles,r)~=nil
end
-- Stage is supplied by existing server growth authority, never by a client.
function M.snapshot(r,id,s)
    if type(s)~="number" or s~=math.floor(s) or s<0 or s>4 then return nil,"INVALID_STAGE" end
    if not M.eligibleNormal(r,id) then return nil,"INVALID_ROLE_OR_ID" end
    local e=normal[id]
    local values={}
    for i,m in ipairs(e.metrics) do values[i]={label=m.label,value=m.values[s+1],note=m.note} end
    return freeze({id=id,role=r,stage=s,name=e.name,rarity=e.rarity,cd=e.cd,energy=e.energy,
        form=e.forms[s+1],metrics=values,designSource=e.designSource,status="DESIGN_DATA_NOT_CONNECTED"})
end
return table.freeze(M)
