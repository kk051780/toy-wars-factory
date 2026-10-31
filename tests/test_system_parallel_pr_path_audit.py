"""Protect multi-chat path selection without claiming exclusive file locks."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from system_parallel_pr_path_audit import audit

SHA = "a" * 40
OTHER = "b" * 40


def fixture():
    return {"schema": 1, "repository": "kk051780/toy-wars-factory", "base_sha": SHA,
            "collection_complete": True,
            "candidate": {"branch": "controller/scope-audit", "paths": ["tools/new_audit.py"]},
            "pulls": [{"number": 153, "repository": "kk051780/toy-wars-factory",
                       "base_branch": "main", "state": "open", "head_sha": OTHER,
                       "paths": ["tools/existing_probe.py"]}]}


class ParallelPrScopeAuditTests(unittest.TestCase):
    def test_unrelated_path_is_only_advisory_clear(self):
        result = audit(fixture())
        self.assertEqual(result["decision"], "CLEAR_ADVISORY")
        self.assertFalse(result["grant_write_authority"])
        self.assertFalse(result["source_authenticated"])

    def test_exact_file_collision_blocks(self):
        data = fixture()
        data["pulls"][0]["paths"] = ["tools/new_audit.py"]
        result = audit(data)
        self.assertEqual(result["decision"], "BLOCK_OVERLAP")
        self.assertEqual(result["collisions"][0]["pr"], 153)
        self.assertEqual(result["collisions"][0]["kind"], "EXACT")

    def test_case_fold_and_unicode_normalization_collide(self):
        data = fixture()
        data["candidate"]["paths"] = ["Tests/Café.py"]
        data["pulls"][0]["paths"] = ["tests/Cafe\u0301.py"]
        self.assertEqual(audit(data)["collisions"][0]["kind"], "CASE_OR_UNICODE")

    def test_renamed_old_path_can_be_passed_as_touched(self):
        data = fixture()
        data["pulls"][0]["paths"] = ["tools/new_audit.py", "tools/renamed.py"]
        self.assertEqual(audit(data)["decision"], "BLOCK_OVERLAP")

    def test_multiple_open_prs_are_stably_reported(self):
        data = fixture()
        data["pulls"].append(dict(data["pulls"][0], number=159, head_sha=SHA))
        data["pulls"][1]["paths"] = ["tools/new_audit.py"]
        data["pulls"][0]["paths"] = ["tools/new_audit.py"]
        self.assertEqual([x["pr"] for x in audit(data)["collisions"]], [153, 159])

    def test_empty_pr_inventory_does_not_confer_write_rights(self):
        data = fixture()
        data["pulls"] = []
        self.assertEqual(audit(data)["decision"], "CLEAR_ADVISORY")
        self.assertFalse(audit(data)["grant_write_authority"])

    def test_reject_incomplete_discovery_and_empty_pages(self):
        for mutate in [lambda d: d.update(collection_complete=False),
                       lambda d: d["pulls"][0].update(paths=[]),
                       lambda d: d["pulls"][0].pop("paths")]:
            data = fixture()
            mutate(data)
            with self.assertRaises(ValueError):
                audit(data)

    def test_reject_foreign_repo_and_malformed_base_branch(self):
        for field, value in [("repository", "attacker/repo"), ("base_branch", ""),
                             ("base_branch", "../escape"), ("base_branch", "a\\b")]:
            data = fixture()
            data["pulls"][0][field] = value
            with self.assertRaises(ValueError):
                audit(data)

    def test_stacked_pr_without_overlap_is_scanned_not_rejected(self):
        data = fixture()
        data["pulls"][0]["base_branch"] = "controller/parent-pr"
        result = audit(data)
        self.assertEqual(result["decision"], "CLEAR_ADVISORY")
        self.assertEqual(result["stacked_prs_checked"], 1)
        self.assertEqual(result["main_prs_checked"], 0)
        self.assertFalse(result["grant_write_authority"])

    def test_stacked_pr_file_collision_reports_its_base(self):
        data = fixture()
        data["pulls"][0]["base_branch"] = "controller/parent-pr"
        data["pulls"][0]["paths"] = ["tools/new_audit.py"]
        result = audit(data)
        self.assertEqual(result["decision"], "BLOCK_OVERLAP")
        self.assertEqual(result["collisions"][0]["base_branch"], "controller/parent-pr")
        self.assertTrue(result["collisions"][0]["stacked"])

    def test_mixed_main_and_stacked_prs_remain_fail_closed(self):
        data = fixture()
        data["pulls"].append(dict(data["pulls"][0], number=158,
                                  base_branch="controller/parent-2", paths=["tools/unrelated.py"]))
        result = audit(data)
        self.assertEqual((result["checked_open_prs"], result["main_prs_checked"],
                          result["stacked_prs_checked"]), (2, 1, 1))
        self.assertFalse(result["source_authenticated"])
        self.assertFalse(result["grant_write_authority"])

    def test_reject_closed_or_merge_complete_input(self):
        data = fixture()
        data["pulls"][0]["state"] = "closed"
        with self.assertRaises(ValueError):
            audit(data)

    def test_reject_duplicate_pr_number(self):
        data = fixture()
        data["pulls"].append(dict(data["pulls"][0]))
        with self.assertRaises(ValueError):
            audit(data)

    def test_reject_duplicate_candidate_path_even_case_only(self):
        data = fixture()
        data["candidate"]["paths"].append("Tools/New_Audit.py")
        with self.assertRaises(ValueError):
            audit(data)

    def test_reject_missing_sha_and_bool_pr_number(self):
        for field, value in [("head_sha", "short"), ("number", True)]:
            data = fixture()
            data["pulls"][0][field] = value
            with self.assertRaises(ValueError):
                audit(data)

    def test_reject_traversal_and_platform_separator(self):
        for name in ("../config/policy.json", "tools/../new_audit.py", "/src/a.py",
                     "tests\\x.py", "tools//a.py", "tools/.hidden/../a.py"):
            data = fixture()
            data["candidate"]["paths"] = [name]
            with self.assertRaises(ValueError, msg=name):
                audit(data)

    def test_reject_duplicate_pr_file_case_variant(self):
        data = fixture()
        data["pulls"][0]["paths"] = ["src/A.lua", "src/a.lua"]
        with self.assertRaises(ValueError):
            audit(data)

    def test_no_allowlist_or_metadata_unknowns_can_be_ignored(self):
        data = fixture()
        data["pulls"][0]["future_field"] = "lie"
        with self.assertRaises(ValueError):
            audit(data)

    def test_command_exit_codes(self):
        script = ROOT / "tools" / "system_parallel_pr_path_audit.py"
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "input.json"
            data = fixture()
            f.write_text(json.dumps(data))
            self.assertEqual(subprocess.run([sys.executable, script, "--input", str(f)],
                                            capture_output=True).returncode, 0)
            data["pulls"][0]["paths"] = ["tools/new_audit.py"]
            f.write_text(json.dumps(data))
            self.assertEqual(subprocess.run([sys.executable, script, "--input", str(f)],
                                            capture_output=True).returncode, 1)
            data["collection_complete"] = False
            f.write_text(json.dumps(data))
            result = subprocess.run([sys.executable, script, "--input", str(f)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("WAIT_METADATA", result.stdout)


if __name__ == "__main__":
    unittest.main()

# REST collection regressions: the converter is inert unless both GitHub
# snapshots agree. Synthetic API payloads are not provider authentication.
from system_parallel_pr_path_audit import from_rest_observations


def rest_fixture():
    first = [{
        'number': 147, 'state': 'open',
        'head': {'sha': OTHER, 'repo': {'full_name': 'kk051780/toy-wars-factory'}},
        'base': {'ref': 'main', 'repo': {'full_name': 'kk051780/toy-wars-factory'}},
    }]
    changed = {'147': [{'filename': 'tools/independent.py', 'status': 'added'}]}
    return dict(repository='kk051780/toy-wars-factory', main_before_sha=SHA,
                main_after_sha=SHA, candidate={'branch': 'controller/scope-audit',
                                               'paths': ['tools/new_audit.py']},
                prs_before=first, prs_after=json.loads(json.dumps(first)),
                changed_files_by_pr=changed)


class ParallelPrRestObservationTests(unittest.TestCase):
    def test_real_style_payload_converts_and_remains_advisory(self):
        item = rest_fixture()
        item['prs_before'][0]['base']['ref'] = 'controller/stack-parent'
        item['prs_after'][0]['base']['ref'] = 'controller/stack-parent'
        envelope = from_rest_observations(**item)
        result = audit(envelope)
        self.assertEqual((result['checked_open_prs'], result['stacked_prs_checked']), (1, 1))
        self.assertEqual(result['decision'], 'CLEAR_ADVISORY')
        self.assertFalse(result['source_authenticated'])

    def test_renamed_old_filename_detects_candidate_collision(self):
        item = rest_fixture()
        item['changed_files_by_pr']['147'] = [{
            'filename': 'tools/moved.py', 'status': 'renamed',
            'previous_filename': 'tools/new_audit.py'}]
        self.assertEqual(audit(from_rest_observations(**item))['decision'], 'BLOCK_OVERLAP')

    def test_case_only_rename_same_record_is_not_duplicate_metadata(self):
        item = rest_fixture()
        item['candidate']['paths'] = ['tools/HERE.py']
        item['changed_files_by_pr']['147'] = [{
            'filename': 'tools/here.py', 'status': 'renamed',
            'previous_filename': 'tools/HERE.py'}]
        self.assertEqual(audit(from_rest_observations(**item))['decision'], 'BLOCK_OVERLAP')

    def test_reject_head_change_between_collection_and_recheck(self):
        item = rest_fixture()
        item['prs_after'][0]['head']['sha'] = SHA
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_main_change_during_collection(self):
        item = rest_fixture()
        item['main_after_sha'] = OTHER
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_open_pr_arrivals_or_departures(self):
        item = rest_fixture()
        item['prs_after'] = []
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_truncated_pr_page_at_exact_page_limit(self):
        item = rest_fixture()
        item['prs_before'] = item['prs_before'] * 100
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_truncated_file_page_at_exact_page_limit(self):
        item = rest_fixture()
        item['changed_files_by_pr']['147'] *= 100
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_missing_files_by_pr_and_extra_stale_file_lists(self):
        item = rest_fixture()
        item['changed_files_by_pr'] = {}
        with self.assertRaises(ValueError):
            from_rest_observations(**item)
        item = rest_fixture()
        item['changed_files_by_pr']['148'] = [{'filename':'tools/extra.py', 'status':'added'}]
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_bad_rename_metadata(self):
        item = rest_fixture()
        item['changed_files_by_pr']['147'] = [{
            'filename': 'tools/moved.py', 'status': 'renamed'}]
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_duplicate_independent_file_record_while_allowing_case_rename(self):
        item = rest_fixture()
        item['changed_files_by_pr']['147'] = [
            {'filename': 'tools/a.py', 'status': 'added'},
            {'filename': 'Tools/A.py', 'status': 'modified'},
        ]
        with self.assertRaises(ValueError):
            from_rest_observations(**item)

    def test_reject_fork_and_corrupted_base_repository(self):
        for field in ('head', 'base'):
            with self.subTest(field=field):
                item = rest_fixture()
                item['prs_before'][0][field]['repo']['full_name'] = 'untrusted/fork'
                item['prs_after'][0][field]['repo']['full_name'] = 'untrusted/fork'
                with self.assertRaises(ValueError):
                    from_rest_observations(**item)


class PrefixTreeCollisionRegressionTests(unittest.TestCase):
    """A file path and its directory descendants cannot coexist in Git."""

    def test_candidate_parent_then_child_rejected(self):
        d = fixture()
        d['candidate']['paths'] = ['tools/cache', 'tools/cache/item.py']
        with self.assertRaisesRegex(ValueError, 'file/directory path collision'):
            audit(d)

    def test_candidate_child_then_parent_rejected(self):
        d = fixture()
        d['candidate']['paths'] = ['tools/cache/item.py', 'tools/cache']
        with self.assertRaisesRegex(ValueError, 'file/directory path collision'):
            audit(d)

    def test_candidate_prefix_casefold_rejected(self):
        d = fixture()
        d['candidate']['paths'] = ['Tools/CACHE', 'tools/cache/item.py']
        with self.assertRaises(ValueError):
            audit(d)

    def test_candidate_prefix_unicode_nfc_rejected(self):
        d = fixture()
        d['candidate']['paths'] = ['docs/Café', 'docs/Cafe\u0301/item.md']
        with self.assertRaises(ValueError):
            audit(d)

    def test_other_pr_parent_directory_blocks_candidate_file(self):
        d = fixture()
        d['pulls'][0]['paths'] = ['tools']
        x = audit(d)
        self.assertEqual(x['decision'], 'BLOCK_OVERLAP')
        self.assertEqual(x['collisions'][0]['kind'], 'PATH_PREFIX')
        self.assertEqual(x['collisions'][0]['existing_path'], 'tools')
        self.assertFalse(x['grant_write_authority'])

    def test_other_pr_child_file_blocks_candidate_parent(self):
        d = fixture()
        d['pulls'][0]['paths'] = ['tools/new_audit.py/other.py']
        x = audit(d)
        self.assertEqual(x['decision'], 'BLOCK_OVERLAP')
        self.assertEqual(x['collisions'][0]['kind'], 'PATH_PREFIX')
        self.assertFalse(x['source_authenticated'])

    def test_prefix_must_be_component_boundary(self):
        d = fixture()
        d['pulls'][0]['paths'] = ['tools/new_audit.py2']
        self.assertEqual(audit(d)['decision'], 'CLEAR_ADVISORY')

    def test_prefix_casefold_and_nfc_across_prs(self):
        d = fixture()
        d['candidate']['paths'] = ['Tests/Café']
        d['pulls'][0]['paths'] = ['tests/cafe\u0301/suite.py']
        x = audit(d)
        self.assertEqual(x['collisions'][0]['kind'], 'PATH_PREFIX')
        self.assertEqual(x['decision'], 'BLOCK_OVERLAP')

    def test_stacked_pr_prefix_is_visible(self):
        d = fixture()
        d['pulls'][0]['base_branch'] = 'controller/staged-parent'
        d['pulls'][0]['paths'] = ['tools']
        x = audit(d)
        self.assertTrue(x['collisions'][0]['stacked'])
        self.assertEqual(x['stacked_prs_checked'], 1)
        self.assertEqual(x['collisions'][0]['kind'], 'PATH_PREFIX')

    def test_one_existing_parent_reports_each_distinct_child(self):
        d = fixture()
        d['candidate']['paths'] = ['tools/a.py', 'tools/b.py']
        d['pulls'][0]['paths'] = ['tools']
        x = audit(d)
        self.assertEqual(len(x['collisions']), 2)
        self.assertEqual([y['candidate_path'] for y in x['collisions']],
                         ['tools/a.py', 'tools/b.py'])

    def test_rest_rename_old_parent_path_is_checked(self):
        d = rest_fixture()
        d['changed_files_by_pr']['147'] = [{
            'filename': 'tools/new_path.py', 'status': 'renamed',
            'previous_filename': 'tools',
        }]
        x = audit(from_rest_observations(**d))
        self.assertEqual(x['decision'], 'BLOCK_OVERLAP')
        self.assertEqual(x['collisions'][0]['kind'], 'PATH_PREFIX')

    def test_unrelated_paths_remain_advisory_without_authority(self):
        d = fixture()
        d['candidate']['paths'] = ['tools/x/item.py']
        d['pulls'][0]['paths'] = ['tools/y/item.py']
        x = audit(d)
        self.assertEqual(x['decision'], 'CLEAR_ADVISORY')
        self.assertFalse(x['grant_write_authority'])
        self.assertFalse(x['source_authenticated'])
