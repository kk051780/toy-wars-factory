#!/usr/bin/env python3
"""Falsification tests against exact original-author #482 Luau source, not fixtures."""
import copy
import json
import os
from pathlib import Path
import unittest

from check_trace import TraceFailure
from probe_v3_author_source import MATRIX, PINS, fetch_pinned_source, run_probe


@unittest.skipUnless(os.getenv("GQ_V3_SOURCE_DIR"), "integration runner must download original author source first")
class OriginalSevenRoleSourceEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = Path(os.environ["GQ_V3_SOURCE_DIR"])
        cls.source = fetch_pinned_source(cls.directory)
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_actual_original_five_blobs_and_eight_domains(self):
        observations = run_probe(self.source, self.matrix)
        self.assertEqual(len(self.source), 5)
        self.assertTrue(all(observations[d] == "SOURCE_ANCHORS_PRESENT_NOT_ENGINE_PROOF"
                            for d in ["CHARACTER", "FIELD", "BATTLE", "CASTLE",
                                      "NEUTRAL", "ITEM", "LOBBY", "BALANCE"]))

    def test_missing_role_branch_cannot_pass(self):
        changed = copy.deepcopy(self.source)
        changed["EGGRUMBLE_SevenRoleCombat.luau"] = changed["EGGRUMBLE_SevenRoleCombat.luau"].replace(
            ' elseif role=="ZOMBIE" then', ' elseif role=="ZOMBIE_MISSING" then', 1)
        with self.assertRaises(TraceFailure):
            run_probe(changed, self.matrix)

    def test_mage_heal_source_change_triggers_reaudit(self):
        changed = copy.deepcopy(self.source)
        changed["EGGRUMBLE_SevenRoleCombat.luau"] = changed["EGGRUMBLE_SevenRoleCombat.luau"].replace(
            "healAllies(session,p,root);blast()", "newRealRescue(session,p);blast()", 1)
        with self.assertRaises(TraceFailure):
            run_probe(changed, self.matrix)

    def test_field_original_3_paths_must_be_present(self):
        changed = copy.deepcopy(self.source)
        changed["EGGRUMBLE_LobbyCastleModesPreview.server.luau"] = changed[
            "EGGRUMBLE_LobbyCastleModesPreview.server.luau"].replace(
                '"TacticalRoute_"', '"UnexpectedRoute_"', 1)
        with self.assertRaises(TraceFailure):
            run_probe(changed, self.matrix)

    def test_castle_egg_source_source_anchor_is_required(self):
        changed = copy.deepcopy(self.source)
        changed["EGGRUMBLE_CastleMatchRules.luau"] = changed["EGGRUMBLE_CastleMatchRules.luau"].replace(
            "function M.takeFieldEgg(", "function M.oldPickup(", 1)
        with self.assertRaises(TraceFailure):
            run_probe(changed, self.matrix)

    def test_falsely_resolved_beast_gap_is_rejected(self):
        changed = copy.deepcopy(self.matrix)
        for row in changed["rows"]:
            if row["CONCEPT_ID"] == "P0D-014":
                row["GAP_TYPE"] = "EVIDENCE_MISSING"
        with self.assertRaises(TraceFailure):
            run_probe(self.source, changed)

    def test_falsely_resolved_rescue_gap_is_rejected(self):
        changed = copy.deepcopy(self.matrix)
        for row in changed["rows"]:
            if row["CONCEPT_ID"] == "P0D-019":
                row["GAP_TYPE"] = "PARTIAL"
        with self.assertRaises(TraceFailure):
            run_probe(self.source, changed)

    def test_original_content_tamper_is_detected(self):
        changed = self.directory / "EGGRUMBLE_SevenRoleCombat.luau"
        original = changed.read_bytes()
        try:
            changed.write_bytes(original + b"\n-- forged\n")
            with self.assertRaises(TraceFailure):
                fetch_pinned_source(self.directory)
        finally:
            changed.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
