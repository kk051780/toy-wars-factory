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

    def test_old_round_dash_timer_cannot_clobber_new_round(self):
        self.assertIn('local buffCharacter=player.Character', SOURCE)
        self.assertIn('if not matchActive() or player.Character~=buffCharacter then return end', SOURCE)
        self.assertLess(SOURCE.index('if not matchActive() or player.Character~=buffCharacter'),
                        SOURCE.index('hum.WalkSpeed=previous'))
        vm = (Path(__file__).resolve().parents[1] / 'tools/make_native_field_item_harness.py').read_text()
        self.assertIn('retired.itemStop()', vm)
        self.assertIn('runTo(now+3.25)', vm)
        self.assertIn('retired round timer must not overwrite new round active DASH', vm)

    def test_v3_reuses_original_shared_server_los_guard(self):
        self.assertIn('script.Parent:FindFirstChild("EGGRUMBLE_InteractionGuard")', SOURCE)
        self.assertIn('session.mode=="TEAM" or session.mode=="BATTLE_ROYALE"', SOURCE)
        self.assertIn('interactionGuard and type(interactionGuard.allow)=="function"', SOURCE)
        self.assertIn('interactionGuard.allow(player,part,"拾う",part.Name)', SOURCE)
        self.assertIn('if isV3Match and not interactionGuard.allow(player,part,"拾う",part.Name) then return end', SOURCE)
        # Author original item-only private preview remains a separate, mode-less sandbox.
        preview = (Path(__file__).resolve().parents[1] / "EGGRUMBLE_FieldItemPreview.server.luau").read_text()
        self.assertIn('Items.start({world=world,rules={phase="ACTIVE",castles=roster}},positions)', preview)

    def test_guard_must_run_before_consumption(self):
        trigger = SOURCE.index('prompt.Triggered:Connect(function(player:Player)')
        g = SOURCE.index('if isV3Match and not interactionGuard.allow(', trigger)
        for downstream in ('consumed[id]=true', 'lastUse[key]=now', 'prompt.Enabled=false', 'hum.Health=math.min', 'hum.WalkSpeed=math.max', 'Instance.new("ForceField")'):
            self.assertLess(g, SOURCE.index(downstream, trigger))

    def test_no_alternative_raycast_engine_or_duplicate_item_owner(self):
        self.assertNotIn('workspace:Raycast(', SOURCE)
        self.assertNotIn('RaycastParams.new()', SOURCE)
        self.assertNotIn('RemoteEvent', SOURCE)
        self.assertEqual(SOURCE.count('function Items.start('), 1)

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
