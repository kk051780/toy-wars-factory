"""Non-duplicating regression for latest weather Guardian42 -> one neutral Swarm43."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class WeatherLineageGuard(unittest.TestCase):
    def test_source_roll_forward_without_stale_42(self):
        flow=(ROOT.parent.parent/".github/workflows/gq800-neutral8-live-real43.yml").read_text(encoding="utf-8")
        composer=(ROOT/"compose_real43.py").read_text(encoding="utf-8")
        packer=(ROOT/"package_real43.py").read_text(encoding="utf-8")
        self.assertIn("gh run download 44319450066",flow)
        self.assertNotIn("gh run download 44316989683",flow)
        self.assertIn("B_PORTABLE42_WEATHER_SOURCE_RECEIPT.json",flow)
        self.assertIn("WEATHER_ROUTES",composer)
        self.assertIn("weather_and_stage_renderer_exact",composer)
        self.assertIn("ecb52ec035f0013d6fd9e19c599bce5fb0f272037e7e091346e3dc38523417d1",composer)
        self.assertIn("parent_weather42_run",packer)
    def test_no_replacement_of_non_swarm_authorities(self):
        source=(ROOT/"compose_real43.py").read_text(encoding="utf-8")
        self.assertIn('RED_DUPLICATE_DAMAGE_OR_SWARM',source)
        self.assertIn('RED_MODIFIED_EXISTING_AUTHORITY_',source)
        self.assertIn('if route!=SWARM and after[route].read_bytes()!=original.read_bytes()',source)
if __name__=="__main__":
    unittest.main()
