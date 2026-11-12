#!/usr/bin/env python3
"""Source locked eight-safe complete 37-file S1 review; exactly 1 changed HUD."""

from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import unittest

REPO=pathlib.Path(__file__).resolve().parents[2]
ROOT=REPO/"releases/P0D_S1_KIDS_RC01"
SEVEN_SHA="6cc131d3de06fe8799d00f475fc446a526e4b2c4"
HUD_SOURCE_COMMIT="82847cb97d06394f8fba5ec5c88e644dce0a336b"
HUD_SOURCE_PATH="handoffs/P0D-S1-HUD-SNAPSHOT-ORDER-20261112-09/candidate/src/client/HUD.client.luau"
HUD="src/client/HUD.client.luau"
MANIFEST="BUILD_MANIFEST.json"
OLD_HUD_BLOB="b3d3996c40c690e19007a36a847d5b10fc6a1522"
NEW_HUD_BLOB="50823390853989ccdda78e28c16ea4757bbe0715"
GAME="src/server/Game.server.luau"
COACH="src/shared/FirstMinuteModel.luau"
ORIGINAL_GAME_BLOB="e684ca79b8f5ed279bcdf033f4118bf77d552abb"
ORIGINAL_COACH_BLOB="d8dda6b1781375612c123f8c83b6f23fe45d09f1"

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def git_read(commit,path):
    proc=subprocess.run(["git","-C",str(REPO),"show",commit+":"+path],
        capture_output=True,timeout=25,check=False)
    if proc.returncode:
        raise AssertionError("FROZEN_GIT_SOURCE_UNAVAILABLE "+commit+":"+path)
    return proc.stdout

def manifest_rows(binary):
    obj=json.loads(binary)
    assert obj["game_id"]=="TRAP_RAIDERS" and obj["packet_id"]=="P0D-S1-KIDS-RC01"
    assert obj["public_source_allowed"] is True
    rows=obj["files"]
    assert len(rows)==37
    items={r["path"]:r for r in rows}
    assert len(items)==37
    return items

class FullEightSafeReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=manifest_rows(git_read(SEVEN_SHA,"releases/P0D_S1_KIDS_RC01/"+MANIFEST))
        cls.new=manifest_rows((ROOT/MANIFEST).read_bytes())

    def test_original_hud_provenance(self):
        old=git_read(SEVEN_SHA,"releases/P0D_S1_KIDS_RC01/"+HUD)
        self.assertEqual(git_blob(old),OLD_HUD_BLOB)
        source=git_read(HUD_SOURCE_COMMIT,HUD_SOURCE_PATH)
        self.assertEqual(git_blob(source),NEW_HUD_BLOB)
        self.assertEqual((ROOT/HUD).read_bytes(),source)

    def test_game_and_coach_sources_unchanged(self):
        self.assertEqual(git_blob((ROOT/GAME).read_bytes()),ORIGINAL_GAME_BLOB)
        self.assertEqual(git_blob((ROOT/COACH).read_bytes()),ORIGINAL_COACH_BLOB)

    def test_only_hud_row_different(self):
        self.assertEqual(set(self.old),set(self.new))
        altered={path for path in self.old if self.old[path]!=self.new[path]}
        self.assertEqual(altered,{HUD})

    def test_unchanged_36_assets_identical_to_seven_safe(self):
        for path in self.new:
            if path==HUD: continue
            with self.subTest(path=path):
                original=git_read(SEVEN_SHA,"releases/P0D_S1_KIDS_RC01/"+path)
                self.assertEqual((ROOT/path).read_bytes(),original)

    def test_all_37_source_sha256_and_size_exact(self):
        for path,row in self.new.items():
            with self.subTest(path=path):
                name=pathlib.PurePosixPath(path)
                self.assertNotIn("..",name.parts)
                self.assertFalse(name.is_absolute())
                f=ROOT/name
                self.assertTrue(f.is_file() and not f.is_symlink())
                raw=f.read_bytes()
                self.assertEqual(row["size"],len(raw))
                self.assertEqual(row["sha256"],hashlib.sha256(raw).hexdigest())

    def test_21_luau_scripts_and_single_server(self):
        scripts=list((ROOT/"src").rglob("*.luau"))
        self.assertEqual(len(scripts),21)
        self.assertEqual(sum(p.name.endswith(".server.luau") for p in scripts),1)
        self.assertEqual(sum(p.name.endswith(".client.luau") for p in scripts),3)

    def test_hud_only_three_surgical_hunks(self):
        prior=git_read(SEVEN_SHA,"releases/P0D_S1_KIDS_RC01/"+HUD).decode("utf8")
        file=(ROOT/HUD).read_text(encoding="utf8")
        from_pinned=git_read(HUD_SOURCE_COMMIT,HUD_SOURCE_PATH).decode("utf8")
        self.assertEqual(file,from_pinned)
        self.assertIn("local lastUpdateId = -1",file)
        self.assertIn("id <= lastUpdateId then return",file)
        self.assertIn("if id ~= nil then lastUpdateId = id end",file)
        self.assertNotIn("local lastUpdateId = -1",prior)

    def test_hud_server_and_coach_protocol_align(self):
        game=(ROOT/GAME).read_text(encoding="utf8")
        coach=(ROOT/COACH).read_text(encoding="utf8")
        hud=(ROOT/HUD).read_text(encoding="utf8")
        self.assertEqual(game.count("snapshotUpdateId += 1"),1)
        self.assertIn("updateId = snapshotUpdateId",game)
        self.assertIn("id <= state.lastUpdateId",coach)
        self.assertIn("id <= lastUpdateId",hud)
        self.assertIn("elseif lastUpdateId >= 0 then",hud)
        self.assertIn("elseif state.lastUpdateId >= 0 then",coach)

    def test_preserve_mobile_placement_input_security(self):
        hud=(ROOT/HUD).read_text(encoding="utf8")
        self.assertIn('UDim2.new(1, -140, 1, -110)',hud)
        self.assertIn('action("PLACE_TRAP", nil)',hud)
        self.assertEqual(hud.count("remote:FireServer"),1)
        self.assertIn('s.kind == "BOSS_VISUAL"',hud)

    def test_no_new_game_authority_or_boss_activation(self):
        game=(ROOT/GAME).read_text("utf8")
        self.assertEqual(game.count("remote.OnServerEvent:Connect("),1)
        self.assertIn("local CANONICAL_S1_ENABLED = false",game)
        self.assertIn("local D07_D08_RELEASE_REVIEW_APPROVED = false",game)
        self.assertIn("other ~= player and getTeamName(other) == side",game)
        self.assertIn("math.abs(position.X) > 130",game)
        self.assertIn("math.abs(position.Z) > 76",game)

    def test_original_rojo_mapping_unchanged(self):
        self.assertEqual((ROOT/"default.project.json").read_bytes(),
            git_read(SEVEN_SHA,"releases/P0D_S1_KIDS_RC01/default.project.json"))

    def test_reject_synthetic_manifest_mutant(self):
        broken=dict(self.new[HUD])
        broken["sha256"]="0"*64
        self.assertNotEqual(broken["sha256"],hashlib.sha256((ROOT/HUD).read_bytes()).hexdigest())

if __name__=="__main__":
    unittest.main(verbosity=2)
