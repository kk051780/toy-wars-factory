import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('world',Path(__file__).with_name('apply_world_upgrade.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
class WorldCandidateTest(unittest.TestCase):
 def make(self,dist):
  files={'server/Game.server.luau':b'--Game','server/MapBuilder.luau':b'--MapBuilder'}
  for i in range(64):files[f'server/extra{i}.luau']=f'--{i}'.encode()
  for path,body in files.items():
   p=dist/'src'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
  pins={p:w.blob(b) for p,b in sorted(files.items())}
  (dist/'SOURCE_LOCK.json').write_text(json.dumps({'total_scripts':66,'blobs':pins}))
  (dist/'RC_FEATURE_LOCK.json').write_text(json.dumps({'total_sources':66,'source_gitblobs':pins,'feature_flags':{}}))
  (dist/'default.project.json').write_text(json.dumps({'tree':{'ServerScriptService':{'TrapRaidersS1':{'$path':'src/server'}}}}))
  return files
 def hashfiles(self,dist):
  return {p.relative_to(dist).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.rglob('*') if p.is_file()}
 def test_off_then_on_original_66_unchanged(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);original=self.make(d);before=self.hashfiles(d)
   self.assertFalse(w.apply(d,False));self.assertEqual(before,self.hashfiles(d))
   self.assertTrue(w.apply(d,True));x=w.sources(d)
   self.assertEqual(len(x),67);self.assertEqual(x[w.DEST],w.SOURCE.read_bytes())
   self.assertTrue(all(x[k]==v for k,v in original.items()))
   self.assertEqual(json.loads((d/'SOURCE_LOCK.json').read_text())['blobs'],{p:w.blob(b) for p,b in sorted(x.items())})
 def test_scene_contract(self):
  code=w.SOURCE.read_text()
  for term in ('arena.Size=Vector3.new(520,4,254)','wall.Position=Vector3.new(0,7,sign*127)',
               'INVASION_ROUTE_', 'RIVER_BRIDGE_', 'name.."_3D_FORTRESS"',
               'gatehouse(castle,side,accent,name)', 'battlement(castle,'):
   self.assertIn(term,code)
  self.assertNotIn('FireServer(',code)
  self.assertNotIn('Instance.new("RemoteEvent")',code)
 def test_source_drift_fail_before_writes(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);self.make(d)
   (d/'src/server/Game.server.luau').write_text('--bad')
   with self.assertRaises(AssertionError):w.apply(d,True)
   self.assertFalse((d/'src'/w.DEST).exists())
if __name__=='__main__':unittest.main()
