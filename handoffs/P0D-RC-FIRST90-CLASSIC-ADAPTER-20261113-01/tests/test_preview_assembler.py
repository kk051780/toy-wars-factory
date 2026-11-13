"""Checks actual source-only one-Game preview assembly, never official RC."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
ASSEMBLER = ROOT / "tools" / "assemble_preview.py"
DIST = ROOT / "dist" / "TRAP_RAIDERS_S1_FIRST90_CLASSIC_PRIVATE_UNPUBLISHED"
ORIGINAL = REPO / "releases" / "P0D_S1_KIDS_RC01"
FROZEN = "1263a03701211a652b99b91d2339575dc8104eff"

def gitblob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class RealPreviewSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "-B", str(ASSEMBLER), "--assemble"],
                       cwd=REPO, check=True, capture_output=True, text=True)

    def test_original_game_and_coach_never_modified(self):
        self.assertEqual(gitblob((ORIGINAL / "src/server/Game.server.luau").read_bytes()),
                         "7c5229f600f17537bc1bbbb0b96b6a2435875374")
        self.assertEqual(gitblob((ORIGINAL / "src/client/FirstMinuteCoach.client.luau").read_bytes()),
                         "63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9")

    def test_source_lock_and_genuine_22_scripts(self):
        lock = json.loads((DIST / "SOURCE_LOCK.json").read_text())
        self.assertEqual(lock["official_rc_sha_frozen"], FROZEN)
        self.assertEqual(lock["source_count"], 22)
        self.assertEqual(lock["original_count"], 21)
        self.assertEqual(lock["unchanged_original_count"], 19)
        self.assertFalse(lock["official_rc_adopted"])
        self.assertEqual(lock["real_roblox_studio_2client"], "NOT_TESTED")
        self.assertEqual(len(list((DIST/"src").rglob("*.luau"))), 22)
        for path, digest in lock["source_git_sha1"].items():
            with self.subTest(path=path):
                self.assertEqual(gitblob((DIST/path).read_bytes()), digest)

    def test_single_game_and_single_original_remote(self):
        server = (DIST / "src/server/Game.server.luau").read_text()
        self.assertEqual(server.count('Instance.new("RemoteEvent")'), 1)
        self.assertEqual(server.count('remote.OnServerEvent:Connect'), 1)
        self.assertEqual(server.count('local function snapshotFor(player: Player)'), 1)
        self.assertEqual(server.count('first90Target = first90Target,'), 1)
        self.assertIn('getTeamName(player)', server)
        self.assertIn('match.startedAt', server)
        self.assertIn('enemyBase.eggPrompt.Enabled', server)
        self.assertIn('enemyEgg.Transparency == 0', server)
        self.assertEqual(len(list((DIST/"src/server").glob("Game.server.luau"))), 1)

    def test_client_uses_only_existing_coach_and_remote(self):
        client = (DIST/"src/client/FirstMinuteCoach.client.luau").read_text()
        model = (DIST/"src/shared/FirstMinuteModel.luau").read_bytes()
        self.assertEqual(client.count('local gui = Instance.new("ScreenGui")'), 1)
        self.assertEqual(client.count('remote.OnClientEvent:Connect'), 1)
        self.assertEqual(client.count('local function repaint()'), 1)
        self.assertIn('first90Text(state.latest)', client)
        self.assertIn('not state.dismissed', client)
        self.assertIn('detail.Text = if route', client)
        self.assertIn('約', client)
        self.assertEqual(gitblob(model), "fcdc399bf95b6cd0532691718f5a54e8a4fd84b4")
        self.assertNotIn('Instance.new("RemoteEvent")', client)

    def test_project_retains_one_server_namespace_and_existing_coach(self):
        config = json.loads((DIST/"default.project.json").read_text())
        tree = config["tree"]
        self.assertEqual(tree["ServerScriptService"]["TrapRaidersS1"]["$path"], "src/server")
        self.assertEqual(
            tree["StarterPlayer"]["StarterPlayerScripts"]["TrapRaidersCoach"]["$path"],
            "src/client/FirstMinuteCoach.client.luau"
        )
        self.assertEqual(gitblob((DIST/"default.project.json").read_bytes()),
                         "ec2918829fa6d87610e42fdcd681a1a31335d962")

    def test_server_only_pure_rule_module(self):
        pure = (DIST/"src/server/S1First90ClassicWaypointRules.luau").read_bytes()
        self.assertEqual(pure, (ROOT/"src/S1First90ClassicWaypointRules.luau").read_bytes())
        self.assertNotIn(b"Instance.new", pure)
        self.assertNotIn(b"OnServerEvent", pure)

    def test_frozen_game_start_is_unchanged_in_copy_except_authorized_hunks(self):
        original = (ORIGINAL/"src/server/Game.server.luau").read_text()
        copy = (DIST/"src/server/Game.server.luau").read_text()
        for section in (
            'local function resetRound()',
            'local function applyAttack(',
            'map.teams[team].eggPrompt.Triggered:Connect',
            'map.teams[team].scorePrompt.Triggered:Connect',
            'local function broadcast()',
        ):
            with self.subTest(section=section):
                self.assertIn(section, original)
                self.assertIn(section, copy)


if __name__ == "__main__":
    unittest.main()
