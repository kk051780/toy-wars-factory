#!/usr/bin/env python3
"""Source exact, reverse exact, and corrupt-input negative checks (NOT engine)."""
import os
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from patch_swarm_subject69 import BASE, TARGET, OLD, NEW, ORIGINAL_SHA, PLACE, \
    PROJECT, RECEIPT, patch, sha, selected, run, selftest

class GQ470SwarmSubjectTests(unittest.TestCase):
    def test_original_scope_and_8_mutations(self):
        selftest()

    def test_no_scope_expansion(self):
        source=('local function soldier(p:Instance,at:Vector3,n:number):Model\n'
                ' local h=Instance.new("Humanoid")\n'+OLD+'\n h.Parent=m\nend')
        changed=patch(source)
        self.assertEqual(changed.replace(NEW,OLD),source)
        self.assertEqual(changed.count("HumanoidDisplayDistanceType.Subject"),1)
        self.assertIn("HealthDisplayDistance=16",changed)
        for bad in [source.replace("NameDisplayDistance=0","NameDisplayDistance=18"),
                    source.replace("HealthDisplayDistance=16","HealthDisplayDistance=0"),
                    source.replace(OLD," h.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.None\n"+OLD),
                    source.replace('h=Instance.new("Humanoid")','h=Instance.new("Folder")')]:
            with self.assertRaises(ValueError):patch(bad)

    def test_actual_formal69_original_byte_exact_optional(self):
        base=os.environ.get("EGGRUMBLE_FORMAL69_ROOT")
        if not base:self.skipTest("Real official 69 artifact path not supplied")
        base=Path(base)
        self.assertEqual(json.loads((base/RECEIPT).read_text())["build_head"],BASE)
        with tempfile.TemporaryDirectory(prefix="gq470_real69_swarm_") as tmp:
            candidate=Path(tmp)/"candidate"
            shutil.copytree(base,candidate)
            before={r:p.read_bytes() for r,p in selected(candidate).items()}
            place_before=(candidate/PLACE).read_bytes()
            self.assertEqual(len(before),69)
            self.assertEqual(sha(before[TARGET]),ORIGINAL_SHA)
            run(candidate)
            after={r:p.read_bytes() for r,p in selected(candidate).items()}
            self.assertEqual({r for r in before if before[r]!=after[r]},{TARGET})
            self.assertEqual(after[TARGET].decode().replace(NEW,OLD).encode(),before[TARGET])
            self.assertEqual({r:v for r,v in after.items() if r!=TARGET},
                             {r:v for r,v in before.items() if r!=TARGET})
            off=candidate/"OFF69_SWARM_SUBJECT_EXACT"
            self.assertEqual((off/PLACE).read_bytes(),place_before)
            self.assertEqual({r:p.read_bytes() for r,p in selected(off).items()},before)
            receipt=json.loads((candidate/RECEIPT).read_text())
            self.assertEqual(receipt["selected_source_count"],69)
            self.assertEqual(receipt["gq470_swarm_subject_visual"]["actual_art_screenshots"],0)
            self.assertFalse(receipt["gq470_swarm_subject_visual"]["formal_adopted"])
            with self.assertRaises(ValueError):run(candidate)

if __name__=="__main__":unittest.main(verbosity=2)
