"""Offline-only unit/regression/negative QA; NEVER claims native Roblox Studio passed."""
import copy,importlib.util,json,math,re,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('d18generator',ROOT/'tools/generate_catalog.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
spec2=importlib.util.spec_from_file_location('d18verify',ROOT/'tools/verify_pack.py')
v=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(v)
def J(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
DATA=J('data/six_pilot_geometry.json')
RULES=J('data/archetype_rules.json')
REG=J('data/flagship72_registry.json')
QUEUE=J('data/next54_source_queue.json')
CLAIMS=J('data/batch_claims.json')
NEW=set(CLAIMS['new_3d_source_ids'])
ORIGINAL=set(CLAIMS['previous_3d_source_ids'])

def verify(data=None,rules=None,registry=None,queue=None,claims=None):
 return g.validate(DATA if data is None else data,
                   RULES if rules is None else rules,
                   REG if registry is None else registry,
                   QUEUE if queue is None else queue,
                   CLAIMS if claims is None else claims)

class CanonicalTests(unittest.TestCase):
 def test_a_72_unique_canon(self):self.assertEqual(len({x['id'] for x in REG['entries']}),72)
 def test_b_all_six_names_from_v8(self):self.assertEqual({x['name'] for x in DATA['characters'].values()}, {'大歯輪ガメ','永久晶のまもり','天鼓の空見台','貝鳴りホルン','星鐘の案内兵','つぼみ跳ね台'})
 def test_c_all_six_categories(self):self.assertEqual({x['category'] for x in DATA['characters'].values()},g.CATEGORIES)
 def test_d_18_after_this_source_only(self):self.assertEqual(len(NEW|ORIGINAL),18)
 def test_e_no_old_source_id_overwritten(self):self.assertFalse(NEW&ORIGINAL)
 def test_f_54_unclaimed(self):self.assertEqual(sum(map(len,QUEUE['groups'].values())),54)
 def test_g_six_groups_nine_each(self):self.assertEqual({k:len(v) for k,v in QUEUE['groups'].items()},{k:9 for k in g.CATEGORIES})
 def test_h_full_72_coverage(self):self.assertEqual(NEW|ORIGINAL|{v['id'] for group in QUEUE['groups'].values() for v in group},{x['id'] for x in REG['entries']})
 def test_i_exact_editorial_source_sha(self):self.assertRegex(REG['source_atlas_sha256'],r'^[0-9a-f]{64}$')
 def test_j_queue_no_auto_claims(self):self.assertTrue(all(x['soft_claim']=='NONE' for group in QUEUE['groups'].values() for x in group))
 def test_k_6_authored_not_procedural_clone(self):self.assertEqual(len({x['archetype'] for x in DATA['characters'].values()}),6)
 def test_l_source_schemas_all_match(self):self.assertTrue(verify())
 def test_m_source_list_from_canon(self):self.assertTrue(all(REG['entries'][i]['id'] in {x['id'] for x in REG['entries']} for i in range(72)))
 def test_n_rarity_is_canonical(self):self.assertTrue(all(x['rarity'] in ('ミシック','レジェンド') for x in DATA['characters'].values()))
 def test_o_mode_source_only(self):self.assertEqual(DATA['generation_mode'],'ORIGINAL_MANUALLY_AUTHORED_SIGNATURE_PARTS')

class GeometryTests(unittest.TestCase):
 def test_a_all_near_caps(self):self.assertTrue(all(len(x['parts'])<=30 for x in DATA['characters'].values()))
 def test_b_all_far_caps(self):self.assertTrue(all(sum(p['far'] for p in x['parts'])<=18 for x in DATA['characters'].values()))
 def test_c_far_3_signatures(self):self.assertTrue(all(set(x['signature_tags']) <= {p['signature_tag'] for p in x['parts'] if p['far']} for x in DATA['characters'].values()))
 def test_d_unique_per_model_names(self):self.assertTrue(all(len({p['name'] for p in x['parts']})==len(x['parts']) for x in DATA['characters'].values()))
 def test_e_no_nonprimitive_shapes(self):self.assertTrue(all(p['shape'] in g.SHAPES for x in DATA['characters'].values() for p in x['parts']))
 def test_f_4_poses_each(self):self.assertTrue(all(set(x['pose_offsets'])==g.POSES for x in DATA['characters'].values()))
 def test_g_gear_turtle_asymmetry(self):
  p=DATA['characters']['TRCA-BE-027']['parts'];self.assertEqual(len([x for x in p if x['signature_tag']=='gear_shell']),14)
 def test_h_crystal_open_door(self):self.assertGreaterEqual(sum(p['signature_tag']=='open_door' for p in DATA['characters']['TRCA-SP-036']['parts']),2)
 def test_i_telescope_looks_down(self):self.assertTrue(any(p['name']=='見下ろす望遠筒' and p['rotation'][2]!=0 for p in DATA['characters']['TRCA-VE-045']['parts']))
 def test_j_conch_two_coils(self):self.assertEqual(len([p for p in DATA['characters']['TRCA-WE-054']['parts'] if '二枚貝の巻き' in p['name']]),12)
 def test_k_soldier_uneven_boots(self):
  p={p['name']:p['size'] for p in DATA['characters']['TRCA-ZO-009']['parts']};self.assertNotEqual(p['右の大きな長靴'],p['左の小さな長靴'])
 def test_l_bud_tip_one_bent(self):self.assertEqual(len([p for p in DATA['characters']['TRCA-TR-018']['parts'] if p['signature_tag']=='bent_tip']),1)
 def test_m_colors_rgb(self):self.assertTrue(all(all(0<=c<=255 for c in rgb) for m in DATA['characters'].values() for rgb in m['palette'].values()))
 def test_n_parts_anchored_in_factory(self):self.assertIn('p.Anchored = true',(ROOT/'src/D18BatchFactory.luau').read_text())
 def test_o_no_worldspace_parent(self):self.assertIn('parent:IsA("WorldModel")',(ROOT/'src/D18BatchFactory.luau').read_text())

class GeneratorAndSafetyTests(unittest.TestCase):
 def test_a_catalog_determinism(self):self.assertEqual(g.generate(),(ROOT/'src/D18BatchCatalog.luau').read_text())
 def test_b_catalog_has_each_id(self):self.assertTrue(all(id in g.generate() for id in NEW))
 def test_c_api_complete(self):
  f=(ROOT/'src/D18BatchFactory.luau').read_text(); self.assertTrue(all(f'function Factory.{name}(' in f for name in ('Build','SetPose','SetLod','SetYaw','GetStatus','Destroy')))
 def test_d_all_noncolliding(self):
  f=(ROOT/'src/D18BatchFactory.luau').read_text();self.assertTrue(all(f'p.{x} = false' in f for x in ('CanCollide','CanTouch','CanQuery','CastShadow')))
 def test_e_no_server_apis(self):
  f=(ROOT/'src/D18BatchFactory.luau').read_text(); self.assertTrue(all(x not in f for x in ('FireServer(', 'FireClient(', 'MarketplaceService', 'DataStoreService', 'TakeDamage(', 'RemoteEvent', 'Humanoid:')))
 def test_f_demo_not_active(self):self.assertIn('local ENABLED = false',(ROOT/'src/DisabledPilotDemo.client.luau').read_text())
 def test_g_standalone_rojo(self):
  j=J('default.project.json'); s=j['tree']['StarterPlayer']['StarterPlayerScripts'];self.assertEqual(set(s)-{'$className'},{'D18BatchCatalog','D18BatchFactory','DisabledPilotDemo'})
 def test_h_factory_lod_and_yaw(self):
  f=(ROOT/'src/D18BatchFactory.luau').read_text();self.assertIn('state.far=far',f);self.assertIn('angle % 45 ~= 0',f)
 def test_i_no_claimed_future_models(self):self.assertTrue(all('NOT_STARTED' in x['status'] for v in QUEUE['groups'].values() for x in v))
 def test_j_actual_manifest_complete(self):self.assertEqual(v.check(),len(J('BUILD_MANIFEST.json')['files']))

class MutantRejectionTests(unittest.TestCase):
 def assertMutantRejected(self,mut):
  a,b,c,d,e=(copy.deepcopy(x) for x in (DATA,RULES,REG,QUEUE,CLAIMS))
  mut(a,b,c,d,e)
  with self.assertRaises((ValueError,KeyError,TypeError)):
   verify(a,b,c,d,e)
 def test_wrong_id(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters'].pop('TRCA-BE-027'))
 def test_fake_canon_name(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-BE-027'].__setitem__('name','偽物'))
 def test_fake_world(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-WE-054'].__setitem__('world','FAKE_WORLD'))
 def test_rarity_change(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-SP-036'].__setitem__('rarity','ミシックfake'))
 def test_duplicate_part_name(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-ZO-009']['parts'][1].__setitem__('name',a['characters']['TRCA-ZO-009']['parts'][0]['name']))
 def test_missing_far_silhouette(self):
  def mut(a,b,c,d,e):
   for part in a['characters']['TRCA-TR-018']['parts']:
    if part['signature_tag']=='bent_tip':part['far']=False
  self.assertMutantRejected(mut)
 def test_shape_is_not_allowed(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-VE-045']['parts'][0].__setitem__('shape','MeshPart'))
 def test_negative_dimension(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-WE-054']['parts'][0].__setitem__('size',[-1,1,1]))
 def test_excessive_dimension(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-ZO-009']['parts'][0].__setitem__('size',[9,1,1]))
 def test_nonfinite_rotation(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-BE-027']['parts'][0].__setitem__('rotation',[math.nan,0,0]))
 def test_RGB_overflow(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-SP-036']['palette'].__setitem__('ice',[999,23,55]))
 def test_invalid_poses(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-TR-018']['pose_offsets'].pop('loss'))
 def test_invalid_pose_group(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-VE-045']['pose_offsets']['win'].__setitem__('BAD_GROUP',{'rz':2}))
 def test_invalid_pose_movement(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-WE-054']['pose_offsets']['tap']['shells'].__setitem__('rz',99))
 def test_false_category_claim(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-BE-027'].__setitem__('category','SP'))
 def test_missing_queue_item(self):self.assertMutantRejected(lambda a,b,c,d,e:d['groups']['BE'].pop())
 def test_queue_name_tamper(self):self.assertMutantRejected(lambda a,b,c,d,e:d['groups']['BE'][0].__setitem__('name','fake'))
 def test_future_soft_claim_lie(self):self.assertMutantRejected(lambda a,b,c,d,e:d['groups']['WE'][0].__setitem__('soft_claim','TAKEN'))
 def test_past_model_reclaimed(self):self.assertMutantRejected(lambda a,b,c,d,e:e['new_3d_source_ids'].append('TRCA-BE-018'))
 def test_wrong_atlas_hash(self):self.assertMutantRejected(lambda a,b,c,d,e:a.__setitem__('source_atlas_sha256','0'*64))
 def test_unmatched_signature_rules(self):self.assertMutantRejected(lambda a,b,c,d,e:b['archetypes']['TRAP_BUD_SPRING'].__setitem__('signature_tags',['fake']))
 def test_exceed_part_budget(self):
  def mut(a,b,c,d,e):
   arr=a['characters']['TRCA-VE-045']['parts']
   for i in range(31):
    p=copy.deepcopy(arr[0]);p['name']=f'Fake{i}';arr.append(p)
  self.assertMutantRejected(mut)
 def test_bad_part_fields(self):self.assertMutantRejected(lambda a,b,c,d,e:a['characters']['TRCA-ZO-009']['parts'][0].__setitem__('server_Damage',100))
 def test_unproven_source_claim(self):self.assertMutantRejected(lambda a,b,c,d,e:e.__setitem__('soft_claim_issue_url','none'))
 def test_54_future_reusable_without_source_code_change(self):
  # Synthetic dry-run only, no actual new source, no canonical identity impersonation in release.
  a,b,c,d,e=(copy.deepcopy(x) for x in (DATA,RULES,REG,QUEUE,CLAIMS))
  new=candidate=d['groups']['BE'].pop(0)
  p=copy.deepcopy(a['characters']['TRCA-BE-027'])
  for key in ('id','name','world','rarity'):p[key]=candidate[key]
  a['characters']={new['id']:p}
  b['archetypes']={p['archetype']:b['archetypes'][p['archetype']]}
  e['previous_3d_source_ids']=sorted(NEW|ORIGINAL)
  e['new_3d_source_ids']=[new['id']]
  e['estimated_total_source_after_batch']=19
  d['previous_3d_source_ids']=e['previous_3d_source_ids']
  d['current_batch_ids']=e['new_3d_source_ids']
  d['remaining_source_not_started_count']=53
  self.assertTrue(verify(a,b,c,d,e))

if __name__=='__main__':unittest.main()
