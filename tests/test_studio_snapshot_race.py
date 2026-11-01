"""PR149: launch only exact immutable staged XML/Luau snapshots.
Mocks never execute Windows Studio or assert an actual engine result.
"""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio_host_gate',ROOT/'tools/studio_host_gate.py')
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
buildspec=importlib.util.spec_from_file_location('export_accepted_rbxlx',ROOT/'tools/export_accepted_rbxlx.py')
producer=importlib.util.module_from_spec(buildspec); buildspec.loader.exec_module(producer)


class PrivateStudioLaunchSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.place_bytes, _=producer.build_place(ROOT)
        assert len(cls.place_bytes)==gate.EXACT_PLACE_BYTES
        assert gate.sha256_bytes(cls.place_bytes)==gate.EXACT_PLACE_SHA256

    def fixture(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        root=Path(t.name)
        studio=root/'RobloxStudioBeta.exe';studio.write_bytes(b'SYNTHETIC_EXE_NEVER_EXECUTED')
        place=root/gate.PLACE_NAME;place.write_bytes(self.place_bytes)
        script=root/'twf_local_place_probe.luau'
        script.write_bytes((ROOT/'tools/twf_local_place_probe.luau').read_bytes())
        return root,studio,place,script

    def runner(self,check):
        def run(cmd,**kwargs):
            self.assertIs(kwargs['shell'],False)
            check(cmd)
            Path(cmd[cmd.index('--outputFile')+1]).write_text(gate.PASS_MARKER+'\n')
            return mock.Mock(stdout='',stderr='',returncode=0)
        return run

    def test_original_xml_mutated_during_signature_staged_snapshot_unchanged(self):
        _,exe,place,script=self.fixture()
        def signature(_):place.write_bytes(b'ALTERED_AFTER_FIRST_HASH');return True
        def check(cmd):
            staged=Path(cmd[cmd.index('--localPlaceFile')+1])
            self.assertNotEqual(staged.resolve(),place.resolve())
            self.assertEqual(staged.read_bytes(),self.place_bytes)
        proof=gate.run_once(studio=exe,place=place,script=script,system='Windows',
                            signature_checker=signature,runner=self.runner(check))
        self.assertFalse(proof['engine_verified'])

    def test_original_luau_mutated_during_signature_staged_snapshot_unchanged(self):
        _,exe,place,script=self.fixture()
        approved=script.read_bytes()
        def signature(_):script.write_bytes(b'print("unreviewed")');return True
        def check(cmd):
            staged=Path(cmd[cmd.index('--runScriptFile')+1])
            self.assertNotEqual(staged.resolve(),script.resolve())
            self.assertEqual(staged.read_bytes(),approved)
        gate.run_once(studio=exe,place=place,script=script,system='Windows',
                      signature_checker=signature,runner=self.runner(check))

    def test_both_snapshot_paths_private_same_dir_and_cleaned_up(self):
        _,exe,place,script=self.fixture()
        observed=[]
        def check(cmd):
            a=Path(cmd[cmd.index('--localPlaceFile')+1])
            b=Path(cmd[cmd.index('--runScriptFile')+1])
            self.assertEqual(a.parent,b.parent)
            self.assertTrue(a.parent.name.startswith('twf-studio-proof-'))
            self.assertNotEqual(a.resolve(),place.resolve())
            self.assertNotEqual(b.resolve(),script.resolve())
            observed.extend([a,b])
        gate.run_once(studio=exe,place=place,script=script,system='Windows',
                      signature_checker=lambda _:True,runner=self.runner(check))
        self.assertEqual(len(observed),2)
        self.assertTrue(all(not p.exists() for p in observed))

    def test_tampered_staged_place_after_signature_must_not_execute(self):
        root,exe,place,script=self.fixture()
        real_tmp=tempfile.TemporaryDirectory
        calls=[]
        def signature(_):
            copies=list(root.glob('twf-studio-proof-*/'+gate.PLACE_NAME))
            self.assertEqual(len(copies),1)
            copies[0].write_bytes(b'STAGED_PLACE_CORRUPTED')
            return True
        with mock.patch.object(gate.tempfile,'TemporaryDirectory',
                               side_effect=lambda **kw:real_tmp(dir=root,**kw)):
            with self.assertRaises(gate.StudioProbeBlocked):
                gate.run_once(studio=exe,place=place,script=script,system='Windows',
                              signature_checker=signature,runner=lambda *_a,**_k:calls.append('EXECUTED'))
        self.assertEqual(calls,[])

    def test_tampered_staged_luau_after_signature_must_not_execute(self):
        root,exe,place,script=self.fixture()
        real_tmp=tempfile.TemporaryDirectory
        calls=[]
        def signature(_):
            copies=list(root.glob('twf-studio-proof-*/twf_local_place_probe.luau'))
            self.assertEqual(len(copies),1)
            copies[0].write_bytes(b'STAGED_LUA_CORRUPTED')
            return True
        with mock.patch.object(gate.tempfile,'TemporaryDirectory',
                               side_effect=lambda **kw:real_tmp(dir=root,**kw)):
            with self.assertRaises(gate.StudioProbeBlocked):
                gate.run_once(studio=exe,place=place,script=script,system='Windows',
                              signature_checker=signature,runner=lambda *_a,**_k:calls.append('EXECUTED'))
        self.assertEqual(calls,[])

    def test_invalid_original_source_refused_before_signer_or_studio(self):
        _,exe,place,script=self.fixture()
        place.write_bytes(b'INVALID_XML')
        events=[]
        with self.assertRaises(gate.StudioProbeBlocked):
            gate.run_once(studio=exe,place=place,script=script,system='Windows',
                          signature_checker=lambda _:(events.append('SIGNED') or True),
                          runner=lambda *_a,**_k:events.append('RUN'))
        self.assertEqual(events,[])

    def test_positive_mock_never_attests_real_engine_or_publish(self):
        _,exe,place,script=self.fixture()
        proof=gate.run_once(studio=exe,place=place,script=script,system='Windows',
                            signature_checker=lambda _:True,runner=self.runner(lambda _:None))
        self.assertFalse(proof['engine_verified'])
        self.assertFalse(proof['play_mode_verified'])
        self.assertFalse(proof['public_publish_authorized'])
        self.assertEqual(proof['network_calls_by_runner'],0)


if __name__=='__main__':unittest.main()
