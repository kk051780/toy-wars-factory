--!strict
-- EGG RAID RUMBLE #287: READ-ONLY FormDex, reconstructed from ORIGINAL
-- trusted EvolutionRules canonical profile + persisted evolution receipts.
-- NO granting, persistence writes, profile mutation, live networking, Game replacement.
-- Pure/server-compatible. Inject original EvolutionRules once via Dex.new(E).
local Dex = {}
Dex.SCHEMA = "EGG_RUMBLE_FORM_DEX_V1"

local function integer(n,lo,hi)
    return type(n)=="number" and n==n and n%1==0 and n>=lo and n<=hi
end
local function textId(s,max)
    return type(s)=="string" and #s>0 and #s<=max
end
local function compareForms(a,b)
    if a.stage~=b.stage then return a.stage<b.stage end
    return a.branch<b.branch
end
local function canonicalFormId(itemId,stage,branch)
    if not textId(itemId,96) or not integer(stage,0,3) then return nil end
    if stage<=1 then
        if branch~="NONE" then return nil end
        return itemId.."_S"..stage
    end
    if branch~="ASSAULT" and branch~="GUARD" then return nil end
    return itemId.."_S"..stage.."_"..branch
end
local function validReceipt(receipt)
    if type(receipt)~="table" or not textId(receipt.itemId,96) or
        not integer(receipt.stage,1,3) or
        (receipt.action~="EVOLVE" and receipt.action~="SWITCH") then
        return false
    end
    local stage=receipt.stage
    if receipt.action=="EVOLVE" then
        if stage==1 and (receipt.branch~="NONE" or receipt.choice~="NONE") then
            return false
        end
        if stage==2 and (receipt.choice~="ASSAULT" and receipt.choice~="GUARD") then
            return false
        end
        if stage==2 and receipt.choice~=receipt.branch then
            return false
        end
        if stage==3 and receipt.choice~="NONE" then return false end
    else
        if stage<2 or receipt.choice~=receipt.branch then return false end
    end
    if stage>=2 and receipt.branch~="ASSAULT" and receipt.branch~="GUARD" then
        return false
    end
    return receipt.formId==canonicalFormId(receipt.itemId,stage,receipt.branch)
end
function Dex.new(evolution)
    assert(type(evolution)=="table" and type(evolution.catalog)=="function" and
        type(evolution.form)=="function", "REQUIRES_TRUSTED_EVOLUTION_RULES")
    local api={}
    local catalog=evolution.catalog()
    -- Only canonical current Source ownership and receipts may be supplied,
    -- never a client-selected formId or "just granted" client action.
    -- Read-only reconstruction is deterministic even if pairs order differs.
    -- Unknown item, malformed receipt or contradictory stage fails CLOSED.
    function api.snapshot(profile,ownedItems)
        if type(profile)~="table" or type(profile.forms)~="table" or
            type(profile.evoReceipts)~="table" or
            type(ownedItems)~="table" or
            not integer(profile.userId,1,9999999999999) then return nil,"INVALID_PROFILE" end
        local result={
            schema=Dex.SCHEMA,playerUserId=profile.userId,items={},
            itemCount=0,discoveredCount=0,activeCount=0,
            serverReadOnly=true,grantEntitlements=false,
            provisionalCatalogue=true,
        }
        local discoveredByItem={}
        local activeStage={}
        -- Deterministic item ordering, with honest "not currently playable"
        -- classification from the original EvolutionRules catalog.
        local items={}
        for itemId,info in pairs(catalog) do
            if integer(ownedItems[itemId],1,1000000) then
                local f=evolution.form(profile,itemId,ownedItems)
                if type(f)~="table" or
                    f.formId~=canonicalFormId(itemId,f.stage,f.branch) or
                    f.category~=info.category then
                    return nil,"INVALID_CANONICAL_FORM"
                end
                table.insert(items,itemId)
                discoveredByItem[itemId]={}
                activeStage[itemId]=f.stage
                discoveredByItem[itemId][itemId.."_S0"]={stage=0,branch="NONE"}
                discoveredByItem[itemId][f.formId]=
                    {stage=f.stage,branch=f.branch}
            end
        end
        -- Never silently show an unknown allegedly-owned item as an evolution
        -- collectible. Other legitimate inventory item systems can coexist,
        -- but they do not gain a FormDex entry until explicitly catalogued.
        for receiptId,receipt in pairs(profile.evoReceipts) do
            if not textId(receiptId,128) or not validReceipt(receipt) then
                return nil,"INVALID_EVOLUTION_RECEIPT"
            end
            if discoveredByItem[receipt.itemId]~=nil then
                if receipt.stage>activeStage[receipt.itemId] then
                    return nil,"FUTURE_RECEIPT_FORM"
                end
                discoveredByItem[receipt.itemId][receipt.formId]={
                    stage=receipt.stage,branch=receipt.branch
                }
            end
        end
        table.sort(items)
        for _,itemId in ipairs(items) do
            local original=evolution.form(profile,itemId,ownedItems)
            local formId=original.formId
            local row={
                itemId=itemId,category=original.category,
                name=original.displayName,
                activeFormId=formId,activeStage=original.stage,
                activeBranch=original.branch,
                isCurrentPlayableId=original.isCurrentPlayableId==true,
                discoveredForms={},
                discoveredCount=0,
                totalPossibleForms=6,
                missingForms=0,
            }
            for discoveredId,record in pairs(discoveredByItem[itemId]) do
                table.insert(row.discoveredForms,{
                    formId=discoveredId,stage=record.stage,branch=record.branch,
                    active=(discoveredId==formId),
                    cosmeticOnly=true,
                    canEquipDirectly=false, -- change branch via server rule!
                })
            end
            table.sort(row.discoveredForms,compareForms)
            row.discoveredCount=#row.discoveredForms
            row.missingForms=row.totalPossibleForms-row.discoveredCount
            if row.discoveredCount>6 or row.missingForms<0 then
                return nil,"INVALID_FORM_COUNT"
            end
            result.discoveredCount+=row.discoveredCount
            result.itemCount+=1
            result.activeCount+=1
            table.insert(result.items,row)
        end
        -- Historical examples: a player who did NOT buy/own an item sees no
        -- entries; a respec changes active but not discovered branch history.
        return result,"OK"
    end
    return api
end
return Dex
