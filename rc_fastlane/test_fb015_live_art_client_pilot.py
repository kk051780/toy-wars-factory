#!/usr/bin/env python3
"""#431 deny-first contract/negative tests. No runtime art acceptance claim."""
import unittest,tempfile
from pathlib import Path
from apply_fb015_live_art_client_pilot import OLD,NEW,FLAG,ATTR,FILES,patch,apply
class T(unittest.TestCase):
    def test_studio_unchanged(self):
        self.assertIn("if RunService:IsStudio() then return true end",NEW)
    def test_public_off(self):
        self.assertIn('if game.PrivateServerId == "" then return false end',NEW)
    def test_private_not_automatically_on(self):
        self.assertIn('workspace:GetAttribute("'+ATTR+'") == true',NEW)
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
    def test_client_cosmetics_only(self):
        self.assertEqual(len(FILES),2)
        self.assertTrue(all(p.startswith("client/") for p in FILES))
        self.assertNotIn("server/Game.server.luau",FILES)
    def test_no_authority_in_switch(self):
        for token in ("FireServer(","TakeDamage(","OnServerEvent","FillBlock(","CanCollide =","DataStore"):
            self.assertNotIn(token,NEW)
if __name__=="__main__":unittest.main()
