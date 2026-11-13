#!/usr/bin/env python3
"""Fail-closed V5->original 40 bridge, SCOUT lifetime and 600-851px HUD overlap."""
from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"tools/build_40_evolution_v5.py"
spec=importlib.util.spec_from_file_location("v5_bridge",p)
assert spec and spec.loader
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
checks=0
def check(condition:bool,label:str):
 global checks
 assert condition,label
 checks+=1
def fails(call,label:str):
 global checks
 try:call()
 except AssertionError:checks+=1
 else:raise AssertionError("FAIL_OPEN_NEGATIVE_"+label)
check(len(b.P39)==len(b.P40)==len(b.H1V5)==40,"immutable pins")
check(len(b.ORIG40_BLOBS)==5,"five exact frozen original40 overlays")
check(all(len(v)==40 for v in b.ORIG40_BLOBS.values()),"original40 blob pins")
check(len(b.V5_HORDE_BLOB)==40 and len(b.BASE39_POWER_BLOB)==40,"real source blobs")
visual_source=(b.OWN/"inputs/MusouHorde.luau").read_bytes()
check(b.gitblob(visual_source)==b.V5_HORDE_BLOB,"real V6 Horde exact GitBlob freeze")
check('MovingClaw_' in visual_source.decode() and 'CrownHorn_' in visual_source.decode(),"real V6 3D toy models")
check('m.arms[1].Orientation' in visual_source.decode() and 'm.attackAt=math.max(m.attackAt,now+.65)' in visual_source.decode(),"actual V6 visual movement and hit delay")
check('popup.Name="RealDamagePopup"' in visual_source.decode(),"v7 overhead damage GUI exists in actual one Horde module")
check('local realDamage=beforeHp-m.hp' in visual_source.decode(),"v7 popup never exaggerates actual lost HP")
check('m.popupUntil=now+.72' in visual_source.decode(),"v7 short bounded one-GUI impact effect")
check('elseif not m.hidden and now>=m.popupUntil then' in visual_source.decode(),"v7 KO remains visible for short feedback window")

