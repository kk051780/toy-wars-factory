"""FB-015 actual Horde visual repair contracts; official RC66 integration in Actions."""
from pathlib import Path
from tempfile import TemporaryDirectory
import ast
import unittest
import apply_fb015_musou_art as art

class MusouArtContracts(unittest.TestCase):
    def test_python_adapter_is_valid_and_versioned(self):
        script=Path(art.__file__).read_text("utf8")
        ast.parse(script)
        self.assertEqual(art.ID,"FB015_ART_MINION_SILHOUETTE_V1")
        self.assertEqual(art.HORDE,"server/MusouHorde.luau")
        self.assertEqual(len(art.ORIGINAL_HORDE_BLOB),40)

    def test_four_distinct_silhouettes_and_animation(self):
        s=art.ART_MAKE
        for marker in ("SIEGE_CHAMPION","SHIELD_WARDEN",
                       "TWINBLADE_SCOUT","HORNED_LANCER",
                       "TOWER_SHIELD","SCOUT_HOOD","LANCE_TIP",
                       "BOSS_AXE_EDGE","HELM_CROWN","ARMOR_BOOT_"):
            self.assertIn(marker,s)
        self.assertIn('model:SetAttribute("P0D_ArtStyle",artStyle)',s)
        self.assertIn('part.CanCollide=false',s)
        self.assertIn('part.CanQuery=false',s)

    def test_hit_vfx_are_emitted_only_at_real_server_hits(self):
        s=art.ART_MAKE
        self.assertIn("fx.Rate=0",s)
        self.assertIn("fx.Lifetime=NumberRange.new(.15,.32)",s)
        for forbidden in ("FireServer(","OnServerEvent:Connect(",
                          "DataStoreService","GetDataStore(","UpdateAsync(",
                          "TakeDamage(","MarketplaceService"):
            self.assertNotIn(forbidden,s)

    def test_off_is_byte_exact_and_no_new_build_folder(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/"nonexistent"
            self.assertFalse(art.apply(path,False))
            self.assertFalse(path.exists())

    def test_incomplete_source_fails_closed_without_file_write(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)
            with self.assertRaises(AssertionError):
                art.apply(path,True)
            self.assertEqual(list(path.iterdir()),[])

    def test_horde_drift_rejected_not_best_effort(self):
        with self.assertRaises(AssertionError):
            art.patch_horde('--!strict\nlocal Horde = {}')
        with self.assertRaises(AssertionError):
            art.sub("test", "missing", "new")

if __name__=="__main__":
    unittest.main()
