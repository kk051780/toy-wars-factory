"""GQ470 matte sky candidate: restrictive offline source/packet regression tests.

These are source-only checks. A pass is NOT Luau Native, Studio, ART, Android, or FUN pass.
"""
from pathlib import Path
import importlib.util
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_FarSkyFacets.client.luau"
PACKER = ROOT / "pack_candidate.py"

def validate(text: str) -> None:
    expected = (
        'MAX_DESKTOP_BANKS = 6', 'MAX_TOUCH_BANKS = 4',
        'FACETS_PER_BANK = 3', 'MAX_PARTS = MAX_DESKTOP_BANKS * FACETS_PER_BANK',
        'Instance.new("WedgePart")', 'part.Anchored = true',
        'part.CanCollide = false', 'part.CanTouch = false',
        'part.CanQuery = false', 'part.CastShadow = false',
        'part.Material = Enum.Material.SmoothPlastic',
        'if made >= MAX_PARTS then', 'folder:SetAttribute("PartBudgetActual", made)',
        'UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled',
        'if Workspace:FindFirstChild(FOLDER_NAME) then', 'for i = 1, bankCount do',
        'math.cos(theta) * distance', 'math.sin(theta) * distance',
        'GQ470_FB015_FAR_SKY_MATTE_CLOUD_BANKS_20261121',
    )
    for marker in expected:
        if marker not in text:
            raise ValueError("SOURCE_GATE_MISSING_" + marker)
    forbidden = (
        'Enum.Material.Neon', 'RemoteEvent', 'RemoteFunction',
        'RunService', 'Heartbeat', 'RenderStepped', '.Touched:',
        'while true', 'task.spawn', 'ParticleEmitter', 'PointLight',
        'Lighting', 'Humanoid', 'TakeDamage', 'DataStore', 'MarketplaceService',
    )
    executable = "\n".join(line.split("--", 1)[0] for line in text.splitlines())
    for word in forbidden:
        if word in executable:
            raise ValueError("SOURCE_GATE_FORBIDDEN_" + word)
    if len(re.findall(r'facet\("Cloud"', text)) != 3:
        raise ValueError("SOURCE_GATE_FACET_CALLS_NOT_THREE")
    for match in re.findall(r',\s*(0\.\d+)\)', text):
        alpha = float(match)
        if alpha < 0.3:
            raise ValueError("SOURCE_GATE_LOW_ALPHA")
    if "source-only" not in SOURCE.name.lower() and len(text.encode()) > 9000:
        raise ValueError("SOURCE_GATE_UNBOUNDED_SIZE")

class SourceGate(unittest.TestCase):
    def test_source_contract(self):
        validate(SOURCE.read_text(encoding="utf-8"))

    def test_mutations_fail_closed(self):
        src = SOURCE.read_text(encoding="utf-8")
        mutations = [
            ('part.CanCollide = false', 'part.CanCollide = true'),
            ('part.CastShadow = false', 'part.CastShadow = true'),
            ('MAX_TOUCH_BANKS = 4', 'MAX_TOUCH_BANKS = 6'),
            ('MAX_DESKTOP_BANKS = 6', 'MAX_DESKTOP_BANKS = 500'),
            ('Instance.new("WedgePart")', 'Instance.new("Part")'),
            ('part.Material = Enum.Material.SmoothPlastic', 'part.Material = Enum.Material.Neon'),
            ('if made >= MAX_PARTS then', 'if false then'),
        ]
        for before, after in mutations:
            self.assertIn(before, src)
            with self.subTest(replacement=after), self.assertRaises(ValueError):
                validate(src.replace(before, after))
        with self.assertRaises(ValueError):
            validate(src + '\nRunService.Heartbeat:Connect(function() end)')

    def test_pack_candidate_isolated(self):
        spec = importlib.util.spec_from_file_location("gq470_sky_pack", PACKER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d)
            result = module.package(dest)
            self.assertEqual(result["stage"], "A_PREP_SOURCE_ONLY")
            self.assertEqual(result["extra_candidate_scripts"], 1)
            self.assertEqual(result["possible_selected_source_count"], 70)
            self.assertEqual(result["native_luau"], "NOT_TESTED")
            self.assertEqual(result["studio"], "NOT_TESTED")
            self.assertEqual(result["art_owner"], "NO_GO")
            routed = dest / module.ROUTE
            self.assertTrue(routed.exists())
            self.assertEqual(routed.read_bytes(), SOURCE.read_bytes())

if __name__ == "__main__":
    unittest.main()
