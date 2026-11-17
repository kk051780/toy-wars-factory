import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class Contract(unittest.TestCase):
    def test_no_second_game_authority(self):
        src=(ROOT/"PassiveRegenPolicy.luau").read_text()
        for forbidden in ("Humanoid.Health =", "DataStoreService", "OnServerEvent", "RemoteEvent", "SetAttribute("):
            self.assertNotIn(forbidden, src)
    def test_pinned_numbers_and_roster(self):
        src=(ROOT/"PassiveRegenPolicy.luau").read_text()
        for value in ('QUIET_SECONDS = 7','RATE_PER_SECOND = 0.007','MAX_ELAPSED_STEP = 0.5',
                      'WARRIOR = 250','MAGE = 195','NINJA = 185','TRAPPER = 205',
                      'BUILDER = 225','BEAST = 220','ZOMBIE = 230'):
            self.assertIn(value,src)
    def test_generator_mutant(self):
        with tempfile.TemporaryDirectory() as d:
            good=Path(d)/"good.luau"
            bad=Path(d)/"bad.luau"
            subprocess.run([sys.executable,str(ROOT/"make_native.py"),"--out",str(good)],check=True)
            subprocess.run([sys.executable,str(ROOT/"make_native.py"),"--out",str(bad),"--mutant"],check=True)
            self.assertIn('QUIET_SECONDS = 7',good.read_text())
            self.assertIn('QUIET_SECONDS = 0',bad.read_text())
            self.assertIn('GQ8_HP_REGEN_NATIVE_19_PLUS_7_ROLES_PASS',good.read_text())
if __name__=="__main__":
    unittest.main()
