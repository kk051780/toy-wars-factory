#!/usr/bin/env python3
"""FB-019: source-locked 80->80 real Game + HUD combat input feedback repair.
Only existing authoritative Game Remote may emit server HIT/MISS, no new authority.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
GAME="server/Game.server.luau"
HUD="client/HUD.client.luau"
KEY="FB019_ATTACK_RESPONSE_V1"
PIN_GAME="7ad806322554499ca91cef7c36f31aad438642b4"
PIN_HUD="0bc1af1af5ff4c30cb51106b3fad5c662a403393"

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
            hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"]
                *earnedDamageMultiplier(player,"PLAYER"))
            attackResponse("HIT","PLAYER")
        elseif mobHits>0 then
            attackResponse("HIT","MINION")
        else
            attackResponse("MISS","NONE")
        end
        return''')
    block=one(block,'    if mobHits>0 then return end','    if mobHits>0 then attackResponse("HIT","MINION"); return end')
    block=one(block,'''            victim.hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"])
            return''','''            victim.hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"])
            attackResponse("HIT","BOT")
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
''','''    match.hp[enemy] = math.max(0, match.hp[enemy] - Config.CastleAttackDamage[roles[player] or "RAIDER"])
    attackResponse("HIT","CASTLE")
''')
    assert block.count('attackResponse("HIT"')==5
    assert block.count('attackResponse("MISS"')==3
    assert block.count('remote:FireClient(player,{kind="P0D_ATTACK_RESULT"')==1
    return (src[:a]+block+src[b:]).encode("utf8")

CUE_CLIENT='''-- FB019: press is input only, never fake damage. Server confirms HIT/MISS.
local attackBaseText=attack.Text
local attackBaseColor=attack.BackgroundColor3
local attackCueVersion=0
local function cueAttack(label:string,color:Color3)
    attackCueVersion+=1
    local version=attackCueVersion
    attack.Text=label
    attack.BackgroundColor3=color
    task.delay(.28,function()
        if attackCueVersion==version and attack.Parent~=nil then
            attack.Text=attackBaseText
            attack.BackgroundColor3=attackBaseColor
        end
    end)
end
attack.Activated:Connect(function()
    if not attack.Visible or not attack.Active then return end
    action("ATTACK",nil)
    cueAttack("⚔ 入力",Color3.fromRGB(180,115,65))
end)
-- Reuse the existing RemoteEvent; no new Game authority or permanent text.
remote.OnClientEvent:Connect(function(packet:any)
    if type(packet)~="table" or packet.kind~="P0D_ATTACK_RESULT"
        or not attack.Visible or packet.serial~=lastSerial then return end
    if packet.status=="HIT" then
        cueAttack("⚔ 命中!",Color3.fromRGB(54,160,105))
    elseif packet.status=="MISS" then
        cueAttack("⚔ 空振り",Color3.fromRGB(98,119,142))
    end
end)'''
def patch_hud(raw:bytes)->bytes:
    src=raw.decode("utf8")
    assert src.count("local lastSerial = -1")==1
    assert src.count("local function action(kind: string, role: string?)")==1
    src=one(src,'attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)',CUE_CLIENT)
    src=one(src,'if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil)',
        'if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil); cueAttack("⚔ 入力",Color3.fromRGB(180,115,65))')
    assert src.count("attack.Activated:Connect(")==1
    assert "attack.MouseButton1Click:Connect" not in src
    assert src.count("remote.OnClientEvent:Connect(")==2
    assert src.count("FireServer({action = kind")==3
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
                    "FB018_ACTION_BUTTON_TEXT_INIT"):
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
        "cue":"existing_attack_button_only_280ms",
        "studio":"NOT_TESTED","owner_acceptance":"NOT_TESTED",
        "official_adopted":False,
        "rollback":"omit FB019 overlay and keep FB018 official RC80",
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
    print("FB019_ATTACK_ONLY_GAME_HUD_CHANGED_OTHER78_EXACT_PASS")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
