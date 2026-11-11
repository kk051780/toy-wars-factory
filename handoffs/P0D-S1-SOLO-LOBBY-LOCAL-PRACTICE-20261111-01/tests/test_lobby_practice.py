"""Python contract oracle and static checks; NOT execution of Roblox native Luau."""
from __future__ import annotations
import json, math, re, unittest, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def finite(n):
    return type(n) in (float,int) and math.isfinite(n)

class Oracle:
    def __init__(self):
        self.serial=-1;self.eligible=False;self.hits=0;self.last=-math.inf

    def consume(self, p):
        if not isinstance(p,dict) or p.get('kind')!='SNAPSHOT': return False
        s=p.get('serial')
        if not finite(s) or s<0 or s>1e9 or s%1: self.eligible=False;return False
        if s<self.serial:return False
        if p.get('phase') not in ('LOBBY','COUNTDOWN','ACTIVE','RESULTS'):
            self.eligible=False;return False
        for side in ('redPlayers','bluePlayers'):
            n=p.get(side)
            if not finite(n) or n<0 or n>100 or n%1:
                self.eligible=False;return False
        team=p.get('team')
        if team not in ('RED','BLUE'):self.eligible=False;return False
        own=p['redPlayers'] if team=='RED' else p['bluePlayers']
        enable=p['phase']=='LOBBY' and p['redPlayers']+p['bluePlayers']==1 and own==1
        if s!=self.serial or (enable and not self.eligible):self.hits=0;self.last=-math.inf
        self.serial=s;self.eligible=enable
        return True

    def hit(self,t,dist,dot):
        if not self.eligible or not all(map(finite,(t,dist,dot))):return False
        if not 0<=dist<=12 or not .12<=dot<=1.0001:return False
        if self.hits>=99 or t<self.last or t-self.last<.45:return False
        self.last=t;self.hits+=1;return True

def pkt(serial=0,phase='LOBBY',team='RED',redPlayers=1,bluePlayers=0,**extra):
    p=dict(kind='SNAPSHOT',serial=serial,phase=phase,team=team,redPlayers=redPlayers,bluePlayers=bluePlayers)
    p.update(extra);return p

