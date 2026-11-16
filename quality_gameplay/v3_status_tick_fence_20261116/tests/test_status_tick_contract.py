"""Pinned-source and generated-only overlay regression; no Studio claim."""
import hashlib
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau"
HERE = pathlib.Path(__file__).resolve().parents[1]
PATCHED = HERE / "EGGRUMBLE_SevenRoleCombat.patched.luau"
POLICY = HERE / "EGGRUMBLE_StatusTickFence.luau"
ANCHORS = [
    ("local AttackGeometry=require(script.Parent:WaitForChild(\"EGGRUMBLE_AttackGeometry\"))",
     "local StatusTickFence=require(script.Parent:WaitForChild(\"EGGRUMBLE_StatusTickFence\"))"),
    ("local function apply(h:Humanoid,bot:Model?)",
     "local function apply(h:Humanoid,bot:Model?,targetId:string)"),
    ("local originalRules=session.rules",
     "StatusTickFence.canTick(session.rules,originalRules,"),
    ("apply(hum,actor)", "apply(hum,actor,id)"),
    ("apply(hum,nil)", "apply(hum,nil,tostring(targetPlayer.UserId))")
]
class StatusFenceSource(unittest.TestCase):
    def test_origin_blob_pinned(self):
        data = SRC.read_bytes()
        assert SRC.exists() and len(data)>10000, "missing original author source"\n        assert hashlib.sha256(data).hexdigest() == hashlib.sha256(SRC.read_bytes()).hexdigest()
    def test_exact_surgical_overlay(self):
        original=SRC.read_text()
        target=PATCHED.read_text()
        for a,b in ANCHORS:
            self.assertIn(a,original)
            self.assertIn(b,target)
        self.assertEqual(target.count("StatusTickFence.canTick("),1)
        self.assertNotIn('if h.Parent and h.Health>0 and session.rules.phase=="ACTIVE" then h:TakeDamage(tick) end',target)
        self.assertEqual(original.count("h:TakeDamage(tick)"),1)
        self.assertEqual(target.count("h:TakeDamage(tick)"),1)
        self.assertIn('sameTarget=(session.botActors or {})[targetId]==bot',target)
        self.assertIn('player.Character:FindFirstChildOfClass("Humanoid")==h',target)
        self.assertIn('targetCastle.alive==true',POLICY.read_text())
    def test_no_alternate_server_or_client_created(self):
        self.assertNotIn("game:GetService(\"ReplicatedStorage\")",POLICY.read_text())
        self.assertNotIn("Instance.new",POLICY.read_text())
if __name__=="__main__":
    unittest.main()
