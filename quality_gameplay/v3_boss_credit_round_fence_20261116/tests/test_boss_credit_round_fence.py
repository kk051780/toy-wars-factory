"""EGGRUMBLE V3: exact-author source gap + non-overlapping boss credit fence."""
import json
import hashlib
import unittest
from pathlib import Path

DIR = Path(__file__).resolve().parents[1]
ROOT = DIR.parents[1]
AUTHOR = ROOT / "handoffs" / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
PINNED_BLOBS = {
    "EGGRUMBLE_LobbyCastleModesPreview.server.luau": "7162b209bf67b74a71553217f3f744e072a0365d",
    "EGGRUMBLE_RoundReplay.luau": "a97e7aeffc988fe9ccde5bf7544b01deb5f243ff",
}
def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

class BossCreditFenceContract(unittest.TestCase):
    def test_author_sources_are_pinned_and_still_have_this_gap(self):
        for name, expected in PINNED_BLOBS.items():
            self.assertEqual(git_blob_sha((AUTHOR / name).read_bytes()), expected, name)
        lobby = (AUTHOR / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text()
        replay = (AUTHOR / "EGGRUMBLE_RoundReplay.luau").read_text()
        self.assertIn('player:SetAttribute("EGGRUMBLE_BossDefeats",total+1)', lobby)
        self.assertNotIn('p:SetAttribute("EGGRUMBLE_BossDefeats",', replay)

    def test_policy_is_pure_and_boundary_specific(self):
        policy = (DIR / "EGGRUMBLE_BossCreditPolicy.luau").read_text()
        self.assertIn("previousMode == currentMode", policy)
        self.assertIn("previousMode == nil or MATCH_MODE[previousMode]", policy)
        self.assertIn("currentMode == nil or MATCH_MODE[currentMode]", policy)
        self.assertNotIn("game:GetService", policy)
        self.assertNotIn("RemoteEvent", policy)

    def test_script_does_not_replace_game_or_erase_current_match_on_boot(self):
        script = (DIR / "EGGRUMBLE_BossCreditRoundFence.server.luau").read_text()
        required = [
            'RunService:IsStudio()', 'Players.PlayerAdded:Connect(bind)',
            'Players.PlayerRemoving:Connect(unbind)', 'GetAttributeChangedSignal(MODE)',
            'Policy.shouldReset(previous, current)', 'player:SetAttribute(COUNTER, 0)',
            'if initial == nil and player.Parent == Players then',
            'connection:Disconnect()', 'previousModes[player] = nil',
        ]
        for fragment in required:
            self.assertIn(fragment, script)
        for forbidden in ["RemoteEvent", "TakeDamage", "DataStore", "LoadCharacter", "Destroy()"]:
            self.assertNotIn(forbidden, script)

    def test_shadow_rojo_project_reuses_author_21_sources_unchanged(self):
        original = json.loads((AUTHOR / "EGGRUMBLE_V3_STUDIO.project.json").read_text())
        shadow = json.loads((DIR / "EGGRUMBLE_BOSS_CREDIT_STUDIO.project.json").read_text())
        old_server = original["tree"]["ServerScriptService"]
        new_server = shadow["tree"]["ServerScriptService"]
        old_client = original["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        new_client = shadow["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertEqual(len(old_server) + len(old_client) - 2, 21)
        self.assertEqual(len(new_server) + len(new_client) - 2, 23)
        for parent, copied in [(old_server, new_server), (old_client, new_client)]:
            for key, value in parent.items():
                if key == "$className": continue
                self.assertEqual(copied[key], {"$path": "../../handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/" + value["$path"]})
        self.assertEqual(new_server["EGGRUMBLE_BossCreditPolicy"], {"$path": "EGGRUMBLE_BossCreditPolicy.luau"})
        self.assertEqual(new_server["EGGRUMBLE_BossCreditRoundFence"], {"$path": "EGGRUMBLE_BossCreditRoundFence.server.luau"})
        self.assertEqual(set(new_server) - set(old_server),
                         {"EGGRUMBLE_BossCreditPolicy", "EGGRUMBLE_BossCreditRoundFence"})

if __name__ == "__main__":
    unittest.main()
