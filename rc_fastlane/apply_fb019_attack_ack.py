#!/usr/bin/env python3
"""FB-019: source-locked, server-acknowledged melee-swing feedback for actual RC80.

Existing Game still alone owns cooldown, target selection, NPC/AI/player/castle
damage and score. One HUD script and that Game script change; source count 80.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
from apply_fb018_button_label import read,blob

HUD="client/HUD.client.luau"
GAME="server/Game.server.luau"
OLD_HUD="0bc1af1af5ff4c30cb51106b3fad5c662a403393"
OLD_GAME="7ad806322554499ca91cef7c36f31aad438642b4"
FEATURE="FB019_SERVER_ACKNOWLEDGED_ATTACK_SWING"
GAME_OLD='    lastAttack[player] = now\n    local look = root.CFrame.LookVector'
GAME_NEW='''    lastAttack[player] = now
    -- P0 FB019: send a swing acknowledgement ONLY after the authoritative
    -- ACTIVE/alive/cooldown/seq gate. It is NOT a hit or damage confirmation.
    remote:FireClient(player,{kind="ATTACK_SWING_ACK",seq=data.seq,serial=match.serial})
    local look = root.CFrame.LookVector'''
HUD_OLD='attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)'
HUD_KEY_OLD='if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil)'
HUD_VFX=r'''-- FB019: one tiny transient world slash; no full-screen guide, false hit or client damage.
local attackPhase="LOBBY"
local lastSwingAck=-1
local function renderAcknowledgedSwing()
    local char=player.Character
    local root=char and char:FindFirstChild("HumanoidRootPart")
    if not root or not root:IsA("BasePart") then return end
    local start=Instance.new("Attachment")
    start.Name="FB019SwingL"
    start.Position=Vector3.new(-2,1.5,-2.6)
    start.Parent=root
    local finish=Instance.new("Attachment")
    finish.Name="FB019SwingR"
    finish.Position=Vector3.new(2,1.65,-2.6)
    finish.Parent=root
    local arc=Instance.new("Beam")
    arc.Name="FB019SwingArc"
    arc.Attachment0=start
    arc.Attachment1=finish
    arc.CurveSize0=2
    arc.CurveSize1=-1.6
    arc.Width0=.48
    arc.Width1=.05
    arc.Color=ColorSequence.new(Color3.fromRGB(255,222,130),Color3.fromRGB(255,255,255))
    arc.Transparency=NumberSequence.new(.1)
    arc.LightEmission=.7
    arc.FaceCamera=true
    arc.Parent=root
    local debris=game:GetService("Debris")
    debris:AddItem(arc,.22)
    debris:AddItem(start,.22)
    debris:AddItem(finish,.22)
end
remote.OnClientEvent:Connect(function(packet)
    if type(packet)~="table" then return end
    if packet.kind=="SNAPSHOT" and type(packet.phase)=="string" then
        attackPhase=packet.phase
    elseif packet.kind=="ATTACK_SWING_ACK" then
        if type(packet.seq)~="number" or packet.seq<=lastSwingAck then return end
        lastSwingAck=packet.seq
        renderAcknowledgedSwing()
    end
end)
local function requestAttack()
    if attackPhase~="ACTIVE" then
        -- Briefly label only the existing button; never persist a guide over play.
        local original=attack.Text
        attack.Text="出撃後に攻撃"
        task.delay(.65,function()
            if attack.Parent and attack.Text=="出撃後に攻撃" then
                attack.Text=original
            end
        end)
        return
    end
    action("ATTACK",nil)
end
attack.Activated:Connect(requestAttack)'''

def single(text:str,before:str,after:str,tag:str)->str:
    count=text.count(before)
    assert count==1,(tag,"ANCHOR_COUNT",count)
    return text.replace(before,after,1)

def transform(sources:dict[str,bytes])->dict[str,bytes]:
    assert len(sources)==80 and HUD in sources and GAME in sources
    assert blob(sources[HUD])==OLD_HUD, "RC80_FB018_HUD_PIN_CHANGED"
    assert blob(sources[GAME])==OLD_GAME, "RC80_GAME_PIN_CHANGED"
    oldgame=sources[GAME].decode("utf8")
    oldhud=sources[HUD].decode("utf8")
    newgame=single(oldgame,GAME_OLD,GAME_NEW,"GAME_ATTACK_COOLDOWN")
    assert newgame.index('remote:FireClient(player,{kind="ATTACK_SWING_ACK"') > newgame.index('lastAttack[player] = now')
    # Never change original damage authority. ACK is *before* the real hit test,
    # after all server anti-replay/phase/cooldown gates.
    newhud=single(oldhud,HUD_OLD,HUD_VFX,"HUD_ATTACK_INPUT")
    newhud=single(newhud,HUD_KEY_OLD,'if input.KeyCode == Enum.KeyCode.F then requestAttack()', "KEY_F_ENTRY")
    assert newhud.count("attack.Activated:Connect(requestAttack)")==1
    assert "MouseButton1Click:Connect(function() action(\"ATTACK\"" not in newhud
    for forbidden in ("TakeDamage(", "FireServer({action=\"ATTACK_SWING_ACK\"", "MarketplaceService"):
        assert forbidden not in HUD_VFX
    updated=dict(sources)
    updated[GAME]=newgame.encode("utf8")
    updated[HUD]=newhud.encode("utf8")
    assert len(updated)==80 and {p for p in sources if sources[p]!=updated[p]}=={GAME,HUD}
    return updated

def apply(base:Path,out:Path,enabled:bool):
    if not enabled:
        assert not out.exists(),"OFF_REQUIRES_ZERO_WRITE"
        print("FB019_OFF_ZERO_WRITE_PASS")
        return
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    pins_old={p:blob(b) for p,b in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins_old
    for needed in ("FB016_FOLIAGE_PASSAGE_20261114",
                   "FB017_NO_PERSISTENT_BATTLE_GUIDES",
                   "FB018_ACTION_BUTTON_TEXT_INIT"):
        assert fl["feature_flags"].get(needed) is True,(needed,"REQUIRED")
    assert FEATURE not in fl["feature_flags"],"DUPLICATE_ADOPTION"
    after=transform(before)
    pins={p:blob(data) for p,data in sorted(after.items())}
    record={
      "feedback":"FB-019","feature_id":FEATURE,
      "sources":80,"modified":[GAME,HUD],"other78_byte_exact":True,
      "old_game_sha":OLD_GAME,"old_hud_sha":OLD_HUD,
      "new_game_sha":pins[GAME],"new_hud_sha":pins[HUD],
      "server_gates":"original seq, phase, alive, cooldown; ACK only after validated swing",
      "client_controls":"Activated supports mouse/touch; F keyboard same requestAttack",
      "no_hit_claim":True,"no_new_remote":True,"single_game_authority":True,
      "feedback":"server-ACK transient 0.22s Beam slash, lobby button 0.65s message",
      "required_studio_tests":["PC mouse","mobile tap","F key","lobby","cooldown",
          "actual NPC/AI damage","miss visual","single/2 client","respawn"],
      "studio":"NOT_TESTED","owner_accepted":False,
      "rollback":"omit FB019 adapter to preserve exact previous RC80"
    }
    sl["blobs"]=pins;sl["fb019_attack_ack"]=record
    fl["source_gitblobs"]=pins
    fl["feature_flags"][FEATURE]=True
    fl["fb019_attack_ack"]=record
    t=Path(tempfile.mkdtemp(prefix=".fb019_",dir=str(out.parent)))
    try:
        staged=t/"dist"
        shutil.copytree(base,staged,symlinks=False)
        for p in (GAME,HUD):
            (staged/"src"/p).write_bytes(after[p])
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(t,ignore_errors=True)
    print("FB019_80SOURCES_2PATCH_SAME_GAME_AUTHORITY_PASS",pins[GAME],pins[HUD])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    x=p.parse_args();apply(x.base,x.out,x.enabled=="true")
