"""Actual, immutable original Real43 source + #801 author policy regression."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("bridge44",HERE/"compose_real44.py")
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

ORIGINAL=Path("artifacts/original/portable43/EGGRUMBLE_SOURCE43.project.json")
POLICY=Path("artifacts/policy/EGGRUMBLE_CurseConversionPolicy.luau")

class Real44Test(unittest.TestCase):
    def setUp(self):
        self.assertTrue(ORIGINAL.exists(),"RED_NEED_VERIFIED_ORIGINAL_REAL43_PACKET")
        self.assertTrue(POLICY.exists(),"RED_NEED_IMMUTABLE_AUTHOR_801_POLICY")
    def test_actual_source_preserved_and_live_hooks(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"on"/"REAL44.project.json"
            r=bridge.compose(ORIGINAL,POLICY,out)
            _,old=bridge.flatten(ORIGINAL)
            _,new=bridge.flatten(out)
            self.assertEqual(len(old),43)
            self.assertEqual(len(new),44)
            self.assertEqual(set(new),set(old)|{bridge.CURSE})
            self.assertEqual(r["exact_existing_sources"],42)
            for key in old:
                if key!=bridge.SWARM:
                    self.assertEqual(old[key].read_bytes(),new[key].read_bytes(),key)
            self.assertEqual(new[bridge.CURSE].read_bytes(),POLICY.read_bytes())
            live=new[bridge.SWARM].read_text()
            self.assertEqual(live.count("function Swarm.start(session:any)"),1)
            self.assertEqual(live.count("NeutralFinisherPolicy.select("),1)
            self.assertEqual(live.count("CurseConversionPolicy.seal("),1)
            self.assertEqual(live.count("nearest:TakeDamage(6)"),1)
            self.assertEqual(live.count("h:TakeDamage(damage)"),1)
            self.assertIn('not charmed[m]',live)
            self.assertIn('applyCurseOnVerifiedHit(user,model,h,hitSerial,origin,role)',live)
            self.assertIn('charmOwnerPosition(m)',live)
            self.assertIn('expireCharms()',live)
            self.assertNotIn("RemoteEvent",live)
            self.assertNotIn("MarketplaceService",live)
    def test_duplicate_and_missing_receipts_fail_closed(self):
        _,files=bridge.flatten(ORIGINAL)
        source=files[bridge.SWARM].read_text()
        with self.assertRaisesRegex(ValueError,"RED_CHARM_ALREADY_INTEGRATED"):
            bridge.patch_swarm(source+'EGGRUMBLE_CurseConversionPolicy')
        with self.assertRaisesRegex(ValueError,"RED_ACTUAL_HIT_HOOK"):
            bridge.patch_swarm(source.replace(
              'local role=user and (user:GetAttribute("EGGRUMBLE_Role") or "WARRIOR") or "WARRIOR",
              "local role=nil"))
        with self.assertRaisesRegex(ValueError,"RED_NOT_IMMUTABLE"):
            with tempfile.TemporaryDirectory() as temp:
                modified=Path(temp)/"evil.luau"
                modified.write_text("return {}")
                bridge.compose(ORIGINAL,modified,Path(temp)/"out"/"test.project.json")

if __name__=="__main__":unittest.main()
