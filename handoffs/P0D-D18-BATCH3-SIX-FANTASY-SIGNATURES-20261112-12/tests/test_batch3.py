"""D18 third-batch fantasy authentic data-driven source-only QA (NOT Roblox Studio/engine)."""
import copy, hashlib, importlib.util, json, math, re, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def import_module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
g=import_module('d18_batch3_generator','tools/generate_catalog.py')
v=import_module('d18_batch3_verify','tools/verify_pack.py')
def J(p): return json.loads((ROOT/p).read_text(encoding='utf8'))
DATA=J('data/six_pilot_geometry.json')
RULES=J('data/archetype_rules.json')
CANON=J('data/flagship72_registry.json')
QUEUE=J('data/next54_source_queue.json')
CLAIMS=J('data/batch_claims.json')
IDS=['TRCA-BE-054','TRCA-SP-072','TRCA-VE-099','TRCA-WE-090','TRCA-ZO-063','TRCA-TR-036']
NAMES=['海鐘クジラ','やさしい月の復帰','終わらない観覧台','時告げホルン','炎炉の門番兵','六花跳ね台']
CATEGORIES={'BE','SP','VE','WE','ZO','TR'}
SIZES={id:(len(c['parts']),sum(p['far'] for p in c['parts'])) for id,c in DATA['characters'].items()}
RULES_SHA='cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01'
PRIOR_BATCH_FACTORY_SHA256=hashlib.sha256((ROOT/'src/D18BatchFactory.luau').read_bytes()).hexdigest()

class OriginalIdentityTests(unittest.TestCase):
    def test_01_exact_six_claimed(self): self.assertEqual(set(IDS),set(DATA['characters']))
    def test_02_names_exact_from_owner_canon(self): self.assertEqual([DATA['characters'][i]['name'] for i in IDS],NAMES)
    def test_03_six_categories_one_each(self): self.assertEqual({i[5:7] for i in IDS},CATEGORIES)
    def test_04_canon72_unique(self): self.assertEqual(len({x['id'] for x in CANON['entries']}),72)
    def test_05_each_canon_category_12(self):
        for c in CATEGORIES:self.assertEqual(sum(x['category']==c for x in CANON['entries']),12)
    def test_06_atlas_sha_pinned(self): self.assertEqual(CANON['source_atlas_sha256'],RULES_SHA)
    def test_07_all_data_atlas_shas_same(self):
        for x in (DATA,CLAIMS,QUEUE):self.assertEqual(x['source_atlas_sha256'],RULES_SHA)
    def test_08_previous_twentyfour_set_preserved(self): self.assertEqual(len(set(CLAIMS['previous_3d_source_ids'])),24)
    def test_09_new_six_not_in_previous(self): self.assertFalse(set(IDS)&set(CLAIMS['previous_3d_source_ids']))
    def test_10_cumulative_30(self): self.assertEqual(len(set(IDS)|set(CLAIMS['previous_3d_source_ids'])),30)
    def test_11_remaining42_remainder(self): self.assertEqual(QUEUE['remaining_source_not_started_count'],42)
    def test_12_each_future_class_7(self):
        for cat in CATEGORIES:self.assertEqual(len(QUEUE['groups'][cat]),7)
    def test_13_remaining_no_overlap(self):
        remaining={r['id'] for rows in QUEUE['groups'].values() for r in rows}
        self.assertEqual(len(remaining),42)
        self.assertFalse(remaining&(set(IDS)|set(CLAIMS['previous_3d_source_ids'])))
    def test_14_all_72_partition_exact(self):
        remaining={r['id'] for rows in QUEUE['groups'].values() for r in rows}
        self.assertEqual(remaining|set(IDS)|set(CLAIMS['previous_3d_source_ids']),{c['id'] for c in CANON['entries']})
    def test_15_no_future_softclaim(self):
        for rows in QUEUE['groups'].values():
            for row in rows:self.assertEqual((row['status'],row['soft_claim']),('NOT_STARTED_3D_SOURCE','NONE'))
    def test_16_original_factory_same_hash_as_previous(self): self.assertEqual(PRIOR_BATCH_FACTORY_SHA256,'879428a78f23af1ec67544897390ae3e0e644ed4b7f2bcbbbc8f69940edb6de7')

