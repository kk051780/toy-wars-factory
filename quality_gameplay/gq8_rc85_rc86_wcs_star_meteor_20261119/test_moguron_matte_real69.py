#!/usr/bin/env python3
"""GQ470/#420 source-only Moguron art regression; NOT Studio/Android beauty proof."""
from pathlib import Path
import re

SOURCE = Path(__file__).with_name("EGGRUMBLE_LegacyCanyonRoutes.server.luau")
s = SOURCE.read_text(encoding="utf-8")
start = s.index(" local function mole(side:string,x:number)")
end = s.index(' mole("WEST",-34);mole("EAST",34)', start)
m = s[start:end]
assert s.startswith("--!strict\n")
assert 'if not RunService:IsStudio() then return end' in s
assert s.count("GQ470_FB015_MOGURON_MATTE_SILHOUETTE_REAL69_20261121") == 1
assert s.count(' mole("WEST",-34);mole("EAST",34)') == 1
assert m.count("local torso=block(") == 1
assert m.count("local nose=block(") == 1
assert m.count("local eye=block(") == 1
assert m.count("local ear=block(") == 1
assert m.count("local paw=block(") == 1
assert m.count("for _,sign in ipairs({-1,1}) do") == 1
assert m.count("block(") == 5, "2 base + 3 bilateral accent constructors"
assert "Enum.Material.Neon" not in m, "No neon sphere artifacts on critter"
assert m.count("Enum.Material.SmoothPlastic,false)") == 5
assert m.count("CastShadow=false") == 5
assert m.count('addPrompt(torso,"橋をひらく","橋掘りモグロン"') == 1
assert m.count("authorized(p,torso)") == 1
assert m.count("setGate(true);gateUntil=os.clock()+14") == 1
assert "Instance.new(" not in m, "All parts go through the non-physics block creator"
assert "CanTouch=false;p.CanQuery=collide;p.CanCollide=collide" in s
assert s.count("os.clock()+4") == 1
assert s.count("not occupied(-15,13)") == 1
assert s.count('block("WestAccessStep_"..i') == 1
assert s.count('block("EastAccessStep_"..i') == 1
assert s.count('block("CanyonCrystal_"..i') == 1, "Do not overwrite separate Canyon PR art"
assert s.count('"GQ8_RC86_StarfallPath"') == 2
assert s.count('"GQ8_RC86_MeteorShortcut"') == 2
assert s.count('"StarStepsOwned",0') == 1
assert s.count('"MeteorOwnedSegments",0') == 1
assert "local LOBBY=" in s and 'elseif candidate.Name=="BATTLE_ROYALE_Arena"' in s
assert "script.Parent" not in m and "DataStoreService" not in m
# Static part budget from one body/nose plus two each eye, ear, paw.
parts_per_moguron = 2 + 2 * 3
assert parts_per_moguron == 8
max_mogurons = 2 * 2  # two sides in each of TEAM and BR
assert parts_per_moguron * max_mogurons == 32
assert (parts_per_moguron - 2) * max_mogurons == 24
print("GQ470_MOGURON_SOURCE_GATE_PASS", "parts_per_npc=8",
      "total_npcs=4", "extra_parts_both_modes=24",
      "gameplay_prompts=unchanged", "studio=NOT_TESTED",
      "art=ART_NO_GO")
