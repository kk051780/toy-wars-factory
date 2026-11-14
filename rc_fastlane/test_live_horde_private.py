#!/usr/bin/env python3
"""#444 exact Game-only private-Horde guard positive + fail-closed source tests."""
from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from apply_live_horde_private import (
    GAME,HORDE,FEATURE,PRIVATE_ATTR,apply,blob,read,patch,parse_guard
)
GAME_FIXTURE='''--!strict
local function resetRound()
    match.serial += 1
    local startupSerial=match.serial
    if match.phase~="ACTIVE" or match.serial~=startupSerial then return end
    if RunService:IsStudio() then
        horde:reset(match.serial,serverNow())
    end
end
local function chooseTeam(player: Player)
    return player
end
-- FB019 RealDamagePopup authoritative server
    -- Original ATTACK cooldown/seq/phase also gates PvE. No second Remote or damage event.
    if RunService:IsStudio() then
        local touched,defeated = horde:hit(player,position)
    end
    -- Existing server tick is the sole PvE attack authority; no extra game loop.
    if RunService:IsStudio() and match.phase=="ACTIVE" then
        -- The same ORIGINAL Game tick drives Studio bots. No second match loop.
        if not EXPERIMENTAL_FIVE_EGG_MODE then
            SoloTeamBots.tick()
        end
        horde:tick(now)
    end
remote.OnServerEvent:Connect(function(player,data)
    return
end)
'''
HORDE_FIXTURE='''local Horde={}
function Horde:reset(serial, now)
 self.mobs={"MUSOU_ELITE_TELEGRAPH","RealDamagePopup"}
end
return Horde
'''
class PrivateLiveHordeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.base=root/"base";self.out=root/"out"
        (self.base/"src/server").mkdir(parents=True)
        (self.base/"src/client").mkdir(parents=True)
        (self.base/"src"/GAME).write_text(GAME_FIXTURE)
        (self.base/"src"/HORDE).write_text(HORDE_FIXTURE)
        (self.base/"src/client/HUD.client.luau").write_text("-- HUD")
        for i in range(78):
            (self.base/"src/server"/f"Legacy{i:03d}.luau").write_text(f"-- source {i}")
        x=read(self.base)
        assert len(x)==81
        pins={p:blob(v) for p,v in sorted(x.items())}
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps({"total_scripts":81,"blobs":pins}))
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps({
          "total_sources":81,"source_gitblobs":pins,
          "feature_flags":{
            "FB019_RESPONSIVE_ATTACK_INPUT_SWING":True,
            "FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2":True,
            "FB015_LIVE_CASTLE_SAFE_PARITY_V1":True
          }
        }))
    def test_single_guard_patch_and_original_damage_authority(self):
        patched=patch(GAME_FIXTURE.encode()).decode()
        self.assertEqual(patched.count("horde:reset("),1)
        self.assertEqual(patched.count("remote.OnServerEvent:Connect("),1)
        self.assertEqual(patched.count("horde:hit("),1)
        self.assertIn('game.PrivateServerId ~= ""',patched)
        self.assertIn('workspace:GetAttribute("'+PRIVATE_ATTR+'") == true',patched)
        self.assertIn("match.serial~=startupSerial",patched)
        self.assertEqual(patched.count('game.PrivateServerId ~= ""'),3)
        self.assertEqual(patched.count('workspace:GetAttribute("'+PRIVATE_ATTR+'") == true'),3)
        self.assertIn('if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then',patched)
        self.assertIn('horde:tick(now)',patched)
        self.assertIn('local touched,defeated = horde:hit(',patched)
        self.assertIn("if RunService:IsStudio() or (",patched)
    def test_one_line_anchor_is_supported(self):
        src=GAME_FIXTURE.replace(
            '    if RunService:IsStudio() then\n        horde:reset(match.serial,serverNow())\n    end',
            '    if RunService:IsStudio() then horde:reset(match.serial,serverNow()) end')
        result=patch(src.encode()).decode()
        self.assertIn(FEATURE,result)
    def test_disabled_no_output_no_original_drift(self):
        before=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertEqual(before,read(self.base))
        self.assertFalse(self.out.exists())
    def test_game_only_and_other80_exact(self):
        old=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        new=read(self.out)
        self.assertEqual(set(new),set(old))
        self.assertEqual(len(new),81)
        self.assertEqual({x for x in old if old[x]!=new[x]},{GAME})
        self.assertEqual(old[HORDE],new[HORDE])
        oldlock=json.loads((self.out/"SOURCE_LOCK.json").read_text())
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        self.assertEqual(oldlock["blobs"],fl["source_gitblobs"])
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertEqual(fl["live_horde_private_canary"]["other_80_sources_exact"],True)
    def test_duplicate_guard_denied(self):
        text=GAME_FIXTURE.replace(
            "local function chooseTeam(",
            "if RunService:IsStudio() then horde:reset(match.serial,serverNow()) end\nlocal function chooseTeam(")
        with self.assertRaises(AssertionError):
            patch(text.encode())
    def test_missing_guard_denied(self):
        with self.assertRaises(AssertionError):
            patch(GAME_FIXTURE.replace("horde:reset(","unused_horde_reset(").encode())
    def test_no_private_auto_enable_in_patch(self):
        s=patch(GAME_FIXTURE.encode()).decode()
        self.assertNotIn('workspace:SetAttribute("'+PRIVATE_ATTR,s)
        self.assertNotIn('game.PrivateServerId =',s)
    def test_bad_lock_rejected(self):
        p=self.base/"SOURCE_LOCK.json"
        data=json.loads(p.read_text())
        data["blobs"][HORDE]="0"*40;p.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_missing_prior_parent_feature_denied(self):
        p=self.base/"RC_FEATURE_LOCK.json"
        data=json.loads(p.read_text())
        data["feature_flags"]["FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2"]=False
        p.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_symlink_denied(self):
        (self.base/"src/server/suspicious.luau").symlink_to(self.base/"src"/GAME)
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
if __name__=="__main__":
    unittest.main()
