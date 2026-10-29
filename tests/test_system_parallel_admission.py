"""Portable negative cases for read-only planner only; NOT live coordinator tests."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "tools" / "system_parallel_admission.py"
spec = importlib.util.spec_from_file_location("system_parallel_admission", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def item(work="GAME_A001", goal="a", mode="SOURCE_WRITE", paths=None, **overrides):
    o = dict(project_id="toy-wars-factory", repository="kk051780/toy-wars-factory",
             work_id=work, goal_sha256=goal * 64, mode=mode,
             write_paths=paths if paths is not None else ["src/ToyWarsServer.server.lua"],
             shared_resources=[], complete_manifest=True, origin="REGISTERED_TASK_CLAIMED")
    o.update(overrides)
    return o


class AdmissionTests(unittest.TestCase):
    def status(self, current, jobs=None):
        return mod.advise(current, jobs or [item()])["status"]

    def test_same_work_id_join(self): self.assertEqual(self.status(item()), "JOIN_EXISTING")
    def test_same_goal_different_work_id_join(self): self.assertEqual(self.status(item(work="GAME_A002")), "JOIN_EXISTING")
    def test_repeated_goal_join(self): self.assertEqual(self.status(item(work="GAME_A002"), [item(), item()]), "JOIN_EXISTING")
    def test_distinct_project_same_goal_is_not_duplicate(self):
        self.assertEqual(self.status(item(work="GAME_A002", project_id="other-game", paths=["src/separate.lua"])), "CANDIDATE_FOR_AUTHENTICATED_CAS")
    def test_distinct_project_same_repo_file_still_conflicts(self):
        self.assertEqual(self.status(item(work="GAME_A002", project_id="other-game", goal="b")), "WAIT_CONFLICT")
    def test_same_work_id_different_goal_is_not_join(self):
        self.assertEqual(self.status(item(work="GAME_A001", goal="b")), "BLOCKED_WORK_ID_CONFLICT")
    def test_unrelated_repo_incomplete_manifest_does_not_block(self):
        foreign = item(repository="other/repo", complete_manifest=False)
        self.assertEqual(self.status(item(work="GAME_B002",goal="b",paths=["src/separate.lua"]),[foreign]),"CANDIDATE_FOR_AUTHENTICATED_CAS")
    def test_distinct_repo_same_goal_is_not_duplicate(self):
        self.assertEqual(self.status(item(work="GAME_A002", repository="another/repo")), "CANDIDATE_FOR_AUTHENTICATED_CAS")
    def test_identical_write_path_blocked(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b")), "WAIT_CONFLICT")
    def test_case_alias_path_blocked(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["SRC/toywarSserver.server.lua"])), "WAIT_CONFLICT")
    def test_parent_directory_collision(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["src"])), "WAIT_CONFLICT")
    def test_unrelated_paths_candidate_only(self):
        r = mod.advise(item(work="GAME_B002", goal="b", paths=["tests/auto/independent_spec.lua"]), [item()])
        self.assertEqual(r["status"], "CANDIDATE_FOR_AUTHENTICATED_CAS")
        self.assertFalse(r["may_write"])
    def test_shared_generated_resource_blocked(self):
        a = item(shared_resources=["source-ledger"])
        b = item(work="GAME_B002", goal="b", paths=["tests/auto/new_spec.lua"], shared_resources=["source-ledger"])
        self.assertEqual(self.status(b, [a]), "WAIT_CONFLICT")
    def test_disjoint_generated_resource_candidate(self):
        a = item(shared_resources=["game-a"])
        b = item(work="GAME_B002", goal="b", paths=["tests/auto/new_spec.lua"], shared_resources=["game-b"])
        self.assertEqual(self.status(b, [a]), "CANDIDATE_FOR_AUTHENTICATED_CAS")
    def test_top_level_governance_files_are_protected(self):
        for path in ("AGENTS.md", "PROJECT_STATE.json", "agents.MD", "project_state.JSON"):
            with self.subTest(path=path):
                self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=[path])), "WAIT_PROTECTED_SCOPE")

    def test_protected_config_wait(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["config/autonomous_repair.json"])), "WAIT_PROTECTED_SCOPE")
    def test_protected_history_wait(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["history/C00130.json"])), "WAIT_PROTECTED_SCOPE")
    def test_protected_workflow_wait(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=[".github/workflows/qa.yml"])), "WAIT_PROTECTED_SCOPE")
    def test_incomplete_manifest_wait(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["tests/z.py"], complete_manifest=False)), "WAIT_INCOMPLETE_MANIFEST")
    def test_incomplete_existing_wait(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["tests/z.py"]), [item(complete_manifest=False)]), "WAIT_INCOMPLETE_MANIFEST")
    def test_chat_unattested_wait(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["tests/z.py"], origin="CHAT_UNVERIFIED")), "WAIT_UNATTESTED_AUTHOR")
    def test_read_only_can_parallelize(self):
        x = item(work="GAME_B002", goal="b", mode="READ_ONLY", paths=[], origin="CHAT_UNVERIFIED")
        self.assertEqual(self.status(x), "READ_ONLY_PARALLEL")
    def test_read_only_cannot_claim_writes(self):
        x = item(work="GAME_B002", goal="b", mode="READ_ONLY", paths=["src/new.lua"])
        self.assertEqual(self.status(x), "BLOCKED_UNSAFE_INPUT")
    def test_invalid_path_traversal(self):
        for p in ["../src/unsafe.lua", "src/../bad.lua", "src//bad.lua", "/etc/passwd", "src\\bad.lua", "src/./bad.lua", "src/bad%2Flua", "src/evil*.lua", ".git/config", "src/bad. "]:
            with self.subTest(p=p):
                self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=[p])), "BLOCKED_UNSAFE_INPUT")
    def test_invalid_unicode_non_nfc(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["src/cafe\u0301.lua"])), "BLOCKED_UNSAFE_INPUT")
    def test_invalid_duplicated_manifest(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["src/NEW.lua", "src/new.lua"])), "BLOCKED_UNSAFE_INPUT")
    def test_invalid_goal(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="bad", paths=["src/new.lua"])), "BLOCKED_UNSAFE_INPUT")
    def test_invalid_record_keys(self):
        x = item(work="GAME_B002", goal="b", paths=["src/new.lua"]);x["hack"] = True
        self.assertEqual(self.status(x), "BLOCKED_UNSAFE_INPUT")
    def test_unknown_origin(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["src/new.lua"], origin="IM_PERSON")), "BLOCKED_UNSAFE_INPUT")
    def test_invalid_manifest_type(self):
        self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=["src/new.lua"], complete_manifest="yes")), "BLOCKED_UNSAFE_INPUT")
    def test_git_control_files_are_protected(self):
        for path in (".gitmodules", ".gitattributes", ".gitignore", "AGENTS.md/fake", "PROJECT_STATE.json/fake"):
            with self.subTest(path=path):
                self.assertEqual(self.status(item(work="GAME_B002", goal="b", paths=[path])), "WAIT_PROTECTED_SCOPE")

    def test_no_write_permission_ever(self):
        for jobs in [[], [item()]]:
            for mode in ["READ_ONLY", "SOURCE_WRITE"]:
                x=item(work="GAME_B002", goal="b", mode=mode, paths=[] if mode=="READ_ONLY" else ["src/other.lua"])
                self.assertFalse(mod.advise(x, jobs)["may_write"])
    def test_unhashable_mode_fails_closed(self):
        for bad in ([], {}, {"value": "SOURCE_WRITE"}):
            with self.subTest(bad=bad):
                self.assertEqual(self.status(item(work="GAME_B002", goal="b", mode=bad)), "BLOCKED_UNSAFE_INPUT")

    def test_unhashable_origin_fails_closed(self):
        for bad in ([], {}, {"value": "REGISTERED_TASK_CLAIMED"}):
            with self.subTest(bad=bad):
                self.assertEqual(self.status(item(work="GAME_B002", goal="b", origin=bad)), "BLOCKED_UNSAFE_INPUT")

    def test_ambiguous_writer_scope_fails_closed(self):
        for bad in (42, None, {"path": "src/file.lua"}, True):
            with self.subTest(bad=bad):
                x = item(work="GAME_B002", goal="b")
                x["write_paths"] = bad
                self.assertEqual(self.status(x), "BLOCKED_UNSAFE_INPUT")

    def test_malformed_active_ledger_rows_fails_closed(self):
        for bad in (None, [], 42, "active", {"work_id": "GAME_A001"}):
            with self.subTest(bad=bad):
                self.assertEqual(mod.advise(item(work="GAME_B002",goal="b",paths=["src/other.lua"]), [bad])["status"], "BLOCKED_UNSAFE_INPUT")

    def test_unknown_active_ledger_blocks(self):
        self.assertEqual(mod.advise(item(work="GAME_B002", goal="b"), None)["status"], "BLOCKED_UNSAFE_INPUT")

class MainPortHardeningTests(unittest.TestCase):
    def candidate(self, **kwargs):
        return item(work='GAME_B002', goal='b', paths=['src/independent.lua'], **kwargs)

    def test_protected_parent_and_control_plane(self):
        for path in ('tools', 'tools/check_meta_diff.py', 'tools/system_alert_notification.py',
                     '.env', '.env.production', '.gitconfig', '.cache/credentials'):
            with self.subTest(path=path):
                self.assertEqual(mod.advise(self.candidate(write_paths=[path]), [])['status'], 'WAIT_PROTECTED_SCOPE')

    def test_same_id_changed_scope_cannot_silent_join(self):
        for override in ({'write_paths':['src/renamed.lua']}, {'shared_resources':['new-schema']},
                         {'mode':'READ_ONLY','write_paths':[]}):
            with self.subTest(override=override):
                self.assertEqual(mod.advise(item(**override), [item()])['status'], 'BLOCKED_WORK_ID_CONFLICT')

    def test_contradictory_active_identity_blocks_unrelated_work(self):
        for row in (item(goal='c'), item(write_paths=['src/other.lua'])):
            with self.subTest(row=row):
                self.assertEqual(mod.advise(self.candidate(), [item(), row])['status'], 'BLOCKED_UNSAFE_INPUT')

    def test_ambiguous_platform_paths(self):
        for path in ('C:/game.lua', 'src/file:stream', 'src/name\u200b.lua',
                     'src/caf\u00e9.lua', 'src/name\u007f.lua', 'src/name space.lua'):
            with self.subTest(path=path):
                self.assertEqual(mod.advise(self.candidate(write_paths=[path]), [])['status'], 'BLOCKED_UNSAFE_INPUT')

    def test_invalid_repository_identity(self):
        for repo in ('./repo', 'owner/..', '-owner/repo', 'owner-/repo', 'owner/name.git', 'owner/'+'r'*101):
            with self.subTest(repo=repo):
                self.assertEqual(mod.advise(self.candidate(repository=repo), [])['status'], 'BLOCKED_UNSAFE_INPUT')

    def test_every_result_denies_authentication_and_execution(self):
        for candidate, active in ((self.candidate(), []), (item(), [item()]),
                (self.candidate(origin='CHAT_UNVERIFIED'), []),
                (self.candidate(mode='READ_ONLY',write_paths=[]), []), (self.candidate(), None)):
            with self.subTest(candidate=candidate):
                r=mod.advise(candidate,active)
                self.assertEqual(r.get('verification'), 'NOT_VERIFIED')
                self.assertEqual(r.get('mode'), 'READ_ONLY_ADMISSION')
                for key in ('may_write','may_run_now','github_cas_performed'):
                    self.assertIs(r.get(key),False)
                self.assertEqual(set(r['authority']), {'write_allowed','start_now_allowed','takeover_allowed',
                    'dispatch_allowed','merge_allowed','publish_allowed','external_spend_allowed','safe_to_next_schedule'})
                self.assertTrue(all(v is False for v in r['authority'].values()))


    def test_repository_case_alias_and_declared_rename_old_path_conflict(self):
        for paths in (['src/ToyWarsServer.server.lua'], ['src/new.lua','src/ToyWarsServer.server.lua']):
            self.assertEqual(mod.advise(self.candidate(repository='KK051780/TOY-WARS-FACTORY',write_paths=paths),
                                        [item()])['status'], 'WAIT_CONFLICT')

    def test_two_synthetic_games_preserve_repo_and_project_scope(self):
        factory=item(project_id='factory-demo',repository='studio/factory')
        puzzle=self.candidate(project_id='puzzle-demo',repository='studio/puzzle',
                              write_paths=['src/ToyWarsServer.server.lua'])
        self.assertEqual(mod.advise(puzzle,[factory])['status'], 'CANDIDATE_FOR_AUTHENTICATED_CAS')
        puzzle['repository']='studio/factory'
        self.assertEqual(mod.advise(puzzle,[factory])['status'], 'WAIT_CONFLICT')

    def test_supplied_authentication_fields_not_service_attestation(self):
        for key in ('provider_verified','task_id','run_id','write_allowed'):
            x=self.candidate();x[key]=True
            self.assertEqual(mod.advise(x,[])['status'], 'BLOCKED_UNSAFE_INPUT')

    def test_result_collections_never_alias_inputs(self):
        import copy
        candidate=self.candidate(write_paths=['src']);active=[item()]
        before=copy.deepcopy((candidate,active));r=mod.advise(candidate,active)
        r['path_collisions'].append('config')
        self.assertEqual((candidate,active),before)
        self.assertNotIn('config',mod.advise(candidate,active)['path_collisions'])

    def test_reordered_identical_scope_remains_idempotent_join(self):
        a=item(write_paths=['src/a.lua','src/b.lua'],shared_resources=['one','two'])
        b=item(write_paths=['src/b.lua','src/a.lua'],shared_resources=['two','one'])
        self.assertEqual(mod.advise(b,[a])['status'], 'JOIN_EXISTING')

    def test_untrusted_inputs_are_bounded(self):
        for candidate,active in ((self.candidate(),[item()]*201),
                (self.candidate(write_paths=['src/f'+str(i) for i in range(301)]),[]),
                (self.candidate(shared_resources=['r'+str(i) for i in range(101)]),[])):
            self.assertEqual(mod.advise(candidate,active)['status'],'BLOCKED_UNSAFE_INPUT')

    def test_incomplete_same_repo_scope_still_waits_across_project_labels(self):
        other=item(project_id='puzzle-demo',complete_manifest=False)
        self.assertEqual(mod.advise(self.candidate(),[other])['status'],'WAIT_INCOMPLETE_MANIFEST')

    def test_current_coordinator_or_work_requests_are_not_a_work_manifest(self):
        for wrong in ({'schema':1,'epoch':246,'holder':None},{'schema':1,'requests':[]}):
            self.assertEqual(mod.advise(self.candidate(),[wrong])['status'],'BLOCKED_UNSAFE_INPUT')



class ReviewJoinRegressionTests(unittest.TestCase):
    """Registered PR124 review regressions; real source, no copied planner."""

    def decision(self, candidate, active, expected):
        result = mod.advise(candidate, active)
        self.assertEqual(result["status"], expected)
        self.assertIs(result["may_write"], False)
        self.assertIs(result["may_run_now"], False)
        self.assertIs(result["github_cas_performed"], False)
        self.assertEqual(result["verification"], "NOT_VERIFIED")
        self.assertTrue(all(value is False for value in result["authority"].values()))
        return result

    def test_same_goal_different_work_changed_paths_fails_closed(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
        b = item(work="GAME_B001", goal="a", paths=["src/b.lua"])
        self.decision(b, [a], "BLOCKED_WORK_ID_CONFLICT")

    def test_same_goal_different_work_changed_shared_resources_fails_closed(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
        b = item(work="GAME_B001", goal="a", paths=["src/a.lua"], shared_resources=["changed-schema"])
        self.decision(b, [a], "BLOCKED_WORK_ID_CONFLICT")

    def test_same_goal_different_work_changed_mode_fails_closed(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
        b = item(work="GAME_B001", goal="a", mode="READ_ONLY", paths=[])
        self.decision(b, [a], "BLOCKED_WORK_ID_CONFLICT")

    def test_protected_writer_scope_checked_before_any_join(self):
        for path in ("config/autonomous_repair.json", "tools/check_meta_diff.py", "AGENTS.md"):
            for work in ("GAME_A001", "GAME_B001"):
                with self.subTest(path=path, work=work):
                    a = item(work="GAME_A001", goal="a", paths=[path])
                    b = item(work=work, goal="a", paths=[path])
                    self.decision(b, [a], "WAIT_PROTECTED_SCOPE")
            with self.subTest(path=path, scope="changed-protected"):
                a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
                b = item(work="GAME_B001", goal="a", paths=[path])
                self.decision(b, [a], "WAIT_PROTECTED_SCOPE")

    def test_duplicate_active_goal_cannot_return_multiple_join_targets(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
        b = item(work="GAME_B001", goal="a", paths=["src/b.lua"])
        c = item(work="GAME_C001", goal="a", paths=["src/c.lua"])
        self.decision(c, [a, b], "BLOCKED_UNSAFE_INPUT")

    def test_ambiguous_active_goal_blocks_even_an_unrelated_candidate(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
        b = item(work="GAME_B001", goal="a", paths=["src/b.lua"])
        c = item(work="GAME_C001", goal="c", paths=["src/c.lua"])
        self.decision(c, [a, b], "BLOCKED_UNSAFE_INPUT")

    def test_two_active_work_ids_with_same_goal_and_scope_still_ambiguous(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
        b = item(work="GAME_B001", goal="a", paths=["src/a.lua"])
        c = item(work="GAME_C001", goal="c", paths=["src/c.lua"])
        self.decision(c, [a, b], "BLOCKED_UNSAFE_INPUT")

    def test_unambiguous_same_goal_identical_normalized_scope_preserves_join(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua", "src/b.lua"],
                 shared_resources=["one", "two"])
        b = item(work="GAME_B001", goal="a", paths=["SRC/B.lua", "src/A.lua"],
                 shared_resources=["two", "one"])
        result = self.decision(b, [a], "JOIN_EXISTING")
        self.assertEqual(result["existing_work_ids"], ["GAME_A001"])

    def test_repeated_identical_canonical_row_is_idempotent(self):
        a = item(work="GAME_A001", goal="a", paths=["src/a.lua"])
        b = item(work="GAME_B001", goal="a", paths=["src/a.lua"])
        result = self.decision(b, [a, a], "JOIN_EXISTING")
        self.assertEqual(result["existing_work_ids"], ["GAME_A001"])

    def test_canonical_goal_isolation_across_project_and_repository(self):
        for repository in ("studio/factory", "studio/puzzle"):
            with self.subTest(repository=repository):
                a = item(work="GAME_A001", goal="a", paths=["src/a.lua"],
                         project_id="factory-demo", repository="studio/factory")
                b = item(work="GAME_B001", goal="a", paths=["src/b.lua"],
                         project_id="puzzle-demo", repository=repository)
                c = item(work="GAME_C001", goal="c", mode="READ_ONLY", paths=[])
                self.decision(c, [a, b], "READ_ONLY_PARALLEL")



if __name__ == "__main__": unittest.main()
