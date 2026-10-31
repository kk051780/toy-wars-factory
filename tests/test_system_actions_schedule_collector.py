"""Adversarial-only tests of read-only GitHub callback page normalization."""
from __future__ import annotations
import copy
import unittest
from tools import system_actions_schedule_collector as m
from tools import system_actions_schedule_cadence as a

REPO = 'kk051780/toy-wars-factory'
H = '.github/workflows/handoff-sync.yml'
W = '.github/workflows/loop-watchdog.yml'
WINDOW = dict(observed_at='2026-10-31T02:05:00Z',
              window_start='2026-10-31T00:00:00Z',
              window_end='2026-10-31T02:00:00Z')

def binding():
    return {'repository':REPO,'workflows':[
        {'path':H,'minute_offsets':[13,33,53],'branch':'main'},
        {'path':W,'minute_offsets':[7,27,47],'branch':'main'}]}

def run(rid, *, path=H, created_at='2026-10-31T01:53:28Z', **changes):
    item={'id':rid,'event':'schedule','path':path,'head_branch':'main',
          'head_sha':'e'*40,'run_attempt':1,'created_at':created_at,
          'status':'completed','conclusion':'success',
          'repository':{'full_name':REPO,'id':1431683395},
          'head_repository':{'full_name':REPO,'id':1431683395},
          'url':f'https://api.github.com/repos/{REPO}/actions/runs/{rid}',
          'actor':{'login':'kk051780'},'secrets':{'token':'DONOTLOG'}}
    item.update(changes)
    return item

def collect(rows, *, total=None, extra_pages=(), policy=None):
    if total is None:total=len(rows)
    calls=[]
    def reader(url):
        calls.append(url)
        page=int(url.rsplit('page=',1)[1]);source=[rows]+list(extra_pages)
        return {'total_count':total,'workflow_runs':source[page-1]}
    result=m.collect_and_analyze(reader,expected_repository=REPO,binding=binding() if policy is None else policy,**WINDOW)
    return result,calls

