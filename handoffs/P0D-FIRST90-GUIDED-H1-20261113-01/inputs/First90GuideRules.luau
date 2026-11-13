--!strict
-- P0D H1 FIRST90: pure read-only child-first guide; ONE original Game validates events.
-- Never creates an egg, player buff, match outcome, Remote, reward or DataStore.
local Guide={}
Guide.WINDOW_SECONDS=90
Guide.ELITE_MAX_SECONDS=1.5
local function boundedInt(x,lo,hi)
    return type(x)=="number" and x==x and x%1==0
        and x>=lo and x<=hi
end
local function bool(x)
    return x==true
end
function Guide.newRound(serial:number)
    if not boundedInt(serial,1,100000000) then return nil end
    return {serial=serial,hit=false,pickup=false,deposit=false,
        scout=false,rescue=false}
end
function Guide.mark(state:any,serial:any,kind:any,serverConfirmed:any):boolean
    if serverConfirmed~=true or type(state)~="table"
        or not boundedInt(serial,1,100000000)
        or state.serial~=serial then return false end
    local field=if kind=="HIT" then "hit"
        elseif kind=="PICKUP" then "pickup"
        elseif kind=="DEPOSIT" then "deposit"
        elseif kind=="SCOUT" then "scout"
        elseif kind=="RESCUE" then "rescue" else nil
    if not field or state[field]~=false then return false end
    state[field]=true
    return true
end
function Guide.view(phase:any,elapsed:any,state:any,data:any):any
    local hidden={visible=false,step="HIDDEN",text="",seconds=0}
    if phase~="ACTIVE" or not boundedInt(elapsed,0,3600)
        or elapsed>=Guide.WINDOW_SECONDS or type(state)~="table"
        or type(data)~="table" then return hidden end
    if not boundedInt(state.serial,1,100000000)
        or state.hit~=true and state.hit~=false
        or state.pickup~=true and state.pickup~=false
        or state.deposit~=true and state.deposit~=false
        or state.scout~=true and state.scout~=false then return hidden end
    if data.mode~="CLASSIC" and data.mode~="SCORE_5" then return hidden end
    local remaining=Guide.WINDOW_SECONDS-elapsed
    local function cue(step,text)
        return {visible=true,step=step,text=text,seconds=remaining}
    end
    -- Urgent danger/help always pre-empts onboarding, then resumes it.
    local elite=if type(data.eliteWarning)=="number" and data.eliteWarning==data.eliteWarning
        and data.eliteWarning>=0 and data.eliteWarning<=Guide.ELITE_MAX_SECONDS
        then data.eliteWarning else 0
    if elite>0 then
        return cue("DODGE","⚠ 赤い円の外へ！ 強い敵の攻撃が来る！")
    end
    if bool(data.bound) then
        return cue("BREAK","⛓ つかまった！「脱出」を押そう")
    end
    if bool(data.rescueNearby) then
        return cue("RESCUE","🤝 仲間がつかまった！「救助」で助けよう")
    end
    if bool(data.carrying) then
        return cue("RETURN",if data.mode=="SCORE_5"
            then "🥚 卵を持って自陣の金庫へ！"
            else "🥚 敵の卵を持って自陣の台へ！")
    end
    -- The introductory attack cue never holds the player hostage.
    if not state.hit and elapsed<24 then
        return cue("ATTACK","⚔ 目の前の中立兵を攻撃！ まとめて倒せるよ")
    end
    if not state.pickup and elapsed<60 then
        return cue("PICKUP",if data.mode=="SCORE_5"
            then "🥚 5つの卵を集めて得点！近づいてタップ"
            else "🥚 敵の卵を盗もう！近づいてタップ")
    end
    if state.pickup and not state.deposit and elapsed<75 then
        -- Egg is NOT carried now: false “return home” guidance would
        -- mislead a child after KO/drop. Reacquire a real available egg.
        return cue("PICKUP","🥚 卵を落としたら、もう一度ひろおう！")
    end
    if not state.scout and elapsed>=20 and elapsed<80 and bool(data.scoutReady) then
        return cue("SCOUT","🐉 魔獣を呼んで敵の卵運びを探そう！")
    end
    return cue("FREE","✨ 好きな戦い方で卵を奪おう！ 仲間と協力！")
end
return Guide
