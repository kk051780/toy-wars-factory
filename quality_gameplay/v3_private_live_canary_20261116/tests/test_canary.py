"""SOURCE-EXACT, public-off, independent Place acceptance; NOT a Roblox engine test."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compose

class PrivateLiveCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="eggrumble-private-canary-")
        cls.out = Path(cls.tmp.name) / "composite"
        cls.manifest = compose.build(cls.out)
        cls.project = json.loads((cls.out / "EGGRUMBLE_V3_PRIVATE_CANARY.project.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_original_sources_are_author_pinned(self):
        self.assertEqual(len(self.manifest["sources"]), 21)
        for entry in self.manifest["sources"]:
            src = compose.SOURCE / entry["name"]
            data = src.read_bytes()
            self.assertEqual(data, compose.pinned_bytes(src))
            self.assertEqual(compose.digest(data), entry["author_sha256"])

    def test_exact_17_studio_guards_replaced(self):
        self.assertEqual(self.manifest["modified_guard_sites"], 17)
        self.assertEqual(sum(e["guard_sites"] for e in self.manifest["sources"]), 17)
        for e in self.manifest["sources"]:
            code = (self.out / "sources" / e["name"]).read_text()
            self.assertNotIn("RunService:IsStudio()", code)
            if e["guard_sites"]:
                self.assertIn("EGGRUMBLE_PrivateLiveGate", code)
            else:
                self.assertEqual(e["author_sha256"], e["canary_sha256"])

    def test_studio_preview_host_is_explicitly_private_gated(self):
        host = (self.out / "sources" / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text()
        self.assertIn("if not PrivateGate.advertiseServerReady() then return end", host)
        self.assertNotIn("if not RunService:IsStudio() then return end", host)

    def test_clients_wait_for_server_ready(self):
        for name in compose.ORIGINAL_CLIENT:
            code = (self.out / "sources" / name).read_text()
            self.assertIn("PrivateGate.waitAllowed(8)", code)
        gate = (self.out / "sources" / "EGGRUMBLE_PrivateLiveGate.luau").read_text()
        self.assertIn("game.PrivateServerId", gate)
        self.assertIn('game.PrivateServerId=="" then return false', gate)
        self.assertIn('GetAttribute(Gate.OPT_IN_ATTRIBUTE)==true', gate)
        self.assertIn("ReplicatedStorage:SetAttribute(Gate.READY_ATTRIBUTE,true)", gate)

    def test_only_isolated_original_21_plus_gate_are_mapped(self):
        maps = compose.mapped_files(json.loads(compose.PROJECT.read_text()))
        self.assertEqual(len(maps), 21)
        proj = self.project["tree"]
        self.assertEqual(set(proj), {"$className", "ServerScriptService", "StarterPlayer", "ReplicatedStorage"})
        self.assertEqual(set(proj["ReplicatedStorage"]), {"$className", "EGGRUMBLE_PrivateLiveGate"})
        self.assertEqual({e["name"] for e in self.manifest["sources"]},
                         compose.ORIGINAL_SERVER | compose.ORIGINAL_CLIENT)
        self.assertEqual(len(self.manifest["sources"])+1, 22)

    def test_unexpected_new_source_guard_is_red(self):
        with self.assertRaises(ValueError):
            compose.transform("--!strict\nassert(RunService:IsStudio())\n", "EGGRUMBLE_ImpactFeedback.luau")
        with self.assertRaises(ValueError):
            compose.transform("--!strict\nreturn {}\n", "EGGRUMBLE_BotActors.luau")

    def test_overwrite_or_repository_output_is_red(self):
        with self.assertRaises(ValueError):
            compose.build(compose.REPO / "bad-output")
        with self.assertRaises(ValueError):
            compose.build(self.out)

    def test_status_never_claims_official_rc_or_engine_pass(self):
        self.assertEqual(self.manifest["runtime"], "ISOLATED_PRIVATE_CANARY_ONLY")
        self.assertEqual(self.manifest["startup_default"], "OFF")
        self.assertIs(self.manifest["official_rc_adopted"], False)
        self.assertEqual(self.manifest["source_pin"], compose.PIN)

if __name__ == "__main__":
    unittest.main()
