#!/usr/bin/env python3
"""Producer boundaries; these checks do not add gameplay acceptance cases."""
import argparse
import copy
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import gate

parser = argparse.ArgumentParser()
for name in ['artifact-zip','run-metadata','artifact-metadata']:
    parser.add_argument('--'+name,type=Path,required=True)
ARGS = parser.parse_args()

class GateBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = gate.load_lock()
        cls.zip_raw = gate.read(ARGS.artifact_zip)
        cls.archive = gate.read_artifact(cls.zip_raw,cls.lock)
        cls.sources = gate.source_map(cls.archive,cls.lock)
        cls.provider_run = gate.strict_json(gate.read(ARGS.run_metadata))
        cls.artifacts = gate.strict_json(gate.read(ARGS.artifact_metadata))
        cls.canonical = gate.canonical_inputs(cls.archive,cls.sources,cls.lock)
        cls.prefix,cls.ranges,cls.fixture = gate.assemble_prefix(cls.canonical['combined_clear_los']['prefix'],cls.sources,cls.lock)

    def test_fixed_real_inputs_reconstruct_exact_canonical_28(self):
        gate.validate_provider(self.provider_run,self.artifacts,self.lock)
        gate.verify_owner_files(gate.REPO,self.lock)
        routes = gate.project_routes(self.archive[gate.PROJECT],self.sources)
        gate.verify_place(self.archive[gate.PLACE],routes,self.sources)
        for values in self.canonical.values():
            self.assertEqual(self.prefix,values['prefix'])
            self.assertEqual(self.prefix+values['case'],values['generated'])
        self.assertEqual(len(self.ranges),28)
        self.assertNotIn(self.lock['target'],self.ranges)
        self.assertNotIn(self.lock['lss'],self.ranges)
        self.assertGreater(self.fixture['bytes'],0)

    def test_all_26_frozen_bomb_programs_reconstruct_exactly(self):
        with tempfile.TemporaryDirectory(prefix='program-boundary-',dir=gate.HERE) as directory:
            root = Path(directory)
            target = root/self.lock['target'];target.parent.mkdir(parents=True)
            target.write_bytes(self.sources[self.lock['target']])
            subprocess.run(['git','apply',str(gate.HERE/'realm_bomb_occlusion.patch')],cwd=root,
                           check=True,capture_output=True)
            candidate = dict(self.sources);candidate[self.lock['target']] = target.read_bytes()
            self.assertEqual(gate.pin(candidate[self.lock['target']]),self.lock['candidate'])
            for oracle in self.lock['bomb_cases']:
                with self.subTest(name=oracle['name']):
                    sources = self.sources if oracle['variant']=='official' else candidate
                    program,ranges = gate.assemble_bomb(self.canonical,self.ranges,sources,self.lock,oracle)
                    self.assertEqual(gate.pin(program),oracle['program'])
                    self.assertEqual(len(ranges),30)
                    self.assertEqual(set(ranges)-set(self.ranges),{self.lock['lss'],self.lock['target']})

    def test_wrong_run_head_event_attempt_or_workflow_rejected(self):
        for field,value in [('head_sha','0'*40),('event','pull_request'),('run_attempt',2),('path','different.yml')]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.provider_run);bad[field]=value
                with self.assertRaisesRegex(ValueError,'OFFICIAL_RUN_METADATA'):
                    gate.validate_provider(bad,self.artifacts,self.lock)

    def test_expired_wrong_id_digest_or_artifact_origin_rejected(self):
        index = next(i for i,a in enumerate(self.artifacts['artifacts']) if a['id']==self.lock['artifact']['id'])
        for field,value in [('expired',True),('id',1),('digest','sha256:'+'0'*64)]:
            with self.subTest(field=field):
                bad=copy.deepcopy(self.artifacts);bad['artifacts'][index][field]=value
                with self.assertRaises(ValueError):
                    gate.validate_provider(self.provider_run,bad,self.lock)
        bad=copy.deepcopy(self.artifacts);bad['artifacts'][index]['workflow_run']['head_sha']='0'*40
        with self.assertRaisesRegex(ValueError,'ARTIFACT_OFFICIAL_LINEAGE'):
            gate.validate_provider(self.provider_run,bad,self.lock)

    def test_zip_corruption_and_traversal_rejected_before_output(self):
        bad=self.zip_raw[:-1]+bytes([self.zip_raw[-1]^1])
        with self.assertRaisesRegex(ValueError,'ARTIFACT_ZIP_BYTES'):
            gate.read_artifact(bad,self.lock)
        stream=io.BytesIO()
        with ZipFile(stream,'w') as archive:
            archive.writestr('../outside.luau',b'not a source')
        raw=stream.getvalue();lower=copy.deepcopy(self.lock);lower['artifact']['zip']=gate.pin(raw)
        with self.assertRaisesRegex(ValueError,'ZIP_ENTRY'):
            gate.read_artifact(raw,lower)

    def test_other_source_change_and_wrong_inverse_rejected(self):
        changed=dict(self.archive);other=next(p for p in self.sources if p!=self.lock['target'])
        changed['sources/'+other]+=b'\n'
        with self.assertRaisesRegex(ValueError,'EXACT_69_SOURCES'):
            gate.source_map(changed,self.lock)
        restored=dict(self.sources);restored[other]+=b'\n'
        with self.assertRaisesRegex(ValueError,'ACTUAL_INVERSE_BYTES'):
            gate.compare_source_maps(restored,self.sources,'ACTUAL_INVERSE')

    def test_generated_case_suffix_and_body_receipt_drift_rejected(self):
        selected=self.lock['canonical_suites']['combined_clear_los']
        bad=dict(self.archive);name=selected['generated_path'];bad[name]=bad[name][:-1]+b'x'
        with self.assertRaisesRegex(ValueError,'CANONICAL_GENERATED'):
            gate.canonical_inputs(bad,self.sources,self.lock)
        bad=dict(self.archive);name=selected['receipt_path'];metadata=gate.strict_json(bad[name])
        metadata['full_body_byte_ranges'][next(iter(self.ranges))]['end']+=1
        bad[name]=gate.json.dumps(metadata).encode()
        with self.assertRaisesRegex(ValueError,'CANONICAL_28_RANGES'):
            gate.canonical_inputs(bad,self.sources,self.lock)

    def test_native_vector_cannot_pass_missing_duplicate_fail_error_or_bad_utf8(self):
        names=['ONE','TWO'];good=b'CASE\tONE\tPASS\tcomplete\nCASE\tTWO\tPASS\tcomplete\n'
        gate.validate_native(0,good,b'',names)
        for code,out,err in [(0,good.splitlines()[0]+b'\n',b''),(0,good+good,b''),
                (0,good.replace(b'PASS',b'FAIL',1),b''),(1,good,b'process failed'),
                (0,good,b'error despite zero exit'),(0,good+b'\xff',b'')]:
            with self.subTest(code=code,out=out[:30],err=err):
                with self.assertRaises((ValueError,UnicodeDecodeError)):
                    gate.validate_native(code,out,err,names)

    def test_old_red_requires_exact_output_observations_reason_and_exit(self):
        oracle=copy.deepcopy(self.lock['bomb_cases'][0])
        result=oracle['result_lines'][0]
        good=(''.join('EXPECT\t'+'\t'.join(row[k] for k in ['label','status','actual','wanted'])+'\n'
                     for row in oracle['observations'])+result+'\n').encode()
        path=Path('/fixture/generated.luau')
        err=str(path).encode()+b':77: SOURCE_ACCEPTANCE_RED:1\n'
        oracle['stdout']=gate.pin(good);oracle['stderr_normalized']=gate.pin(err.replace(str(path).encode(),b'<PROGRAM>'))
        gate.validate_bomb(1,good,err,path,oracle)
        for code,out,stderr in [(0,good,err),(1,good.replace(b'\tFAIL\t',b'\tPASS\t'),err),
                (1,b'',b'boot error'),(1,good,b'unrelated exception'),(1,good+good,err),
                (1,good+b'\xff',err)]:
            with self.subTest(code=code,out=out[:30],err=stderr[:30]):
                with self.assertRaises((ValueError,UnicodeDecodeError)):
                    gate.validate_bomb(code,out,stderr,path,oracle)

    def test_superseded_fractional_clock_cannot_substitute_exact_clock(self):
        oracle=copy.deepcopy(next(row for row in self.lock['bomb_cases']
                    if row['scenario']=='OUTSIDE_RADIUS' and row['variant']=='official'))
        oracle['case_file']='bomb_cases_original12.luau'
        with self.assertRaisesRegex(ValueError,'BOMB_CASE_VERSION'):
            gate.assemble_bomb(self.canonical,self.ranges,self.sources,self.lock,oracle)

    def test_existing_overlapping_and_symlink_output_rejected(self):
        with tempfile.TemporaryDirectory(prefix='output-boundary-',dir=gate.HERE) as directory:
            root=Path(directory);source=root/'source';source.mkdir()
            with self.assertRaisesRegex(ValueError,'OUTPUT_MUST_BE_NEW'):
                gate.safe_output(source,[])
            with self.assertRaisesRegex(ValueError,'OUTPUT_INPUT_OVERLAP'):
                gate.safe_output(source/'new',[source])
            link=root/'link';link.symlink_to(source,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'SYMLINK_ROOT'):
                gate.safe_output(link/'new',[])
            self.assertEqual(list(source.iterdir()),[])

    def test_built_place_source_and_non_source_drift_rejected(self):
        routes=gate.project_routes(self.archive[gate.PROJECT],self.sources)
        expected=gate.verify_place(self.archive[gate.PLACE],routes,self.sources)
        for kind in ['source','property']:
            tree=ET.fromstring(self.archive[gate.PLACE])
            item=next(item for item in tree.iter('Item') if any(p.attrib.get('name')=='Source' for p in item.find('Properties')))
            props=item.find('Properties')
            if kind=='source':
                node=next(p for p in props if p.attrib.get('name')=='Source');node.text+='\n'
            else:
                ET.SubElement(props,'bool',{'name':'Disabled'}).text='true'
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    gate.verify_place(ET.tostring(tree),routes,self.sources,expected)

    def test_original_owner_runtime_and_old_job_edits_rejected(self):
        with tempfile.TemporaryDirectory(prefix='owner-boundary-',dir=gate.HERE) as directory:
            root=Path(directory)
            for path in self.lock['original_owner_files']:
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(gate.read(gate.REPO/path))
            gate.verify_owner_files(root,self.lock)
            for path in ['handoffs/EGGRUMBLE-REALM-CORE-20261118/EGGRUMBLE_RealmBattleCore.server.luau',gate.WORKFLOW]:
                target=root/path;before=target.read_bytes();target.write_bytes(b'x'+before[1:])
                with self.subTest(path=path):
                    with self.assertRaisesRegex(ValueError,'ORIGINAL_OWNER_FILE'):
                        gate.verify_owner_files(root,self.lock)
                target.write_bytes(before)

    def test_hosted_context_cannot_claim_local_or_wrong_checkout(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'},clear=True):
            with self.assertRaisesRegex(ValueError,'HOSTED_CANNOT_CLAIM_LOCAL'):
                gate.execution_context('LOCAL_NONCANONICAL',Path('/usr/bin/git'))
        env={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'kk051780/toy-wars-factory',
             'GITHUB_EVENT_NAME':'push','GITHUB_SHA':'1'*40}
        with patch.dict(os.environ,env,clear=True),patch.object(gate.toolchain,'git_output',return_value=b'2'*40+b'\n'):
            with self.assertRaisesRegex(ValueError,'CHECKOUT_GITHUB_SHA'):
                gate.execution_context('GITHUB_NONCANONICAL_QA',Path('/usr/bin/git'))

if __name__=='__main__':
    unittest.main(argv=[__file__],verbosity=2)
