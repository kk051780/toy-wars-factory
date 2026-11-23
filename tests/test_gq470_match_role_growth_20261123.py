#!/usr/bin/env python3
"""Adversarial input and exact inverse tests using the genuine H93 artifact."""
import copy
import hashlib
import json
import stat
import subprocess
import sys
from unittest import mock
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / 'quality_gameplay/gq470_match_role_growth_20261123'
SPEC = importlib.util.spec_from_file_location('gq470_s1a_applier_tests', PACKAGE / 'apply_growth.py')
patcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(patcher)


class ExactCandidateInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get('GQ470_H93_ARTIFACT')
        if value is None:
            raise unittest.SkipTest('NOT_RUN: GQ470_H93_ARTIFACT is unset; genuine H93 artifact tests were not run')
        if not value.strip():
            raise RuntimeError('GQ470_H93_ARTIFACT must name the actual pinned H93 artifact; no synthetic fallback')
        cls.baseline = Path(value).resolve()
        cls.lock, cls.patch = patcher.load_contract()
        if patcher.source_snapshot(cls.baseline / 'sources') != cls.lock['sources_before']:
            raise RuntimeError('actual H93 source contract is required before any test')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gq470-s1a-test-')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def copy_input(self):
        source = self.root / 'input'
        shutil.copytree(self.baseline / 'sources', source / 'sources')
        shutil.copyfile(self.baseline / patcher.PROJECT, source / patcher.PROJECT)
        return source

    def test_actual_four_source_forward_and_full_inverse(self):
        on, off = self.root / 'on', self.root / 'off'
        forward = patcher.apply(self.baseline, on)
        inverse = patcher.apply(on, off, reverse=True)
        self.assertEqual(forward['changed_count'], 4)
        self.assertEqual(patcher.source_snapshot(off / 'sources'), self.lock['sources_before'])
        self.assertEqual((off / patcher.PROJECT).read_bytes(), (self.baseline / patcher.PROJECT).read_bytes())
        self.assertEqual({p.name for p in on.iterdir()}, {'sources', patcher.PROJECT, patcher.RECEIPT})
        self.assertFalse(inverse['formal_rc_adoption'])

    def test_modified_unchanged_host_rejected_before_output(self):
        source = self.copy_input()
        host = source / 'sources/ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau'
        host.write_bytes(host.read_bytes() + b'\n-- stale different host\n')
        output = self.root / 'output'
        with self.assertRaisesRegex(ValueError, 'ENTIRE69_INPUT_PROFILE'):
            patcher.apply(source, output)
        self.assertFalse(output.exists())

    def test_modified_selected_source_rejected_before_output(self):
        source = self.copy_input()
        swarm = source / 'sources/ServerScriptService/EGGRUMBLE_SwarmCombat.luau'
        swarm.write_bytes(swarm.read_bytes().replace(b'local', b' local', 1))
        with self.assertRaisesRegex(ValueError, 'ENTIRE69_INPUT_PROFILE'):
            patcher.apply(source, self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_existing_output_is_not_overwritten(self):
        output = self.root / 'output'
        output.mkdir()
        sentinel = output / 'sentinel'
        sentinel.write_bytes(b'preserve existing user data')
        with self.assertRaisesRegex(ValueError, 'OUTPUT_MUST_BE_NEW'):
            patcher.apply(self.baseline, output)
        self.assertEqual(sentinel.read_bytes(), b'preserve existing user data')
        self.assertEqual(len(list(output.iterdir())), 1)

    def test_extra_source_and_symlink_are_rejected(self):
        source = self.copy_input()
        extra = source / 'sources/unregistered.luau'
        extra.write_text('return true\n')
        with self.assertRaisesRegex(ValueError, 'ENTIRE69_INPUT_PROFILE'):
            patcher.apply(source, self.root / 'output')
        extra.unlink()
        extra.symlink_to(self.baseline / patcher.PROJECT)
        with self.assertRaisesRegex(ValueError, 'SOURCE_SYMLINK'):
            patcher.apply(source, self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_sources_root_symlink_rejected_before_output(self):
        source = self.root / 'input'
        source.mkdir()
        donor = self.root / 'donor_sources'
        shutil.copytree(self.baseline / 'sources', donor)
        (source / 'sources').symlink_to(donor, target_is_directory=True)
        shutil.copyfile(self.baseline / patcher.PROJECT, source / patcher.PROJECT)
        before = patcher.source_snapshot(donor)
        output = self.root / 'output'
        error = None
        try:
            patcher.apply(source, output)
        except ValueError as exc:
            error = str(exc)
        self.assertEqual(patcher.source_snapshot(donor), before)
        self.assertFalse(output.exists(), 'linked sources root must be rejected before writes')
        self.assertIsNotNone(error)
        self.assertIn('SYMLINK_ROOT', error)

    def test_sources_alias_output_overlap_rejected_before_input_mutation(self):
        source = self.root / 'input'
        source.mkdir()
        donor = self.root / 'donor_sources'
        shutil.copytree(self.baseline / 'sources', donor)
        (source / 'sources').symlink_to(donor, target_is_directory=True)
        shutil.copyfile(self.baseline / patcher.PROJECT, source / patcher.PROJECT)
        def raw_snapshot():
            return {path.relative_to(donor).as_posix(): path.read_bytes()
                    for path in donor.rglob('*') if path.is_file()}
        before = raw_snapshot()
        output = donor / 'nested_output'
        error = None
        try:
            patcher.apply(source, output)
        except ValueError as exc:
            error = str(exc)
        self.assertTrue(raw_snapshot() == before, 'read-only input tree was changed')
        self.assertFalse(output.exists(), 'aliased overlap must be rejected before writes')
        self.assertIsNotNone(error)
        self.assertIn('SYMLINK_ROOT', error)

    def test_nested_output_and_changed_project_are_rejected(self):
        source = self.copy_input()
        with self.assertRaisesRegex(ValueError, 'OVERLAPPING_INPUT_OUTPUT'):
            patcher.apply(source, source / 'nested')
        project = source / patcher.PROJECT
        project.write_bytes(project.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'PROJECT_CHANGED'):
            patcher.apply(source, self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_same_candidate_cannot_be_applied_twice(self):
        on = self.root / 'on'
        patcher.apply(self.baseline, on)
        with self.assertRaisesRegex(ValueError, 'ENTIRE69_INPUT_PROFILE'):
            patcher.apply(on, self.root / 'twice')
        self.assertFalse((self.root / 'twice').exists())

    def test_same_class_source_swap_is_rejected_at_exact_instance(self):
        native_spec = importlib.util.spec_from_file_location('gq470_s1a_native_tests', PACKAGE / 'native/run_growth.py')
        native = importlib.util.module_from_spec(native_spec)
        native_spec.loader.exec_module(native)
        original = self.baseline / 'EGGRUMBLE_REAL69_PRIVATE.rbxlx'
        native.verify_place(original, original, self.baseline / 'sources', self.baseline / 'sources')
        tree = ET.fromstring(original.read_bytes())
        sources = [item.find("Properties/*[@name='Source']")
                   for item in tree.iter('Item') if item.attrib.get('class') == 'ModuleScript']
        self.assertGreaterEqual(len(sources), 2)
        self.assertNotEqual(sources[0].text, sources[1].text)
        sources[0].text, sources[1].text = sources[1].text, sources[0].text
        swapped = self.root / 'same-class-source-swap.rbxlx'
        swapped.write_bytes(ET.tostring(tree))
        with self.assertRaisesRegex(ValueError, 'PLACE_INSTANCE_SOURCE_OR_STRUCTURE_CHANGED'):
            native.verify_place(swapped, original, self.baseline / 'sources', self.baseline / 'sources')


class HistoricalCapsuleInputs(unittest.TestCase):
    """Capsule boundaries run in discovery without the optional H93 artifact."""

    NATIVE_RELATIVE = 'quality_gameplay/gq470_union22_real69_20261122/native'
    HISTORICAL_COMMIT = '93a1147561a531610ac1609ebc68cc0ecf546623'
    HISTORICAL_TREE = 'ca7a6b532ff325ebf125423484dde1ee57ce219b'
    HISTORICAL_NAMES = (
        'INPUT_LOCK.json', 'run_profile.py', 'combined_cases_clear_los.luau',
        'objective_full_cases.luau', 'objective_full_cases_clear_los.luau',
        'fixtures/INPUT_MANIFEST.json', 'fixtures/combined_cases.luau',
        'fixtures/combined_fixture_additions.luau', 'fixtures/fixture_additions.luau',
        'fixtures/native_prefix.luau', 'fixtures/speed_fixture_additions.luau',
    )
    OWN_PATHS = (
        'quality_gameplay/gq470_match_role_growth_20261123/README.md',
        'quality_gameplay/gq470_match_role_growth_20261123/growth_patch.json',
        'quality_gameplay/gq470_match_role_growth_20261123/source_lock.json',
        'quality_gameplay/gq470_match_role_growth_20261123/apply_growth.py',
        'quality_gameplay/gq470_match_role_growth_20261123/native/growth_cases.luau',
        'quality_gameplay/gq470_match_role_growth_20261123/native/run_growth.py',
        'quality_gameplay/gq470_match_role_growth_20261123/native/INPUT_LOCK.json',
        'tests/test_gq470_match_role_growth_20261123.py',
        '.github/workflows/gq470-match-role-growth.yml',
    )

    @staticmethod
    def load_native(repo):
        path = repo / 'quality_gameplay/gq470_match_role_growth_20261123/native/run_growth.py'
        spec = importlib.util.spec_from_file_location('gq470_s1a_capsule_tests', path)
        native = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, 'dont_write_bytecode', True):
            spec.loader.exec_module(native)
        return native

    @classmethod
    def setUpClass(cls):
        cls.native = cls.load_native(REPO)
        cls.contract = cls.native.load_native_contract()
        cls.capsule = cls.contract['historical_inputs']

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gq470-capsule-test-', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        bytecode = mock.patch.object(sys, 'dont_write_bytecode', True)
        bytecode.start()
        self.addCleanup(bytecode.stop)

    def copy_own(self, target):
        target.mkdir()
        for relative in self.OWN_PATHS:
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, output)
        return target

    @staticmethod
    def raw_tree(root):
        """Independent, read-only after-failure oracle; never follows member links."""
        entries = {}
        for path in [root, *sorted(root.rglob('*'))]:
            info = path.lstat()
            mode = stat.S_IMODE(info.st_mode)
            relative = path.relative_to(root).as_posix()
            if stat.S_ISLNK(info.st_mode):
                entries[relative] = ('symlink', mode, os.readlink(path))
            elif stat.S_ISDIR(info.st_mode):
                entries[relative] = ('directory', mode)
            elif stat.S_ISREG(info.st_mode):
                entries[relative] = ('regular_file', mode, path.read_bytes())
            else:
                entries[relative] = ('special', mode, stat.S_IFMT(info.st_mode))
        info = root.lstat()
        return {'root_identity': (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode)),
                'entries': entries}

    def git(self, repo, *arguments, check=True):
        executable = shutil.which('git')
        self.assertIsNotNone(executable, 'git is required for the isolated HEAD-bound repository test')
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith('GIT_')}
        environment.update({
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_SYSTEM': os.devnull,
            'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_AUTHOR_NAME': 'Capsule test fixture',
            'GIT_AUTHOR_EMAIL': 'capsule-fixture@example.invalid',
            'GIT_COMMITTER_NAME': 'Capsule test fixture',
            'GIT_COMMITTER_EMAIL': 'capsule-fixture@example.invalid',
        })
        return subprocess.run(
            [executable, '-C', str(repo), '-c', 'core.hooksPath=/dev/null',
             '-c', 'commit.gpgsign=false', *arguments],
            env=environment, check=check, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=20)

    def test_historical_capsule_rejects_invalid_payload_before_write_or_import(self):
        member = self.NATIVE_RELATIVE + '/run_profile.py'
        objective = self.NATIVE_RELATIVE + '/objective_full_cases.luau'
        outside = self.root / 'outside.txt'
        outside.write_bytes(b'existing outside input must remain unchanged')
        outside_before = outside.read_bytes()
        cases = []

        def changed(name, reason, mutate):
            value = copy.deepcopy(self.capsule)
            mutate(value)
            cases.append((name, reason, value))

        def rename(value, replacement):
            value['files'][replacement] = value['files'].pop(objective)

        changed('schema', 'HISTORICAL_SCHEMA',
                lambda value: value.update(schema='UNTRUSTED_CAPSULE'))
        changed('source-commit', 'HISTORICAL_ORIGIN',
                lambda value: value.update(source_commit='0' * 40))
        changed('source-tree', 'HISTORICAL_ORIGIN',
                lambda value: value.update(source_tree='0' * 40))
        changed('missing-original-objective', 'HISTORICAL_MEMBER_SET',
                lambda value: value['files'].pop(objective))
        changed('extra-member', 'HISTORICAL_MEMBER_SET',
                lambda value: value['files'].update({
                    self.NATIVE_RELATIVE + '/unregistered.luau':
                    copy.deepcopy(value['files'][objective])}))
        changed('same-count-unknown-member', 'HISTORICAL_MEMBER_SET',
                lambda value: rename(value, self.NATIVE_RELATIVE + '/unknown.luau'))
        changed('parent-escape', 'HISTORICAL_MEMBER_PATH',
                lambda value: rename(value, '../outside.txt'))
        changed('absolute-escape', 'HISTORICAL_MEMBER_PATH',
                lambda value: rename(value, str(outside)))
        changed('backslash-path', 'HISTORICAL_MEMBER_PATH',
                lambda value: rename(value, objective.replace('/', '\\')))
        changed('member-origin', 'HISTORICAL_ORIGIN',
                lambda value: value['files'][member].update(origin_commit='0' * 40))
        changed('extra-field', 'HISTORICAL_MEMBER_FIELDS',
                lambda value: value['files'][member].update(unregistered=True))
        changed('wrong-field-type', 'HISTORICAL_MEMBER_FIELDS',
                lambda value: value['files'][member].update(bytes='1'))
        changed('invalid-utf8', 'HISTORICAL_MEMBER_UTF8',
                lambda value: value['files'][member].update(utf8='\ud800'))
        changed('body-longer', 'HISTORICAL_MEMBER_BYTES',
                lambda value: value['files'][member].update(
                    utf8=value['files'][member]['utf8'] + '\n'))
        changed('body-same-length', 'HISTORICAL_MEMBER_SHA256',
                lambda value: value['files'][member].update(
                    utf8='!' + value['files'][member]['utf8'][1:]))
        changed('bytes-pin', 'HISTORICAL_MEMBER_BYTES',
                lambda value: value['files'][member].update(
                    bytes=value['files'][member]['bytes'] + 1))
        changed('sha256-pin', 'HISTORICAL_MEMBER_SHA256',
                lambda value: value['files'][member].update(sha256='0' * 64))
        changed('git-blob-pin', 'HISTORICAL_MEMBER_GIT_BLOB',
                lambda value: value['files'][member].update(git_blob='0' * 40))

        for index, (name, reason, value) in enumerate(cases):
            with self.subTest(boundary=name):
                output = self.root / ('rejected-' + str(index))
                with mock.patch.object(
                        self.native, 'module',
                        side_effect=AssertionError('invalid capsule reached module import')) as imported:
                    with self.assertRaisesRegex(ValueError, reason):
                        self.native.materialize_historical_inputs(value, output)
                self.assertEqual(imported.call_count, 0)
                self.assertFalse(output.exists(), 'invalid capsule created an output root')
                self.assertEqual(outside.read_bytes(), outside_before)
        self.assertEqual(set(self.root.iterdir()), {outside})

        # A fully self-consistent replacement still cannot replace the outer trust anchor.
        own = self.copy_own(self.root / 'outer-lock-replacement')
        native = self.load_native(own)
        lock_path = own / 'quality_gameplay/gq470_match_role_growth_20261123/native/INPUT_LOCK.json'
        contract = json.loads(lock_path.read_bytes())
        record = contract['historical_inputs']['files'][member]
        record['utf8'] += '\n# self-consistent but unauthorized historical replacement\n'
        raw = record['utf8'].encode('utf-8')
        record.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                      git_blob=hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest())
        lock_path.write_text(json.dumps(contract, ensure_ascii=False, sort_keys=True, indent=2) + '\n',
                             encoding='utf-8')
        self.assertEqual(native.INPUT_LOCK_SHA256, self.native.INPUT_LOCK_SHA256)
        historical = self.root / 'untrusted-history'
        with mock.patch.object(
                native, 'module',
                side_effect=AssertionError('modified outer lock reached historical import')) as imported:
            with self.assertRaisesRegex(ValueError, 'NATIVE_LOCK_CHANGED'):
                native.load_inputs(historical)
        self.assertEqual(imported.call_count, 0)
        self.assertFalse(historical.exists())
        self.assertEqual(outside.read_bytes(), outside_before)

    def test_historical_capsule_confines_root_and_rejects_same_root_tampering(self):
        existing = self.root / 'existing'
        existing.mkdir()
        sentinel = existing / 'sentinel'
        sentinel.write_bytes(b'do not overwrite an existing historical root')
        with self.assertRaisesRegex(ValueError, 'HISTORICAL_ROOT_EXISTS'):
            self.native.materialize_historical_inputs(self.capsule, existing)
        self.assertEqual(sentinel.read_bytes(), b'do not overwrite an existing historical root')
        self.assertEqual(set(existing.iterdir()), {sentinel})

        actual = self.root / 'actual'
        actual.mkdir()
        alias = self.root / 'alias'
        alias.symlink_to(actual, target_is_directory=True)
        for path in (alias, alias / 'child'):
            with self.subTest(symlink_root=str(path)):
                with self.assertRaisesRegex(ValueError, 'SYMLINK_ROOT'):
                    self.native.materialize_historical_inputs(self.capsule, path)
                self.assertEqual(list(actual.iterdir()), [])

        historical = self.root / 'valid-history'
        before = self.native.materialize_historical_inputs(self.capsule, historical)
        self.assertEqual(before, self.native.snapshot_historical_inputs(self.capsule, historical))
        with mock.patch.object(self.native, 'module', wraps=self.native.module) as imported:
            with mock.patch.object(subprocess, 'run',
                                   side_effect=AssertionError('capsule loading must not launch a process')):
                loaded = self.native.load_inputs(historical)
        history_calls = [call for call in imported.call_args_list
                         if Path(call.args[1]).name == 'run_profile.py']
        self.assertEqual(len(history_calls), 1)
        self.assertEqual(len(loaded), 6)
        self.assertEqual(before, self.native.revalidate_historical_inputs(self.capsule, historical, before))

        member = self.NATIVE_RELATIVE + '/run_profile.py'
        objective = self.NATIVE_RELATIVE + '/objective_full_cases.luau'
        external = self.root / 'outside-run-profile.py'
        external.write_bytes((historical / member).read_bytes())
        external_before = external.read_bytes()

        def append_body(root):
            path = root / member
            path.write_bytes(path.read_bytes() + b'\n# changed after use\n')

        def link_member(root):
            path = root / member
            path.unlink()
            path.symlink_to(external)

        def change_mode(root):
            path = root / member
            path.chmod(stat.S_IMODE(path.stat().st_mode) ^ stat.S_IXUSR)

        mutations = (
            ('runner-bytes', 'HISTORICAL_MEMBER_BYTES', append_body, True),
            ('missing-member', 'HISTORICAL_MEMBER_SET',
             lambda root: (root / objective).unlink(), True),
            ('extra-member', 'HISTORICAL_MEMBER_SET',
             lambda root: (root / 'unregistered.luau').write_bytes(b'return true\n'), True),
            ('extra-directory', 'HISTORICAL_ENTRY_SET',
             lambda root: (root / 'unregistered-directory').mkdir(), True),
            ('linked-member', 'HISTORICAL_MEMBER_TYPE', link_member, True),
            ('member-mode', 'HISTORICAL_SNAPSHOT_CHANGED', change_mode, False),
        )
        for name, reason, mutate, reject_before_import in mutations:
            with self.subTest(boundary=name):
                target = self.root / ('tampered-' + name)
                original = self.native.materialize_historical_inputs(self.capsule, target)
                mutate(target)
                tampered = self.raw_tree(target)
                with mock.patch.object(
                        self.native, 'module',
                        side_effect=AssertionError('tampered history reached module import')) as imported:
                    if reject_before_import:
                        with self.assertRaisesRegex(ValueError, reason):
                            self.native.load_inputs(target)
                    with self.assertRaisesRegex(ValueError, reason):
                        self.native.revalidate_historical_inputs(self.capsule, target, original)
                self.assertEqual(imported.call_count, 0)
                self.assertEqual(self.raw_tree(target), tampered, 'validation repaired or replaced the input tree')
                self.assertEqual(external.read_bytes(), external_before)

        # A mode is measured at materialization, not invented as an original H93 mode.
        # A fresh root with identical content must not replace the root used before.
        other = self.root / 'different-valid-root'
        other_before = self.native.materialize_historical_inputs(self.capsule, other)
        with self.assertRaisesRegex(ValueError, 'HISTORICAL_ROOT_CHANGED'):
            self.native.revalidate_historical_inputs(self.capsule, other, before)
        self.assertEqual(other_before, self.native.snapshot_historical_inputs(self.capsule, other))
        self.assertEqual(before, self.native.revalidate_historical_inputs(self.capsule, historical, before))

    def test_historical_capsule_loads_in_own_only_repository_without_canonical_tree(self):
        own = self.copy_own(self.root / 'own-only')
        self.assertEqual(
            {path.relative_to(own).as_posix() for path in own.rglob('*') if path.is_file()},
            set(self.OWN_PATHS))
        self.assertFalse((own / 'quality_gameplay/gq470_union22_real69_20261122').exists())
        self.git(own, 'init', '--quiet', '--object-format=sha1', '--template=')
        self.git(own, 'add', '--', *self.OWN_PATHS)
        self.git(own, 'commit', '--quiet', '-m', 'Test fixture: own S1A inputs only')
        head = self.git(own, 'rev-parse', 'HEAD').stdout.decode().strip()
        self.assertNotEqual(
            self.git(own, 'cat-file', '-e', self.HISTORICAL_COMMIT + '^{commit}', check=False).returncode, 0)
        self.assertEqual(self.git(own, 'remote').stdout, b'')
        native = self.load_native(own)
        contract = native.load_native_contract()
        capsule = contract['historical_inputs']
        self.assertEqual(capsule['source_commit'], self.HISTORICAL_COMMIT)
        self.assertEqual(capsule['source_tree'], self.HISTORICAL_TREE)
        members = {self.NATIVE_RELATIVE + '/' + name for name in self.HISTORICAL_NAMES}
        self.assertEqual(set(capsule['files']), members)
        self.assertEqual(len(members), 11)
        historical = self.root / 'isolated-history'
        before = native.materialize_historical_inputs(capsule, historical)
        with mock.patch.object(native, 'module', wraps=native.module) as imported:
            with mock.patch.object(subprocess, 'run',
                                   side_effect=AssertionError('isolated capsule loading must not launch a process')):
                loaded = native.load_inputs(historical)
        history_calls = [call for call in imported.call_args_list
                         if Path(call.args[1]).name == 'run_profile.py']
        self.assertEqual(len(history_calls), 1)
        self.assertEqual(Path(history_calls[0].args[1]).resolve(),
                         historical / self.NATIVE_RELATIVE / 'run_profile.py')
        self.assertEqual(len(loaded), 6)
        loaded_contract, sections, frozen, old, source_lock, helpers = loaded
        self.assertEqual(loaded_contract, contract)
        self.assertEqual(Path(frozen.__file__).resolve(),
                         historical / self.NATIVE_RELATIVE / 'run_profile.py')
        self.assertEqual(frozen.HERE.resolve(), historical / self.NATIVE_RELATIVE)
        self.assertEqual(old['sources'], source_lock['sources_before'])
        self.assertIsInstance(helpers, bytes)
        self.assertEqual(set(sections), set(contract['sections']))
        self.assertEqual(set(before['files']), members)
        for relative, record in capsule['files'].items():
            self.assertEqual((historical / relative).read_bytes(), record['utf8'].encode('utf-8'))

        snapshot = native.repository_snapshot(frozen, shutil.which('git'), head, contract)
        self.assertEqual(set(snapshot), set(self.OWN_PATHS))
        for relative, actual in snapshot.items():
            raw = (own / relative).read_bytes()
            mode = '100755' if (own / relative).stat().st_mode & 0o111 else '100644'
            self.assertEqual(actual, {
                'git_blob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
                'mode': mode, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            })
        self.assertEqual(before, native.revalidate_historical_inputs(capsule, historical, before))
        self.assertEqual(self.git(own, 'status', '--porcelain=v1', '--untracked-files=all').stdout, b'')
        self.assertFalse((own / 'quality_gameplay/gq470_union22_real69_20261122').exists())
        self.assertFalse(list(historical.rglob('__pycache__')))
        self.assertFalse(list(own.rglob('__pycache__')))


if __name__ == '__main__':
    value = os.environ.get('GQ470_H93_ARTIFACT')
    if value is None or not value.strip():
        raise RuntimeError('GQ470_H93_ARTIFACT must name the actual pinned H93 artifact; no synthetic fallback')
    unittest.main(verbosity=2)
