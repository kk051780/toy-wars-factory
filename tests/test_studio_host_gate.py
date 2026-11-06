import hashlib, io, importlib.util, os, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio_host_gate',ROOT/'tools/studio_host_gate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# The actual PR147 producer is part of this stacked branch. Use its verified
# exact unmerged combined QA game source bytes; do NOT claim accepted main.
EXP=importlib.util.spec_from_file_location('export_accepted_rbxlx',ROOT/'tools/export_accepted_rbxlx.py')
export=importlib.util.module_from_spec(EXP); EXP.loader.exec_module(export)

class StudioHostedGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml, receipt = export.build_place(ROOT)
        assert receipt["rbxlx_sha256"] == m.EXACT_PLACE_SHA256
    def fixture(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
        d=Path(td.name); studio=d/'RobloxStudioBeta.exe';studio.write_bytes(b'safe fixture exe')
        place=d/m.PLACE_NAME;place.write_bytes(self.xml)
        script=d/'twf_local_place_probe.luau';script.write_text((ROOT/'tools/twf_local_place_probe.luau').read_text())
        return d,studio,place,script
    def test_real_connected_xml_is_exact(self):self.assertEqual(m.validate_file(self.xml)['file_sha256'],m.EXACT_PLACE_SHA256)
    def test_changed_payload_rejected(self):
        with self.assertRaises(m.StudioProbeBlocked):m.validate_file(self.xml+b'x')
    def test_empty_payload_rejected(self):
        with self.assertRaises(m.StudioProbeBlocked):m.validate_file(b'')
    def test_executable_arguments_strict_and_noshell(self):
        d,s,p,sc=self.fixture();args=m.build_args(s,p,sc,d/'output.log')
        self.assertEqual(args[1:3],['--task','RunScript']);self.assertIn('--localPlaceFile',args)
        self.assertIn('--quitAfterExecution',args)
    def test_fake_studio_executable_rejected(self):
        d,s,p,sc=self.fixture();n=d/'Python.exe';n.write_bytes(b'bad')
        with self.assertRaises(m.StudioProbeBlocked):m.build_args(n,p,sc,d/'output.log')
    def test_xml_wrong_name_rejected(self):
        d,s,p,sc=self.fixture();n=d/'other.rbxlx';n.write_bytes(self.xml)
        with self.assertRaises(m.StudioProbeBlocked):m.build_args(s,n,sc,d/'output.log')
    def test_source_probe_wrong_name_rejected(self):
        d,s,p,sc=self.fixture();n=d/'evil.luau';n.write_text('return nil')
        with self.assertRaises(m.StudioProbeBlocked):m.build_args(s,p,n,d/'output.log')
    def test_missing_stdout_marker_rejected(self):
        with self.assertRaises(m.StudioProbeBlocked):m.parse_studio_output('', '', '', exit_code=0)
    def test_stdout_only_not_proof(self):
        with self.assertRaises(m.StudioProbeBlocked):m.parse_studio_output(m.PASS_MARKER,'','',exit_code=0)
    def test_false_exit_failure(self):
        with self.assertRaises(m.StudioProbeBlocked):m.parse_studio_output('',m.PASS_MARKER,'',exit_code=1)
    def test_stderr_error_rejected(self):
        with self.assertRaises(m.StudioProbeBlocked):m.parse_studio_output('',m.PASS_MARKER,'failed to load place',exit_code=0)
    def test_two_sentinels_rejected(self):
        with self.assertRaises(m.StudioProbeBlocked):m.parse_studio_output('',m.PASS_MARKER+'\n'+m.PASS_MARKER,'',exit_code=0)
    def test_positive_fixture_is_not_engine_proof(self):
        proof=m.parse_studio_output('',m.PASS_MARKER,'',exit_code=0)
        self.assertEqual(proof['status'],'STUDIO_EDIT_MODEL_STRUCTURE_VERIFIED_ONLY')
        self.assertFalse(proof['play_mode_verified']);self.assertFalse(proof['mobile_verified'])
    def test_non_windows_must_block(self):
        d,s,p,sc=self.fixture()
        with self.assertRaises(m.StudioProbeBlocked):m.run_once(studio=s,place=p,script=sc,system='Linux')
    def test_trusted_windows_fixture_does_not_call_real_studio(self):
        d,s,p,sc=self.fixture()
        def runner(cmd,**kw):
            self.assertEqual(kw['shell'],False);self.assertLessEqual(kw['timeout'],180)
            Path(cmd[cmd.index('--outputFile')+1]).write_text(m.PASS_MARKER+'\n')
            return Mock(stdout='',stderr='',returncode=0)
        answer=m.run_once(studio=s,place=p,script=sc,system='Windows',runner=runner,signature_checker=lambda exe: True)
        self.assertEqual(answer['proof_origin'],'UNATTESTED_LOCAL_HOST')
        self.assertFalse(answer['engine_verified']);self.assertEqual(answer['network_calls_by_runner'],0)
    def test_timeout_does_not_retry(self):
        d,s,p,sc=self.fixture();count=0
        def bad(cmd,**kwargs):
            nonlocal count;count+=1;raise subprocess.TimeoutExpired('studio',100)
        with self.assertRaises(m.StudioProbeBlocked):m.run_once(studio=s,place=p,script=sc,system='Windows',runner=bad,signature_checker=lambda exe: True)
        self.assertEqual(count,1)
    def test_explicit_positive_timeout_bounds(self):
        d,s,p,sc=self.fixture()
        with self.assertRaises(m.StudioProbeBlocked):m.run_once(studio=s,place=p,script=sc,system='Windows',timeout=300,signature_checker=lambda exe: True)
    def test_cli_default_is_disabled(self):
        p=subprocess.run([sys.executable,str(ROOT/'tools/studio_host_gate.py')],capture_output=True,text=True)
        self.assertEqual(p.returncode,0);self.assertIn('DISABLED_PLAN_ONLY',p.stdout)
    def test_real_local_cli_on_linux_fails_closed(self):
        p=subprocess.run([sys.executable,str(ROOT/'tools/studio_host_gate.py'),'--run','--place','bad','--studio','bad','--script','bad'],capture_output=True,text=True)
        if os.name != 'nt':self.assertEqual(p.returncode,2)
    def test_source_contains_only_relevant_studio_services(self):
        src=(ROOT/'tools/twf_local_place_probe.luau').read_text()
        for forbidden in ('HttpService','SavePlaceAsync','DataStoreService','TeleportService','ExecuteMultiplayerTestAsync','LoadAsset'):
            self.assertNotIn(forbidden,src)
    def test_trusted_powershell_launcher_checks_code_signing(self):
        src=(ROOT/'tools/launch_trusted_studio_probe.ps1').read_text()
        for required in ('Get-AuthenticodeSignature','RobloxStudioBeta.exe','-LiteralPath','studio_host_gate.py','--run'):
            self.assertIn(required,src)
        for forbidden in ('Invoke-WebRequest','Start-Process','Set-ExecutionPolicy','x-api-key','publish-place'):
            self.assertNotIn(forbidden,src)
    def test_reject_tampered_luau_probe(self):
        d,s,p,sc=self.fixture();sc.write_text(sc.read_text()+'\nprint(42)')
        with self.assertRaises(m.StudioProbeBlocked):m.build_args(s,p,sc,d/'output.log')
    def test_reject_unsigned_studio_before_process(self):
        d,s,p,sc=self.fixture();calls=[]
        def r(*a,**kw):calls.append('invoked');raise AssertionError('forbidden')
        with self.assertRaises(m.StudioProbeBlocked):
            m.run_once(studio=s,place=p,script=sc,system='Windows',runner=r,signature_checker=lambda exe: False)
        self.assertEqual(calls,[])
    def test_reject_truthy_string_signature(self):
        d,s,p,sc=self.fixture()
        with self.assertRaises(m.StudioProbeBlocked):
            m.run_once(studio=s,place=p,script=sc,system='Windows',runner=lambda *_a,**_kw:None,
                       signature_checker=lambda exe:'true')
    def test_real_signature_check_fails_closed_without_signer(self):
        d,s,p,sc=self.fixture()
        result=Mock(stdout='untrusted',stderr='',returncode=1)
        with self.assertRaises(m.StudioProbeBlocked):
            m.verify_windows_studio_signature(s,runner=lambda *_a,**_kw:result,system='Windows')
    def test_signature_check_accepts_only_exact_sentinel(self):
        d,s,p,sc=self.fixture()
        result=Mock(stdout=m.SIGNATURE_SENTINEL+'\n',stderr='',returncode=0)
        self.assertTrue(m.verify_windows_studio_signature(s,runner=lambda *_a,**_kw:result,system='Windows'))
        result=Mock(stdout=m.SIGNATURE_SENTINEL+'\nsecond line',stderr='',returncode=0)
        with self.assertRaises(m.StudioProbeBlocked):
            m.verify_windows_studio_signature(s,runner=lambda *_a,**_kw:result,system='Windows')
    def test_real_artifact_id_is_fixed(self):self.assertEqual(m.ARTIFACT_ID,13478848965)
    def test_result_not_claiming_play_or_mobiles(self):
        d,s,p,sc=self.fixture()
        def runner(cmd,**kw):
            Path(cmd[cmd.index('--outputFile')+1]).write_text(m.PASS_MARKER+'\n');return Mock(stdout='',stderr='',returncode=0)
        got=m.run_once(studio=s,place=p,script=sc,system='Windows',runner=runner,signature_checker=lambda exe: True)
        self.assertFalse(got['client_verified']);self.assertFalse(got['two_client_verified']);self.assertIsNone(got['roblox_saved_version'])
if __name__=='__main__':unittest.main()
