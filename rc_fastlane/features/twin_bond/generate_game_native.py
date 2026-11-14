#!/usr/bin/env python3
"""Extract and execute the ACTUAL composed Game attack helper and minion expression.

This tests Game integration in native Luau without faking a Roblox Studio run.
No feature source modification; wrong helper, missing guarded call or a cap
regression refuses to generate a runner.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

MARKER='local twinBondStorage = game:GetService("ServerStorage")'
END="local function applyAttack(player: Player, data)"
ATTACK=re.compile(
    r"math\.min\(3\.8,\s*savedPveMinionMultiplier\(player\)"
    r"\s*\*\s*twinBondOnlyNeutralMobBonus\(player\)\)"
)

TESTS=r'''--!nocheck
-- Generated from the exact COMPOSED Game, not from the adapter template.
local checked=0
local player={}
local studio=true
local available=true
local validType=true
local flagOn=true
local team="RED"
local bonus=1.1
local saved=1
local flag={Value=true,IsA=function(_,kind) return validType and kind=="BoolValue" end}
local storage={
    FindFirstChild=function(_,name)
        assert(name=="P0D_ENABLE_TWIN_BOND_PVE_V1")
        flag.Value=flagOn
        return if available then flag else nil
    end
}
local game={
    GetService=function(_,name)
        assert(name=="ServerStorage")
        return storage
    end
}
local RunService={IsStudio=function() return studio end}
local match={phase="ACTIVE"}
local carry={}
local function getTeamName(p)
    assert(p==player)
    return team
end
local TwinBond={pveMultiplier=function(p,t)
    assert(p==player and type(t)=="number")
    return bonus
end}
local function savedPveMinionMultiplier(p)
    assert(p==player)
    return saved
end
{{HELPER}}
local function combinedDamageMultiplier(p)
    return {{EXPR}}
end
local function check(name,actual,expected)
    checked+=1
    assert(math.abs(actual-expected)<0.000001,
        "BONDED_GAME_"..name.." got "..tostring(actual).." expected "..tostring(expected))
end
check("normal_red_level2",twinBondOnlyNeutralMobBonus(player),1.1)
bonus=1.2
check("normal_blue_level3",(function()team="BLUE"; return twinBondOnlyNeutralMobBonus(player)end)(),1.2)
team="RED"
bonus=9
check("bond_bonus_upper_clamp",twinBondOnlyNeutralMobBonus(player),1.2)
bonus=0.4
check("bond_bonus_lower_clamp",twinBondOnlyNeutralMobBonus(player),1)
bonus=1.2
available=false
check("no_flag_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
available=true
flagOn=false
check("flag_false_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
flagOn=true
validType=false
check("wrong_flag_type_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
validType=true
studio=false
check("not_studio_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
studio=true
match.phase="LOBBY"
check("lobby_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
match.phase="COUNTDOWN"
check("countdown_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
match.phase="ACTIVE"
carry[player]={egg=true}
check("egg_carrier_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
carry[player]=nil
team="NONE"
check("invalid_team_fails_closed",twinBondOnlyNeutralMobBonus(player),1)
team="RED"
saved=1
check("normal_damage_plus20",combinedDamageMultiplier(player),1.2)
saved=2
check("earned_damage_plus20",combinedDamageMultiplier(player),2.4)
saved=3.8
check("existing_max38_stays_capped",combinedDamageMultiplier(player),3.8)
saved=3.6
check("near_cap_stays_capped",combinedDamageMultiplier(player),3.8)
studio=false
saved=2
check("not_studio_no_bonus",combinedDamageMultiplier(player),2)
studio=true
flagOn=false
check("flag_off_no_bonus",combinedDamageMultiplier(player),2)
-- Real Game helper now exercises the EXACT compiled policy body, not a stub.
-- This proves the actual session Lv2/Lv3 state produces the promised bonus.
flagOn=true
saved=1
TwinBond=(function()
{{POLICY}}
end)()
check("real_no_bond_contract",combinedDamageMultiplier(player),1)
local accept2=TwinBond.select(player,"AWARIN",2,os.clock())
check("real_accept_level2",if accept2 then 1 else 0,1)
check("real_level2_bonus",twinBondOnlyNeutralMobBonus(player),1.1)
check("real_level2_horde_multiplier",combinedDamageMultiplier(player),1.1)
TwinBond.forget(player)
local accept3=TwinBond.select(player,"RAIKO",3,os.clock())
check("real_accept_level3",if accept3 then 1 else 0,1)
check("real_level3_bonus",twinBondOnlyNeutralMobBonus(player),1.2)
saved=2
check("real_level3_saved_damage",combinedDamageMultiplier(player),2.4)
saved=3.8
check("real_level3_cap38",combinedDamageMultiplier(player),3.8)
TwinBond.forget(player)
saved=1
check("real_after_forget_no_bonus",combinedDamageMultiplier(player),1)
assert(checked==27,"BONDED_GAME_ASSERTIONS_NOT_27_"..tostring(checked))
print("P0D_BOND_REAL_GAME_HELPER_NATIVE_27_CASES_PASS")
'''

def generate(source: Path, policy: Path, output: Path) -> None:
    game=source.read_text("utf8")
    pure=policy.read_text("utf8")
    assert pure.count("return Bond")==1 and "function Bond.select(" in pure
    assert "function Bond.pveMultiplier(" in pure and "function Bond.forget(" in pure
    assert game.count(MARKER)==1, "BOUND_GAME_SERVICE_MISSING_OR_DUPLICATE"
    assert game.count(END)==1, "ORIGINAL_GAME_ATTACK_AUTHORITY_CHANGED"
    start=game.index(MARKER)
    end=game.index(END,start)
    helper=game[start:end]
    assert helper.count("local function twinBondOnlyNeutralMobBonus(")==1
    assert 'not RunService:IsStudio() or not flag or not flag:IsA("BoolValue")' in helper
    assert 'flag.Value~=true or match.phase~="ACTIVE" or carry[player]~=nil' in helper
    assert 'return math.clamp(TwinBond.pveMultiplier(player,os.clock()),1,1.2)' in helper
    assert game.count('remote.OnServerEvent:Connect(')==1, "SECOND_GAME_REMOTE"
    matches=list(ATTACK.finditer(game))
    assert len(matches)==1, "BONDED_MINION_ATTACK_NOT_EXACTLY_ONCE"
    attack=matches[0]
    # Bind the expression to the ACTUAL single Horde call argument, not just
    # text within 650 bytes of a possibly unwired horde:hit invocation.
    pre='horde:hit(root.Position,look,'
    calls=[m.start() for m in re.finditer(re.escape(pre),game)]
    assert len(calls)==1,"HORDE_HIT_AUTHORITY_COUNT_NOT_ONE"
    call_at=calls[0]
    depth=1
    end_call=None
    for i in range(call_at+len('horde:hit('),len(game)):
        if game[i]=='(': depth+=1
        elif game[i]==')':
            depth-=1
            if depth==0:
                end_call=i
                break
    assert end_call is not None,"UNTERMINATED_HORDE_HIT"
    assert call_at < attack.start() < attack.end() < end_call,"BONUS_UNWIRED_FROM_HORDE"
    args=game[call_at+len('horde:hit('):end_call]
    pieces=[]
    level=0
    begin=0
    for pos,char in enumerate(args):
        if char=='(': level+=1
        elif char==')': level-=1
        elif char==',' and level==0:
            pieces.append(args[begin:pos].strip())
            begin=pos+1
        assert level>=0,"BAD_HORDE_ARGUMENT_PARENS"
    pieces.append(args[begin:].strip())
    assert len(pieces)==5,("BAD_HORDE_SIGNATURE",len(pieces))
    assert pieces[0]=="root.Position" and pieces[1]=="look"
    assert pieces[3]=="now" and pieces[4]=="player.Character"
    assert pieces[2].count(attack.group(0))==1,"BONUS_NOT_IN_DAMAGE_ARGUMENT"
    assert len(list(ATTACK.finditer(pieces[2])))==1,"MULTIPLIER_NOT_HORDE_DAMAGE"
    native=(TESTS.replace("{{HELPER}}",helper)
           .replace("{{EXPR}}",attack.group(0))
           .replace("{{POLICY}}",pure))
    assert "{{" not in native
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(native,encoding="utf8")
    print("P0D_BOND_REAL_COMPOSED_GAME_HANDLER_SOURCE_PIN_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--game",required=True,type=Path)
    parser.add_argument("--policy",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    generate(args.game,args.policy,args.out)
