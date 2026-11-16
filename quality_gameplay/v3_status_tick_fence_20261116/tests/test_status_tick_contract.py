"""Pinned author-source and generated-only status tick overlay regression."""
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
ORIGIN = ROOT / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
SRC = ORIGIN / "EGGRUMBLE_SevenRoleCombat.luau"
HERE = pathlib.Path(__file__).resolve().parents[1]
PATCHED = HERE / "EGGRUMBLE_SevenRoleCombat.patched.luau"
POLICY = HERE / "EGGRUMBLE_StatusTickFence.luau"
ORIGINAL_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


class StatusFenceSource(unittest.TestCase):
    def test_origin_blob_pinned(self):
        self.assertEqual(git_blob_sha(SRC.read_bytes()), ORIGINAL_BLOB,
                         "author source drift; fail closed, never silently rebase")

    def test_surgical_status_overlay(self):
        original = SRC.read_text()
        target = PATCHED.read_text()
        self.assertEqual(original.count('if h.Parent and h.Health>0 and session.rules.phase=="ACTIVE" then h:TakeDamage(tick) end'), 1)
        self.assertNotIn('if h.Parent and h.Health>0 and session.rules.phase=="ACTIVE" then h:TakeDamage(tick) end', target)
        self.assertEqual(target.count("StatusTickFence.canTick("), 1)
        self.assertEqual(original.count("h:TakeDamage(tick)"), 1)
        self.assertEqual(target.count("h:TakeDamage(tick)"), 1)
        for needle in (
            'local originalRules=session.rules',
            'local function apply(h:Humanoid,bot:Model?,targetId:string)',
            'apply(hum,actor,id)',
            'apply(hum,nil,tostring(targetPlayer.UserId))',
            'sameTarget=(session.botActors or {})[targetId]==bot',
            'player.Character:FindFirstChildOfClass("Humanoid")==h',
        ):
            self.assertIn(needle, target)
        for needle in ('targetCastle.alive==true', 'originalRules.winner~=nil',
                       'originalRules.castles[targetId]~=targetCastle'):
            self.assertIn(needle, POLICY.read_text())
        self.assertNotIn('StatusTickFence', original)

    def test_isolated_exact_22_source_composition(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "private_status22"
            subprocess.run([sys.executable, str(HERE / "tools/compose_private22.py"),
                            "--out", str(out)], check=True, cwd=ROOT)
            project = json.loads((out / "EGGRUMBLE_STATUS22.project.json").read_text())
            mapped = []
            def walk(node):
                if isinstance(node, dict):
                    if "$path" in node:
                        mapped.append(node["$path"])
                    else:
                        for key, value in node.items():
                            if not key.startswith("$"):
                                walk(value)
            walk(project["tree"])
            self.assertEqual(len(mapped), 22)
            self.assertEqual(len(set(mapped)), 22)
            orig_project=json.loads((ORIGIN/"EGGRUMBLE_V3_STUDIO.EGGRUMBLE_STATUS22.project.json").read_text())
            old=[]
            walk_origin=lambda node: None
            def walk_before(node):
                if isinstance(node,dict):
                    if "$path" in node:
                        old.append(node["$path"])
                    else:
                        for key,val in node.items():
                            if not key.startswith("$"): walk_before(val)
            walk_before(orig_project["tree"])
            self.assertEqual(len(old),21)
            self.assertEqual(set(mapped)-set(old),{"EGGRUMBLE_StatusTickFence.luau"})
            receipt=json.loads((out/"SOURCE_RECEIPT.json").read_text())
            self.assertEqual(receipt["original_unchanged"],20)
            self.assertEqual(receipt["private_source_count"],22)
            self.assertEqual(receipt["official_rc_integrated"],False)
            self.assertEqual((out/"EGGRUMBLE_SevenRoleCombat.luau").read_bytes(),PATCHED.read_bytes())
            for path in old:
                if path=="EGGRUMBLE_SevenRoleCombat.luau": continue
                self.assertEqual((out/path).read_bytes(),(ORIGIN/path).read_bytes(),path)

    def test_no_alternate_game_authority(self):
        self.assertNotIn("Instance.new", POLICY.read_text())
        self.assertNotIn("RemoteEvent", POLICY.read_text())
        self.assertNotIn("TakeDamage", POLICY.read_text())


if __name__ == "__main__":
    unittest.main()
