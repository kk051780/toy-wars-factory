from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT/'EGGRUMBLE_NeutralSpawnPacing.luau').read_text(encoding='utf-8')
SPEC = (ROOT/'tests/spec_native.luau').read_text(encoding='utf-8')

class Contract(unittest.TestCase):
    def test_source_is_real_luau_and_no_second_authority(self):
        self.assertIn('function Pacing.step(', SRC)
        self.assertIn('Pacing.MAX_ALIVE = 110', SRC)
        self.assertIn('Pacing.NOMINAL_RATE = 40', SRC)
        self.assertNotIn('SetAttribute(', SRC)
        self.assertNotIn('OnServerEvent', SRC)
        self.assertNotIn('Humanoid:TakeDamage', SRC)
        self.assertNotIn('Instance.new(', SRC)
    def test_native_spec_proves_throughput_and_safety(self):
        self.assertIn('for _=1, 5000', SPEC)
        self.assertIn('total >= 30000', SPEC)
        self.assertIn('"FINISHED"', SPEC)
        self.assertIn('"CAP"', SPEC)
    def test_harness_includes_original_source_without_mock(self):
        spec = importlib.util.spec_from_file_location('builder', ROOT/'tools/build_native_harness.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.build()
        self.assertIn('function Pacing.step(', result)
        self.assertIn('NEUTRAL_PACING_NATIVE_PASS', result)
        self.assertNotIn('return Pacing\n', result)

if __name__=='__main__':
    unittest.main()
