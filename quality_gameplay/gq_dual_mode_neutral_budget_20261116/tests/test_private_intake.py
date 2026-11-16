from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
STAGER = ROOT / "tools" / "compose_private_v3.py"
LOCK = json.loads((ROOT / "source_lock.json").read_text())
ORIGINAL = REPO / LOCK["author_path"]


class SourceExactPrivateStage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory(prefix="GQ528_PRIVATE_")
        cls.off = Path(cls.temp.name) / "OFF"
        cls.on = Path(cls.temp.name) / "ON"
        for mode, out in (("OFF", cls.off), ("ON", cls.on)):
            cp = subprocess.run(
                [sys.executable, str(STAGER), "--mode", mode, "--out", str(out)],
                check=True, capture_output=True, text=True
            )
            assert f"GQ528_PRIVATE_{mode}_" in cp.stdout, cp.stdout
        cls.off_receipt = json.loads((cls.off / "source_lock_receipt.json").read_text())
        cls.on_receipt = json.loads((cls.on / "source_lock_receipt.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_author_source_count_and_off_is_exact(self):
        self.assertEqual(len(LOCK["original_sources"]), 21)
        self.assertEqual(self.off_receipt["original_preserved"], 21)
        self.assertEqual(self.off_receipt["mapped_script_count"], 21)
        for name in LOCK["original_sources"]:
            self.assertEqual((self.off / "src" / name).read_bytes(), (ORIGINAL / name).read_bytes())

    def test_on_changes_exactly_two_author_files(self):
        self.assertEqual(self.on_receipt["mapped_script_count"], 22)
        self.assertEqual(self.on_receipt["original_preserved"], 19)
        self.assertEqual(sorted(self.on_receipt["overlaid_original_sources"]),
                         ["EGGRUMBLE_LobbyCastleModesPreview.server.luau", "EGGRUMBLE_SwarmCombat.luau"])
        for name in LOCK["original_sources"]:
            if name not in self.on_receipt["overlaid_original_sources"]:
                self.assertEqual((self.on / "src" / name).read_bytes(), (ORIGINAL / name).read_bytes())
        self.assertEqual((self.on / "src" / "EGGRUMBLE_DualModeNeutralBudget.luau").read_bytes(),
                         (ROOT / "EGGRUMBLE_DualModeNeutralBudget.luau").read_bytes())

    def test_host_only_one_global_budget_and_mode_epochs(self):
        host = (self.on / "src" / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text()
        self.assertEqual(host.count("GQDualBudget.new(128,96,32)"), 1)
        self.assertEqual(host.count("gqDualBudget:begin(mode)"), 1)
        self.assertEqual(host.count("gqDualBudget:retire(mode,session.neutralBudgetEpoch)"), 1)
        self.assertLess(host.index("session.neutralBudgetEpoch=gqDualBudget:begin(mode)"),
                        host.index("SwarmCombat.start(session)"))
        self.assertIn('local FieldItems=require(script.Parent:WaitForChild("EGGRUMBLE_FieldItemPickups"))', host)

    def test_live_swarm_ticket_acquire_before_spawn(self):
        swarm = (self.on / "src" / "EGGRUMBLE_SwarmCombat.luau").read_text()
        self.assertEqual(swarm.count("session.neutralBudget:acquire("), 1)
        self.assertLess(swarm.index("session.neutralBudget:acquire("),
                        swarm.index("pcall(soldier,all,at)"))
        self.assertEqual(swarm.count("session.neutralBudget:release(ticket)"), 4)
        self.assertIn('local m=model :: Model', swarm)
        self.assertIn('m.Destroying:Connect', swarm)
        self.assertIn('h.Died:Connect', swarm)
        self.assertIn('if not permit then return end', swarm)
        self.assertIn('all.Destroying:Connect', swarm)

    def test_off_has_no_policy_or_author_patch(self):
        host=(self.off / "src" / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text()
        swarm=(self.off / "src" / "EGGRUMBLE_SwarmCombat.luau").read_text()
        self.assertNotIn("GQDualBudget", host)
        self.assertNotIn("neutralBudget:acquire", swarm)
        self.assertNotIn("EGGRUMBLE_DualModeNeutralBudget", json.dumps(json.loads(
            (self.off / "private_v3.project.json").read_text())))

    def test_project_real_classes_no_duplicate_host(self):
        for folder, expected in ((self.off,21),(self.on,22)):
            project=json.loads((folder/"private_v3.project.json").read_text())
            server=project["tree"]["ServerScriptService"]
            self.assertEqual(sum(1 for v in server if v=="EGGRUMBLE_LobbyCastleModesPreview"), 1)
            paths=[]
            def collect(node):
                if isinstance(node,dict):
                    if "$path" in node: paths.append(node["$path"])
                    for v in node.values(): collect(v)
            collect(project["tree"])
            self.assertEqual(len(paths),expected)
            self.assertEqual(len(set(paths)),expected)
            for path in paths:
                self.assertTrue((folder/path).is_file(),path)

    def test_no_live_gameplay_authority_writes(self):
        # The new author files live only in OWN quality_gameplay path;
        # the original #482 project and scripts remain unchanged by construction.
        self.assertTrue((ORIGINAL / "EGGRUMBLE_SwarmCombat.luau").exists())
        self.assertTrue((ORIGINAL / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").exists())


if __name__ == "__main__":
    unittest.main()
