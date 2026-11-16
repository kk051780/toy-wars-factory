#!/usr/bin/env python3
"""Deterministic selector regression, corruption negatives and 31-source OFF test."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from select_lobby_safe_spawn import TAG, TARGET, OUTPUT_NAME, mapping, prepare, transform

HOST = """--!strict
local Players=game:GetService("Players")
local folder=Instance.new("Folder")
local joined:{[number]:string}={}
local sessions:{[string]:any}={}
local function block(parent,name,pos,size,color)
 return nil
end
local function board(at,label)
 return nil
end
"""

class LobbySafeSpawnTests(unittest.TestCase):
    def test_floor_and_spawn_are_singletons_and_return_inactive_only(self):
        new=transform(HOST)
        self.assertEqual(new.count("GQ648_LOBBY_SAFE_FLOOR"),1)
        self.assertEqual(new.count("GQ648_LOBBY_NEUTRAL_SPAWN"),1)
        self.assertIn("Vector3.new(118,4,144)",new)
        self.assertIn("safeLobbySpawn.Neutral=true",new)
        self.assertIn("if matchMode and sessions[matchMode] then return end",new)
        self.assertIn("player.Character~=character",new)
        self.assertIn("humanoid.Health<=0",new)
        self.assertIn("Players.PlayerAdded:Connect(gq648BindLobbyCharacter)",new)
        self.assertIn("for _,player in ipairs(Players:GetPlayers()) do",new)

    def test_duplicate_application_refused(self):
        with self.assertRaisesRegex(ValueError,"RED_SPAWN_PATCH_ALREADY_EXISTS"):
            transform(transform(HOST))

    def test_missing_placement_refused(self):
        with self.assertRaisesRegex(ValueError,"RED_HOST_BLOCK_BOARD_ANCHOR_DRIFT"):
            transform(HOST.replace("local function board(","local function noBoard("))

    def test_missing_match_session_guard_refused(self):
        with self.assertRaisesRegex(ValueError,"RED_HOST_REQUIRED_TOKEN"):
            transform(HOST.replace("local sessions:","local missingSessions:"))

    def test_exactly_31_sources_one_host_only_off_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            tree={"$className":"DataModel","ServerScriptService":{"$className":"ServerScriptService"}}
            for i in range(30):
                name="Keep"+str(i)
                fn=name+".luau"
                (d/fn).write_text("return {}\n",encoding="utf8")
                tree["ServerScriptService"][name]={"$path":fn}
            fn="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
            (d/fn).write_text(HOST,encoding="utf8")
            tree["ServerScriptService"][TARGET]={"$path":fn}
            base=d/"base.project.json"
            out=d/"after.project.json"
            base.write_text(json.dumps({"name":"GQ648","tree":tree}),encoding="utf8")
            old=mapping(base)[1]
            prepare(base,out)
            new=mapping(out)[1]
            changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
            self.assertEqual(changed,[("ServerScriptService",TARGET)])
            self.assertEqual(len(new),31)
            self.assertTrue((d/OUTPUT_NAME).exists())
            receipt=json.loads((d/"GQ648_LOBBY_SAFE_SPAWN_RC31_RECEIPT.json").read_text())
            self.assertTrue(receipt["off_inverse_host_byte_exact"])
            self.assertTrue(receipt["other_30_byte_exact"])
            self.assertFalse(receipt["formal_rc_adopted"])

if __name__=="__main__":
    unittest.main()
