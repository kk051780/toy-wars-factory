"""EGGRUMBLE V3 guard contract, negative mutation tests; not Roblox runtime."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
LOBBY=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
GUARD=(ROOT/"EGGRUMBLE_InteractionGuard.luau").read_text(encoding="utf-8")

class InteractionSecurityTests(unittest.TestCase):
    def test_all_prompts_use_same_server_authority(self):
        self.assertEqual(LOBBY.count("p.Triggered:Connect("),1,
                         "Only shared prompt wrapper may bind client-initiated actions")
        self.assertIn("InteractionGuard.allow(actor,at,action,at.Name)",LOBBY)
        self.assertIn("InteractionGuard.clear(p)",LOBBY)
        for word in ('"攻城攻撃"','"敵の卵を奪取"','"卵を納入"',
                     '"卵を拾う"','"拾う"','"旗の装飾変更"',
                     '"参加する"','"装備する"'):
            self.assertIn(word,GUARD)
    def test_siege_is_rate_limited_by_server(self):
        self.assertIn('["攻城攻撃"]=1.6',GUARD)
        self.assertIn('os.clock()',GUARD)
        self.assertIn('clock-previous<COOLDOWN[verb]',GUARD)
        self.assertIn('if not positionValid(actor,part) then return false end',GUARD)
        self.assertIn('humanoid.Health<=0',GUARD)
        self.assertIn('part:GetClosestPointOnSurface(',GUARD)
        self.assertIn('workspace:Raycast(origin,cast,params)',GUARD)
    def test_no_client_trust_or_purchase(self):
        for word in ('RemoteEvent','MarketplaceService','ProcessReceipt','DataStoreService'):
            self.assertNotIn(word,GUARD)
        self.assertNotIn("p.Triggered:Connect(callback)",LOBBY)
    def test_no_client_action_without_guard(self):
        mutant=LOBBY.replace(
            'if InteractionGuard.allow(actor,at,action,at.Name) then callback(actor) end',
            'callback(actor)')
        self.assertNotIn('if InteractionGuard.allow(actor,at,action,at.Name) then callback(actor) end', mutant)
    def test_defense_guard_does_not_use_client_prompt_duration_as_authority(self):
        self.assertNotIn("part.HoldDuration",GUARD)
        self.assertNotIn("part.MaxActivationDistance",GUARD)

if __name__=="__main__":
    unittest.main()
