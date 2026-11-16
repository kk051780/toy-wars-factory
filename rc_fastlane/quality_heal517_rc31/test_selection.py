"""Independent source-slice negative QA of existing author's #517 HEAL guard on latest #489."""
from __future__ import annotations
import json
import os
import unittest
from pathlib import Path
from select_original_heal517 import (
    AUTHOR489_ITEM_BLOB, ANCHOR, ITEM, blob, collect, get_author_patch,
)

ROOT=Path(os.environ.get("GQ517_TEST_DIR","artifacts/gq539_official_select"))
BASE_NAME=os.environ.get("GQ517_TEST_BASE","GQ539_ITEM489_SELECTED31.project.json")
ON_NAME=os.environ.get("GQ517_TEST_ON","GQ539_ITEM489_HEAL517_SELECTED31.project.json")
AUTHOR517=Path("_gq517_original/quality_gameplay/v3_heal_no_waste_20261116/patch_heal_item.py")

class AuthorHeal517ExactIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=get_author_patch(AUTHOR517)
        cls.base=ROOT/BASE_NAME
        cls.on=ROOT/ON_NAME
        cls.originalMap,cls.old=collect(cls.base)
        cls.selectedMap,cls.new=collect(cls.on)
        cls.oldSource=cls.old[ITEM].read_text(encoding="utf-8")
        cls.newSource=cls.new[ITEM].read_text(encoding="utf-8")

    def test_existing_author489_unmodified_as_parent(self):
        self.assertEqual(blob(self.old[ITEM].read_bytes()),AUTHOR489_ITEM_BLOB)

    def test_exact_author517_used_and_one_gameplay_change(self):
        self.assertEqual(self.newSource,self.author.patch(self.oldSource))
        self.assertEqual([k for k in self.old if self.old[k].read_bytes()!=self.new[k].read_bytes()],[ITEM])
        self.assertEqual(len(self.old),len(self.new),31)

    def test_reverse_uses_exact_original_item(self):
        self.assertEqual(self.newSource.replace(self.author.HELPER,"",1).replace(self.author.CALL,"",1),self.oldSource)

    def test_no_second_heal_guard_or_item_authority(self):
        self.assertEqual(self.newSource.count("function Items.start("),1)
        self.assertEqual(self.newSource.count(ANCHOR),1)
        self.assertEqual(self.newSource.count("return Items"),1)

    def test_before_consumption_or_cooldown(self):
        p=self.newSource.index(ANCHOR)
        for token in ("local key=tostring(player.UserId)", "consumed[id]=true;lastUse[key]=now",
                      'interactionGuard.allow(player,part,"拾う",part.Name)',
                      "prompt.Enabled=false"):
            self.assertLess(p,self.newSource.index(token))

    def test_existing_item_cargo_stealth_los_and_respawn_preserved(self):
        for token in (
            'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end',
            'interactionGuard.allow(player,part,"拾う",part.Name)',
            "if not matchActive() or player.Character~=buffCharacter then return end",
            "local RESPAWN_SECONDS=35",
        ):
            self.assertIn(token,self.newSource)

    def test_explicit_bad_anchor_and_duplicate_feature_fail_closed(self):
        with self.assertRaises(AssertionError):
            self.author.patch(self.oldSource.replace(self.author.CALL_ANCHOR,"-- changed root distance anchor"))
        with self.assertRaises(AssertionError):
            self.author.patch(self.newSource)

    def test_actual_receipt_is_not_studio_or_owner_acceptance(self):
        r=json.loads((ROOT/"GQ517_HEAL_RC31_RECEIPT.json").read_text())
        self.assertEqual(r["script_count"],31)
        self.assertEqual(r["original_other_source_bytes_exact"],30)
        self.assertFalse(r["engine_tested"])
        self.assertFalse(r["owner_accepted"])
        self.assertEqual(r["source_class_exact"],31)
        self.assertEqual(r["changed_script"],"ServerScriptService/EGGRUMBLE_FieldItemPickups")

if __name__=="__main__":unittest.main()
