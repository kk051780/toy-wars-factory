#!/usr/bin/env python3
"""FB-019 follow-on: source-locked server HIT/MISS after official local 3D swing gesture.
Only existing authoritative Game Remote may emit server HIT/MISS, no new authority.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
GAME="server/Game.server.luau"
HUD="client/HUD.client.luau"
KEY="FB019_ATTACK_RESPONSE_V1"
PIN_GAME="5648ff17b54fd9f9e949d641b41178d43e8a9c28"
PIN_HUD="0cfa5b882ff44bf6ba12dfce96ca11e262dd3ec1"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def read(dist:Path)->dict[str,bytes]:
    assert dist.is_dir() and not dist.is_symlink()
    for p in dist.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(dist.resolve()),p
    src=dist/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}
def one(s:str,old:str,new:str)->str:
    assert s.count(old)==1,("FB019_EXACT_DRIFT",old[:100],s.count(old))
    assert new not in s,("FB019_ALREADY_APPLIED",new[:80])
    return s.replace(old,new,1)

def patch_game(raw:bytes)->bytes:
    assert blob(raw)==PIN_GAME,"FB019_DIRECT_GAME_PIN_DRIFT"
    src=raw.decode("utf8")
    marker="local function applyAttack(player: Player, data)"
    end="-- H1 RAIDER wind:"
    assert src.count(marker)==src.count(end)==1
    a=src.index(marker);b=src.index(end,a)
    block=src[a:b]
    assert 'if type(data) ~= "table" or data.action ~= "ATTACK" then return end' in block
    assert 'if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end' in block
    assert 'SoloTeamBots.tryHumanHit(' in block and 'horde:hit(' in block
    assert 'remote:FireClient(player, {kind="P0D_ATTACK_RESULT"' not in block
    block=one(block,'    lastAttack[player] = now\n','''    lastAttack[player] = now
    -- Only accepted valid-sequence / correct-phase / cooldown-cleared hits.
    -- Never use client-selected target, client position, or client damage.
    local function attackResponse(status:string,target:string)
        remote:FireClient(player,{kind="P0D_ATTACK_RESULT",status=status,
            target=target,serial=match.serial,seq=data.seq})
    end
''')
    block=one(block,'''        if ok and hum then
            hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"]
                *earnedDamageMultiplier(player,"PLAYER"))
        end
        return''','''        if ok and hum then
            local beforeHealth = hum.Health
            hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"]
                *earnedDamageMultiplier(player,"PLAYER"))
            -- A ForceField or zero effective damage must never display a fake HIT.
            -- If a sweep also hit a real minion, prioritize that result.
            if mobHits>0 then
                attackResponse("HIT","MINION")
            elseif hum.Health < beforeHealth then
                attackResponse("HIT","PLAYER")
            else
                attackResponse("MISS","BLOCKED")
            end
        elseif mobHits>0 then
            attackResponse("HIT","MINION")
        else
            attackResponse("MISS","NONE")
        end
        return''')
    block=one(block,'    if mobHits>0 then return end','    if mobHits>0 then attackResponse("HIT","MINION"); return end')
    block=one(block,'''            victim.hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"])
            return''','''            local beforeBotHealth = victim.hum.Health
            victim.hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"])
            if victim.hum.Health < beforeBotHealth then
                attackResponse("HIT","BOT")
            else
                attackResponse("MISS","BLOCKED")
            end
            return''')
    block=one(block,'    if not Rules.damageCandidate(distance, aim, Config.CastleReach) then return end','''    if not Rules.damageCandidate(distance, aim, Config.CastleReach) then
        attackResponse("MISS","NONE")
        return
    end''')
    block=one(block,'    if hit and hit.Instance ~= core then return end','''    if hit and hit.Instance ~= core then
        attackResponse("MISS","BLOCKED")
        return
    end''')
    block=one(block,'''    match.hp[enemy] = math.max(0, match.hp[enemy] - Config.CastleAttackDamage[roles[player] or "RAIDER"])
''','''    local beforeCastleHealth = match.hp[enemy]
    match.hp[enemy] = math.max(0, match.hp[enemy] - Config.CastleAttackDamage[roles[player] or "RAIDER"])
    if match.hp[enemy] < beforeCastleHealth then
        attackResponse("HIT","CASTLE")
    else
        attackResponse("MISS","NONE")
    end
''')
    assert block.count('attackResponse("HIT"')==6
    assert block.count('attackResponse("MISS"')==6
    assert block.count('remote:FireClient(player,{kind="P0D_ATTACK_RESULT"')==1
    return (src[:a]+block+src[b:]).encode("utf8")

CUE_CLIENT='''-- FB-019 follow-on: physical swing remains from the existing official HUD.
-- Only the authoritative server-confirmed HIT/MISS updates the same button briefly.
local originalAttackText = attack.Text
local originalAttackColor = attack.BackgroundColor3
local lastAttackFeedbackSeq = -1
local attackFeedbackVersion = 0
local function flashConfirmedAttack(message:string,color:Color3)
    attackFeedbackVersion += 1
    local version = attackFeedbackVersion
    attack.Text = message
    attack.BackgroundColor3 = color
    task.delay(.28,function()
        if attackFeedbackVersion==version and attack.Parent~=nil then
            attack.Text = originalAttackText
            attack.BackgroundColor3 = originalAttackColor
        end
    end)
end
remote.OnClientEvent:Connect(function(packet:any)
    if type(packet)~="table" or packet.kind~="P0D_ATTACK_RESULT"
        or not attack.Visible or packet.serial~=lastSerial then return end
    -- An old ACK cannot label a newer swing as its own hit or miss.
    if type(packet.seq)~="number" or packet.seq~=lastIssuedAttackSeq
        or packet.seq<=lastAttackFeedbackSeq then return end
    lastAttackFeedbackSeq=packet.seq
    if packet.status=="HIT" then
        flashConfirmedAttack("⚔ 命中!",Color3.fromRGB(54,160,105))
    elseif packet.status=="MISS" then
        flashConfirmedAttack("⚔ 空振り",Color3.fromRGB(98,119,142))
    end
end)'''

def patch_hud(raw:bytes)->bytes:
    assert blob(raw)==PIN_HUD,"FB019_DIRECT_HUD_PIN_DRIFT"
    src=raw.decode("utf8")
    assert src.count("local lastSerial = -1")==1
    assert src.count("attack.Activated:Connect(pressAttack)")==1
    assert src.count("local function showLocalSwing()")==1
    assert src.count("local function pressAttack()")==1
    assert "P0D_ATTACK_RESULT" not in src
    src=one(src,"local seq = 0\n",
        "local seq = 0\nlocal lastIssuedAttackSeq=-1\n")
    src=one(src,'    seq += 1\n    -- No target, position, score, damage or client-side server timestamps in payload.',
        '    seq += 1\n    if kind=="ATTACK" then lastIssuedAttackSeq=seq end\n    -- No target, position, score, damage or client-side server timestamps in payload.')
    src=one(src,"attack.Activated:Connect(pressAttack)",
        "attack.Activated:Connect(pressAttack)\n"+CUE_CLIENT)
    assert src.count("attack.Activated:Connect(pressAttack)")==1
    assert src.count("remote.OnClientEvent:Connect(")==2
    assert src.count("FireServer({action = kind")==3
    assert src.count("local function showLocalSwing()")==1
    assert src.count("local function pressAttack()")==1
    return src.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"FB019_OFF_ZERO_WRITE"
        print("FB019_ATTACK_OFF_ZERO_WRITE_PASS");return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==80 and GAME in before and HUD in before
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    oldpins={p:blob(v) for p,v in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==oldpins
    assert oldpins[GAME]==PIN_GAME and oldpins[HUD]==PIN_HUD
    for feature in ("FB016_FOLIAGE_PASSAGE_20261114",
                    "FB017_NO_PERSISTENT_BATTLE_GUIDES",
                    "FB018_ACTION_BUTTON_TEXT_INIT",
                    "FB019_RESPONSIVE_ATTACK_INPUT_SWING",
                    "FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2"):
        assert fl["feature_flags"][feature] is True,("FB019_REQUIRED_PARENT",feature)
    assert KEY not in fl["feature_flags"]
    after={**before,GAME:patch_game(before[GAME]),HUD:patch_hud(before[HUD])}
    assert len(after)==80 and {p for p in before if before[p]!=after[p]}=={GAME,HUD}
    pins={p:blob(v) for p,v in sorted(after.items())}
    receipt={
        "feedback":"FB-019","id":KEY,"source_count":80,
        "changed_sources":[GAME,HUD],"other78_byte_exact":True,
        "original_blob":{GAME:oldpins[GAME],HUD:oldpins[HUD]},
        "new_blob":{GAME:pins[GAME],HUD:pins[HUD]},
        "server_valid_seq_phase_cooldown_kept":True,
        "client_hit_not_authoritative":True,
        "one_game_one_remote_same_damage_authority":True,
        "new_source_count":0,
        "cue":"preserve_official_3D_swing_add_server_confirmed_280ms_hit_miss",
        "studio":"NOT_TESTED","owner_acceptance":"NOT_TESTED",
        "official_adopted":False,
        "rollback":"omit this follow-on overlay and keep official FB019 swing RC80",
    }
    sl["blobs"]=pins;sl["fb019_attack"]=receipt
    fl["source_gitblobs"]=pins;fl["feature_flags"][KEY]=True
    fl["fb019_attack"]=receipt
    temp=Path(tempfile.mkdtemp(prefix=".fb019_",dir=str(out.parent)))
    staged=temp/"dist"
    try:
        shutil.copytree(base,staged,symlinks=False)
        for path in (GAME,HUD):(staged/"src"/path).write_bytes(after[path])
        for name,obj in (("SOURCE_LOCK.json",sl),("RC_FEATURE_LOCK.json",fl)):
            (staged/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("FB019_SERVER_ACK_AFTER_OFFICIAL_SWING_2_CHANGED_78_EXACT_PASS")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
