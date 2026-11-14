"""P0D Twin companion: static regressions and source-authority gate.

No Roblox engine claims; actual Luau40/Place Rojo verified by separate CI.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
WORLD=(ROOT/"features/twin_bond/TwinBiomesBonded.server.luau").read_text("utf8")
POLICY=(ROOT/"features/twin_bond/TwinBondPolicy.luau").read_text("utf8")
NATIVE=(ROOT/"features/twin_bond/TwinBondNative.luau").read_text("utf8")
ADAPTER=(ROOT/"apply_twin_bond.py").read_text("utf8")
FLAGS=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
CAT=json.loads((ROOT/"FEATURE_CATALOG.json").read_text("utf8"))["rows"]

def blob(source:str)->str:
    raw=source.encode("utf8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

class TwinBond(unittest.TestCase):
    def test_01_world_source_pin(self):
        self.assertEqual(blob(WORLD),"3a28a749bd1df8e4c5acf291b9d350c771074d58")
    def test_02_policy_source_pin(self):
        self.assertEqual(blob(POLICY),"d217e8cf03893efeebe437607e196f9a6f27d50f")
    def test_03_real_native_40(self):
        self.assertEqual(NATIVE.count('check("'),40)
        self.assertIn("assert(tested==40",NATIVE)
    def test_04_exact_canonical65_parent(self):
        self.assertIn('PREV_COUNT=65',ADAPTER)
        self.assertIn('GAME_PREV="cdc995d8a64f6a6f6df5abd43fb8210486328572"',ADAPTER)
        self.assertIn('TWIN_PREV="ff7c57aae79f03e3f34f5ba8b997cad669a5143"',ADAPTER)
    def test_05_explicit_studio_flag(self):
        self.assertIn('P0D_ENABLE_TWIN_BOND_PVE_V1',ADAPTER)
        self.assertIn('not RunService:IsStudio()',ADAPTER)
    def test_06_world_existing_studio_off(self):
        self.assertIn('if not RunService:IsStudio() then',WORLD)
        self.assertIn('if not value or not value:IsA("BoolValue") or value.Value ~= true then',WORLD)
    def test_07_one_follower_per_player(self):
        self.assertIn('local companionsByPlayer = {}',WORLD)
        self.assertIn('local prior=companionsByPlayer[player]',WORLD)
        self.assertIn('if prior and prior.part.Parent then prior.part:Destroy() end',WORLD)
    def test_08_follower_no_physics(self):
        for key in ('buddy.Anchored=true','buddy.CanCollide=false',
                    'buddy.CanTouch=false','buddy.CanQuery=false'):
            self.assertIn(key,WORLD)
    def test_09_owner_policy_only(self):
        self.assertIn('local Bond = require(script.Parent:WaitForChild("TwinBondPolicy"))',WORLD)
        self.assertIn('Bond.select(player,info.id,level,now)',WORLD)
        self.assertNotIn('OnServerEvent:Connect(',WORLD)
    def test_10_level2_gate(self):
        self.assertIn('if level < 2 or player.Parent ~= Players then return end',WORLD)
        self.assertIn('if level<2 or level>3',POLICY)
    def test_11_cooldown_and_timeout(self):
        self.assertIn('local MAX_DURATION = 180',POLICY)
        self.assertIn('local SWITCH_WAIT = 20',POLICY)
        self.assertIn('now>=current.untilAt',POLICY)
    def test_12_bounded_multiplier(self):
        self.assertIn('if current.level==3 then return 1.2 end',POLICY)
        self.assertIn('return 1.1',POLICY)
        self.assertIn('return 1',POLICY)
    def test_13_game_is_only_attacker(self):
        self.assertIn('twinBondOnlyNeutralMobBonus(player)',ADAPTER)
        self.assertIn('savedPveMinionMultiplier(player))',ADAPTER)
        self.assertIn('remote.OnServerEvent:Connect(',ADAPTER)
        self.assertNotIn('horde:hit(',WORLD)
    def test_14_no_client_damage_authority(self):
        for key in ('DataStoreService','UpdateAsync(','MarketplaceService',
                    'Instance.new("RemoteEvent")','TakeDamage(',
                    'PromptProductPurchase('):
            self.assertNotIn(key,POLICY)
            self.assertNotIn(key,WORLD)
    def test_15_cleanup_on_leave(self):
        self.assertIn('Bond.forget(p)',WORLD)
        self.assertIn('companionsByPlayer[p]=nil',WORLD)
        self.assertIn('function Bond.forget(player)',POLICY)
    def test_16_one_original_game_and_other63_byte_exact(self):
        self.assertIn('assert len(new)==66',ADAPTER)
        self.assertIn('if p not in {GAME,TWIN}',ADAPTER)
        self.assertIn('SINGLE_GAME',ADAPTER)
    def test_17_independent_zero_write_off(self):
        self.assertIn('P0D_TWIN_BOND_OFF_PRESERVES_OFFICIAL65_ALL_BYTES_PASS',ADAPTER)
        self.assertLess(ADAPTER.index('if not enabled:'),ADAPTER.index('before=scripts(dist)'))
    def test_18_66th_source_pure_module(self):
        self.assertIn('new[MODULE]=bond',ADAPTER)
        self.assertIn('assert len(new)==66',ADAPTER)
        self.assertIn('ONE_GAME',ADAPTER)
    def test_19_no_hidden_automatic_purchase(self):
        for key in ('Purchase','Robux','GamePass','DataStore','Cash'):
            self.assertNotIn(key,POLICY)
    def test_20_registry_source_not_official(self):
        f=FLAGS['TWIN_BOND_PVE_COMPANION_V1']
        self.assertTrue(f['enabled'])
        self.assertFalse(f['official_rc_adopted'])
        self.assertEqual(next(v for v in CAT if v["id"]=="P0D-067")["stage"],"SOURCE")
    def test_21_bounded_single_world_loop(self):
        self.assertEqual(WORLD.count('while world.Parent do'),1)
        self.assertEqual(WORLD.count('task.spawn(function()'),1)
        self.assertIn('for player,companion in pairs(companionsByPlayer) do',WORLD)
    def test_22_no_auto_score_or_damage(self):
        self.assertIn('buddy:SetAttribute("NoDamageAuthority",true)',WORLD)
        self.assertNotIn('leaderstats',WORLD)
        self.assertNotIn('Humanoid:TakeDamage(',WORLD)

if __name__=="__main__":
    unittest.main()
