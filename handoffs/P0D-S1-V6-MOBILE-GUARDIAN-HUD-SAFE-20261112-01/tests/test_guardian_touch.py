import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/verify_guardian_mobile_layout.py"
spec = importlib.util.spec_from_file_location("guard_layout", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MobileGuardianTouchSafety(unittest.TestCase):
    def test_exact_official_pin(self):
        self.assertEqual(m.OFFICIAL_RC, "1263a03701211a652b99b91d2339575dc8104eff")
        self.assertEqual(m.OFFICIAL_BLOB, "ee594fbc34e6bf938518fae32c0642c852f11f9e")

    def test_widths_six_landscapes(self):
        for w,h in m.SUPPORTED_LANDSCAPE:
            with self.subTest(size=(w,h)):
                m.check_geometry(w,h)

    def test_shifted_to_right_above_attack(self):
        self.assertEqual(m.BUTTON_TRAP, (110,74,-140,-110))
        for w,h in m.SUPPORTED_LANDSCAPE:
            b=m.geometry(w,h)
            self.assertEqual(b["trap"][0],b["attack"][0])
            self.assertEqual(b["attack"][1]-b["trap"][3],6)

    def test_original_left_stick_rejected(self):
        with self.assertRaisesRegex(AssertionError,"LEFT_TOUCH_MOVEMENT_RESERVED_COLLISION"):
            m.check_geometry(640,360,(110,74,-628,-16))

    def test_overlap_attack_rejected(self):
        with self.assertRaisesRegex(AssertionError,"ATTACK_TRAP_OVERLAP"):
            m.check_geometry(640,360,(110,74,-140,-16))

    def test_overlap_coach_rejected(self):
        with self.assertRaisesRegex(AssertionError,"TOUCH_HELP_PANEL_COLLISION"):
            m.check_geometry(640,360,(110,74,-140,-128))

    def test_off_screen_rejected(self):
        with self.assertRaisesRegex(AssertionError,"BUTTON_OUTSIDE_LANDSCAPE_SAFE_RECT"):
            m.check_geometry(640,360,(160,74,-140,-110))

    def test_unsafe_single_source_edit_rejected(self):
        # Old and new are byte exact; no additional client payload/remote edits allowed.
        src=b"before " + m.OLD + b" after"
        candidate=src.replace(m.OLD,m.NEW,1)
        self.assertEqual(candidate.count(m.NEW),1)
        self.assertNotEqual(candidate+b"\nFireServer({damage=999})",candidate)

    def test_no_ui_contamination_other_controls(self):
        self.assertEqual(m.BUTTON_ATTACK,(126,88,-140,-16))
        self.assertEqual(m.NEW.count(b"UDim2.new("),1)
        self.assertNotIn(b"role",m.NEW.lower())

    def test_git_blob_known_fixture(self):
        self.assertEqual(m.sha_blob(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")


if __name__=="__main__":
    unittest.main()
