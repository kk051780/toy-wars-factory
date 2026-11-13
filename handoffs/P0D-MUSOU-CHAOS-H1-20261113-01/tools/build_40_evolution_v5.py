#!/usr/bin/env python3
"""Rebuild the EXACT 40-Luau owned evolution H1 with the #288 v5 elite warning.

READ-ONLY frozen upstream snapshots:
  _p0d_frozen_39 = verified parent #285 SHA cb2540... (rebuild actual 39 scripts)
  _p0d_frozen_40 = original #40 evolution SHA 1b21bf... (five pinned overlays)
Writes only our own #288 dist; NEVER edits author sources or RC/main.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

OWN=Path(__file__).resolve().parents[1]
REPO=OWN.parents[1]
P39="cb2540dc4a3e5b819c0e3598d4af5e2b6dca76d3"
P40="1b21bf8e5fc6afa5c74813d7f1037f877e1273ed"
H1V5="adb1150951c5b5a6221f71204ce91ea693e34847"
OLD39=REPO/"_p0d_frozen_39"
OLD40=REPO/"_p0d_frozen_40"
ORIG40=OLD40/"handoffs/P0D-EARNED-EVOLUTION-FULL-H1-20261113-01/inputs"
BASE39=OLD39/"handoffs/P0D-MUSOU-EARNED-POWER-H1-20261113-01"
DIST=OWN/"dist/EGG_RAID_RUMBLE_H1_EVOLUTION_MUSOU_V5_PRIVATE_BRIDGE"
ORIG40_BLOBS={
 "server/Game.server.luau":"8b5fdf62f764ab6c963758d699cdfc681ed2ef96",
 "client/HUD.client.luau":"8c83efc18f63cea077de3dc3a8006bc11f05200c",
 "server/PersistentHatchStore.luau":"7e00a53e72479ffa643556ae5fe07c931f7507e7",
 "server/MusouHorde.luau":"7edfda9e5a1d4ac8ae47d66ea7cf908eb8e4af6e",
 "server/EvolutionRules.luau":"0efca67b41e34917038fdc883c8ad34f3eb3c2e2",
}
V5_HORDE_BLOB="8c147c801e7fa1ff362922d66c9a6fd432fc8b6e"
BASE39_POWER_BLOB="86e79877cf0e58603a4de67db29155bf98cc511d"

def gitblob(raw:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def scripts(path:Path)->dict[str,bytes]:
 return {f.relative_to(path/"src").as_posix():f.read_bytes()
         for f in sorted((path/"src").rglob("*.luau"))}
def insertion(src:str,old:str,new:str,label:str)->str:
 assert src.count(old)==1,("PATCH_CONFLICT_FAIL_CLOSED",label,src.count(old))
 assert new not in src,("DUPLICATE_PATCH_FAIL_CLOSED",label)
 return src.replace(old,old+new,1)

def upgrade_game(s:str)->str:
 assert "Evolution.nextEvolution(" in s and "Power.beginAwaken(" in s
 assert 'if mobHits>0 then return end' in s
 s=insertion(s,"        musouMobCount = horde:livingCount(),\n",
    "        musouEliteWarningSeconds = if RunService:IsStudio()\n"
    "            then horde:eliteWarningSeconds(now) else 0,\n",
    "EXACT_EVOLUTION40_GAME_SNAPSHOT")
 # Independent QA detected an *actual* gameplay mismatch in original 40:
 # token/SCOUT_DURATION=5s, guard claimed 8s but cleanup dies at 5s,
 # assault 12s repeat never fires during the 5s scout. Preserve token
 # authority. Use one real clock expiry for existing 5s token AND guard;
 # stage2+ assault can execute at most 2 opportunities per 5s summon.
 for before,after,label in [
  ("    local epoch=match.serial\n    -- The only H1 Game owns both actual abilities;",
   "    local epoch=match.serial\n    local scoutExpiresAt=serverNow()+SCOUT_DURATION\n    -- The only H1 Game owns both actual abilities;","SCOUT_EXPIRY_CLOCK"),
  ("evolutionGuards[player]={untilAt=serverNow()+8,",
   "evolutionGuards[player]={untilAt=scoutExpiresAt,","GUARD_5S_REAL_EXPIRY"),
  ("        local nextEvolvedStrike=0\n",
   "        local nextEvolvedStrike=0\n        local evolvedStrikes=0\n","ASSAULT_STRIKE_COUNTER"),
  ("        local t=0\n        while t<SCOUT_DURATION and scoutModels[player]==model",
   "        while serverNow()<scoutExpiresAt and scoutModels[player]==model","SCOUT_REAL_CLOCK_DURATION"),
  ("            if stage>=2 and branch==\"ASSAULT\"\n                and serverNow()>=nextEvolvedStrike then",
   "            if stage>=2 and branch==\"ASSAULT\"\n                and evolvedStrikes<2 and serverNow()>=nextEvolvedStrike then","ASSAULT_MAX_TWO_OPPORTUNITIES"),
  ("                nextEvolvedStrike=serverNow()+12",
   "                evolvedStrikes+=1\n                nextEvolvedStrike=serverNow()+2.5","ASSAULT_REPEAT_2_5S"),
  ("            task.wait(.2);t+=.2","            task.wait(.2)","REMOVE_FAKE_ELAPSED_CLOCK"),
 ]:
  assert s.count(before)==1,("PATCH_CONFLICT_FAIL_CLOSED",label,s.count(before))
  # Generic task.wait(.2) legitimately appears in other original Game loops.
  # Require the exact source anchor once; reject duplicated specific tokens.
  if label!="REMOVE_FAKE_ELAPSED_CLOCK":
   assert after not in s,("DUPLICATE_PATCH_FAIL_CLOSED",label)
  s=s.replace(before,after,1)
 return s

HUD_OLD='''        mobCue.Text="⚔ 中立兵 "..tostring(alive).."体  |  "
            ..(if combo>1 then tostring(combo).."連撃！" else "斬って進もう！")'''
HUD_NEW='''        local warn=s.musouEliteWarningSeconds
        local remaining=if type(warn)=="number" and warn==warn and warn>0
            and warn<=1.5 then math.ceil(warn*10)/10 else 0
        mobCue.Text=if remaining>0
            then "⚠ 赤い円の外へ！ "..tostring(remaining).."秒"
            else "⚔ 中立兵 "..tostring(alive).."体  |  "
                ..(if combo>1 then tostring(combo).."連撃！" else "斬って進もう！")
        mobCue.TextColor3=if remaining>0 then Color3.fromRGB(255,110,90)
            else Color3.fromRGB(255,221,132)'''

def upgrade_hud(s:str)->str:
 assert 'EVOLVE_SCOUT' in s and 'AWAKEN_POWER' in s
 assert s.count(HUD_OLD)==1,("PATCH_CONFLICT_FAIL_CLOSED","EXACT_EVOLUTION40_HUD",s.count(HUD_OLD))
 assert HUD_NEW not in s, "DUPLICATE_PATCH_FAIL_CLOSED"
 s=s.replace(HUD_OLD,HUD_NEW,1)
 # 851x393 landscape: old 0.56w warning banner x.22..78 overlaps
 # rescue button from w-265..w-150 (y~146-208). Shrink banner and
 # top/status/level text to avoid earned awakening (x w-140..w-30).
 for before,after,label in [
  ('local mobCue=label(gui,"MusouHordeCue",UDim2.new(.56,0,0,27),',
   'local mobCue=label(gui,"MusouHordeCue",UDim2.new(.35,0,0,27),',
   'MOBILE_MOB_CUE_NARROW'),
  ('    UDim2.new(.22,0,0,142),Color3.fromRGB(255,221,132),14)',
   '    UDim2.new(.20,0,0,142),Color3.fromRGB(255,221,132),14)',
   'MOBILE_MOB_CUE_CENTER'),
  ('local status = label(gui, "Status", UDim2.new(.76, 0, 0, 34),',
   'local status = label(gui, "Status", UDim2.new(.64, 0, 0, 34),',
   'MOBILE_STATUS_NOT_UNDER_AWAKEN'),
  ('local progressBadge=label(gui,"RealH1ServerLevel",UDim2.new(.76,0,0,35),',
   'local progressBadge=label(gui,"RealH1ServerLevel",UDim2.new(.64,0,0,35),',
   'MOBILE_LEVEL_NOT_UNDER_AWAKEN'),
 ]:
  assert s.count(before)==1,("PATCH_CONFLICT_FAIL_CLOSED",label,s.count(before))
  assert after not in s,("DUPLICATE_PATCH_FAIL_CLOSED",label)
  s=s.replace(before,after,1)
 return s

def assemble():
 assert not DIST.exists(),"FAIL_CLOSED_NO_DESTRUCTIVE_REPLACE"
 for checkout,sha in [(OLD39,P39),(OLD40,P40)]:
  assert (checkout/".git").exists(),("FROZEN_CHECKOUT_REQUIRED",checkout)
  head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=checkout,text=True).strip()
  assert head==sha,("FROZEN_GIT_HEAD_DRIFT",checkout,sha,head)
 assert not (BASE39/"dist/EGG_RAID_RUMBLE_MUSOU_EARNED_POWER_H1_PRIVATE_STUDIO_ONLY").exists(), "NO_PARENT_DIST_OVERWRITE"
 subprocess.run([sys.executable,"-B",str(BASE39/"tools/assemble.py"),"--assemble"],
                cwd=OLD39,check=True)
 old=BASE39/"dist/EGG_RAID_RUMBLE_MUSOU_EARNED_POWER_H1_PRIVATE_STUDIO_ONLY"
 before=scripts(old)
 assert len(before)==39,len(before)
 assert gitblob(before["server/PowerFantasyRules.luau"])==BASE39_POWER_BLOB
 assert "server/MusouHorde.luau" in before
 assert "server/EvolutionRules.luau" not in before
 for rel,expected in ORIG40_BLOBS.items():
  raw=(ORIG40/Path(rel).name).read_bytes()
  assert gitblob(raw)==expected,("40_BASE_INPUT_DRIFT",rel)
 shutil.copytree(old,DIST)
 for rel in ORIG40_BLOBS:
  dst=DIST/"src"/rel
  dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes((ORIG40/Path(rel).name).read_bytes())
 base=scripts(DIST)
 assert len(base)==40
 assert sorted(set(base)-set(before))==["server/EvolutionRules.luau"]
 assert sorted(k for k in before if before[k]!=base[k])==[
    "client/HUD.client.luau","server/Game.server.luau",
    "server/MusouHorde.luau","server/PersistentHatchStore.luau"]
 assert all(base[k]==before[k] for k in before if k not in ORIG40_BLOBS)
 assert base["server/PowerFantasyRules.luau"]==before["server/PowerFantasyRules.luau"]
 game=upgrade_game(base["server/Game.server.luau"].decode("utf8"))
 hud=upgrade_hud(base["client/HUD.client.luau"].decode("utf8"))
 new_horde=(OWN/"inputs/MusouHorde.luau").read_bytes()
 assert gitblob(new_horde)==V5_HORDE_BLOB, "ORIGINAL_288_V5_HORDE_DRIFT"
 assert 'z.Name="ELITE_SWEEP_DANGER_RADIUS"' in new_horde.decode()
 assert "function Horde:eliteWarningSeconds(now: number): number" in new_horde.decode()
 patched={
  "server/Game.server.luau":game.encode(),
  "client/HUD.client.luau":hud.encode(),
  "server/MusouHorde.luau":new_horde,
 }
 for name,raw in patched.items():
  (DIST/"src"/name).write_bytes(raw)
 result=scripts(DIST)
 assert len(result)==40
 assert sorted(k for k in base if base[k]!=result[k])==[
  "client/HUD.client.luau","server/Game.server.luau","server/MusouHorde.luau"]
 assert all(result[k]==base[k] for k in base if k not in patched)
 g=result["server/Game.server.luau"].decode()
 h=result["client/HUD.client.luau"].decode()
 assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert g.count("remote.OnServerEvent:Connect(")==1
 assert g.count("local function applyAttack(")==1
 assert g.count("local function tickRound(")==1
 assert g.count("Evolution.nextEvolution(")==2
 assert "Power.beginAwaken(" in g
 assert "horde:eliteWarningSeconds(now)" in g
 assert "if mobHits>0 then return end" in g
 assert "local scoutExpiresAt=serverNow()+SCOUT_DURATION" in g
 assert "evolutionGuards[player]={untilAt=scoutExpiresAt," in g
 assert "while serverNow()<scoutExpiresAt" in g
 assert "evolvedStrikes<2 and serverNow()>=nextEvolvedStrike" in g
 assert "nextEvolvedStrike=serverNow()+2.5" in g
 assert "PersistentHatch.settleProgress(" in g
 assert "Evolution.creditRound(" in result["server/PersistentHatchStore.luau"].decode()
 assert h.count("local seq = 0")==1
 assert h.count("remote:FireServer(")==3
 assert "EVOLVE_SCOUT" in h and "AWAKEN_POWER" in h
 assert h.count("s.musouEliteWarningSeconds")==1
 assert 'MusouHordeCue",UDim2.new(.35,0,0,27)' in h
 assert 'RealH1ServerLevel",UDim2.new(.64,0,0,35)' in h
 assert len([k for k in result if k.endswith("/Game.server.luau")])==1
 assert len([k for k in result if k.endswith(".server.luau")])==2
 assert len([k for k in result if k.endswith(".client.luau")])==5
 project=DIST/"default.project.json"
 data=json.loads(project.read_text())
 assert data["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 data["name"]="EGG_RAID_RUMBLE_EVOLUTION40_PLUS_MUSOU_V5_STUDIO_ONLY_NOT_PUBLISHED"
 project.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 lock={
  "source":"SOURCE_ONLY_REPRODUCIBLE_INDEPENDENT_BRIDGE",
  "frozen_original_39_head":P39,
  "frozen_original_40_head":P40,
  "frozen_288_horde_v5_head":H1V5,
  "source_count":40,"original_40_unchanged":37,
  "only_three_modified":["client/HUD.client.luau","server/Game.server.luau","server/MusouHorde.luau"],
  "base_40_source_sha1":{k:gitblob(raw) for k,raw in sorted(base.items())},
  "source_blob_sha1":{k:gitblob(raw) for k,raw in sorted(result.items())},
  "source_sha256":{k:hashlib.sha256(raw).hexdigest() for k,raw in sorted(result.items())},
  "original_atomic_store_unchanged":True,
  "pure_evolution_source_unchanged":True,
  "pure_power_source_unchanged":True,
  "single_game_and_remote":True,"studio_only":True,
  "actual_studio_tested":False,"android_tested":False,
  "human_FUN_accepted":False,"official_RC_adopted":False,"published":False,
 }
 (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,indent=2,ensure_ascii=False)+"\n")
 print("P0D_REAL_40_EVOLUTION_PLUS_MUSOU_V5_BRIDGE_ASSEMBLY_PASS")
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--assemble",action="store_true",required=True)
 ap.parse_args()
 assemble()