check(b.HUD_OLD!=b.HUD_NEW,"real HUD count patch")
# Test genuine immutable author 40 source; no hand-made dummy source.
game_path=b.ORIG40/"Game.server.luau"
hud_path=b.ORIG40/"HUD.client.luau"
game=game_path.read_text(encoding="utf8")
hud=hud_path.read_text(encoding="utf8")
check(b.gitblob(game.encode())==b.ORIG40_BLOBS["server/Game.server.luau"],"real pinned Game blob")
check(b.gitblob(hud.encode())==b.ORIG40_BLOBS["client/HUD.client.luau"],"real pinned HUD blob")
g=b.upgrade_game(game)
h=b.upgrade_hud(hud)
check('musouEliteWarningSeconds' in g,"original Game server warning snapshot")
check('Evolution.nextEvolution(' in g and 'Power.beginAwaken(' in g,"all original evolution+power")
check('SCOUT_DURATION=5' in g and 'token.duration~=SCOUT_DURATION' in g,"original ability token duration preserved")
check('local scoutExpiresAt=serverNow()+SCOUT_DURATION' in g,"fixed real-server-clock scout lifetime")
check('evolutionGuards[player]={untilAt=scoutExpiresAt,' in g,"guard ends with real scout lifetime")
check('while serverNow()<scoutExpiresAt' in g,"no fictitious elapsed t plus .2")
check('evolvedStrikes<2' in g and 'nextEvolvedStrike=serverNow()+2.5' in g,"2 opportunities per 5-second assault summon")
check('evolvedStrikes+=1' in g,"attempt budget decremented on opportunity")
check('evolutionGuards[player]={untilAt=serverNow()+8,' not in g,"no falsely advertised guard8 when scout5")
check('nextEvolvedStrike=serverNow()+12' not in g,"no impossible assault second shot")
check('local hits=horde:hit(currentRoot.Position,currentRoot.CFrame.LookVector,' in g,"evolved assault starts at true player body height")
check('local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,' not in g,"no ungrounded aerial scout damage origin")
check('task.wait(.2);t+=.2' not in g,"no duration drift from scheduler delay")
check('PersistentHatch.settleProgress(' in g,"original Store still active")
check('赤い円の外へ' in h and 's.musouEliteWarningSeconds' in h,"real warning HUD")
check('EVOLVE_SCOUT' in h and 'AWAKEN_POWER' in h,"evolution and awakening controls retained")
check('MusouHordeCue",UDim2.new(.35,0,0,27)' in h,"mobile warning banner safe width")
check('RealH1ServerLevel",UDim2.new(.64,0,0,35)' in h,"level banner not under awaken")
check('local status = label(gui, "Status", UDim2.new(.64, 0, 0, 34)' in h,"status banner not under awaken")
check(h.count('local seq = 0')==1 and h.count('remote:FireServer(')==3,"one client intent path")
check(g.count('remote.OnServerEvent:Connect(')==1 and g.count('local function applyAttack(')==1,"one server intent authority")
# Negative mutations MUST fail at *the precise frozen author source shape*.
fails(lambda:b.upgrade_game(game.replace('horde:livingCount(),','horde:allEnemies(),')),"Game drift")
fails(lambda:b.upgrade_game(game.replace('evolutionGuards[player]={untilAt=serverNow()+8,','evolutionGuards[player]={untilAt=serverNow()+5,')),"guard drift")
fails(lambda:b.upgrade_game(game.replace('nextEvolvedStrike=serverNow()+12','nextEvolvedStrike=serverNow()+3')),"assault cooldown drift")
fails(lambda:b.upgrade_game(game.replace('local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,','local hits=horde:hit(fakeBody.Position,currentRoot.CFrame.LookVector,')),"assault true origin drift")
fails(lambda:b.upgrade_game(g),"double Game injection")
fails(lambda:b.upgrade_hud(hud.replace(b.HUD_OLD,'-- missing cue')),"HUD cue drift")
fails(lambda:b.upgrade_hud(hud.replace('MusouHordeCue",UDim2.new(.56,0,0,27)','MusouHordeCue",UDim2.new(.50,0,0,27)')),"HUD position drift")
fails(lambda:b.upgrade_hud(h),"double HUD injection")
fails(lambda:b.insertion("foo","bar","baz","missing"),"strict anchored source")
# Geometric proof on common phone landscape viewports. Labels ARE rectangular,
# rescue is conditional, but worst case both visible. x/y are GUI pixels.
def intersects(a,b):
 x,y,w,h=a
 xx,yy,ww,hh=b
 return min(x+w,xx+ww)>max(x,xx) and min(y+h,yy+hh)>max(y,yy)
for width,height in [(851,393),(768,432),(736,414),(600,400)]:
 rescue=(width-265,height-185-62,115,62)
 awaken=(width-140,height-260-62,110,62)
 cue=(width*.2,142,width*.35,27)
 status=(width*.12,65,width*.64,34)
 level=(width*.12,105,width*.64,35)
 check(not intersects(cue,rescue),f"{width}x{height} red-zone text vs rescue tap")
 check(not intersects(status,awaken),f"{width}x{height} status vs awaken")
 check(not intersects(level,awaken),f"{width}x{height} level vs awaken")
old_cue=(851*.22,142,851*.56,27)
old_rescue=(851-265,393-185-62,115,62)
check(intersects(old_cue,old_rescue),"old 40 HUD was genuinely overlapping on 851x393")
check("shutil.copytree(old,DIST)" in p.read_text(),"separate output dir only")
check("FAIL_CLOSED_NO_DESTRUCTIVE_REPLACE" in p.read_text(),"no destructive source overwrite")
check("original_40_unchanged" in p.read_text(),"all existing original40 source retained")
check("official_RC_adopted" in p.read_text() and "actual_studio_tested" in p.read_text(),"honest status")
print(f"P0D_EVOLUTION40_V5_SURGICAL_PATCH_NEGATIVE_PASS {checks}/{checks}")
