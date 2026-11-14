-- P0D TALKING NPC pure Director native-Luau behavior (no Roblox engine required).
local count = 0
local function case(ok, label)
    assert(ok, label)
    count += 1
end
local function fact(speaker, intent, extras)
    local f = {featureEnabled=true, speakerId=speaker, signal=intent}
    for k, v in pairs(extras or {}) do f[k]=v end
    return f
end
local function says(f, text, expectedIntent)
    local result = Director.Compose(f)
    case(type(result)=="table" and result.text==text and result.intent==expectedIntent,
        "COMPOSE_MISMATCH_"..expectedIntent)
    case(result.caption==text and result.voiceText==text and result.isGeneratedAI==false,
        "SAFE_MAPPED_DIALOGUE_"..expectedIntent)
    return result
end
case(Director.Compose(nil)==nil, "NIL_CLOSED")
case(Director.Compose({})==nil, "EMPTY_CLOSED")
case(Director.Compose({featureEnabled=false, speakerId="NAVI",signal="HELLO"})==nil, "FLAG_OFF")
case(Director.Compose(fact("UNKNOWN","HELLO"))==nil,"UNKNOWN_SPEAKER_CLOSED")
says(fact("NAVI","HELLO"),"卵を運ぶ味方を守ろう！こまったら呼んでね。","HELLO")
says(fact("NAVI","EGG_RETURN",{ourEggCarrier=true}),
    "卵を確保！ 自陣まで守って帰ろう！","EGG_RETURN")
case(Director.Compose(fact("NAVI","EGG_RETURN"))==nil,"EGG_NOT_OWNED_CLOSED")
says(fact("NAVI","ENEMY_ALERT",{areaCode="east",observedByTeam=true}),
    "注意！東の道に敵を発見！","ENEMY_ALERT")
case(Director.Compose(fact("NAVI","ENEMY_ALERT",{areaCode="east"}))==nil,
    "ENEMY_NOT_VERIFIED_CLOSED")
case(Director.Compose(fact("NAVI","ENEMY_ALERT",{areaCode="private_sector",observedByTeam=true}))==nil,
    "ENEMY_UNKNOWN_AREA_CLOSED")
says(fact("NAVI","KNOWN_ITEM",{areaCode="star_bridge",itemCode="star_shard",itemKnownByTeam=true}),
    "星降る橋に星のかけらがあるよ！","KNOWN_ITEM")
case(Director.Compose(fact("NAVI","KNOWN_ITEM",{areaCode="star_bridge",itemCode="star_shard"}))==nil,
    "ITEM_NOT_OBSERVED_CLOSED")
says(fact("TRICK","TRICK_RUMOR"),"ふふっ、こっちに宝があるかもね？ 信じる？","TRICK_RUMOR")
says(fact("TRICK","TAUNT"),"その卵、ほんとに守りきれるかな？","TAUNT")
says(fact("ORACLE","INTRO"),"4つの秘境を探索して、印を集めよう！","INTRO")
says(fact("ORACLE","SECRET_HINT",{hintUnlocked=true,missingRealm="SKY"}),
    "次は「空」の印を探してみよう！","SECRET_HINT")
says(fact("ORACLE","SECRET_HINT",{hintUnlocked=true,missingRealm="SEA"}),
    "次は「海」の印を探してみよう！","SECRET_HINT")
says(fact("ORACLE","SECRET_HINT",{hintUnlocked=true,missingRealm="EMBER"}),
    "次は「炎」の印を探してみよう！","SECRET_HINT")
says(fact("ORACLE","SECRET_HINT",{hintUnlocked=true,missingRealm="STAR"}),
    "次は「星」の印を探してみよう！","SECRET_HINT")
says(fact("ORACLE","REALM_COMPLETE",{allRealmsComplete=true}),
    "4つの秘境の印がそろったね！探索王だ！","REALM_COMPLETE")
case(Director.Compose(fact("ORACLE","REALM_COMPLETE"))==nil,"COMPLETE_NOT_OWNED_CLOSED")
case(Director.Compose(fact("ORACLE","SECRET_HINT",{hintUnlocked=true,missingRealm="INVALID"}))==nil,"NO_UNKNOWN_REALM_HINT")
case(Director.Compose(fact("ORACLE","SECRET_HINT",{missingRealm="SKY"}))==nil,"HINT_LOCKED_CLOSED")
case(Director.CanSpeak(25,nil,false)==true,"FIRST_MESSAGE")
case(Director.CanSpeak(29,0,false)==false,"NORMAL_29S_BLOCK")
case(Director.CanSpeak(30,0,false)==true,"NORMAL_30S_ALLOW")
case(Director.CanSpeak(14,0,true)==false,"URGENT_14S_BLOCK")
case(Director.CanSpeak(15,0,true)==true,"URGENT_15S_ALLOW")
case(Director.CanSpeak(1,2,true)==false,"CLOCK_REWIND_BLOCK")
print("P0D_TALKING_NPC_NATIVE_DIRECTOR_"..tostring(count).."_CASES_PASS")
