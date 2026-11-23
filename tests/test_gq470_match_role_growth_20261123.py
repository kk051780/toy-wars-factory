#!/usr/bin/env python3
"""Adversarial input and exact inverse tests using the genuine H93 artifact."""
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
        if not value:
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
