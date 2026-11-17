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
    def test_hit_audio_coexists_with_one_original_hud_listener(self):
        a,b=fixture()
        original=a[m.TARGET][0]
        audio=(b'\n-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117\n'
               b'local GROUP="EGGRUMBLE_GQ_ConfirmedHitAudio"\n'
               b'local onHit=player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(confirmedHit)\n'
               b'-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117\n')
        current=original+audio
        a[m.TARGET]=(current,"LocalScript");b[m.TARGET]=(current,"LocalScript")
        self.assertTrue(m.certify(a,b)["current_hit042_present_in_optional"])
        # An extra generic ImpactSequence listener outside the authored audio is RED.
        extra=current+b'\n'+m.IMPACT_LISTENER.encode()
        a[m.TARGET]=(extra,"LocalScript");b[m.TARGET]=(extra,"LocalScript")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
        # If original audio loses its unique callback or end fence, reject.
        bad=current.replace(m.AUDIO_LISTENER.encode(),b"")
        a[m.TARGET]=(bad,"LocalScript");b[m.TARGET]=(bad,"LocalScript")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
        noend=current.replace(m.AUDIO_END.encode(),b"")
        a[m.TARGET]=(noend,"LocalScript");b[m.TARGET]=(noend,"LocalScript")
        with self.assertRaisesRegex(ValueError,"RED_"):m.certify(a,b)
if __name__=="__main__":unittest.main()
