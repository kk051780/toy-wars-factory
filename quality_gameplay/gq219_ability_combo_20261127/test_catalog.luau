local C=require("./AbilityCatalog")
local normal=require("./AbilityNormalData")
local premium=require("./AbilityPremiumData")
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local count,pc,stages,roleStages=0,0,0,0
local function eq(a,b) assert(a==b,tostring(a).." != "..tostring(b)) end
for id,e in pairs(normal) do
    count+=1
    eq(e.id,id)
    assert(#e.name>0 and #e.description>0 and #e.specification>0 and #e.designSource>0)
    eq(#e.forms,5);eq(#e.metrics,2)
    assert(e.cd>0 and e.energy>0 and e.energy<=100)
    for s=0,4 do
        stages+=1;assert(#e.forms[s+1]>0)
        for _,m in ipairs(e.metrics) do eq(#m.values,5);assert(type(m.values[s+1])=="number" and m.values[s+1]==m.values[s+1]) end
        for _,r in ipairs(roles) do
            local eligible=table.find(e.roles,r)~=nil
            eq(C.eligibleNormal(r,id),eligible)
            local snap=C.snapshot(r,id,s);eq(snap~=nil,eligible)
            if snap then
                roleStages+=1;eq(snap.stage,s);eq(snap.form,e.forms[s+1])
                eq(snap.cd,e.cd);eq(snap.energy,e.energy);eq(snap.status,"DESIGN_DATA_NOT_CONNECTED")
                for i,m in ipairs(snap.metrics) do eq(m.value,e.metrics[i].values[s+1]);eq(m.label,e.metrics[i].label) end
                assert(table.isfrozen(snap) and table.isfrozen(snap.metrics[1]))
            end
        end
    end
    assert(table.isfrozen(e) and table.isfrozen(e.forms) and table.isfrozen(e.metrics[1].values))
    eq(C.getPremium(id),nil)
end
for id,e in pairs(premium) do
    pc+=1;eq(e.id,id);eq(e.standalone,false);eq(e.requiredSlots,2);eq(e.cd,40);eq(e.energy,80);eq(e.maxPerRound,2);eq(#e.roles,7)
    assert(#e.specification>0 and #e.name>0 and table.isfrozen(e))
    eq(C.getNormal(id),nil);eq(C.snapshot("WARRIOR",id,0),nil)
end
eq(count,772);eq(pc,100);eq(stages,3860);eq(roleStages,4970)
for _,r in ipairs(roles) do
    local ids=C.normalForRole(r);eq(#ids,142);eq(#C.premiumForRole(r),100)
    local seen={}
    for _,id in ipairs(ids) do assert(not seen[id]);seen[id]=true;assert(C.eligibleNormal(r,id)) end
    for i=1,100 do assert(C.getNormal(string.format("%s-%03d",r,i))) end
end
for i=1,30 do eq(#C.getNormal(string.format("COMMON-%03d",i)).roles,7) end
local pairCounts={}
for i=1,42 do
    local e=C.getNormal(string.format("SHARED-%03d",i));eq(#e.roles,2)
    local a,b=e.roles[1],e.roles[2];assert(a~=b)
    local k=a<b and a..":"..b or b..":"..a;pairCounts[k]=(pairCounts[k] or 0)+1
end
local nPairs=0
for _,v in pairs(pairCounts) do eq(v,2);nPairs+=1 end
eq(nPairs,21)
for i=1,100 do assert(C.getPremium(string.format("PREMIUM-%03d",i))) end
eq(C.getNormal("TRAPPER-101"),nil);eq(C.getNormal("TRAPPER-102"),nil)
eq(C.getNormal("COMBO-022"),nil);eq(C.snapshot("WARRIOR","MAGE-001",0),nil)
for _,s in ipairs({-1,5,0.5,math.huge,-math.huge,0/0,"4",false}) do eq(C.snapshot("WARRIOR","WARRIOR-001",s),nil) end
eq(C.snapshot("WARRIOR","WARRIOR-001",nil),nil)
eq(#C.normalForRole("INVALID"),0);eq(#C.premiumForRole("INVALID"),0)
eq(C.getNormal({}),nil);eq(C.getPremium(1),nil)
for s=0,4 do
    eq(C.snapshot("WARRIOR","COMMON-002",s).metrics[2].value,1)
    eq(C.snapshot("WARRIOR","COMMON-009",s).metrics[2].value,1)
    eq(C.getNormal("SHARED-026").metrics[2].values[s+1],0.5)
    eq(C.getNormal("SHARED-036").metrics[2].values[s+1],0.6)
end
assert(not pcall(function() C.getNormal("WARRIOR-001").forms[1]="tamper" end))
assert(not pcall(function() C.normalForRole("WARRIOR")[1]="tamper" end))
print("ABILITY_CATALOG_PASS: 772 normal / 100 premium / 3860 stages / 4970 role-stage snapshots")
