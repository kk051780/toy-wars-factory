"""Negative source tests for the existing-author 26->27 integration adapter."""
from pathlib import Path
import os
import importlib.util
import unittest

MOD_PATH = Path(__file__).resolve().parents[1] / "tools/compose_private_27.py"
spec = importlib.util.spec_from_file_location("deadline_composer", MOD_PATH)
comp = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(comp)

HOST_STUB = '''
local BossSessionFence=require(script.Parent:WaitForChild("EGGRUMBLE_BossSessionFence"))
local function startSession(mode:string)
 session.closeRound=function() end
 session.refresh=function()
  ResultService.showIfFinished(session,queue,mode)
  RoundReplay.schedule(session,session.closeRound)
 end
 Rules.start(session.rules)
end
'''

SCORE_STUB = '''
local ranking=ScoreBalance.build(session.rules,session.swarm and session.swarm.kills or {})
if session.resultsDelivered then return false end
local status=if won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"
'''

class SourceSelectiveAdapterTest(unittest.TestCase):
    def test_host_uses_existing_result_replay_after_expire(self):
        patched = comp.patch_host(HOST_STUB)
        self.assertEqual(patched.count("DeadlinePolicy.expire("), 1)
        self.assertEqual(patched.count("session.refresh()"), 1)
        self.assertIn('sessions[mode]==session', patched)
        self.assertIn('session.rules.phase=="ACTIVE"', patched)
        self.assertIn('DeadlinePolicy.new(os.clock(),deadlineId)', patched)

    def test_host_rejects_wrong_author_base(self):
        with self.assertRaises(AssertionError):
            comp.patch_host(HOST_STUB.replace(' Rules.start(session.rules)', ' Rules.start(other.rules)'))

    def test_host_rejects_duplicate_timer_injection(self):
        modified = comp.patch_host(HOST_STUB)
        with self.assertRaises(AssertionError):
            comp.patch_host(modified)

    def test_score_keeps_real_score_and_draw_non_winner(self):
        patched = comp.patch_result(SCORE_STUB)
        self.assertIn('local ranking=ScoreBalance.build(', patched)
        self.assertIn('session.rules.winner=="DRAW" then "引き分け"', patched)
        self.assertEqual(patched.count('local status='), 1)

    def test_score_rejects_wrong_owner_script(self):
        with self.assertRaises(AssertionError):
            comp.patch_result(SCORE_STUB.replace("ScoreBalance.build", "AnotherScore.build"))

    def test_regression_future_start_semantics(self):
        with self.assertRaises(AssertionError):
            comp.patch_host(HOST_STUB.replace("session.refresh=function()", "session.someOtherRefresh=function()"))



class ItemAuthorSourceSelectTest(unittest.TestCase):
    """Execute the real file overlay composer against synthetic 26 mapped authors."""

    def setUp(self):
        from tempfile import TemporaryDirectory
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.base = self.path / "base"
        self.artifacts = self.path / "artifacts"
        self.base.mkdir()
        self.artifacts.mkdir()

        def source(name, data, suffix=".luau"):
            p = self.base / (name + suffix)
            p.write_text(data, encoding="utf-8")
            return {"$path": os.path.relpath(p, self.artifacts)}

        self.old_item = "local DEFINITIONS={}\\nlocal RESPAWN_SECONDS=35\\nreturn Items\\n"
        self.new_item = (
            'local DEFINITIONS={}\\n'
            'local function carryingEnemyEggs() return true end\\n'
            'local function cancelBuffIfCarrier() end\\n'
            'interactionGuard.allow(player,part,"拾う",part.Name)\\n'
            'local RESPAWN_SECONDS=35\\n'
            'return Items\\n'
        )
        server = {"$className": "ServerScriptService"}
        server[comp.HOST] = source(comp.HOST, HOST_STUB, ".server.luau")
        server[comp.RESULT] = source(comp.RESULT, SCORE_STUB)
        server[comp.ITEM] = source(comp.ITEM, self.old_item)
        server["EGGRUMBLE_BossSessionFence"] = source("EGGRUMBLE_BossSessionFence", "return {}\\n")
        for i in range(19):
            key = f"OtherOriginalModule{i}"
            server[key] = source(key, "return {}\\n")
        self.assertEqual(len(server)-1, 23)
        client = {"$className": "StarterPlayerScripts"}
        for name in ("EGGRUMBLE_ProceduralSkills", "EGGRUMBLE_ArtDistanceLOD", "EGGRUMBLE_CombatFeel"):
            client[name] = source(name, "print('client')\\n", ".client.luau")
        # Both #484 composer and #499 overlay project manifests live in artifacts/.
        # Paths in each manifest are relative to that shared directory.
        self.project = self.artifacts / "base26.project.json"
        self.project.write_text(__import__("json").dumps({"tree":{
            "ServerScriptService": server,
            "StarterPlayer":{"$className":"StarterPlayer","StarterPlayerScripts":client},
        }}), encoding="utf-8")
        self.policy = self.base / "EGGRUMBLE_DeadlinePolicy.luau"
        self.policy.write_text("local Deadline={}\\nfunction Deadline.expire() end\\nreturn Deadline\\n", encoding="utf-8")
        self.item = self.base / (comp.ITEM + ".luau")
        # item is a separate source checkout, not the base original file
        self.author_item = self.path / "item_authored" / (comp.ITEM + ".luau")
        self.author_item.parent.mkdir()
        self.author_item.write_text(self.new_item, encoding="utf-8")
        self.output = self.artifacts / "complete27.project.json"

    def test_overlay_preserves_23_original_sources_and_uses_actual_item_bytes(self):
        import json
        receipt = comp.compose(self.project, self.policy, self.output, self.author_item)
        self.assertEqual(receipt["source_count"], 27)
        self.assertEqual(receipt["unchanged_original_sources"], 23)
        self.assertTrue(receipt["item_author_byte_exact"])
        self.assertEqual(receipt["private_modified_original_sources"],
                         [comp.ITEM, comp.HOST, comp.RESULT])
        manifest = json.loads(self.output.read_text(encoding="utf-8"))
        placed = manifest["tree"]["ServerScriptService"][comp.ITEM]
        got = (self.output.parent / placed["$path"]).resolve(strict=True).read_bytes()
        self.assertEqual(got, self.author_item.read_bytes())
        # Never mutate original standalone item or 26-source base manifest.
        self.assertEqual(self.item.read_text(encoding="utf-8"), self.old_item)
        self.assertNotIn("EGGRUMBLE_DeadlinePolicy",
                         json.loads(self.project.read_text())["tree"]["ServerScriptService"])

    def test_rejects_unrelated_item_source(self):
        self.author_item.write_text("return Items\\n", encoding="utf-8")
        with self.assertRaises(AssertionError):
            comp.compose(self.project, self.policy, self.output, self.author_item)

    def test_rejects_wrong_item_author_name(self):
        bad = self.author_item.with_name("NotTheFieldItems.luau")
        bad.write_text(self.new_item, encoding="utf-8")
        with self.assertRaises(AssertionError):
            comp.compose(self.project, self.policy, self.output, bad)

if __name__=="__main__":
    unittest.main()
