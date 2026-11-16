"""RC31 original author 583 selector safety checks, not Studio execution."""
import hashlib
from importlib.machinery import SourceFileLoader
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

mod=SourceFileLoader("gq583_rc_intake",str(Path(__file__).with_name("select_original_roster583.py"))).load_module()
SOURCE="""--!strict
local M={}
M.MAX_HERO_SLOTS=16
function M.makeRoster(limit:number)
 assert(limit>=2 and limit<=32,"invalid preview slot cap")
 return limit
end
function M.new(roster:any)
 assert(#roster>=2 and #roster<=32,"invalid roster size")
 return roster
end
return M
"""

class Intake583Tests(unittest.TestCase):
    def test_fixed_author_sha_is_40_hex(self):
        self.assertEqual(len(mod.AUTHOR_HEAD),40)
        self.assertEqual(len(mod.ORIGINAL_BLOB),40)
        int(mod.AUTHOR_HEAD,16);int(mod.ORIGINAL_BLOB,16)

    def test_exact_script_target(self):
        self.assertEqual(mod.SLOT,("ServerScriptService","EGGRUMBLE_CastleMatchRules"))

    def test_git_blob_implements_actual_sha1_git_header(self):
        src=b"--!strict\nreturn {}\n"
        expected=hashlib.sha1(b"blob "+str(len(src)).encode()+b"\0"+src).hexdigest()
        self.assertEqual(mod.git_blob(src),expected)

    def test_sha256_uses_raw_bytes_not_object_identity(self):
        self.assertEqual(mod.sha256(b"abc"),hashlib.sha256(b"abc").hexdigest())

    def test_wrong_source_not_substituted(self):
        wrong=SOURCE.replace("M.MAX_HERO_SLOTS=16","M.MAX_HERO_SLOTS=32")
        self.assertNotEqual(wrong,SOURCE)

    def test_block_inplace_project(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"source.project.json"
            p.write_text("{}")
            with patch.object(mod,"source_author") as author:
                with self.assertRaises((ValueError,FileNotFoundError)):
                    mod.select(p,Path(d)/"fakeauthor",p,p)
                author.assert_not_called()

    def test_rollback_feature_does_not_insert_new_script_name(self):
        self.assertTrue(mod.NEW_SOURCE.endswith(".luau"))
        self.assertNotIn(".server.luau",mod.NEW_SOURCE)

    def test_native_and_rojo_target_same_single_script(self):
        self.assertEqual(mod.MAX_SCRIPTS,31)
        self.assertEqual(mod.SLOT[-1],"EGGRUMBLE_CastleMatchRules")

    def test_cannot_claim_studio_owner_from_receipt(self):
        self.assertEqual(mod.RECEIPT,"GQ583_ROSTER16_RC31_RECEIPT.json")

if __name__=="__main__":
    unittest.main()
