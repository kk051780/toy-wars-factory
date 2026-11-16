import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "tools" / "overlay_current26.py"
spec = importlib.util.spec_from_file_location("overlay_current26", SRC)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)


class Reuse27NegativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        game = sorted(overlay.SERVER_REQUIRED)
        server_names = game + ["UNIQUE_AUTHOR_" + str(i) for i in range(23 - len(game))]
        self.assertEqual(len(server_names), 23)
        base = {"$className": "ServerScriptService"}
        clients = {"$className": "StarterPlayerScripts"}
        sha = {}
        for name in server_names:
            kind = ".server.luau" if name == overlay.GAME_HOST else ".luau"
            p = self.root / (name + kind)
            p.write_text("--!strict\nreturn {}\n", encoding="utf-8")
            base[name] = {"$path": "../" + p.name}
            sha[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        for name in overlay.CLIENT_SET:
            p = self.root / (name + ".client.luau")
            p.write_text("--!strict\nreturn nil\n", encoding="utf-8")
            clients[name] = {"$path": "../" + p.name}
            sha[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        self.base = self.artifacts / "original26.project.json"
        self.base.write_text(json.dumps({"name": "existing", "tree": {
            "$className": "DataModel", "ServerScriptService": base,
            "StarterPlayer": {"$className": "StarterPlayer", "StarterPlayerScripts": clients}
        }}), encoding="utf-8")
        self.receipt = self.artifacts / "SOURCE_RECEIPT.json"
        self.receipt.write_text(json.dumps({"status": "SOURCE_ONLY_NOT_OFFICIAL_RC",
            "script_count": 26, "source_sha256": sha}), encoding="utf-8")
        self.script = self.root / "EGGRUMBLE_ObjectiveCompass.client.luau"
        self.script.write_text("--!strict\n-- EGGRUMBLE_GQ_ObjectiveCompass\n"
            "if not RunService:IsStudio() then return end\n", encoding="utf-8")
        self.dest = self.artifacts / "new27.project.json"

    def make(self):
        return overlay.compose(self.base, self.receipt, self.script, self.dest)

    def test_real_overlay_keeps_all_existing_26_exact(self):
        old = json.loads(self.base.read_text())
        report = self.make()
        new = json.loads(self.dest.read_text())
        before = overlay.flatten(old["tree"])
        after = overlay.flatten(new["tree"])
        self.assertEqual(len(before), 26)
        self.assertEqual(len(after), 27)
        self.assertEqual({k: after[k] for k in before}, before)
        self.assertEqual(report["total_sources"], 27)
        self.assertEqual(report["official_rc_integrated"], False)
        self.assertTrue((self.artifacts / "GQ_OBJECTIVE_27_RECEIPT.json").is_file())

    def test_mutated_original_author_source_is_red(self):
        original = self.root / (overlay.GAME_HOST + ".server.luau")
        original.write_text("--!strict\n-- unreviewed mutation\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Underlying"):
            self.make()

    def test_missing_boss_or_art_fails_closed(self):
        data = json.loads(self.base.read_text())
        del data["tree"]["ServerScriptService"]["EGGRUMBLE_BossSessionFence"]
        # Maintain count to prove check detects missing required logical source, not just size.
        data["tree"]["ServerScriptService"]["UNAUTHORIZED_SOURCE"] = {"$path": "../UNIQUE_AUTHOR_0.luau"}
        self.base.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Original combat"):
            self.make()

    def test_new_client_cannot_be_server_or_remote(self):
        self.script.write_text("--!strict\n-- EGGRUMBLE_GQ_ObjectiveCompass\n"
            "if RunService:IsStudio() then FireServer() end\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.make()

    def test_other_project_path_and_existing_overlay_refused(self):
        with self.assertRaisesRegex(ValueError, "same artifacts"):
            overlay.compose(self.base, self.receipt, self.script, self.root / "different.json")
        data = json.loads(self.base.read_text())
        data["tree"]["StarterPlayer"]["StarterPlayerScripts"][overlay.CLIENT_NAME] = {
            "$path": "../EGGRUMBLE_ObjectiveCompass.client.luau"}
        self.base.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already installed"):
            self.make()


    def authored_item(self):
        owner = self.root / "item_owner"
        owner.mkdir(exist_ok=True)
        item = owner / "EGGRUMBLE_FieldItemPickups.luau"
        item.write_text('--!strict\\n-- canary source contract only\\n'
            'local function carryingEnemyEggs() end\\n'
            'local function cancelBuffIfCarrier() end\\n'
            'local RESPAWN_SECONDS=35\\n'
            'local interactionGuard = {}\\n'
            'function Items.start() interactionGuard.allow(player,part,"拾う",part.Name) end\\n',
            encoding="utf-8")
        return item, hashlib.sha256(item.read_bytes()).hexdigest()

    def test_reuse_exact_item_author_single_file_and_keep_other_25(self):
        before = overlay.flatten(json.loads(self.base.read_text())["tree"])
        item, sha = self.authored_item()
        report = overlay.compose(self.base, self.receipt, self.script, self.dest,
                                 item_source=item, item_sha256=sha)
        after = overlay.flatten(json.loads(self.dest.read_text())["tree"])
        self.assertEqual(len(after), 27)
        for k, path in before.items():
            if k != overlay.ITEM_PATH:
                self.assertEqual(after[k], path, k)
        self.assertNotEqual(after[overlay.ITEM_PATH], before[overlay.ITEM_PATH])
        self.assertTrue(report["item_source_selectively_replaced"])
        self.assertTrue(report["original_25_source_paths_preserved"])
        self.assertFalse(report["original_26_sources_preserved"])
        self.assertEqual(report["item_author_sha256"], sha)

    def test_wrong_item_author_sha_fails_closed_without_output(self):
        item, sha = self.authored_item()
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            overlay.compose(self.base, self.receipt, self.script, self.dest,
                            item_source=item, item_sha256="0"*64)
        self.assertFalse(self.dest.exists())

    def test_missing_original_item_guard_and_carrier_safety_fails(self):
        item, sha = self.authored_item()
        item.write_text("function Items.start() end\\n", encoding="utf-8")
        new_sha = hashlib.sha256(item.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "fairness/LOS"):
            overlay.compose(self.base, self.receipt, self.script, self.dest,
                            item_source=item, item_sha256=new_sha)
        self.assertFalse(self.dest.exists())


if __name__ == "__main__":
    unittest.main()