class ModelContract(unittest.TestCase):
    def setUp(self): self.o=Oracle()
    def ready(self):self.assertTrue(self.o.consume(pkt()));self.assertTrue(self.o.eligible)
    def test_initial_closed(self):self.assertFalse(self.o.eligible)
    def test_one_red(self):self.ready()
    def test_one_blue(self):self.assertTrue(self.o.consume(pkt(team='BLUE',redPlayers=0,bluePlayers=1)));self.assertTrue(self.o.eligible)
    def test_two_opposing_closes(self):self.ready();self.o.consume(pkt(phase='COUNTDOWN',bluePlayers=1));self.assertFalse(self.o.eligible)
    def test_same_phase_second_join(self):self.ready();self.o.consume(pkt(bluePlayers=1));self.assertFalse(self.o.eligible)
    def test_active_closes(self):self.ready();self.o.consume(pkt(phase='ACTIVE'));self.assertFalse(self.o.eligible)
    def test_results_closes(self):self.ready();self.o.consume(pkt(phase='RESULTS'));self.assertFalse(self.o.eligible)
    def test_two_on_one_team_closed(self):self.assertTrue(self.o.consume(pkt(redPlayers=2)));self.assertFalse(self.o.eligible)
    def test_empty_lobby_closed(self):self.assertTrue(self.o.consume(pkt(redPlayers=0)));self.assertFalse(self.o.eligible)
    def test_own_mismatch_closed(self):self.assertTrue(self.o.consume(pkt(team='BLUE')));self.assertFalse(self.o.eligible)
    def test_wrong_remote_kind_ignored(self):self.ready();self.assertFalse(self.o.consume(pkt(kind='ALARM')));self.assertTrue(self.o.eligible)
    def test_non_table_ignored(self):self.ready();self.assertFalse(self.o.consume(None));self.assertTrue(self.o.eligible)
    def test_invalid_phase_disables(self):self.ready();self.assertFalse(self.o.consume(pkt(phase='OTHER')));self.assertFalse(self.o.eligible)
    def test_invalid_serial_disables(self):self.ready();self.assertFalse(self.o.consume(pkt(serial=float('nan'))));self.assertFalse(self.o.eligible)
    def test_bad_serial_types(self):
        for x in (-1,1.2,float('inf'),float('-inf'),'3',None,1000000001):
            with self.subTest(x=x):
                self.o=Oracle();self.assertFalse(self.o.consume(pkt(serial=x)));self.assertFalse(self.o.eligible)
    def test_stale_serial_is_ignored(self):
        self.o.consume(pkt(serial=5));self.o.consume(pkt(serial=6,phase='ACTIVE'));self.assertFalse(self.o.eligible)
        self.assertFalse(self.o.consume(pkt(serial=5)));self.assertFalse(self.o.eligible)
    def test_new_serial_clears_hits(self):
        self.ready();self.o.hit(1,8,.9);self.o.consume(pkt(serial=1));self.assertEqual(self.o.hits,0)
    def test_reenter_lobby_clears_hits(self):
        self.ready();self.o.hit(1,8,.9);self.o.consume(pkt(bluePlayers=1));self.o.consume(pkt());self.assertEqual(self.o.hits,0)
    def test_invalid_team_disables(self):self.ready();self.assertFalse(self.o.consume(pkt(team='NONE')));self.assertFalse(self.o.eligible)
    def test_bad_player_counts(self):
        for bad in (-1,1.5,float('nan'),float('inf'),'1',None,101):
            with self.subTest(bad=bad):
                self.o=Oracle();self.assertFalse(self.o.consume(pkt(redPlayers=bad)))
    def test_valid_hit(self):self.ready();self.assertTrue(self.o.hit(1,8,.9));self.assertEqual(self.o.hits,1)
    def test_hit_not_ready(self):self.assertFalse(self.o.hit(1,8,.9))
    def test_cooldown(self):self.ready();self.assertTrue(self.o.hit(1,8,.9));self.assertFalse(self.o.hit(1.44,8,.9));self.assertTrue(self.o.hit(1.46,8,.9))
    def test_negative_time(self):self.ready();self.assertTrue(self.o.hit(5,8,1));self.assertFalse(self.o.hit(4,8,1))
    def test_near_and_far(self):
        self.ready();self.assertTrue(self.o.hit(1,12,.12));self.assertFalse(self.o.hit(2,12.0001,.12));self.assertFalse(self.o.hit(3,-.1,.12))
    def test_facing(self):self.ready();self.assertFalse(self.o.hit(1,8,.119));self.assertTrue(self.o.hit(2,8,.12))
    def test_invalid_hit_numbers(self):
        self.ready()
        for bad in (float('nan'),float('inf'),-float('inf'),'2',None):
            with self.subTest(bad=bad):
                self.assertFalse(self.o.hit(bad,8,1));self.assertFalse(self.o.hit(1,bad,1));self.assertFalse(self.o.hit(1,8,bad))
    def test_hit_counter_max_99(self):
        self.ready()
        for i in range(99):self.assertTrue(self.o.hit(i,8,1))
        self.assertEqual(self.o.hits,99);self.assertFalse(self.o.hit(100,8,1))
    def test_reset_after_countdown_reopens(self):
        self.ready();self.o.hit(1,8,1);self.o.consume(pkt(phase='COUNTDOWN',bluePlayers=1));self.o.consume(pkt());self.assertTrue(self.o.eligible);self.assertEqual(self.o.hits,0)

class NativeSourceStaticContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=(ROOT/'src/LobbyPracticeModel.luau').read_text()
        cls.client=(ROOT/'src/LobbySoloPractice.client.luau').read_text()
    def test_model_available_and_pure(self):
        self.assertIn('function Practice.consume',self.model)
        self.assertIn('function Practice.hit',self.model)
        self.assertIn('return Practice',self.model)
        self.assertNotIn('game:GetService',self.model)
    def test_correct_server_snapshot_source(self):
        self.assertIn('TrapRaidersS1Remote',self.client)
        self.assertIn('OnClientEvent:Connect',self.client)
    def test_no_client_server_writes(self):
        for bad in (':FireServer(',':FireClient(','OnServerEvent','Instance.new("RemoteEvent")','DataStoreService','MarketplaceService','UpdateAsync','SetAsync','TakeDamage','LoadCharacter','leaderstats'):
            with self.subTest(bad=bad): self.assertNotIn(bad,self.client)
    def test_no_rpc_in_model(self):
        for bad in (':FireServer(',':FireClient(','Instance.new(', 'OnServerEvent'):
            with self.subTest(bad=bad): self.assertNotIn(bad,self.model)
    def test_no_collision_or_touch_query(self):
        for expected in ('p.CanCollide = false','p.CanTouch = false','p.CanQuery = false','p.Anchored = true'):
            with self.subTest(expected=expected):self.assertIn(expected,self.client)
    def test_phase_gate_and_exactly_one(self):
        self.assertIn('packet.phase == "LOBBY" and online == 1 and own == 1',self.model)
    def test_local_counter_cap(self):
        self.assertIn('MAX_HITS = 99',self.model)
        self.assertIn('COOLDOWN_SECONDS = 0.45',self.model)
    def test_cleanup_on_lifecycle(self):
        for term in ('CharacterAdded:Connect','CharacterRemoving:Connect','AncestryChanged:Connect','remote.OnClientEvent:Connect','dummy:Destroy()'):
            with self.subTest(term=term):self.assertIn(term,self.client)
    def test_cleanup_on_phase(self):self.assertIn('if retired or not state.eligible then hide(); return end',self.client)
    def test_no_loop_or_camera_subscription(self):self.assertNotIn('RenderStepped',self.client);self.assertNotIn('while true',self.client)
    def test_integration_document(self):
        t=(ROOT/'docs/INTEGRATION.md').read_text()
        self.assertIn('StarterPlayerScripts',t);self.assertIn('LobbyPracticeModel',t)
        self.assertIn('NOT_TESTED',t);self.assertIn('rollback',t.lower()) if 'rollback' in t.lower() else self.assertIn('Remove both',t)
    def test_source_end_newline(self):
        for f in ROOT.rglob('*'):
            if f.is_file() and f.name!='BUILD_MANIFEST.json' and '__pycache__' not in f.parts:
                self.assertTrue(f.read_bytes().endswith(b'\n'),str(f))

class ManifestStaticContract(unittest.TestCase):
    def test_manifest_strict_schema(self):
        manifest=ROOT/'BUILD_MANIFEST.json'
        self.assertTrue(manifest.exists())
        data=json.loads(manifest.read_text())
        self.assertEqual(set(data),{'format','game_id','work_id','packet_id','public_source_allowed','files'})
        self.assertEqual(data['format'],'P0D_PUBLIC_SOURCE_V1')
        self.assertTrue(data['public_source_allowed'])
    def test_manifest_bytes_hash(self):
        doc=json.loads((ROOT/'BUILD_MANIFEST.json').read_text())
        paths=set()
        for e in doc['files']:
            self.assertEqual(set(e),{'path','sha256','size'})
            self.assertNotIn('..',e['path']);self.assertNotIn('\\',e['path'])
            f=ROOT/e['path'];self.assertTrue(f.is_file())
            b=f.read_bytes();self.assertEqual(len(b),e['size'])
            self.assertEqual(hashlib.sha256(b).hexdigest(),e['sha256'])
            self.assertNotIn(e['path'],paths);paths.add(e['path'])
        allfiles={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(paths,allfiles-{'BUILD_MANIFEST.json'})

if __name__=='__main__': unittest.main()
