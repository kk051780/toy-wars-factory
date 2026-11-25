#!/usr/bin/env python3
"""GQ522 author-reuse, precise old Host inverse and fail-closed tests."""
import hashlib
import unittest
from pathlib import Path
from select_inline import (exact_author,select_host,rollback,inline_source,
    REQUIRE,EQUIP,CLOSE,HOOK,STAMP,git_blob,BUILDER_BLOB,POLICY_BLOB)

SRC = Path("_gq522_builder_original/quality_gameplay/v3_builder_construction_20261116")
BUILDER = SRC/"EGGRUMBLE_BuilderConstruction.luau"
POLICY = SRC/"EGGRUMBLE_BuilderPlacementPolicy.luau"

def fixture():
    return (REQUIRE+"\n"
        "local function start(session,p,role)\n"
        " session.isCurrentHuman=function() return true end\n"
        " "+EQUIP+"\nend\n"
        "local function respawn(session,p,role)\n "+EQUIP+"\nend\n"
        "local function close(session)\n  "+CLOSE+"\nend\n")

class OriginalBuilderReuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder,cls.policy=exact_author(BUILDER,POLICY)

    def test_immutable_author_blobs(self):
        self.assertEqual(git_blob(BUILDER.read_bytes()),BUILDER_BLOB)
        self.assertEqual(git_blob(POLICY.read_bytes()),POLICY_BLOB)

    def test_inline_real_author_and_exact_inverse(self):
        source=fixture()
        out,block=select_host(source,self.builder,self.policy)
        self.assertEqual(rollback(out,block),source)
        self.assertEqual(out.count("BuilderConstruction.equip(session,p,true,false)"),2)
        self.assertEqual(out.count("BuilderConstruction.clear(session)"),1)
        self.assertIn("function Build.place(session:any,p:Player,kind:string,serverEnabled:boolean?)",out)
        self.assertIn("tool.Activated:Connect(function()",out)
        self.assertIn("if typeof(session.isCurrentHuman)~=\"function\" then return nil,nil end",out)
        self.assertIn("BuilderConstruction=Build",out)
        self.assertNotIn('require(script.Parent:WaitForChild("EGGRUMBLE_BuilderPlacementPolicy"))',out)

    def test_bridge_is_not_visible_and_original_skills_remain(self):
        out,_=select_host(fixture(),self.builder,self.policy)
        self.assertIn("BuilderConstruction.equip(session,p,true,false)",out)
        self.assertNotIn("BuilderConstruction.equip(session,p,true,true)",out)
        self.assertEqual(out.count(EQUIP),2)
        self.assertIn("Build.DEFAULT_ENABLED=false",out)

    def test_double_source_selection_is_red(self):
        out,_=select_host(fixture(),self.builder,self.policy)
        with self.assertRaisesRegex(ValueError,"ALREADY_SELECTED"):
            select_host(out,self.builder,self.policy)

    def test_no_live_membership_rejected(self):
        with self.assertRaisesRegex(ValueError,"CURRENT_HUMAN"):
            select_host(fixture().replace("session.isCurrentHuman=function","session.old=function"),
                        self.builder,self.policy)

    def test_missing_equip_is_red(self):
        with self.assertRaisesRegex(ValueError,"HOST_ORIGIN_DRIFT"):
            select_host(fixture().replace(EQUIP,"--equip",1),self.builder,self.policy)

    def test_missing_cleanup_is_red(self):
        with self.assertRaisesRegex(ValueError,"HOST_ORIGIN_DRIFT"):
            select_host(fixture().replace(CLOSE,"--close",1),self.builder,self.policy)

    def test_immutable_author_mutation_is_red(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp:
            b=Path(temp)/"builder.luau"
            b.write_bytes(BUILDER.read_bytes().replace(b"Build.DEFAULT_ENABLED=false",b"Build.DEFAULT_ENABLED=true"))
            with self.assertRaisesRegex(ValueError,"AUTHOR_BLOB_DRIFT"):
                exact_author(b,POLICY)

    def test_rollback_rejects_partial_corruption(self):
        out,block=select_host(fixture(),self.builder,self.policy)
        with self.assertRaisesRegex(ValueError,"INVERSE_SHAPE_DRIFT"):
            rollback(out.replace("BuilderConstruction.clear(session)","--removed",1),block)

    def test_policy_original_real_not_rewritten(self):
        out,block=select_host(fixture(),self.builder,self.policy)
        self.assertIn("Policy.MAX_PER_HERO=2",out)
        self.assertIn("Policy.MAX_PER_SESSION=12",out)
        self.assertIn("Policy.LIFETIME=9",out)
        self.assertIn("local function getActor(session:any,p:Player)",out)

if __name__=="__main__":
    unittest.main()
