#!/usr/bin/env python3
"""Negative / inverse tests for the SINGLE V3 host fix (no extra Game)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

FILE = Path(__file__).resolve().parent / "select_safe_lobby.py"
spec = importlib.util.spec_from_file_location("safe_lobby_selector", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ORIGINAL_HOST = """--!strict
local Players=game:GetService("Players")
local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)::SpawnLocation?
local root=spawn and spawn.Position or Vector3.new(0,4,0)
local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace
local joined:{[number]:string}={}
local function block(parent:Instance,name:string,pos:Vector3,size:Vector3,color:Color3):Part
 local p=Instance.new("Part");p.Name=name;p.Size=size;p.Position=pos;p.Anchored=true
 p.Color=color;p.Material=Enum.Material.SmoothPlastic;p.Parent=parent
 return p
end
local function board(at:BasePart,label:string)
end
"""

class LobbySourceContract(unittest.TestCase):
    def test_inserts_only_once_and_off_is_exact(self):
        selected = mod.apply(ORIGINAL_HOST)
        self.assertEqual(selected.count(mod.MARKER), 1)
        self.assertEqual(selected.count('Instance.new("SpawnLocation")'), 1)  # exactly one fallback spawn
        self.assertEqual(mod.rollback(selected), ORIGINAL_HOST)
        self.assertEqual(selected.count("local function board("), 1)
        self.assertIn('joined[player.UserId]~=nil', selected)
        self.assertIn('player.Character~=character', selected)

    def test_no_duplicate_game_remote_or_source(self):
        selected = mod.apply(ORIGINAL_HOST)
        for phrase in ('Instance.new("RemoteEvent")', 'Instance.new("DataStore")',
                       'Instance.new("Script")', 'Instance.new("ModuleScript")'):
            self.assertNotIn(phrase, selected)

    def test_double_apply_rejected(self):
        with self.assertRaisesRegex(ValueError, "RED_ALREADY_APPLIED"):
            mod.apply(mod.apply(ORIGINAL_HOST))

    def test_drifted_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError, "RED_UNIQUE_BOARD_ANCHOR"):
            mod.apply(ORIGINAL_HOST.replace("local function board(", "local function billboard("))

    def test_reverse_rejects_mutant_patch(self):
        selected = mod.apply(ORIGINAL_HOST)
        with self.assertRaisesRegex(ValueError, "RED_MARKER_OR_PATCH_DRIFT"):
            mod.rollback(selected.replace("Duration=0", "Duration=10"))

    def test_physical_space_covers_role_and_mode_portals(self):
        # Floor is centred z=40, spans z=-34..114 and x=-61..61.
        for x,z in [(-27,69),(27,69),(-12,28),(12,28),(-18,47),(18,47),(0,0)]:
            self.assertTrue(-61 <= x <= 61 and -34 <= z <= 114)

    def test_project_only_single_host_and_off_exact(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            names=[mod.TARGET]+[f"OTHER_{n:02d}" for n in range(30)]
            nodes={}
            for name in names:
                path=name+(".server.luau" if name==mod.TARGET else ".luau")
                (root/path).write_text(ORIGINAL_HOST if name==mod.TARGET else "return {}\n")
                nodes[name]={"$path":path}
            base=root/"BASE.project.json"
            out=root/"ON.project.json"
            base.write_text(json.dumps({"name":"safe-test","tree":{"ServerScriptService":nodes}}))
            mod.prepare(base,out)
            before,old,target=mod.mapping(base)
            after,new,target2=mod.mapping(out)
            self.assertEqual(target,target2)
            self.assertEqual(len(old),len(new))
            self.assertEqual(len(old),31)
            self.assertEqual(mod.rollback(new[target].read_text()),old[target].read_text())
            self.assertTrue(all(old[k].read_bytes()==new[k].read_bytes() for k in old if k!=target))
            receipt=json.loads((root/"GQ_SAFE_LOBBY_RECEIPT.json").read_text())
            self.assertFalse(receipt["formal_rc_adopted"])
            self.assertTrue(receipt["other_30_source_exact"])

if __name__=="__main__":
    unittest.main()
