"""EGGRUMBLE cargo-buff fairness regression: original one-author ITEM source only.

Source contracts do NOT imply Roblox Studio or Android engine validation.
"""
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "EGGRUMBLE_FieldItemPickups.luau").read_text()

class CarrierItemFairness(unittest.TestCase):
    def test_server_authoritative_egg_ownership(self):
        self.assertIn('castles[tostring(player.UserId)]', SOURCE)
        self.assertIn('type(castle.heldEggs)=="number" and castle.heldEggs>0', SOURCE)
        self.assertNotIn('player:GetAttribute("EGGRUMBLE_HeldEggs")', SOURCE)

    def test_no_consumption_or_cooldown_on_carrier_rejection(self):
        gate = 'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end'
        self.assertIn(gate, SOURCE)
        trigger = SOURCE.index('prompt.Triggered:Connect(function(player:Player)')
        reject = SOURCE.index(gate, trigger)
        self.assertLess(reject, SOURCE.index('lastUse[key]=now', trigger))
        self.assertLess(reject, SOURCE.index('consumed[id]=true', trigger))
        self.assertLess(reject, SOURCE.index('prompt.Enabled=false', trigger))

    def test_late_egg_pickup_cancels_speed_and_shield(self):
        self.assertIn('task.wait(.25)', SOURCE)
        self.assertIn('if not matchActive() or carryingEnemyEggs(player,session) then', SOURCE)
        self.assertIn('cancelBuffIfCarrier(player,5,restoreSpeed)', SOURCE)
        self.assertIn('cancelBuffIfCarrier(player,4,clearShield)', SOURCE)
        self.assertIn('task.delay(5,restoreSpeed)', SOURCE)
        self.assertIn('task.delay(4,clearShield)', SOURCE)

    def test_existing_author_functions_preserved(self):
        for token in (
            'function Items.start(session:any,positions:{Vector3}):()',
            'RunService:IsStudio()',
            'local RESPAWN_SECONDS=35',
            'HEAL={label=',
            'DASH={label=',
            'SHIELD={label=',
            'session.itemStop=function()',
        ):
            self.assertIn(token, SOURCE)
        for forbidden in ('RemoteEvent', 'DataStoreService', 'MarketplaceService'):
            self.assertNotIn(forbidden, SOURCE)

if __name__ == "__main__":
    unittest.main()
