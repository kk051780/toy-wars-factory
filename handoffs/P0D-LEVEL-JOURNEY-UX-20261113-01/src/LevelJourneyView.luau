--!strict
-- EGG RAID RUMBLE: server-owned read-only level presentation contract.
-- Does NOT grant XP, equipment, cosmetics, paid items or DataStore rights.
-- Inject the EXACT #281 ProgressionRules module: local V=View.new(ProgressionRules).
local View = {}

local PLAYER_REWARD = {
    WELCOME_BANNER="はじめての卵バナー",
    PERSONAL_NEST_DECOR="マイ巣の飾り",
    TEAM_EMOTE="チーム勝利エモート",
    MOUNT_TRAIL_COSMETIC="乗り物の軌跡",
    CASTLE_FLAG_COSMETIC="城のオリジナル旗",
    MASTER_AURA_COSMETIC="マスターのオーラ",
}
local MASTERY_REWARD = {
    CREATURE_PALETTE="魔獣の色違い",
    ALTERNATE_ANIMATION="魔獣の特別モーション",
    MASTERY_TITLE="熟練者の称号",
}
local PLAYER_STEPS={2,5,10,20,30,50}
local MASTERY_STEPS={3,6,10}
local function isInt(v,min,max)
    return type(v)=="number" and v==v and v%1==0 and v>=min and v<=max
end
local function displayMilestone(policy,kind,level)
    local raw = kind=="PLAYER" and policy.playerMilestone(level) or policy.masteryMilestone(level)
    if type(raw)~="string" then return nil end
    local label = kind=="PLAYER" and PLAYER_REWARD[raw] or MASTERY_REWARD[raw]
    if not label then return nil end
    return {level=level,id=raw,label=label,kind=kind,claimStatus="PREVIEW_ONLY"}
end
local function nextMilestone(policy,kind,level)
    local steps=kind=="PLAYER" and PLAYER_STEPS or MASTERY_STEPS
    for _, target in ipairs(steps) do
        if target>level then return displayMilestone(policy,kind,target) end
    end
    return nil
end
local function crossed(policy,kind,old,new)
    local steps=kind=="PLAYER" and PLAYER_STEPS or MASTERY_STEPS
    local r={}
    for _,n in ipairs(steps) do
        if n>old and n<=new then
            local e=displayMilestone(policy,kind,n)
            if e then table.insert(r,e) end
        end
    end
    return r
end
local function percent(xp,need)
    if need<=0 then return 100 end
    return math.floor(math.clamp(xp/need,0,1)*100)
end
local function levelInfo(level,xp,threshold,maxLevel)
    local need=level>=maxLevel and 0 or threshold(level)
    if not isInt(need,0,10000000) then return nil end
    if level==maxLevel then
        if xp~=0 then return nil end
        return {level=level,xp=0,needed=0,remaining=0,percent=100,max=true}
    end
    if need==0 or not isInt(xp,0,need-1) then return nil end
    return {level=level,xp=xp,needed=need,remaining=need-xp,
        percent=percent(xp,need),max=false}