class GeometryTests(unittest.TestCase):
    def test_17_full_json_validates(self): self.assertTrue(g.validate(DATA,RULES,CANON,QUEUE,CLAIMS))
    def test_18_near_budget_each(self):
        for id,(near,far) in SIZES.items():self.assertTrue(8<=near<=30,id)
    def test_19_far_budget_each(self):
        for id,(near,far) in SIZES.items():self.assertTrue(6<=far<=18,id)
    def test_20_each_three_signature_roles_far(self):
        for id,c in DATA['characters'].items():
            tags=set(c['signature_tags']); far={p['signature_tag'] for p in c['parts'] if p['far']}
            self.assertEqual(len(tags),3,id);self.assertTrue(tags<=far,id)
    def test_21_unique_signature_names_across_six(self):
        tags=sum((c['signature_tags'] for c in DATA['characters'].values()),[])
        self.assertEqual(len(tags),len(set(tags)))
    def test_22_each_unique_archetype(self):
        ar=[x['archetype'] for x in DATA['characters'].values()]
        self.assertEqual(len(ar),len(set(ar)))
    def test_23_part_names_unique_within_model(self):
        for id,c in DATA['characters'].items():
            x=[p['name'] for p in c['parts']]
            self.assertEqual(len(x),len(set(x)),id)
    def test_24_all_groups_pose4(self):
        for c in DATA['characters'].values():self.assertEqual(set(c['pose_offsets']),{'idle','tap','win','loss'})
    def test_25_silhouette_text_individual(self):
        all_sil=[c['signature_silhouette'] for c in DATA['characters'].values()]
        self.assertEqual(len(set(all_sil)),6)
        for c in DATA['characters'].values():self.assertGreaterEqual(len(c['signature_silhouette']),15)
    def test_26_all_parts_primitive_and_no_physics_spec(self):
        for c in DATA['characters'].values():
            for p in c['parts']:
                self.assertEqual(set(p),set(RULES['required_field_per_part']))
                self.assertIn(p['shape'],['Cylinder','Block','Ball'])
    def test_27_part_positions_not_all_identical(self):
        for id,c in DATA['characters'].items():self.assertGreater(len({tuple(p['position']) for p in c['parts']}),8,id)
    def test_28_color_palettes_distinct(self):
        all_palettes=[tuple(sorted(tuple(x) for x in c['palette'].values())) for c in DATA['characters'].values()]
        self.assertEqual(len(set(all_palettes)),6)
    def test_29_pinned_world_and_rarity(self):
        canon={x['id']:x for x in CANON['entries']}
        for id,c in DATA['characters'].items():
            for k in ('name','world','rarity','category'):self.assertEqual(c[k],canon[id][k])
    def test_30_generator_reproducible(self):
        self.assertEqual((ROOT/'src/D18BatchCatalog.luau').read_text(encoding='utf8'),g.generate())

class RuntimeContractStaticTests(unittest.TestCase):
    def test_31_factory_api_exposed(self):
        s=(ROOT/'src/D18BatchFactory.luau').read_text(encoding='utf8')
        for method in ('Build','SetPose','SetLod','SetYaw','GetStatus','Destroy'):
            self.assertIn('function Factory.'+method+'(',s)
    def test_32_requires_worldmodel(self):
        self.assertIn('parent:IsA("WorldModel")',(ROOT/'src/D18BatchFactory.luau').read_text(encoding='utf8'))
    def test_33_no_collision_touch_or_query(self):
        s=(ROOT/'src/D18BatchFactory.luau').read_text(encoding='utf8')
        for attr in ('CanCollide','CanTouch','CanQuery','CastShadow'):self.assertIn('p.'+attr+' = false',s)
    def test_34_anchored(self):self.assertIn('p.Anchored = true',(ROOT/'src/D18BatchFactory.luau').read_text(encoding='utf8'))
    def test_35_cap_max12(self):self.assertIn('MAX_ACTIVE = 12',(ROOT/'src/D18BatchFactory.luau').read_text(encoding='utf8'))
    def test_36_manual_yaw_45(self):self.assertIn('angle % 45 ~= 0',(ROOT/'src/D18BatchFactory.luau').read_text(encoding='utf8'))
    def test_37_demo_off(self):self.assertIn('local ENABLED = false',(ROOT/'src/DisabledPilotDemo.client.luau').read_text(encoding='utf8'))
    def test_38_rojo_only_source_modules_and_disabled_demo(self):
        x=J('default.project.json')['tree']['StarterPlayer']['StarterPlayerScripts']
        self.assertEqual(set(x)-{'$className'}, {'D18BatchCatalog','D18BatchFactory','DisabledPilotDemo'})
    def test_39_no_game_authority_patterns(self):
        source='\n'.join((ROOT/f).read_text(encoding='utf8') for f in ('src/D18BatchFactory.luau','src/DisabledPilotDemo.client.luau'))
        for bad in ('RemoteEvent','FireServer(','DataStoreService','MarketplaceService','TakeDamage(','Humanoid:','PublishAsync'):
            self.assertNotIn(bad,source)
    def test_40_manifest_strict_and_complete(self):
        self.assertEqual(v.check(),len(J('BUILD_MANIFEST.json')['files']))

