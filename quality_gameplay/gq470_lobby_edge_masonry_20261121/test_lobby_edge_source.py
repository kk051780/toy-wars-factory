#!/usr/bin/env python3
"""Fast static/geometry ART420 guard for optional lobby edge masonry.

Source safety/shape tests only. NOT Roblox Studio, art comparison, FPS or FUN.
"""
from __future__ import annotations
import math
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_LobbyEdgeMasonry.client.luau"


def safe_code(code: str) -> bool:
    required = [
        'local PARTS_PER_FLOOR = 8',
        'local MAX_FLOORS = 1',
        'local MAX_EXTRA_PARTS = PARTS_PER_FLOOR * MAX_FLOORS',
        'local REFRESH_SECONDS = 2.5',
        'GQ646_LOBBY_SAFE_GROUND',
        'EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW',
        'player:GetAttribute("EGGRUMBLE_ReducedEffects")',
        'Workspace.DescendantAdded:Connect',
        'Workspace.DescendantRemoving:Connect',
        'while script.Parent do',
        'for index = 1, PARTS_PER_FLOOR do',
        'stone.CanCollide = false',
        'stone.CanTouch = false',
        'stone.CanQuery = false',
        'stone.CastShadow = false',
        'stone.Anchored = true',
        'stone.Material = Enum.Material.Slate',
        'stone.Reflectance = 0',
        'floor.Size.Y * .5 - .46',
        'assert(floors * PARTS_PER_FLOOR <= MAX_EXTRA_PARTS)',
        'folder.Parent = floor',
    ]
    forbidden = [
        'RemoteEvent', 'FireServer', 'InvokeServer', 'DataStoreService',
        'TakeDamage', 'LoadCharacter', 'SpawnLocation")',
        'Instance.new("ScreenGui")', 'Instance.new("BillboardGui")',
        'Enum.Material.Neon', 'RenderStepped', 'Heartbeat:Connect',
        'RunService', '.CanCollide = true', '.CanQuery = true',
        'task.wait(0)', 'Lighting.Brightness',
    ]
    return (all(token in code for token in required)
            and all(token not in code for token in forbidden)
            and code.count('Instance.new("WedgePart")') == 1
            and code.count('stone.Parent = folder') == 1
            and bool(re.search(r'^\\s*stone\\.Reflectance = 0\\s*
            and code.count('GQ470_FB015_LOBBY_EDGE_MASONRY_20261121') == 1)


def sample_geometry(along: float, across: float, thickness: float) -> list[dict]:
    assert all(math.isfinite(x) and x >= 4 for x in (along, across, thickness))
    size = min(max(along * .21, 1.4), 11.)
    entries = []
    for section in (1, 2):
        lateral = (-.27 if section == 1 else .27) * along
        outward = across * .5 + .17
        floor_top = thickness * .5
        stone_center = floor_top - .46
        entries.append({
            "lateral": lateral, "half_width": size / 2,
            "outer": outward + .35, "inner": outward - .35,
            "z_floor_edge": across * .5,
            "top": stone_center + .85 / 2,
            "floor_top": floor_top
        })
    return entries


class TestLobbyEdgeMasonry(unittest.TestCase):
    def test_art_source_contract(self):
        self.assertTrue(safe_code(SOURCE.read_text()), "RED_ART_SOURCE_POLICY")

    def test_eight_parts_one_floor(self):
        code = SOURCE.read_text()
        self.assertRegex(code, r'for side = 1, 4 do')
        self.assertRegex(code, r'for section = 1, 2 do')
        self.assertIn('local index = (side - 1) * 2 + section', code)
        self.assertEqual(4 * 2, 8)

    def test_geometry_inside_edges_and_below_walkable_top(self):
        for along, across, depth in [
            (4, 4, 4), (8, 4, 4), (16, 24, 6),
            (60, 60, 4), (120, 24, 10), (200, 200, 12)
        ]:
            for g in sample_geometry(along, across, depth):
                self.assertLessEqual(abs(g["lateral"]) + g["half_width"],
                                     along * .5)
                self.assertLess(g["inner"], g["z_floor_edge"])
                self.assertGreater(g["outer"], g["z_floor_edge"])
                self.assertLess(g["top"], g["floor_top"])
                self.assertGreater(g["floor_top"] - g["top"], 0.03)

    def test_fail_closed_negative_mutations(self):
        code = SOURCE.read_text()
        mutations = {
            "collision": code.replace('stone.CanCollide = false',
                                      'stone.CanCollide = true', 1),
            "touch": code.replace('stone.CanTouch = false',
                                  'stone.CanTouch = true', 1),
            "query": code.replace('stone.CanQuery = false',
                                  'stone.CanQuery = true', 1),
            "shadow": code.replace('stone.CastShadow = false',
                                   'stone.CastShadow = true', 1),
            "over_budget": code.replace('local PARTS_PER_FLOOR = 8',
                                        'local PARTS_PER_FLOOR = 96', 1),
            "per_frame": code + '\nRunService.RenderStepped:Connect(refresh)\n',
            "neon": code.replace('Enum.Material.Slate', 'Enum.Material.Neon', 1),
            "privacy": code.replace('player:GetAttribute("EGGRUMBLE_ReducedEffects")',
                                    'player:GetAttribute("EGGRUMBLE_ExtraEffects")', 1),
            "streaming": code.replace('Workspace.DescendantRemoving:Connect',
                                      'Workspace.DescendantGone:Connect', 1),
            "floor_owner": code.replace('GQ646_LOBBY_SAFE_GROUND',
                                         'GQ646_UNKNOWN', 1),
            "no_cast_shadow": code.replace('stone.Reflectance = 0',
                                          'stone.Reflectance = 0.5', 1),
            "move_above_top": code.replace('floor.Size.Y * .5 - .46',
                                           'floor.Size.Y * .5 + .46', 1),
        }
        for name, mutated in mutations.items():
            self.assertNotEqual(mutated, code, f"BAD_MUTATION_NO_OP_{name}")
            self.assertFalse(safe_code(mutated), f"BAD_MUTATION_ACCEPTED_{name}")

    def test_qa_does_not_claim_runtime_pass(self):
        composer = (ROOT / "compose_real70.py").read_text()
        for label in ("NOT_TESTED", "0/32", "ART_NO_GO",
                      "A_SOURCE_ONLY_NOT_FORMAL"):
            self.assertIn(label, composer)
        self.assertNotIn('"studio_solo": "PASS"', composer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
, code, re.MULTILINE))
            and code.count('local FEATURE_ID = ') == 1
            and code.count('GQ470_FB015_LOBBY_EDGE_MASONRY_20261121') == 1)