end
function View.new(policy)
    assert(type(policy)=="table" and type(policy.xpToNext)=="function" and
        type(policy.masteryToNext)=="function" and
        type(policy.playerMilestone)=="function" and
        type(policy.masteryMilestone)=="function", "INCOMPATIBLE_XP_POLICY")
    local api={}
    -- Caller MUST be the trusted server and must validate inventory's actual ownership.
    -- revision monotonic per player, never a client input or timestamp.
    function api.snapshot(profile,round,ownedEquippedItemId,revision)
        if type(profile)~="table" or not isInt(revision,1,2147483647) then return nil end
        if not isInt(profile.level,1,policy.PLAYER_MAX_LEVEL) then return nil end
        local account=levelInfo(profile.level,profile.xp,policy.xpToNext,policy.PLAYER_MAX_LEVEL)
        if not account then return nil end
        account.nextReward=nextMilestone(policy,"PLAYER",profile.level)
        local focus={level=1,points=0,needed=25,percent=0,nextGoal="卵を守る・運ぶ"}
        if round~=nil then
            if type(round)~="table" or round.closed==true or not isInt(round.focusXp,0,1000) then return nil end
            if type(round.playerUserId)~="number" or profile.playerUserId~=round.playerUserId then return nil end
            focus.level=policy.focusLevel(round)
            focus.points=round.focusXp
            focus.needed=if focus.level==1 then 25 elseif focus.level==2 then 60 else 0
            focus.percent=if focus.level>=3 then 100 else percent(round.focusXp,focus.needed)
            focus.nextGoal=if focus.level>=3 then "試合内成長MAX！"
                elseif focus.level==2 then "次は卵を届けよう" else "まず卵の争奪に参加しよう"
        end
        local mastery=nil
        if ownedEquippedItemId~=nil then
            if type(ownedEquippedItemId)~="string" or #ownedEquippedItemId<1 or
                #ownedEquippedItemId>96 or type(profile.mastery)~="table" then return nil end
            local m=profile.mastery[ownedEquippedItemId] or {level=1,xp=0}
            if type(m)~="table" or not isInt(m.level,1,policy.MASTERY_MAX_LEVEL) then return nil end
            mastery=levelInfo(m.level,m.xp,policy.masteryToNext,policy.MASTERY_MAX_LEVEL)
            if not mastery then return nil end
            mastery.itemId=ownedEquippedItemId
            mastery.nextReward=nextMilestone(policy,"MASTERY",m.level)
        end
        return {schema="P0D_LEVEL_VIEW_V1",revision=revision,kind="SNAPSHOT",
            account=account,focus=focus,mastery=mastery,gameplayStatsIncreased=false,
            requiresPaidPurchase=false,source="SERVER_AUTHORITATIVE",
            nextAction="卵を運ぶ・守る → 試合後に無料孵化 → 装備を使う"}
    end
    -- Not a grant. This only PREVIEWS milestones crossed after a canonical
    -- ProgressionRules.commit and a separately completed durable entitlement grant.
    function api.settlement(before,after,receipt,itemId,revision)
        if type(before)~="table" or type(after)~="table" or type(receipt)~="table" or
            before.playerUserId~=after.playerUserId or not isInt(revision,1,2147483647) then return nil end
        if receipt.rewardKind~="FAIR_PROGRESS_ONLY" or
            receipt.gameplayStatsIncreased~=false or receipt.requiresPaidPurchase~=false then return nil end
        if not isInt(before.level,1,policy.PLAYER_MAX_LEVEL) or
            not isInt(after.level,before.level,policy.PLAYER_MAX_LEVEL) or
            receipt.accountLevelBefore~=before.level or
            receipt.accountLevelAfter~=after.level or
            not isInt(receipt.grantedXp,1,policy.XP_CAP_PER_ROUND) then return nil end
        local masteryCrossed={}
        if receipt.masteryLevelBefore~=nil or receipt.masteryLevelAfter~=nil then
            if type(itemId)~="string" or #itemId==0 or #itemId>96 or
                not isInt(receipt.masteryLevelBefore,1,policy.MASTERY_MAX_LEVEL) or
                not isInt(receipt.masteryLevelAfter,receipt.masteryLevelBefore,policy.MASTERY_MAX_LEVEL) then return nil end
            masteryCrossed=crossed(policy,"MASTERY",receipt.masteryLevelBefore,receipt.masteryLevelAfter)
        end
        return {schema="P0D_LEVEL_VIEW_V1",kind="SETTLEMENT",revision=revision,
            accountLevelBefore=before.level,accountLevelAfter=after.level,
            gainedXp=receipt.grantedXp,focusLevel=receipt.focusLevel or 1,
            accountMilestones=crossed(policy,"PLAYER",before.level,after.level),
            masteryMilestones=masteryCrossed,
            playerLeveled=after.level>before.level,
            itemLeveled=receipt.masteryLevelAfter~=nil and
                receipt.masteryLevelAfter>receipt.masteryLevelBefore or false,
            entitlementState="NOT_GRANTED_BY_THIS_MODULE",
            requiresPaidPurchase=false}
    end
    return api
end
return View
