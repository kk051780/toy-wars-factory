from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from rc_intake_preflight import InvalidManifest, validate, compare, validate_observed

D = 'a' * 64
E = 'b' * 64

def file(p, d=D, size=10):
    return {'path':p,'sha256':d,'size':size}

def mf(files, **extra):
    return {'format':'P0D_PUBLIC_SOURCE_V1','game_id':'TRAP_RAIDERS','work_id':'p0d-siege-v19','packet_id':'S1-RC','public_source_allowed':True,'files':files,**extra}

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.old=mf([file('a.luau'),file('b.luau')],status='LEGACY')
        self.new=mf([file('a.luau'),file('b.luau',E),file('c.luau')])
    def test_changes(self):
        r=compare(self.old,self.new)
        self.assertEqual(r['counts'],{'unchanged':1,'changed':1,'added':1,'removed':0})
    def test_same(self):
        r=compare(mf([file('a.luau')]),mf([file('a.luau')]))
        self.assertEqual(r['counts']['unchanged'],1)
    def test_added_only(self):
        r=compare(mf([file('a.luau')]),mf([file('a.luau'),file('b.luau')]))
        self.assertEqual(r['counts']['added'],1)
    def test_legacy_status_accepted_only_on_rc(self):
        self.assertEqual(len(validate(self.old,original=True)),2)
        with self.assertRaises(InvalidManifest):validate(self.old)
    def test_extra_candidate_key_rejected(self):
        x=copy.deepcopy(self.new);x['status']='unexpected'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_unknown_original_key_rejected(self):
        x=copy.deepcopy(self.old);x['injection']='x'
        with self.assertRaises(InvalidManifest):compare(x,self.new)
    def test_wrong_format(self):
        x=copy.deepcopy(self.new);x['format']='OTHER'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_wrong_game(self):
        x=copy.deepcopy(self.new);x['game_id']='OTHER'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_wrong_work(self):
        x=copy.deepcopy(self.new);x['work_id']='OTHER'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_public_false(self):
        x=copy.deepcopy(self.new);x['public_source_allowed']=False
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_duplicate_path(self):
        x=copy.deepcopy(self.new);x['files'].append(file('c.luau'))
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_traversal_rejected(self):
        x=copy.deepcopy(self.new);x['files'][2]['path']='../../secret'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_absolute_path_rejected(self):
        x=copy.deepcopy(self.new);x['files'][2]['path']='/a'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_hidden_untracked_path(self):
        x=copy.deepcopy(self.new);x['files'][2]['path']='a/../c'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_bad_sha(self):
        x=copy.deepcopy(self.new);x['files'][2]['sha256']='no'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_negative_size(self):
        x=copy.deepcopy(self.new);x['files'][2]['size']=-1
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_bool_size(self):
        x=copy.deepcopy(self.new);x['files'][2]['size']=True
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_removed_file_fails_closed(self):
        with self.assertRaises(InvalidManifest):compare(self.old,mf([file('a.luau')]))
    def test_extra_file_keys_rejected(self):
        x=copy.deepcopy(self.new);x['files'][2]['status']='skip'
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_modified_size_is_change(self):
        x=copy.deepcopy(self.new);x['files'][0]['size']=11
        self.assertEqual(compare(self.old,x)['counts']['changed'],2)
    def test_bad_top(self):
        with self.assertRaises(InvalidManifest):validate([])
    def test_nan_size(self):
        x=copy.deepcopy(self.new);x['files'][2]['size']=float('nan')
        with self.assertRaises(InvalidManifest):compare(self.old,x)
    def test_bad_expected_reject(self):
        r=compare(self.old,self.new);p=copy.deepcopy(r);p['counts']['added']=8
        with self.assertRaises(InvalidManifest):validate_observed(r,p)
    def test_no_unrequested_side_effects(self):
        x=copy.deepcopy(self.old);y=copy.deepcopy(self.new);compare(x,y)
        self.assertEqual(x,self.old);self.assertEqual(y,self.new)
    def test_bad_file_metadata_key(self):
        x=copy.deepcopy(self.new);x['files'][0].pop('sha256')
        with self.assertRaises(InvalidManifest):compare(self.old,x)

if __name__ == '__main__':unittest.main()