def sample_geometry(along: float, across: float, thickness: float) -> list[dict]:
    assert all(math.isfinite(x) and x >= 4 for x in (along, across, thickness))
    size = min(max(along * .21, 1.4), 11.)
    entries = []
    for section in (1, 2):
        lateral = (-.27 if section == 1 else .27) * along
        outward = across * .5 + .17
        floor_top = thickness * .5
        stone_center = floor_top - .46
        entries.append({
            "lateral": lateral, "half_width": size / 2,
            "outer": outward + .35, "inner": outward - .35,
            "z_floor_edge": across * .5,
            "top": stone_center + .85 / 2,
            "floor_top": floor_top
        })
    return entries


class TestLobbyEdgeMasonry(unittest.TestCase):
    def test_art_source_contract(self):
        self.assertTrue(safe_code(SOURCE.read_text()), "RED_ART_SOURCE_POLICY")

    def test_eight_parts_one_floor(self):
        code = SOURCE.read_text()
        self.assertRegex(code, r'for side = 1, 4 do')
        self.assertRegex(code, r'for section = 1, 2 do')
        self.assertIn('local index = (side - 1) * 2 + section', code)
        self.assertEqual(4 * 2, 8)

    def test_geometry_inside_edges_and_below_walkable_top(self):
        for along, across, depth in [
            (4, 4, 4), (8, 4, 4), (16, 24, 6),
            (60, 60, 4), (120, 24, 10), (200, 200, 12)
        ]:
            for g in sample_geometry(along, across, depth):
                self.assertLessEqual(abs(g["lateral"]) + g["half_width"],
                                     along * .5)
                self.assertLess(g["inner"], g["z_floor_edge"])
                self.assertGreater(g["outer"], g["z_floor_edge"])
                self.assertLess(g["top"], g["floor_top"])
                self.assertGreater(g["floor_top"] - g["top"], 0.03)

    def test_fail_closed_negative_mutations(self):
        code = SOURCE.read_text()
        mutations = {
            "collision": code.replace('stone.CanCollide = false',
                                      'stone.CanCollide = true', 1),
            "touch": code.replace('stone.CanTouch = false',
                                  'stone.CanTouch = true', 1),
            "query": code.replace('stone.CanQuery = false',
                                  'stone.CanQuery = true', 1),
            "shadow": code.replace('stone.CastShadow = false',
                                   'stone.CastShadow = true', 1),
            "over_budget": code.replace('local PARTS_PER_FLOOR = 8',
                                        'local PARTS_PER_FLOOR = 96', 1),
            "per_frame": code + '\nRunService.RenderStepped:Connect(refresh)\n',
            "neon": code.replace('Enum.Material.Slate', 'Enum.Material.Neon', 1),
            "privacy": code.replace('player:GetAttribute("EGGRUMBLE_ReducedEffects")',
                                    'player:GetAttribute("EGGRUMBLE_ExtraEffects")', 1),
            "streaming": code.replace('Workspace.DescendantRemoving:Connect',
                                      'Workspace.DescendantGone:Connect', 1),
            "floor_owner": code.replace('GQ646_LOBBY_SAFE_GROUND',
                                         'GQ646_UNKNOWN', 1),
            "no_cast_shadow": code.replace('stone.Reflectance = 0',
                                          'stone.Reflectance = 0.5', 1),
            "move_above_top": code.replace('floor.Size.Y * .5 - .46',
                                           'floor.Size.Y * .5 + .46', 1),
        }
        for name, mutated in mutations.items():
            self.assertNotEqual(mutated, code, f"BAD_MUTATION_NO_OP_{name}")
            self.assertFalse(safe_code(mutated), f"BAD_MUTATION_ACCEPTED_{name}")

    def test_qa_does_not_claim_runtime_pass(self):
        composer = (ROOT / "compose_real70.py").read_text()
        for label in ("NOT_TESTED", "0/32", "ART_NO_GO",
                      "A_SOURCE_ONLY_NOT_FORMAL"):
            self.assertIn(label, composer)
        self.assertNotIn('"studio_solo": "PASS"', composer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
