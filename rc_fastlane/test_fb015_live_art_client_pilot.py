#!/usr/bin/env python3
"""#431 deny-first contract/negative tests. No runtime art acceptance claim."""
import unittest,tempfile
from pathlib import Path
from apply_fb015_live_art_client_pilot import OLD,NEW,SERVER_OLD,SERVER_NEW,SERVER,OWNER_OPTIN,CLIENTS,FLAG,ATTR,FILES,patch,patch_server,apply
class T(unittest.TestCase):
    def test_studio_unchanged(self):
        self.assertIn("if RunService:IsStudio() then return true end",NEW)
    def test_public_off(self):
        self.assertIn('game.PrivateServerId ~= ""',SERVER_NEW)
        self.assertIn('if not RunService:IsStudio() then',SERVER_NEW)
        self.assertNotIn("PrivateServerId",NEW)
    def test_private_not_automatically_on(self):
        self.assertIn('workspace:GetAttribute("'+OWNER_OPTIN+'") == true',SERVER_NEW)
        self.assertIn('workspace:SetAttribute("'+ATTR+'", true)',SERVER_NEW)
        self.assertIn('workspace:GetAttribute("'+ATTR+'") == true',NEW)
    def test_late_server_authorization_is_bounded(self):
        self.assertIn("for _ = 1, 40 do",NEW)
        self.assertIn("task.wait(.2)",NEW)
        self.assertIn("return false",NEW)
    def test_original_source_byte_restored(self):
        b=("foo\n"+OLD+"\nbar").encode()
        self.assertEqual(patch(b).replace(NEW.encode(),OLD.encode()),b)
    def test_second_patch_fails(self):
        with self.assertRaises(AssertionError):patch(patch(OLD.encode()))
    def test_two_guards_fails(self):
        with self.assertRaises(AssertionError):patch((OLD+"\n"+OLD).encode())
    def test_missing_guard_fails(self):
        with self.assertRaises(AssertionError):patch(b"foo")
    def test_disabled_no_disk_write(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"destination"
            self.assertFalse(apply(Path(d)/"none",p,False))
            self.assertFalse(p.exists())
    def test_cosmetics_only_and_single_server_authorizer(self):
        self.assertEqual(len(FILES),3)
        self.assertTrue(all(p.startswith("client/") for p in CLIENTS))
        self.assertEqual(SERVER,"server/CastleDetailArt.server.luau")
        self.assertNotIn("server/Game.server.luau",FILES)
    def test_server_guard_exact_restore(self):
        raw=(SERVER_OLD+"\nprint(123)").encode()
        fixed=patch_server(raw)
        self.assertEqual(fixed.replace(SERVER_NEW.encode(),SERVER_OLD.encode()),raw)
    def test_server_double_guard_rejected(self):
        with self.assertRaises(AssertionError):patch_server(patch_server(SERVER_OLD.encode()))
    def test_server_missing_guard_rejected(self):
        with self.assertRaises(AssertionError):patch_server(b"print(3)")
    def test_no_authority_in_switch(self):
        for token in ("FireServer(","TakeDamage(","OnServerEvent","FillBlock(","CanCollide =","DataStore"):
            self.assertNotIn(token,NEW)
if __name__=="__main__":unittest.main()
