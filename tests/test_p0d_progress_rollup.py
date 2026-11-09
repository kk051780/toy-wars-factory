import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import p0d_progress_rollup as m


def fixture():
    base=[f'D{i:02}' for i in range(1,18)]
    def pack(n, features, sha=None, path=None):
        return dict(packet_id='p'+str(n),commit=sha or str(n)*40,
                    feature_ids=features,envelope_path=path or 'handoffs/secret.json',
                    readme_path='handoffs/README.md',
                    windows_restore='NOT_TESTED',studio_qa='NOT_TESTED')
    return dict(schema='P0D_READONLY_INTAKE_V1',game_id='TRAP_RAIDERS',work_id='p0d-siege-v19',
                pc_status='PARTIAL_NOT_READY',baseline_feature_ids=base,
                pc_partial_feature_ids=base[:5],sealed_packets=[pack(1,['D06']),pack(2,['D16']),pack(3,['D16'])],
                new_design_feature_items=[dict(feature_id='D18',status='DESIGN_ONLY')])

class TestRollup(unittest.TestCase):
    def test_feature_and_packet_counts(self):
        s=m.summarize(fixture())
        self.assertEqual((s['indexed_sealed_packets'],s['github_reference_feature_groups'],s['candidate_features_in_all_known_groups'],s['total_known_feature_groups']),(3,2,7,18))
    def test_delivered_design_still_no_game_code(self):
        d=fixture();d['new_design_feature_items'][0]['status']='DESIGN_ARTIFACT_DELIVERED_NO_GAME_CODE'
        s=m.summarize(d)
        self.assertEqual(s['new_design_artifact_delivered_groups'],1)
        self.assertEqual(s['candidate_features_in_all_known_groups'],7)
    def test_14_packets_cover_12_reference_groups_17_of_18(self):
        d=fixture()
        scopes=[['D06'],['D07','D08','D09','D10'],['D11'],['D12'],
                ['D13'],['D14'],['D15'],['D16'],['D16'],['D16'],
                ['D16'],['D17'],['D17'],['D07']]
        d['sealed_packets']=[dict(packet_id='p'+str(i),commit=f'{i:040x}',
                                  feature_ids=ids,envelope_path='handoffs/cipher.json',
                                  readme_path='handoffs/note.md',
                                  windows_restore='NOT_TESTED',studio_qa='NOT_TESTED')
                             for i,ids in enumerate(scopes,1)]
        d['new_design_feature_items'][0]['status']='DESIGN_ARTIFACT_DELIVERED_NO_GAME_CODE'
        report=m.summarize(d)
        self.assertEqual(report['indexed_sealed_packets'],14)
        self.assertEqual(report['github_reference_feature_groups'],12)
        self.assertEqual(report['candidate_features_in_historical_baseline'],17)
        self.assertEqual(report['candidate_features_in_all_known_groups'],17)
        self.assertEqual(report['total_known_feature_groups'],18)
        self.assertEqual(report['new_design_artifact_delivered_groups'],1)
        self.assertEqual(report['windows_restored_packets_verified'],0)
    def test_baseline_fixed(self):
        d=fixture();d['baseline_feature_ids'].append('D18')
        with self.assertRaisesRegex(m.ProgressError,'BASELINE_CHANGED'):m.summarize(d)
    def test_design_only_not_code(self):
        s=m.summarize(fixture()); self.assertEqual(s['new_design_only_features'],1)
        self.assertEqual(s['candidate_features_in_all_known_groups'],7)
    def test_fake_pc_stage_blocked(self):
        d=fixture();d['sealed_packets'][0]['studio_qa']='PASS'
        with self.assertRaisesRegex(m.ProgressError,'CANNOT_ATTEST'):m.summarize(d)
    def test_fake_pc_global_blocked(self):
        d=fixture();d['pc_status']='STUDIO_QA_PASS'
        with self.assertRaisesRegex(m.ProgressError,'UNVERIFIED_PC'):m.summarize(d)
    def test_cross_commit_same_path_allowed(self):m.summarize(fixture())
    def test_same_commit_same_path_blocked(self):
        d=fixture();d['sealed_packets'][1]['commit']=d['sealed_packets'][0]['commit']
        with self.assertRaisesRegex(m.ProgressError,'COLLISION'):m.summarize(d)
    def test_duplicate_packet_blocked(self):
        d=fixture();d['sealed_packets'][1]['packet_id']='p1'
        with self.assertRaisesRegex(m.ProgressError,'DUPLICATE'):m.summarize(d)
    def test_bad_path_blocked(self):
        d=fixture();d['sealed_packets'][0]['envelope_path']='handoffs/../../key'
        with self.assertRaisesRegex(m.ProgressError,'UNSAFE'):m.summarize(d)
    def test_added_feature_fake_studio_rejected(self):
        d=fixture();d['new_design_feature_items'][0]['status']='STUDIO_QA_PASS'
        with self.assertRaisesRegex(m.ProgressError,'CANNOT_CLAIM'):m.summarize(d)
    def test_duplicate_d18_rejected(self):
        d=fixture();d['new_design_feature_items'].append({'feature_id':'D18','status':'DESIGN_ONLY'})
        with self.assertRaisesRegex(m.ProgressError,'DUPLICATE'):m.summarize(d)
    def test_issue_comments_spoofed_pass_never_counted(self):
        d=fixture(); comments=[{'body':'[P0D_DELIVERY]\npacket_id=newpacket\ncommit_sha='+('a'*40)+'\nstudio_tests=PASS\n'}]
        s=m.summarize(d,comments)
        self.assertEqual(len(s['discovered_unindexed_delivery_claims']),1)
        self.assertEqual(s['github_reference_feature_groups_studio_qa_pass'],0)
    def test_registered_comment_not_unindexed(self):
        c=[{'body':'[P0D_DELIVERY]\npacket_id=p1\ncommit_sha='+('1'*40)}]
        self.assertEqual(len(m.summarize(fixture(),c)['discovered_unindexed_delivery_claims']),0)
    def test_invalid_comment_untrusted(self):
        c=[{'body':'[P0D_DELIVERY]\npacket_id=../key\ncommit_sha='+('1'*40)}]
        self.assertEqual(len(m.summarize(fixture(),c)['discovered_unindexed_delivery_claims']),0)
    def test_duplicate_json_rejected(self):
        with self.assertRaisesRegex(m.ProgressError,'DUPLICATE_JSON_KEY'):m.strict_loads('{"a":1,"a":2}')
    def test_markdown_contains_real_blocker(self):
        s=m.summarize(fixture()); text=m.to_markdown(s)
        self.assertIn('PC_REPORT_NOT_SUPPLIED',text)
        self.assertIn('0/3',text)
    def test_exclusive_output(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/'reg.json';p.write_text(json.dumps(fixture()),encoding='utf8');out=root/'report.md'
            with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
                self.assertEqual(m.main(['--registry',str(p),'--output',str(out)]),0)
                self.assertEqual(m.main(['--registry',str(p),'--output',str(out)]),2)
    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);real=root/'reg.json';real.write_text(json.dumps(fixture()))
            link=root/'link.json'
            try:link.symlink_to(real)
            except (OSError,NotImplementedError):self.skipTest('symlink unsupported')
            with self.assertRaisesRegex(m.ProgressError,'SYMLINK_INPUT'):m.load_file(link)

