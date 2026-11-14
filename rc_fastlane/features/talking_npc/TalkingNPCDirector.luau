--!strict
-- P0D-TALKING-NPC-V1 / source-only prototype. NOT connected to the game or RC build.
-- The caller MUST run on the server and pass only already authorized, observed game facts.
-- No player/client text, raw coordinates, RemoteEvent, saves, combat or rewards are read/written.
local Director = {}

local AREAS = {
    north = "北の道", south = "南の道", east = "東の道",
    west = "西の道", center = "中央", sky = "空のエリア",
    sea = "海のエリア", cave = "洞窟", home = "自陣", star_bridge = "星降る橋",
}
local ITEMS = {
    rare_egg = "レア卵", healing = "回復アイテム",
    beast_stone = "魔獣の進化石", speed = "加速アイテム", star_shard = "星のかけら",
}
local WEATHER = {
    thunder = "雷雨", snow = "吹雪", meteor = "流星",
    clear = "晴れ",
}
local SPEAKERS = {
    NAVI = { display = "ナビィ", voiceId = "701", team = "ALLY" },
    TRICK = { display = "マドロン", voiceId = "702", team = "ENEMY" },
    ORACLE = { display = "オラクル", voiceId = "701", team = "NEUTRAL" },
}

local function output(speakerId, intent, text, urgent, suspicious)
    local speaker = SPEAKERS[speakerId]
    -- All output is authored static text plus approved enums. No raw chat interpolation.
    return {
        speakerId = speakerId,
        displayName = speaker.display,
        faction = speaker.team,
        intent = intent,
        text = text,
        caption = text,
        voiceText = text,
        voiceId = speaker.voiceId,
        urgent = urgent == true,
        suspicious = suspicious == true,
        isGeneratedAI = false,
    }
end

-- Returns one short, deterministic announcement or nil. All secrets default closed.
function Director.Compose(facts)
    if type(facts) ~= "table" or facts.featureEnabled ~= true then
        return nil
    end
    local speakerId = facts.speakerId
    local signal = facts.signal
    if SPEAKERS[speakerId] == nil or type(signal) ~= "string" then
        return nil
    end
    if facts.cooldownActive == true and facts.urgent ~= true then
        return nil
    end
    if speakerId == "NAVI" then
        if signal == "HELLO" then
            return output(speakerId, signal, "卵を運ぶ味方を守ろう！こまったら呼んでね。", false, false)
        end
        if signal == "ENEMY_ALERT" and facts.observedByTeam == true then
            local area = AREAS[facts.areaCode]
            if area ~= nil then
                return output(speakerId, signal, "注意！" .. area .. "に敵を発見！", true, false)
            end
        elseif signal == "EGG_RETURN" and facts.ourEggCarrier == true then
            return output(speakerId, signal, "卵を確保！ 自陣まで守って帰ろう！", true, false)
        elseif signal == "KNOWN_ITEM" and facts.itemKnownByTeam == true then
            local area = AREAS[facts.areaCode]
            local item = ITEMS[facts.itemCode]
            if area ~= nil and item ~= nil then
                return output(speakerId, signal, area .. "に" .. item .. "があるよ！", false, false)
            end
        end
    elseif speakerId == "TRICK" then
        if signal == "TRICK_RUMOR" then
            return output(speakerId, signal, "ふふっ、こっちに宝があるかもね？ 信じる？", false, true)
        elseif signal == "TAUNT" then
            return output(speakerId, signal, "その卵、ほんとに守りきれるかな？", false, true)
        end
    elseif speakerId == "ORACLE" then
        if signal == "INTRO" then
            return output(speakerId, signal, "4つの秘境の印を見つけると、秘密が分かるぞ。", false, false)
        end
        if signal == "SECRET_HINT" and facts.hintUnlocked == true then
            if facts.secretTier == 1 then
                return output(speakerId, signal, "天空と海、まだ見つけていない印はあるかな？", false, false)
            elseif facts.secretTier == 2 then
                return output(speakerId, signal, "4つの秘境の印を集めると、不思議な光が現れる……", false, false)
            end
        elseif signal == "WEATHER" and facts.weatherObserved == true then
            local weather = WEATHER[facts.weatherCode]
            if weather ~= nil then
                return output(speakerId, signal, "いまは" .. weather .. "。地形の変化を見逃すな……", false, false)
            end
        end
    end
    return nil
end

-- Pure cooldown helper. The caller must enforce per-player and per-NPC buckets.
function Director.CanSpeak(nowSeconds, previousSeconds, urgent)
    if type(nowSeconds) ~= "number" then
        return false
    end
    if previousSeconds == nil then
        return true
    end
    if type(previousSeconds) ~= "number" then
        return false
    end
    local gap = urgent == true and 15 or 30
    return nowSeconds >= previousSeconds and (nowSeconds - previousSeconds) >= gap
end

return Director