class AdversarialMutantTests(unittest.TestCase):
    def check_reject(self,mod):
        a,b,c,d,e=map(copy.deepcopy,(DATA,RULES,CANON,QUEUE,CLAIMS))
        mod(a,b,c,d,e)
        with self.assertRaises((ValueError,KeyError,TypeError,AssertionError)):
            g.validate(a,b,c,d,e)
    def test_41_unknown_id(self):self.check_reject(lambda a,b,c,d,e:a['characters'].__setitem__('TRCA-BE-777',a['characters'].pop(IDS[0])))
    def test_42_no_model(self):self.check_reject(lambda a,b,c,d,e:a['characters'].pop(IDS[1]))
    def test_43_fake_name(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[2]].__setitem__('name','偽物'))
    def test_44_world_tamper(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[3]].__setitem__('world','OTHER'))
    def test_45_rarity_tamper(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[4]].__setitem__('rarity','UNVERIFIED'))
    def test_46_duplicate_name(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[0]]['parts'][0].__setitem__('name',a['characters'][IDS[0]]['parts'][1]['name']))
    def test_47_invisible_far_signature(self):
        def mut(a,b,c,d,e):
            model=a['characters'][IDS[0]]
            for p in model['parts']:
                if p['signature_tag']=='crescent_flukes':p['far']=False
        self.check_reject(mut)
    def test_48_unexpected_server_field(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[5]]['parts'][0].__setitem__('serverHitDamage',1000))
    def test_49_negative_size(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[2]]['parts'][0].__setitem__('size',[-1,1,1]))
    def test_50_large_position(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[3]]['parts'][0].__setitem__('position',[999,1,1]))
    def test_51_nan_rotation(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[0]]['parts'][0].__setitem__('rotation',[math.nan,0,0]))
    def test_52_bad_primitive(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[3]]['parts'][0].__setitem__('shape','MeshPart'))
    def test_53_invalid_rgb(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[4]]['palette'].__setitem__('sky',[9,300,90]))
    def test_54_no_loss_pose(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[1]]['pose_offsets'].pop('loss'))
    def test_55_bad_pose_group(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[4]]['pose_offsets']['tap'].__setitem__('UnknownGroup',{'dx':.1}))
    def test_56_excessive_pose_rotation(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[5]]['pose_offsets']['tap']['spring'].__setitem__('rz',99))
    def test_57_one_incorrect_category(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[5]].__setitem__('category','SP'))
    def test_58_missing_queue_id(self):self.check_reject(lambda a,b,c,d,e:d['groups']['BE'].pop())
    def test_59_duplicate_queue_id(self):self.check_reject(lambda a,b,c,d,e:d['groups']['BE'][0].__setitem__('id',d['groups']['BE'][1]['id']))
    def test_60_future_claim_false_positive(self):self.check_reject(lambda a,b,c,d,e:d['groups']['WE'][0].__setitem__('soft_claim','TAKEN'))
    def test_61_previous_source_reclaimed(self):self.check_reject(lambda a,b,c,d,e:e['new_3d_source_ids'].append(e['previous_3d_source_ids'][0]))
    def test_62_wrong_atlas_sha(self):self.check_reject(lambda a,b,c,d,e:a.__setitem__('source_atlas_sha256','0'*64))
    def test_63_unknown_signature_in_rule(self):self.check_reject(lambda a,b,c,d,e:b['archetypes']['TRAP_SIXFOLD_SNOW'].__setitem__('signature_tags',['fake']))
    def test_64_over_part_budget(self):
        def mod(a,b,c,d,e):
            q=a['characters'][IDS[2]]['parts']
            for i in range(31):
                x=copy.deepcopy(q[0]);x['name']='OVER_'+str(i);q.append(x)
        self.check_reject(mod)
    def test_65_no_soft_claim_proof(self):self.check_reject(lambda a,b,c,d,e:e.__setitem__('soft_claim_issue_url','none'))
    def test_66_duplicate_canon_id(self):self.check_reject(lambda a,b,c,d,e:c['entries'][1].__setitem__('id',c['entries'][0]['id']))
    def test_67_category_ownership_reversal(self):self.check_reject(lambda a,b,c,d,e:c['entries'][1].__setitem__('category','BE' if c['entries'][1]['category']!='BE' else 'SP'))
    def test_68_missing_far_parts(self):
        def mod(a,b,c,d,e):
            for p in a['characters'][IDS[3]]['parts']:
                p['far']=False
        self.check_reject(mod)
    def test_69_incorrect_source_budget_30(self):self.check_reject(lambda a,b,c,d,e:e.__setitem__('estimated_total_source_after_batch',31))
    def test_70_atlas_provenance_bad(self):self.check_reject(lambda a,b,c,d,e:a['characters'][IDS[0]]['provenance'].__setitem__('atlas_sha256','fake'))
    def test_71_synthetic_future_claim_needs_new_original_geometry(self):
        # An exploratory dry-run verifies extensibility only; the cloned shape is NOT a real, deliverable next character.
        a,b,c,d,e=map(copy.deepcopy,(DATA,RULES,CANON,QUEUE,CLAIMS))
        future=d['groups']['BE'].pop(0)
        cloned=copy.deepcopy(a['characters'][IDS[0]])
        for field in ('id','name','world','rarity'):cloned[field]=future[field]
        a['characters']={future['id']:cloned}
        b['archetypes']={cloned['archetype']:b['archetypes'][cloned['archetype']]}
        e['previous_3d_source_ids']=sorted(set(e['previous_3d_source_ids'])|set(IDS))
        e['new_3d_source_ids']=[future['id']]
        e['estimated_total_source_after_batch']=31
        d['previous_3d_source_ids']=e['previous_3d_source_ids'];d['current_batch_ids']=e['new_3d_source_ids']
        d['remaining_source_not_started_count']=41
        self.assertTrue(g.validate(a,b,c,d,e))