if __name__=='__main__':unittest.main()


class TestPcEvidence(unittest.TestCase):
    def registry(self):
        return json.loads((ROOT/'docs'/'P0D_INTAKE_REGISTRY.json').read_text())

    def evidence(self):
        return json.loads((ROOT/'docs'/'P0D_PC_EVIDENCE_v39_SCOPED.json').read_text())

    def test_real_source_linked_v39_one_scoped_pass(self):
        s=m.summarize(self.registry(),pc_evidence=self.evidence())
        self.assertEqual(s['indexed_sealed_packets'],16)
        self.assertEqual(s['windows_restored_packets_pc_reported'],1)
        self.assertEqual(s['github_reference_feature_groups_studio_scoped_pc_reported'],1)
        self.assertEqual(s['github_reference_feature_groups_studio_qa_pass'],0)
        self.assertEqual(s['pc_status'],'PARTIAL_NOT_READY')
        self.assertIn('issuecomment-6753848890',s['pc_evidence']['source_issue_comment'])
        self.assertIn('V39_FINAL',s['pc_blocker'])
        self.assertEqual(len(s['pc_evidence']['remaining_qa']),5)

    def test_no_evidence_means_no_pc_claim(self):
        s=m.summarize(self.registry())
        self.assertEqual(s['windows_restored_packets_pc_reported'],0)
        self.assertEqual(s['github_reference_feature_groups_studio_scoped_pc_reported'],0)
        self.assertEqual(s['pc_evidence']['status'],'NOT_SUPPLIED_TO_THIS_COMMAND')

    def test_spoofed_issue_comment_does_not_replace_evidence(self):
        body='[P0D_PROGRESS_EVENT v1]\npacket_id=v39-h1-chatlead-ref-20261110\ncommit_sha='+('b'*40)+'\nstudio_tests=PASS\n'
        s=m.summarize(self.registry(),comments=[{'body':body}])
        self.assertEqual(s['windows_restored_packets_pc_reported'],0)
        self.assertEqual(s['github_reference_feature_groups_studio_qa_pass'],0)

    def test_wrong_source_domain_rejected(self):
        e=self.evidence();e['source_issue_comment']='https://evil.com/issues/213#issuecomment-6753848890'
        with self.assertRaisesRegex(m.ProgressError,'BAD_SOURCE'):m.summarize(self.registry(),pc_evidence=e)

    def test_wrong_issue_thread_rejected(self):
        e=self.evidence();e['coordination_comment']='https://github.com/kk051780/toy-wars-factory/issues/999#issuecomment-1'
        with self.assertRaisesRegex(m.ProgressError,'BAD_COORDINATION'):m.summarize(self.registry(),pc_evidence=e)

    def test_wrong_zip_sha_rejected(self):
        e=self.evidence();e['packet_results'][0]['restored_zip_sha256']='0'*64
        with self.assertRaisesRegex(m.ProgressError,'PIN_OR_ZIP_MISMATCH'):m.summarize(self.registry(),pc_evidence=e)

    def test_wrong_commit_rejected(self):
        e=self.evidence();e['packet_results'][0]['pinned_commit']='0'*40
        with self.assertRaisesRegex(m.ProgressError,'PIN_OR_ZIP_MISMATCH'):m.summarize(self.registry(),pc_evidence=e)

    def test_wrong_packet_id_rejected(self):
        e=self.evidence();e['packet_results'][0]['packet_id']='other'
        with self.assertRaisesRegex(m.ProgressError,'UNKNOWN_OR_DUPLICATE'):m.summarize(self.registry(),pc_evidence=e)

    def test_duplicate_pc_claim_rejected(self):
        e=self.evidence();e['packet_results'].append(copy.deepcopy(e['packet_results'][0]))
        with self.assertRaisesRegex(m.ProgressError,'UNKNOWN_OR_DUPLICATE'):m.summarize(self.registry(),pc_evidence=e)

    def test_false_full_studio_pass_rejected(self):
        e=self.evidence();e['packet_results'][0]['studio_full_qa']='PASS'
        with self.assertRaisesRegex(m.ProgressError,'FINAL_STUDIO_NOT_SUPPORTED'):m.summarize(self.registry(),pc_evidence=e)

    def test_false_global_pass_rejected(self):
        e=self.evidence();e['global_release_status']='READY'
        with self.assertRaisesRegex(m.ProgressError,'GLOBAL_PASS_UNSUPPORTED'):m.summarize(self.registry(),pc_evidence=e)

    def test_no_remaining_qa_rejected(self):
        e=self.evidence();e['packet_results'][0]['remaining_qa']=[]
        with self.assertRaisesRegex(m.ProgressError,'REMAINDERS_REQUIRED'):m.summarize(self.registry(),pc_evidence=e)

    def test_invalid_studio_exit_rejected(self):
        e=self.evidence();e['pc_studio_exit']='OPEN'
        with self.assertRaisesRegex(m.ProgressError,'EXIT_NOT_CONFIRMED'):m.summarize(self.registry(),pc_evidence=e)

    def test_wrong_pc_place_sha_rejected(self):
        e=self.evidence();e['pc_place_sha256']='bad'
        with self.assertRaisesRegex(m.ProgressError,'PC_HASH_INVALID'):m.summarize(self.registry(),pc_evidence=e)

    def test_output_with_evidence_explicit_is_scoped(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out.json'
            with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
                rc=m.main(['--registry',str(ROOT/'docs'/'P0D_INTAKE_REGISTRY.json'),
                           '--pc-evidence',str(ROOT/'docs'/'P0D_PC_EVIDENCE_v39_SCOPED.json'),
                           '--format','json','--output',str(out)])
            self.assertEqual(rc,0)
            s=json.loads(out.read_text())
            self.assertEqual(s['windows_restored_packets_pc_reported'],1)
            self.assertEqual(s['github_reference_feature_groups_studio_qa_pass'],0)
            self.assertFalse(s['remote_readback_performed_by_this_rollup'])
