#!/usr/bin/env python3
"""Static source smoke tests for #361 READY/900 adapter.

These inspect the actual original author Game/HUD/Config; assembled RC66
and real Roblox Studio remain separate explicit acceptance gates.
"""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "releases" / "P0D_S1_KIDS_RC01" / "src"
MODULE = ROOT / "rc_fastlane" / "apply_owner361_ready900.py"

spec = importlib.util.spec_from_file_location("owner361_ready900", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def read(path: str) -> str:
    return (SOURCE / path).read_text(encoding="utf8")


class Owner361Ready900Tests(unittest.TestCase):
    def test_authoritative_original_game_ready_and_replay(self):
        src = read(mod.GAME)
        out = mod.patch_game(src)
        self.assertEqual(src.count("remote.OnServerEvent:Connect("), 1)
        self.assertEqual(out.count("remote.OnServerEvent:Connect("), 1)
        self.assertEqual(out.count("local function applyVoluntaryReady("), 1)
        self.assertIn('if match.phase ~= "LOBBY" and match.phase ~= "COUNTDOWN" then return end', out)
        self.assertIn("if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end", out)
        self.assertIn("if type(data.ready) ~= \"boolean\" then return end", out)
        self.assertIn("voluntaryReady[player] = false", out)
        self.assertIn("voluntaryReady[player] = nil", out)
        self.assertIn("if not allHumansReady() then return end", out)
        self.assertIn('    elseif match.phase == "COUNTDOWN" then\n        if not allHumansReady() then', out)
        self.assertIn("voluntaryReady[human] = false", out)
        self.assertIn("ready = voluntaryReady[player] == true", out)
        self.assertIn('data.action == "READY"', out)
        self.assertNotIn("DataStoreService", out)

    def test_exact_original_hud_wire_ready_and_mobile_button(self):
        src = read(mod.HUD)
        out = mod.patch_hud(src)
        self.assertIn('button(gui, "Owner361Ready"', out)
        self.assertIn('ready = if kind == "READY" then not voluntaryReady else nil', out)
        self.assertIn('readyButton.MouseButton1Click:Connect', out)
        self.assertIn('readyButton.Visible = s.phase == "LOBBY" or s.phase == "COUNTDOWN"', out)
        self.assertIn('status.Text = if voluntaryReady', out)
        self.assertEqual(src.count('remote:FireServer('), out.count('remote:FireServer('))

    def test_default_is_fifteen_minutes_not_six(self):
        out = mod.patch_config(read(mod.CONFIG))
        self.assertIn("MatchSeconds = 900,", out)
        self.assertNotIn("MatchSeconds = 360,", out)

    def test_foreign_source_fails_closed(self):
        with self.assertRaisesRegex(AssertionError, "SOURCE_DRIFT"):
            mod.patch_game("--!strict\n")
        with self.assertRaisesRegex(AssertionError, "SOURCE_DRIFT"):
            mod.patch_hud("local seq = 0\n")
        with self.assertRaisesRegex(AssertionError, "SOURCE_DRIFT"):
            mod.patch_config("MatchSeconds = 900,\n")

    def test_off_never_writes_even_without_dist(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "does-not-exist"
            self.assertFalse(mod.apply(path, False))
            self.assertFalse(path.exists())

    def test_blob_function_matches_git(self):
        data = b"hello\n"
        digest = hashlib.sha1(b"blob 6\0hello\n").hexdigest()
        self.assertEqual(mod.gitblob(data), digest)


if __name__ == "__main__":
    unittest.main()
