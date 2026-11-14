-- Native executable assertions against the REAL authored Director module.
local cases = 0
local function expect(ok, reason)
    assert(ok, reason or ("CASE_" .. tostring(cases+1)))
    cases += 1
end
for _, entry in ipairs({
    {"SKY","空"},{"SEA","海"},{"EMBER","炎"},{"STAR","星"},
}) do
    local fact={featureEnabled=true,speakerId="ORACLE",signal="SECRET_HINT",
        hintUnlocked=true,missingRealm=entry[1]}
    local m=Director.Compose(fact)
    expect(type(m)=="table" and m.isGeneratedAI==false,entry[1].."_VISIBLE")
    expect(string.find(m.text,entry[2],1,true)~=nil,entry[1].."_TEXT")
    expect(m.text==m.voiceText and m.caption==m.text,entry[1].."_VOICE")
end
local completed=Director.Compose({featureEnabled=true,speakerId="ORACLE",
    signal="REALM_COMPLETE",allRealmsComplete=true})
expect(completed~=nil and string.find(completed.text,"4つ",1,true)~=nil,"FOUR_REALM_COMPLETE")
expect(Director.Compose({featureEnabled=true,speakerId="ORACLE",
    signal="REALM_COMPLETE",allRealmsComplete=false})==nil,"NO_FAKE_COMPLETE")
expect(Director.Compose({featureEnabled=true,speakerId="ORACLE",
    signal="SECRET_HINT",hintUnlocked=false,missingRealm="SKY"})==nil,"NO_LOCKED_HINT")
expect(Director.Compose({featureEnabled=true,speakerId="ORACLE",
    signal="SECRET_HINT",hintUnlocked=true,missingRealm="UNKNOWN"})==nil,"NO_UNKNOWN_REALM")
local battle=Director.Compose({featureEnabled=true,speakerId="NAVI",
    signal="ENEMY_ALERT",observedByTeam=true,areaCode="west"})
expect(battle~=nil and battle.urgent==true,"LOS_ENEMY_ALERT")
expect(Director.Compose({featureEnabled=true,speakerId="NAVI",
    signal="ENEMY_ALERT",observedByTeam=false,areaCode="west"})==nil,"BLOCK_UNSEEN_ENEMY")
expect(Director.Compose({featureEnabled=true,speakerId="NAVI",signal="HELLO"})~=nil,"SAFE_GREETING")
expect(Director.Compose({featureEnabled=true,speakerId="TRICK",signal="TRICK_RUMOR"})~=nil,"TRICK_RUMOR")
expect(Director.CanSpeak(10,nil,false)==true,"FIRST_SPEECH")
expect(Director.CanSpeak(15,10,false)==false,"COOLDOWN_30S")
expect(Director.CanSpeak(24,10,true)==false,"URGENT_15S")
expect(Director.CanSpeak(25,10,true)==true,"URGENT_15S_COMPLETE")
expect(Director.CanSpeak(40,10,false)==true,"NORMAL_30S_COMPLETE")
print("P0D_NPC_ORACLE_NATIVE_DIRECTOR_PASS",cases)
