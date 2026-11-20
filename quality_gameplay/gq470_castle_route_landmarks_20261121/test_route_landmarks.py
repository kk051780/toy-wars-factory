#!/usr/bin/env python3
"""Isolated source-only contract for the optional 3-route landmark sculpture.

These are synthetic checks and never establish Studio visibility, physics
behavior, Android FPS, player FUN, or 69-source RC integration.
"""
from __future__ import annotations
import pathlib
import re
import unittest

SOURCE = pathlib.Path(__file__).with_name("RouteLandmarks.luau")
MARK = "GQ470_ROUTE_LANDMARKS_REAL69_20261121"
PART_NAMES = ("_LeftPillar", "_RightPillar", "_Lintel", "_Crest")
NO_AUTHORITY = ("RemoteEvent", "RemoteFunction", "DataStoreService",
                "TakeDamage", "MarketplaceService", "ProximityPrompt",
                "BillboardGui", "ScreenGui", "CollectionService")

def audit(src: str) -> dict:
    if src.count(MARK) != 1: raise ValueError("SOURCE_MARKER")
    if "local EXPECTED_ROUTES = 3" not in src: raise ValueError("THREE_ROUTES")
    if "local PARTS_PER_ROUTE = 4" not in src: raise ValueError("FOUR_PARTS")
    if "local SIDE_OFFSET = 20" not in src: raise ValueError("CORRIDOR_OFFSET")
    if "local MIN_ANCHOR_SEPARATION = 24" not in src: raise ValueError("UNIQUE_ANCHORS")
    if src.count("makePart(decoration,") != 4: raise ValueError("GEOMETRY_COUNT")
    if any(name not in src for name in PART_NAMES): raise ValueError("DISTINCT_PARTS")
    if src.count("Instance.new(\"WedgePart\")") != 1: raise ValueError("TAPERED_CRESTS")
    if src.count("Instance.new(\"Part\")") != 1: raise ValueError("COLUMN_PART")
    for field in ("Anchored = true", "CanCollide = false", "CanTouch = false",
                  "CanQuery = false", "CastShadow = false"):
        if src.count(field) != 1: raise ValueError("NONPHYSICAL_" + field)
    for banned in NO_AUTHORITY:
        # The code may mention exclusions in comments; only active source matters.
        active = "\n".join(line.split("--", 1)[0] for line in src.splitlines())
        if banned in active: raise ValueError("GAME_AUTHORITY_" + banned)
    for guard in ("not root:IsDescendantOf(workspace)",
                  "not current:IsDescendantOf(workspace)",
                  "current == anchors[j]",
                  "not RouteLandmarks.clear(root)",
                  'prior:GetAttribute("GQ470RouteVisual") ~= true',
                  "prior:Destroy()"):
        if guard not in src: raise ValueError("LIFECYCLE_" + guard)
    if not src.rstrip().endswith("return RouteLandmarks"):
        raise ValueError("MODULE_RETURN")
    if "for index = 1, EXPECTED_ROUTES do" not in src:
        raise ValueError("LOOP_BOUND")
    if "decoration.Parent = root" not in src:
        raise ValueError("NO_PARENTED_GEOMETRY")
    return {"routes": 3, "parts_each": 4, "max_per_attach": 12,
            "physics": "OFF", "existing_sources_modified": 0,
            "studio": "NOT_TESTED", "android": "NOT_TESTED",
            "art_gate": "ART_NO_GO", "owner_accepted": False}

class RouteLandmarkSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_positive_twelve_real_parts(self):
        v = audit(self.source)
        self.assertEqual(v["max_per_attach"], 12)
        self.assertFalse(v["owner_accepted"])

    def test_rejects_dangerous_physics_and_fake_parts(self):
        for before, after in (("CanCollide = false", "CanCollide = true"),
                              ("CanTouch = false", "CanTouch = true"),
                              ("CanQuery = false", "CanQuery = true"),
                              ("CastShadow = false", "CastShadow = true"),
                              ("PARTS_PER_ROUTE = 4", "PARTS_PER_ROUTE = 40"),
                              ("SIDE_OFFSET = 20", "SIDE_OFFSET = 2"),
                              ("MIN_ANCHOR_SEPARATION = 24", "MIN_ANCHOR_SEPARATION = 0")):
            with self.subTest(before=before), self.assertRaises(ValueError):
                audit(self.source.replace(before, after, 1))

    def test_rejects_new_authority(self):
        for term in NO_AUTHORITY:
            with self.subTest(term=term), self.assertRaises(ValueError):
                audit(self.source.replace("return RouteLandmarks", 'local _unused = "' + term + '"\nreturn RouteLandmarks'))

    def test_rejects_removed_cleanup_or_world_verification(self):
        for fragment in ("prior:Destroy()", "current == anchors[j]",
                         "not current:IsDescendantOf(workspace)",
                         "not RouteLandmarks.clear(root)"):
            with self.subTest(fragment=fragment), self.assertRaises(ValueError):
                audit(self.source.replace(fragment, "false", 1))

    def test_distinct_profiles_and_no_eggs_or_castle_damage(self):
        self.assertEqual(len(re.findall(r'\{Vector3\.new\(', self.source)), 3)
        self.assertNotIn("eggScore", self.source)
        self.assertNotIn("castleHealth", self.source)

if __name__ == "__main__":
    unittest.main()
