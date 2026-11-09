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
        self.assertIn('V37_FINAL_SAVED_PLACE',text)
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
