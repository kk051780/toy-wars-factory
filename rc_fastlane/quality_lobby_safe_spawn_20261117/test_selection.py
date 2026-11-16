#!/usr/bin/env python3
"""GQ646 fast negative and reversible source mutation tests."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location("gq646",Path(__file__).with_name("select_safe_lobby.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE='''local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace
local sessions:{[string]:any}={}
local joined:{[number]:string}={}
local function block(parent:Instance,name:string,pos:Vector3,size:Vector3,color:Color3):Part
 return nil
end
'''

class SafeLobbyTest(unittest.TestCase):
    def test_off_exact(self):
        on=mod.transform(BASE)
        self.assertEqual(on.replace(mod.INSERT,"",1),BASE)
        self.assertEqual(on.count(mod.MARKER),1)
        self.assertIn("Players.PlayerAdded:Connect(bindGQ646LobbyCharacter)",on)
        self.assertIn("if mode and sessions[mode] then return end",on)
        self.assertIn("lobbyGround.CanCollide=true",on)
        self.assertIn("lobbySpawn.Neutral=true",on)
        self.assertIn("hrp.CFrame=CFrame.new(root+Vector3.new(0,5,-27))",on)
    def test_no_duplicate(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            mod.transform(mod.transform(BASE))
    def test_reject_missing_anchor(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            mod.transform(BASE.replace(mod.ANCHOR,"NO_ANCHOR"))
    def test_reject_no_membership(self):
        with self.assertRaisesRegex(ValueError,"MEMBERSHIP"):
            mod.transform(BASE.replace("local sessions:","local states:"))
    def test_reject_wrong_folder(self):
        with self.assertRaisesRegex(ValueError,"MODEL"):
            mod.transform(BASE.replace("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW","other"))

if __name__=="__main__":
    unittest.main()
