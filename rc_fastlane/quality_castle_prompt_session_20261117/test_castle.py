"""Castle attack/decoration/vault original Host session fence tests."""
import os
from pathlib import Path
import tempfile
import json
import unittest
from select_castle import PAIR,HOST,patch,unpatch,mapping,FEATURE

SAMPLE = """--!strict
-- GQ_DEPOSIT_CURRENT_MATCH_586
 session.isCurrentHuman=function(player:Player):boolean
  return true
 end
 prompt(door,"攻城攻撃","敵城を攻める",function(p)
  if joined[p.UserId]~=session.mode or not session.rules then return end
 end)
 prompt(deco,"旗の装飾変更","自分の城",function(p)
  if not session.rules or tostring(p.UserId)~=entry.id then return end
 end)
 prompt(vault,"敵の卵を奪取","卵3個から1個ずつ",function(p)
  if not session.rules or joined[p.UserId]~=session.mode then return end
 end)
"""

class CastleSessionSource(unittest.TestCase):
    def test_selected_host_keeps_original_server_script_class(self):
        from select_castle import FILE
        self.assertTrue(FILE.endswith('.server.luau'))
        self.assertNotEqual(FILE.endswith('.client.luau'),True)

    def test_one_host_three_reversible_guards(self):
        changed=patch(SAMPLE)
        self.assertEqual(unpatch(changed),SAMPLE)
        self.assertEqual(sum(changed.count(new) for _,new in PAIR),3)
        self.assertEqual(changed.count("session.isCurrentHuman(p)~=true"),3)

    def test_fail_closed_callback_missing(self):
        new=patch(SAMPLE)
        self.assertEqual(new.count('type(session.isCurrentHuman)~="function"'),3)

    def test_double_overlay_rejected(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            patch(patch(SAMPLE))

    def test_old_deposit_not_overwritten(self):
        x=patch(SAMPLE)
        self.assertIn("-- GQ_DEPOSIT_CURRENT_MATCH_586",x)
        self.assertIn("session.isCurrentHuman=function",x)

    def test_cannot_miss_old_author_guard(self):
        with self.assertRaisesRegex(ValueError,"MEMBERSHIP_AUTHORITY"):
            patch(SAMPLE.replace("session.isCurrentHuman=function","session.member=function"))

    def test_one_missing_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            patch(SAMPLE.replace(PAIR[2][0],"if true then return end"))

    def test_not31_source_map_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json";p.write_text(json.dumps({"tree":{}}))
            with self.assertRaisesRegex(ValueError,"SINGLE_HOST_31"):
                mapping(p)

    def test_actual_31_if_ci(self):
        base=os.environ.get("GQ8_CASTLE_BASE31")
        if not base:self.skipTest("Official selected31 is supplied by PR Actions")
        _,files=mapping(Path(base))
        self.assertIn(HOST,files)
        original=files[HOST].read_text(encoding="utf-8")
        selected=patch(original)
        self.assertNotEqual(original,selected)
        self.assertEqual(unpatch(selected),original)
        for old,new in PAIR:
            self.assertEqual(original.count(old),1)
            self.assertEqual(selected.count(new),1)
            self.assertNotIn(new,original)

if __name__=="__main__":unittest.main()
