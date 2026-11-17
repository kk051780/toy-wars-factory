import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("prove",Path(__file__).with_name("prove_hit_inheritance.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture():
    a={"F"+str(n):(b"unchanged","ModuleScript") for n in range(30)}
    a[m.TARGET]=(b'''hitToast.Name="ConfirmedHit042"
task.delay(.42,function()
player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")
task.delay(.17,function()''',"LocalScript")
    b=dict(a);b[m.EXTRA]=(b"spectate","LocalScript")
    return a,b
class HitInheritance(unittest.TestCase):
    def test_31_identical_plus_one_spectator(self):
        self.assertTrue(m.certify(*fixture())["current_hit042_present_in_optional"])
    def test_old_spectator_base_is_rejected(self):
        a,b=fixture();b[m.TARGET]=(b"previous GQ522 Wall","LocalScript")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
    def test_tampered_gameplay_source_rejected(self):
        a,b=fixture();b["F11"]=(b"tampered","ModuleScript")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
    def test_extra_second_or_missing_spectator_rejected(self):
        a,b=fixture();b["DuplicateHost"]=(b"bad","Script")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
        a,b=fixture();del b[m.EXTRA]
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
    def test_wrong_class_and_markers_rejected(self):
        a,b=fixture();b[m.TARGET]=(a[m.TARGET][0],"Script")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
        a,b=fixture();b[m.EXTRA]=(b"spectate","ModuleScript")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
        a,b=fixture();b[m.TARGET]=(b"no hit indicator","LocalScript")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
if __name__=="__main__":unittest.main()
