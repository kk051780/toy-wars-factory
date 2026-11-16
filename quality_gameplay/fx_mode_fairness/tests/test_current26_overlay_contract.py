import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
BASE=Path(__file__).resolve().parents[1]
SCRIPT=BASE/"compose_mode_fair_on_current26.py"
class SourceOnly(unittest.TestCase):
    def test_uses_existing_original_composer_output_not_reimplementation(self):
        s=SCRIPT.read_text()
        self.assertIn("base_project",s)
        self.assertIn("base_receipt",s)
        self.assertIn("kept_25_of_26_source_bytes_exact",s)
        self.assertIn('len(before)==26',s)
        self.assertIn('len(after)==27',s)
        self.assertNotIn("RobloxPublish",s)
        self.assertNotIn("git push",s)
    def test_only_skillfx_and_one_helper_replace(self):
        s=SCRIPT.read_text()
        self.assertIn('ss["EGGRUMBLE_SkillFX"]=',s)
        self.assertIn('ss["EGGRUMBLE_FXModeFairQuota"]=',s)
        self.assertIn('if name!="EGGRUMBLE_SkillFX":assert',s)
        self.assertIn('EGGRUMBLE_ArtDistanceLOD',s)
        self.assertIn('EGGRUMBLE_ScoreBalance',s)
if __name__=="__main__":unittest.main()
