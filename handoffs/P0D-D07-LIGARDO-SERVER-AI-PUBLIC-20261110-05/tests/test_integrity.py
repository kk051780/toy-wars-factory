import copy
import io
import json
import stat
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from verify_packet import verify,sha256
ROOT=Path(__file__).resolve().parents[1]

def sample(files=None, manifests=None):
    files={'src/valid.lua':b'-- valid', 'docs/qa.md':b'pass=offline'} if files is None else files
    entries=[{'path':p,'size':len(data),'sha256':sha256(data)} for p,data in files.items()]
    m={'schema':'P0D_HANDOFF_SHA256_V1','packet_id':'P0D-D07-LIGARDO-SERVER-AI-20261110-04','entries':entries}
    if manifests:m.update(manifests)
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w') as z:
        for name,blob in files.items():z.writestr(name,blob)
        z.writestr('BUILD_MANIFEST.json',json.dumps(m))
    return output.getvalue()

class IntegrityTest(unittest.TestCase):
    def test_good(self):self.assertEqual(verify(sample())['entry_count'],2)
    def test_missing_manifest(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('src/valid.lua',b'ok')
        with self.assertRaises(ValueError):verify(out.getvalue())
    def test_manifest_wrong_packet(self):
        with self.assertRaises(ValueError):verify(sample(manifests={'packet_id':'oops'}))
    def test_manifest_wrong_schema(self):
        with self.assertRaises(ValueError):verify(sample(manifests={'schema':'bad'}))
    def test_tampered_content_hash(self):
        with self.assertRaises(ValueError):verify(sample(manifests={'entries':[{'path':'src/valid.lua','size':2,'sha256':'x'*64}]}))
    def test_absolute_path(self):
        with self.assertRaises(ValueError):verify(sample(files={'/tmp/x':b'a','doc':b'b'}))
    def test_traversal(self):
        with self.assertRaises(ValueError):verify(sample(files={'../evil':b'a','doc':b'b'}))
    def test_backslash(self):
        with self.assertRaises(ValueError):verify(sample(files={'a\\b':b'a','doc':b'b'}))
    def test_dot_segment(self):
        with self.assertRaises(ValueError):verify(sample(files={'a/./b':b'a','doc':b'b'}))
    def test_drive(self):
        with self.assertRaises(ValueError):verify(sample(files={'C:/file':b'a','doc':b'b'}))
    def test_casefold_collision(self):
        with self.assertRaises(ValueError):verify(sample(files={'Foo':b'a','foo':b'b'}))
    def test_oversized_uncompressed(self):
        with self.assertRaises(ValueError):verify(sample(files={'big':b'a'*2_000_001,'ok':b'a'}))
    def test_extra_file_missing_entry(self):
        with self.assertRaises(ValueError):verify(sample(manifests={'entries':[]}))
    def test_truncated_zip(self):
        with self.assertRaises((ValueError,zipfile.BadZipFile)):verify(sample()[:30])
    def test_corrupt_zip(self):
        with self.assertRaises((ValueError,zipfile.BadZipFile)):verify(b'not a zip')
    def test_duplicate(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('dup',b'a');z.writestr('dup',b'b');z.writestr('BUILD_MANIFEST.json',b'{}')
        with self.assertRaises(ValueError):verify(out.getvalue())

class StaticSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=(ROOT/'src/LigardoServerPolicy.luau').read_text()
        cls.adapter=(ROOT/'src/LigardoServerAdapter.luau').read_text()
    def test_server_authority_guard(self):self.assertIn('round.authorized~=true',self.policy)
    def test_no_remote(self):self.assertNotIn('OnServerEvent',self.policy+self.adapter)
    def test_no_humanoid_write(self):self.assertNotIn(':TakeDamage(',self.policy+self.adapter)
    def test_no_random_target_selection(self):self.assertNotIn('math.random(',self.policy+self.adapter)
    def test_no_extrapolated_damage_without_los(self):self.assertIn('serverLineOfSight',self.adapter)
    def test_no_event_chooser(self):self.assertNotIn('math.random(',self.policy)
    def test_no_network_calls(self):
        for forbidden in ('HttpService','DataStoreService','MarketplaceService','TeleportService','MessagingService'):
            self.assertNotIn(forbidden,self.policy+self.adapter)
    def test_disallow_stale(self):self.assertIn('seq<=s.seq',self.policy)
    def test_damage_intent_cap(self):self.assertIn('damageCap=7',self.policy)
    def test_telegraph(self):self.assertIn('CHARGE_SECONDS = 2',self.policy)
    def test_attacks_capped(self):self.assertIn('MAX_ATTACKS = 3',self.policy)
    def test_boss_leash(self):self.assertIn('LEASH = 36',self.policy)
    def test_boss_lifetime(self):self.assertIn('MAX_LIFE = 16',self.policy)
    def test_adapter_dedupe(self):self.assertIn('ledger.consumed[intent.attackNo]=true',self.adapter)
    def test_same_round_guard(self):self.assertIn('snapshot.roundId~=intent.roundId',self.adapter)
    def test_position_recheck(self):self.assertIn('d(snapshot.bossPos,intent.bossPos)>2',self.adapter)

if __name__=='__main__':unittest.main()