class CollectorTests(unittest.TestCase):
    def test_two_live_shapes_counts_without_authentication(self):
        x,urls=collect([run(110,path=H),run(111,path=W)])
        self.assertEqual(x['workflows'][H]['observed_schedule_runs'],1)
        self.assertEqual(x['workflows'][W]['observed_schedule_runs'],1)
        self.assertEqual(x['read_pages'],1)
        self.assertEqual(urls,[f'https://api.github.com/repos/{REPO}/actions/runs?event=schedule&per_page=100&page=1']*2)
        self.assertEqual(x['collection_method'],m.PROVENANCE)
        self.assertEqual(x['source_verification'],'UNTRUSTED_INPUT_ONLY')
        self.assertFalse(x['historical_cron_source_authenticated'])
        self.assertFalse(x['origin_run_details_authenticated'])
        self.assertTrue(all(v is False for v in x['authority'].values()))
    def test_zero_records_uses_one_get(self):
        x,urls=collect([])
        self.assertEqual(len(urls),2)
        self.assertEqual(x['run_count_in_pages'],0)
        self.assertEqual(x['workflows'][H]['observed_schedule_runs'],0)
    def test_complete_two_page_order_and_ids(self):
        rows=[run(i+1,path=H if i%2 else W) for i in range(100)]
        next_rows=[run(101,path=H),run(102,path=W)]
        x,urls=collect(rows,total=102,extra_pages=[next_rows])
        self.assertEqual(x['run_count_in_pages'],102)
        self.assertEqual(x['read_pages'],2)
        self.assertEqual(len(urls),4)
        self.assertEqual(x['get_requests'],4)
        self.assertTrue(x['stable_two_pass_comparison'])
        self.assertEqual(x['workflows'][H]['observed_schedule_runs'],51)
        self.assertEqual(x['workflows'][W]['observed_schedule_runs'],51)
    def test_ten_page_hard_cap_proven(self):
        pages=[[run(i+1) for i in range(j*100,(j+1)*100)] for j in range(10)]
        result,calls=collect(pages[0],total=1000,extra_pages=pages[1:])
        self.assertEqual(result['read_pages'],10)
        self.assertEqual(len(calls),20)
    def test_more_than_ten_pages_denied_without_more_calls(self):
        calls=[]
        def reader(url):calls.append(url);return {'total_count':1001,'workflow_runs':[]}
        with self.assertRaisesRegex(a.CadenceError,'INVALID_OR_UNBOUNDED_TOTAL'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),**WINDOW)
        self.assertEqual(len(calls),1)
    def test_short_first_page_blocked(self):
        with self.assertRaisesRegex(a.CadenceError,'INCOMPLETE_PAGE'):
            collect([run(1)],total=101)
    def test_short_last_page_blocked(self):
        rows=[run(i+1) for i in range(100)]
        with self.assertRaisesRegex(a.CadenceError,'INCOMPLETE_PAGE'):
            collect(rows,total=102,extra_pages=[[run(101)]])
    def test_mutating_total_denied(self):
        rows=[run(i+1) for i in range(100)]
        def reader(url):
            p=int(url.rsplit('page=',1)[1]);return {'total_count':101 if p==1 else 102,
                                                       'workflow_runs':rows if p==1 else [run(101)]}
        with self.assertRaisesRegex(a.CadenceError,'PAGE_COUNT_CHANGED'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),**WINDOW)
    def test_overlapping_page_id_denied(self):
        rows=[run(i+1) for i in range(100)]
        with self.assertRaisesRegex(a.CadenceError,'PAGINATION_DUPLICATE_RUN'):
            collect(rows,total=101,extra_pages=[[run(1)]])
    def test_malformed_page_blocked(self):
        for bad in [None,[],{}, {'workflow_runs':[]},{'total_count':0},
                    {'total_count':0,'workflow_runs':{}}]:
            with self.subTest(bad=str(bad)),self.assertRaises(a.CadenceError):
                m.collect_and_analyze(lambda url:bad,expected_repository=REPO,binding=binding(),**WINDOW)
    def test_missing_reader_blocked(self):
        with self.assertRaisesRegex(a.CadenceError,'SOURCE_READER_MISSING'):
            m.collect_and_analyze(None,expected_repository=REPO,binding=binding(),**WINDOW)
    def test_reader_exception_sanitized_no_token(self):
        def bad(_):raise RuntimeError('TOKEN=SECRET_123')
        with self.assertRaisesRegex(a.CadenceError,'SOURCE_GET_FAILED') as err:
            m.collect_and_analyze(bad,expected_repository=REPO,binding=binding(),**WINDOW)
        self.assertNotIn('SECRET_123',str(err.exception))
    def test_foreign_repository_rejected(self):
        with self.assertRaisesRegex(a.CadenceError,'FOREIGN_SOURCE_REPOSITORY'):
            collect([run(1,repository={'full_name':'evil/repo'})])
    def test_foreign_head_repository_rejected(self):
        with self.assertRaisesRegex(a.CadenceError,'FOREIGN_SOURCE_REPOSITORY'):
            collect([run(1,head_repository={'full_name':'evil/repo'})])
    def test_null_head_repository_rejected(self):
        with self.assertRaisesRegex(a.CadenceError,'FOREIGN_SOURCE_REPOSITORY'):
            collect([run(1,head_repository=None)])
    def test_run_url_redirect_rejected(self):
        with self.assertRaisesRegex(a.CadenceError,'WRONG_RUN_URL'):
            collect([run(1,url='https://untrusted.example/1')])
    def test_user_inserted_unexpected_workflow_rejected(self):
        with self.assertRaisesRegex(a.CadenceError,'FOREIGN_WORKFLOW'):
            collect([run(1,path='.github/workflows/unknown.yml')])
    def test_run_attempt_2_does_not_count_as_new_schedule_delivery(self):
        with self.assertRaisesRegex(a.CadenceError,'RETRIED_RUN_AMBIGUITY'):
            collect([run(1,run_attempt=2)])
    def test_bad_id_shapes_denied(self):
        for bad in [True,'42',-3,2**63,None]:
            with self.subTest(x=bad),self.assertRaisesRegex(a.CadenceError,'INVALID_RAW_RUN'):
                collect([run(bad)])
    def test_non_schedule_event_denied_by_analyzer(self):
        with self.assertRaisesRegex(a.CadenceError,'FOREIGN_OR_INVALID_RUN'):
            collect([run(1,event='workflow_dispatch')])
    def test_queued_run_not_a_success(self):
        x,_=collect([run(1,status='queued',conclusion=None)])
        self.assertEqual(x['workflows'][H]['outcomes']['nonterminal'],1)
    def test_bad_run_created_time_rejected(self):
        with self.assertRaisesRegex(a.CadenceError,'INVALID_TIME'):
            collect([run(1,created_at='bad')])
    def test_invalid_binding_prevents_api_get(self):
        calls=[]
        def reader(url):calls.append(url);return {'total_count':0,'workflow_runs':[]}
        b=binding();b['workflows'][0]['minute_offsets']=[13,13]
        with self.assertRaisesRegex(a.CadenceError,'INVALID_CRON'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=b,**WINDOW)
        self.assertFalse(calls)
    def test_foreign_binding_prevents_api_get(self):
        calls=[]
        def reader(url):calls.append(url);return {'total_count':0,'workflow_runs':[]}
        b=binding();b['repository']='evil/repo'
        with self.assertRaisesRegex(a.CadenceError,'REPOSITORY_BINDING_MISMATCH'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=b,**WINDOW)
        self.assertFalse(calls)
    def test_binding_path_traversal_denied(self):
        calls=[]
        def reader(url):calls.append(url);return {'total_count':0,'workflow_runs':[]}
        b=binding();b['workflows'][0]['path']='.github/workflows/../../evil.yml'
        with self.assertRaisesRegex(a.CadenceError,'INVALID_WORKFLOW'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=b,**WINDOW)
        self.assertFalse(calls)
    def test_future_window_denied_without_get(self):
        calls=[]
        def reader(url):calls.append(url);return {'total_count':0,'workflow_runs':[]}
        with self.assertRaisesRegex(a.CadenceError,'INVALID_WINDOW'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),observed_at='2026-10-30T00:00:00Z',
                                  window_start=WINDOW['window_start'],window_end=WINDOW['window_end'])
        self.assertFalse(calls)
    def test_secret_fields_not_copied_or_returned(self):
        x,_=collect([run(1, actor={'login':'SECRET_CUSTOM'}, secrets={'token':'SECRET_NEVER_ECHO'})])
        self.assertNotIn('SECRET_NEVER_ECHO',str(x))
        self.assertNotIn('SECRET_CUSTOM',str(x))
    def test_source_input_not_mutated(self):
        rows=[run(1)];before=copy.deepcopy(rows)
        collect(rows)
        self.assertEqual(rows,before)
    def test_invalid_result_total_type_denied(self):
        with self.assertRaisesRegex(a.CadenceError,'INVALID_OR_UNBOUNDED_TOTAL'):
            collect([],total=True)
    def test_empty_page_when_total_zero(self):
        x,_=collect([],total=0)
        self.assertEqual(x['workflows'][W]['configured_cron_slots'],6)

    def test_first_page_replaced_same_count_denied(self):
        calls=[]
        def reader(url):
            calls.append(url)
            return {'total_count':1,'workflow_runs':[run(1 if len(calls)==1 else 2)]}
        with self.assertRaisesRegex(a.CadenceError,'PAGINATION_SNAPSHOT_CHANGED'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),**WINDOW)
        self.assertEqual(len(calls),2)

    def test_same_run_id_changing_outcome_denied(self):
        calls=[]
        def reader(url):
            calls.append(url)
            return {'total_count':1,'workflow_runs':[run(1,conclusion='success' if len(calls)==1 else 'failure')]}
        with self.assertRaisesRegex(a.CadenceError,'PAGINATION_SNAPSHOT_CHANGED'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),**WINDOW)

    def test_same_total_count_changed_on_second_walk_denied(self):
        calls=[]
        def reader(url):
            calls.append(url)
            return {'total_count':1 if len(calls)==1 else 2,'workflow_runs':[run(1)]}
        with self.assertRaisesRegex(a.CadenceError,'PAGE_COUNT_CHANGED'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),**WINDOW)

    def test_second_page_changes_without_top_page_change_denied(self):
        calls=[]
        p1=[run(i) for i in range(1,101)]
        def reader(url):
            calls.append(url)
            page=int(url.rsplit('page=',1)[1]);walk=(len(calls)-1)//2
            if page==1:return {'total_count':101,'workflow_runs':p1}
            return {'total_count':101,'workflow_runs':[run(101 if walk==0 else 102)]}
        with self.assertRaisesRegex(a.CadenceError,'PAGINATION_SNAPSHOT_CHANGED'):
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),**WINDOW)
        self.assertEqual(len(calls),4)

    def test_repeat_walk_same_source_confirmed_but_not_provider_authenticated(self):
        x,urls=collect([run(1),run(2,path=W)])
        self.assertEqual(x['get_requests'],2)
        self.assertTrue(x['stable_two_pass_comparison'])
        self.assertEqual(x['source_verification'],'UNTRUSTED_INPUT_ONLY')
        self.assertFalse(x['authority']['provider_authenticated'])

    def test_replay_second_pass_failure_sanitized(self):
        seen=[]
        def reader(url):
            seen.append(url)
            if len(seen)>1:raise RuntimeError('SUPER_SECRET_IN_ERROR')
            return {'total_count':1,'workflow_runs':[run(1)]}
        with self.assertRaisesRegex(a.CadenceError,'SOURCE_GET_FAILED') as err:
            m.collect_and_analyze(reader,expected_repository=REPO,binding=binding(),**WINDOW)
        self.assertNotIn('SUPER_SECRET_IN_ERROR',str(err.exception))

    def test_no_automatic_calls_to_github_on_import(self):
        self.assertFalse(hasattr(m,'urlopen'))
        self.assertFalse(hasattr(m,'requests'))

if __name__=='__main__':unittest.main()