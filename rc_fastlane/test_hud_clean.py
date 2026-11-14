import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('hud',Path(__file__).with_name('apply_hud_clean.py'))
hud=importlib.util.module_from_spec(spec);spec.loader.exec_module(hud)

class HUDContract(unittest.TestCase):
    def make_dist(self,root):
        src=root/'src'; (src/'server').mkdir(parents=True); (src/'client').mkdir(parents=True)
        files={'server/Game.server.luau':b'-- original Game\n',
               'client/HUD.client.luau':b'-- original HUD\n'}
        for i in range(64): files[f'client/additional{i}.luau']=f'-- {i}\n'.encode()
        for path,body in files.items():
            dest=src/path;dest.write_bytes(body)
        pins={p:hud.blob(v) for p,v in sorted(files.items())}
        (root/'SOURCE_LOCK.json').write_text(json.dumps({'total_scripts':66,'blobs':pins}))
        (root/'RC_FEATURE_LOCK.json').write_text(json.dumps({'total_sources':66,'source_gitblobs':pins,'feature_flags':{}}))
        (root/'default.project.json').write_text(json.dumps({'tree':{'StarterPlayer':{'StarterPlayerScripts':{'TrapRaidersHUD':{'$path':'src/client/HUD.client.luau'}}}}}))
        return files
    def hashes(self,root):
        return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    def test_off_is_byte_exact_and_on_preserves_author_66(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist=Path(tmp);old=self.make_dist(dist)
            original=self.hashes(dist)
            self.assertFalse(hud.apply(dist,False))
            self.assertEqual(original,self.hashes(dist))
            self.assertTrue(hud.apply(dist,True))
            new=hud.read_src(dist)
            self.assertEqual(len(new),67)
            self.assertTrue(all(new[path]==body for path,body in old.items()))
            self.assertEqual(hud.blob(new[hud.DEST]),hud.BLOB)
            self.assertEqual(json.loads((dist/'SOURCE_LOCK.json').read_text())['blobs'],{p:hud.blob(v) for p,v in sorted(new.items())})
            self.assertEqual(json.loads((dist/'default.project.json').read_text())['tree']['StarterPlayer']['StarterPlayerScripts']['BattleHUDGovernor']['$path'],'src/client/BattleHUDGovernor.client.luau')
    def test_no_server_authority_and_numeric_hp(self):
        code=hud.SOURCE.read_text()
        self.assertIn('BattleSelfHPNumerical',code)
        self.assertIn('math.ceil(math.max(0, hum.Health))',code)
        self.assertIn('bounded(castle.RED)',code)
        self.assertIn('bounded(castle.BLUE)',code)
        self.assertIn('compactScore',code)
        self.assertIn('instructionLabel.Visible = false',code)
        self.assertNotIn('FireServer(',code)
        self.assertNotIn('Instance.new("RemoteEvent")',code)
        self.assertTrue(code.count('remote.OnClientEvent:Connect(')==1)
    def test_drift_blocks_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist=Path(tmp);self.make_dist(dist)
            src=dist/'src/server/Game.server.luau';src.write_bytes(b'bad')
            with self.assertRaises(AssertionError):hud.apply(dist,True)
            self.assertFalse((dist/'src'/hud.DEST).exists())
    def test_original_author_markers_kept(self):
        code=hud.SOURCE.read_text()
        for t in ('MaxDistance = 36', 'AlwaysOnTop = false',
                  'statusLabel.Visible = true','statusLabel.Visible = false',
                  'savedEnabled','Studio','TrapRaidersS1HUD'):
            self.assertIn(t,code)

if __name__=='__main__':unittest.main()