class Batch3OriginalArtGuarantees(unittest.TestCase):
    def test_72_prior24_unique_names_and_exact_canon(self):
        previous=set(CLAIMS['previous_3d_source_ids'])
        self.assertEqual(len(previous),24)
        self.assertTrue(previous<={r['id'] for r in CANON['entries']})
    def test_73_source_story_exact_original_atlas(self):
        canon={x['id']:x for x in CANON['entries']}
        for id,c in DATA['characters'].items():
            self.assertEqual(c['story'],canon[id]['original_story_hook'],id)
    def test_74_no_duplicate_part_sets(self):
        signatures=[]
        for c in DATA['characters'].values():
            signatures.append(tuple(sorted((p['shape'],tuple(p['position']),tuple(p['size']),p['signature_tag']) for p in c['parts'])))
        self.assertEqual(len(signatures),len(set(signatures)))
    def test_75_six_categories_cumulative_five_each(self):
        for cat in CATEGORIES:
            current=sum(id[5:7]==cat for id in IDS)
            previous=sum(id[5:7]==cat for id in CLAIMS['previous_3d_source_ids'])
            self.assertEqual((previous,current,previous+current),(4,1,5))
    def test_76_varied_visual_worlds(self):
        self.assertEqual(len({c['world'] for c in DATA['characters'].values()}),6)
    def test_77_visible_silhouette_parts_minimum_3(self):
        for id,c in DATA['characters'].items():
            for tag in c['signature_tags']:
                self.assertTrue(any(p['far'] and p['signature_tag']==tag for p in c['parts']),(id,tag))
    def test_78_all_mythic_legendary_exact_canon(self):
        self.assertTrue({c['rarity'] for c in DATA['characters'].values()} <= {'ミシック','レジェンド'})
    def test_79_no_audio_or_particle_auto_effect_in_factory(self):
        src=(ROOT/'src/D18BatchFactory.luau').read_text(encoding='utf8')
        for token in ('ParticleEmitter','SoundService','Sound:Play','FireServer','InvokeServer','Humanoid:','TeleportService','Instance.new("Humanoid")'):
            self.assertNotIn(token,src)
    def test_80_queue72_exhaustive_disjoint_partition(self):
        previous=set(CLAIMS['previous_3d_source_ids'])
        now=set(CLAIMS['new_3d_source_ids'])
        future={x['id'] for rows in QUEUE['groups'].values() for x in rows}
        self.assertFalse(previous&now or now&future or previous&future)
        self.assertEqual(len(previous|now|future),72)
    def test_81_reject_story_replacement_with_placeholder(self):
        a,b,c,d,e=map(copy.deepcopy,(DATA,RULES,CANON,QUEUE,CLAIMS))
        a['characters'][IDS[0]]['story']='x'
        with self.assertRaises(ValueError):g.validate(a,b,c,d,e)

if __name__=='__main__':unittest.main()
