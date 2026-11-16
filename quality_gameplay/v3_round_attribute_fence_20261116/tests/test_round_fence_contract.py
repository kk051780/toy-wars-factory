import json
import re
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[1]
ROOT = REPO / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
ORIG = json.loads((ROOT / "EGGRUMBLE_V3_STUDIO.project.json").read_text())
NEW = json.loads((BASE / "EGGRUMBLE_V3_ROUND_FENCE.project.json").read_text())
MODULE = (BASE / "EGGRUMBLE_RoundAttributeFence.luau").read_text()
SCRIPT = (BASE / "EGGRUMBLE_RoundAttributeFence.server.luau").read_text()

def mapped(tree, base):
    result = {}
    def walk(node, prefix=""):
        for name, value in node.items():
            if name.startswith("$") or not isinstance(value, dict):
                continue
            key = f"{prefix}/{name}"
            if "$path" in value:
                result[key] = (base / value["$path"]).resolve(strict=True)
            else:
                walk(value, key)
    walk(tree)
    return result

class RoundAttributeFenceContract(unittest.TestCase):
    def test_original_21_untouched(self):
        a = mapped(ORIG["tree"], ROOT)
        b = mapped(NEW["tree"], BASE)
        self.assertEqual(len(a), 21)
        self.assertEqual(len(b), 23)
        for key, path in a.items():
            self.assertEqual(b.get(key), path, key)
    def test_one_additive_module_and_one_server_script(self):
        b = mapped(NEW["tree"], BASE)
        self.assertEqual(len(set(b.values())), 23)
        self.assertEqual(set(b) - set(mapped(ORIG["tree"], ROOT)), {
            "/ServerScriptService/EGGRUMBLE_RoundAttributeFence",
            "/ServerScriptService/EGGRUMBLE_RoundAttributeFenceServer",
        })
    def test_source_original_reset_defect_present(self):
        replay = (ROOT / "EGGRUMBLE_RoundReplay.luau").read_text()
        for original in ("EGGRUMBLE_NeutralKOs", "EGGRUMBLE_BattleLevel", "EGGRUMBLE_SlashEvolution"):
            self.assertIn(original, replay)
        for stale in ("EGGRUMBLE_Combo", "EGGRUMBLE_BestCombo", "EGGRUMBLE_BossDefeats"):
            self.assertNotIn(stale, replay)
    def test_only_three_round_local_attributes(self):
        self.assertEqual(set(re.findall(r'"(EGGRUMBLE_\\w+)"', MODULE)), {
            "EGGRUMBLE_Combo", "EGGRUMBLE_BestCombo", "EGGRUMBLE_BossDefeats"})
    def test_exact_server_exit_gate(self):
        self.assertIn("LIVE_MODES[previous] == true and current == nil", MODULE)
        self.assertIn('GetAttributeChangedSignal("EGGRUMBLE_QueuedMode")', SCRIPT)
        self.assertIn("Fence.shouldClear(previous, current)", SCRIPT)
    def test_player_listener_cleanup(self):
        self.assertIn("Players.PlayerRemoving:Connect", SCRIPT)
        self.assertIn("connection:Disconnect()", SCRIPT)
        self.assertIn("connections[player] = nil", SCRIPT)
    def test_original_runtime_studio_only(self):
        self.assertIn("if not RunService:IsStudio() then return end", SCRIPT)
    def test_no_new_state_authority(self):
        combined = MODULE + SCRIPT
        for danger in ("DataStore", "RemoteEvent", "RemoteFunction", "TakeDamage", "leaderstats",
                       "CastleMatchRules", "EGGRUMBLE_NeutralKOs", "SetAsync", "PublishAsync"):
            self.assertNotIn(danger, combined)
    def test_no_world_or_gui_allocations(self):
        self.assertNotIn("Instance.new(", MODULE + SCRIPT)
        self.assertNotIn("task.delay(", MODULE + SCRIPT)

if __name__ == "__main__":
    unittest.main()
