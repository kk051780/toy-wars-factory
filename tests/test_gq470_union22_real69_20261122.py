#!/usr/bin/env python3
"""Focused fail-closed controls for the additional union boundary.

Repository discovery without UNION22_TEST_* runs artifact-free contracts.
Explicit core/final integration requires actual workflow outputs and runs the
complete fixed suite; missing context never becomes a skip or an empty PASS.
"""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
HERE = REPO / "quality_gameplay/gq470_union22_real69_20261122"
sys.path.insert(0, str(HERE))
import compose_union22 as compose
import verify_union22 as verify
spec = importlib.util.spec_from_file_location("union22_native_tests", HERE / "native/run_profile.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


ARTIFACT_ENV = ("UNION22_TEST_PRIOR", "UNION22_TEST_REPORTS", "UNION22_TEST_ROOT",
                "UNION22_TEST_NATIVE", "UNION22_TEST_STAGE")
INTEGRATION_COUNTS = {"core": 72, "final": 21}


def restore_combat(on, lock):
    shorefoam_off = compose.shorefoam_parent(*restore_pre_team_gate(on, lock))
    touch_off = compose.private_touch_parent(*compose.portrait_parent(*shorefoam_off))
    relay_off = compose.relay_eligibility_parent(*compose.moguron_parent(*touch_off))
    mage_off = compose.mage_contact_parent(*relay_off)
    return compose.combat_visual_parent(*compose.growth_musou_parent(*compose.art_polish_parent(*mage_off)))


def restore_pre_team_gate(on, lock):
    ground_on = compose.cover_orders_parent(*compose.mage_field_arcs_parent(on, lock))
    field_on = compose.return_convert_parent(*compose.ground_night_parent(*ground_on))
    water_on = compose.ninja_s4_parent(*compose.wing_warrior_parent(*compose.field_loadouts_parent(*field_on)))
    hp_on, hp_on_lock = compose.mage_projectile_parent(*compose.mage_water_chain_parent(*water_on))
    return compose.team_win_rule_parent(*compose.fractional_hp_parent(hp_on, hp_on_lock))


def restore_canyon(on, lock):
    wall_off = compose.guardian_wall_parent(*restore_combat(on, lock))
    neutral_off = compose.neutral_names_parent(*wall_off)
    return compose.br_canyon_parent(*compose.role_readability_parent(*compose.field_prompt_parent(*neutral_off)))


def before_guardian(lock):
    repair = lock["guardian_followup_repair"]
    return lock | {
        "sources": lock["sources"] | {
            name: row["parent"] for name, row in lock["mage_field_arcs_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["cover_orders_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["ground_night_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["return_convert_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["field_loadouts_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["wing_warrior_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["ninja_s4_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["mage_water_chain_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["mage_projectile_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["fractional_hp_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["team_win_rule_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["shorefoam_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["portrait_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["moguron_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["relay_eligibility_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["mage_contact_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["art_polish_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["growth_musou_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["combat_visual_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["neutral_names_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["role_readability_followup"]["rows"].items()
        } | {
            name: row["parent"] for name, row in lock["br_canyon_followup"]["rows"].items()
        } | {compose.GUARDIAN_SOURCE: repair["parent_guardian_row"],
                                      compose.ITEM_SOURCE: lock["item_cleanup_followup"]["parent_item_row"],
                                      compose.SCORE_SOURCE: lock["score_relay_followup"]["parent_score_row"],
                                      compose.HUD_SOURCE: lock["relay_presentation_followup"]["rows"][compose.HUD_SOURCE]["parent"],
                                      compose.VAULT_SOURCE: lock["empty_vault_followup"]["parent_host_row"]},
        "final_place": repair["parent_place"],
    }


def artifact_environment(expected_stage=None):
    supplied = {key: value for key, value in os.environ.items() if key.startswith("UNION22_TEST_")}
    if set(supplied) - set(ARTIFACT_ENV):
        raise ValueError("RED_UNION22_UNKNOWN_TEST_ENVIRONMENT")
    stage = supplied.get("UNION22_TEST_STAGE", "core")
    if stage not in INTEGRATION_COUNTS or expected_stage is not None and stage != expected_stage:
        raise ValueError("RED_UNION22_UNKNOWN_OR_MISMATCHED_TEST_STAGE")
    required = ARTIFACT_ENV[:3] + (("UNION22_TEST_NATIVE",) if stage == "final" else ())
    missing = [key for key in required if not supplied.get(key, "").strip()]
    if missing:
        raise ValueError("RED_UNION22_MISSING_ARTIFACT_CONTEXT:" + ",".join(missing))
    paths = {key: Path(supplied[key]).resolve() for key in ARTIFACT_ENV[:4] if key in supplied}
    for key, path in paths.items():
        if not supplied[key].strip() or not path.is_dir():
            raise ValueError("RED_UNION22_ARTIFACT_DIRECTORY_MISSING:" + key)
    return stage, paths


def checked_suite(loader, case, expected_count):
    suite = loader.loadTestsFromTestCase(case)
    if suite.countTestCases() != expected_count:
        raise ValueError("RED_UNION22_INCOMPLETE_TEST_SELECTION")
    return suite


class UnionBoundary(unittest.TestCase):
    ARTIFACT_STAGE = "core"

    @classmethod
    def setUpClass(cls):
        _, paths = artifact_environment(cls.ARTIFACT_STAGE)
        cls.prior = paths["UNION22_TEST_PRIOR"]
        cls.reports = paths["UNION22_TEST_REPORTS"]
        cls.current = paths["UNION22_TEST_ROOT"]
        cls.lock = compose.load_lock()
        cls.native_lock = native.load_lock()
        cls.context = verify.data(cls.current / "CORE_BUILD_REPORT.json")["context"]
        cls.first = next(iter(cls.lock["sources"]))
        # Missing or invalid artifacts must fail before a negative test can
        # mistake that setup failure for the particular rejection it exercises.
        verify.verify_core(cls.current, cls.prior, cls.reports, cls.context)

    def temporary(self):
        context = tempfile.TemporaryDirectory(prefix="union22-negative-")
        self.addCleanup(context.cleanup)
        return Path(context.name)

    def prior_copy(self):
        dest = self.temporary() / "prior"
        dest.mkdir()
        for name in (compose.PROJECT, compose.PLACE, compose.RECEIPT):
            shutil.copyfile(self.prior / name, dest / name)
        shutil.copytree(self.prior / "sources", dest / "sources")
        for name in self.lock["prior_report_names"] + self.lock["prior_opaque_rollback_names"]:
            shutil.copyfile(self.reports / name, dest / name)
        return dest

    def current_copy(self):
        dest = self.temporary() / "current"
        shutil.copytree(self.current, dest)
        return dest

    def reject_core(self, root):
        with self.assertRaises(ValueError):
            verify.verify_core(root, self.prior, self.reports, self.context)
        self.assertFalse((root / "delivery").exists())

    def test_actual_parent_and_core(self):
        result = verify.verify_core(self.current, self.prior, self.reports, self.context)
        self.assertEqual(len(result["current"]["sources"]), 69)
        self.assertEqual(len(result["archive_members"]), 75)
        active = compose.REPO / "rc_fastlane"
        selection = verify.data(active / "ACTIVE.json")
        private_blobs = set()
        for row in result["current"]["sources"].values():
            source = row["source"]
            blob = b"blob " + str(len(source)).encode() + b"\0" + source
            private_blobs.add(hashlib.sha1(blob).hexdigest())
        ready = verify.data(active / "features/active_ready/source_lock.json")
        self.assertEqual(ready["profile"], selection["active_profile"])
        self.assertEqual(ready["source_commit"], selection["active_source_commit"])
        self.assertTrue(private_blobs.isdisjoint(route["after"] for route in ready["routes"].values()))
        ended = verify.data(active / "features/active_results/source_lock.json")
        self.assertEqual(ended["profile"], selection["active_profile"])
        self.assertEqual(ended["before"], ready["routes"]["server/Game.server.luau"]["after"])
        self.assertNotIn(ended["after"], private_blobs)
        match_mode = verify.data(active / "features/active_mode_start/source_lock.json")
        self.assertEqual(match_mode["profile"], selection["active_profile"])
        self.assertEqual(match_mode["routes"]["server/Game.server.luau"]["before"], ended["after"])
        self.assertTrue(private_blobs.isdisjoint(row["after"] for row in match_mode["routes"].values()))
        bot_package = active / "features/active_solo_bots"
        solo_bots = verify.data(bot_package / "source_lock.json")
        self.assertEqual(solo_bots["profile"], selection["active_profile"])
        self.assertEqual(solo_bots["before_game"], match_mode["routes"]["server/Game.server.luau"]["after"])
        bot_body = (bot_package / "SoloTeamBots.luau").read_bytes()
        bot_gitblob = hashlib.sha1(b"blob " + str(len(bot_body)).encode() + b"\0" + bot_body).hexdigest()
        self.assertEqual(bot_gitblob, solo_bots["bot_blob"])
        self.assertTrue(private_blobs.isdisjoint((bot_gitblob, solo_bots["after_game"])))
        h2_exit = verify.data(active / "features/active_h2_exit/source_lock.json")
        self.assertEqual(h2_exit["profile"], selection["active_profile"])
        self.assertEqual(h2_exit["before"], solo_bots["after_game"])
        self.assertNotIn(h2_exit["after"], private_blobs)
        persistence = verify.data(active / "features/active_persistence_lifecycle/source_lock.json")
        self.assertEqual(persistence["profile"], selection["active_profile"])
        self.assertEqual(persistence["routes"]["server/Game.server.luau"]["before"], h2_exit["after"])
        self.assertTrue(private_blobs.isdisjoint(row["after"] for row in persistence["routes"].values()))
        lobby = verify.data(active / "features/active_safe_lobby/source_lock.json")
        self.assertEqual(lobby["profile"], selection["active_profile"])
        self.assertEqual(lobby["routes"]["server/Game.server.luau"]["before"],
                         persistence["routes"]["server/Game.server.luau"]["after"])
        island = (active / "features/fb007_lobby/LobbyDojoIsland.luau").read_bytes()
        blob = b"blob " + str(len(island)).encode() + bytes([0]) + island
        self.assertEqual(hashlib.sha1(blob).hexdigest(), lobby["routes"]["server/LobbyDojoIsland.luau"]["after"])
        hit = verify.data(active / "features/active_confirmed_hit/source_lock.json")
        self.assertEqual(hit["profile"], selection["active_profile"])
        self.assertEqual(hit["routes"]["server/Game.server.luau"]["before"],
                         lobby["routes"]["server/Game.server.luau"]["after"])
        self.assertEqual(hit["routes"]["client/HUD.client.luau"]["before"],
                         persistence["routes"]["client/HUD.client.luau"]["after"])
        self.assertTrue(private_blobs.isdisjoint(row["after"] for row in hit["routes"].values()))
        undead_package = active / "features/active_undead_squad"
        undead = verify.data(undead_package / "source_lock.json")
        self.assertEqual(undead["profile"], selection["active_profile"])
        self.assertEqual(undead["routes"]["server/Game.server.luau"]["before"],
                         hit["routes"]["server/Game.server.luau"]["after"])
        self.assertEqual(undead["horde"], hit["horde"])
        original_actor = (undead_package / "UndeadSquad.luau").read_bytes()
        header = b"blob " + str(len(original_actor)).encode() + bytes([0])
        self.assertEqual(hashlib.sha1(header + original_actor).hexdigest(),
                         undead["source_origin"]["module_git_blob"])
        self.assertTrue(private_blobs.isdisjoint(row["after"] for row in undead["routes"].values()))
        wind = verify.data(active / "features/active_assassin_wind/source_lock.json")
        self.assertEqual(wind["profile"], selection["active_profile"])
        self.assertEqual(wind["routes"]["server/Game.server.luau"]["before"],
                         undead["routes"]["server/Game.server.luau"]["after"])
        self.assertEqual(wind["routes"]["client/HUD.client.luau"]["before"],
                         hit["routes"]["client/HUD.client.luau"]["after"])
        self.assertTrue(private_blobs.isdisjoint(row["after"] for row in wind["routes"].values()))
        touch_dir = active / "features/active_touch_attack"
        touch = verify.data(touch_dir / "source_lock.json")
        self.assertEqual(touch["profile"], selection["active_profile"])
        touch_hud = touch["routes"]["client/HUD.client.luau"]
        self.assertEqual(touch_hud["before"], wind["routes"]["client/HUD.client.luau"]["after"])
        self.assertNotIn(touch_hud["after"], private_blobs)
        for name in ("touch-layout.luau","touch-ui.luau"):
            self.assertEqual(hashlib.sha256((touch_dir / name).read_bytes()).hexdigest(), touch["original"][name])
        growth_dir = active / "features/active_role_growth"
        growth = verify.data(growth_dir / "source_lock.json")
        self.assertEqual(growth["profile"], selection["active_profile"])
        routes = growth["routes"]
        self.assertEqual(routes["client/HUD.client.luau"]["before"], touch_hud["after"])
        self.assertEqual(routes["server/MusouHorde.luau"]["before"], hit["horde"])
        self.assertEqual(routes["server/Game.server.luau"]["before"],
                         wind["routes"]["server/Game.server.luau"]["after"])
        author = (growth_dir / "TimePremiumRules.luau").read_bytes()
        self.assertEqual(hashlib.sha1(b"blob " + str(len(author)).encode() + bytes([0]) + author).hexdigest(),
                         growth["source_origin"]["natural_growth_blob"])
        self.assertTrue(private_blobs.isdisjoint(route["after"] for route in routes.values()))
        mage_dir = active / "features/active_mage_armament"
        mage = verify.data(mage_dir / "source_lock.json")
        self.assertEqual(mage["profile"], selection["active_profile"])
        for relative in ("server/Game.server.luau", "server/MusouHorde.luau"):
            self.assertEqual(mage["routes"][relative]["before"], routes[relative]["after"])
        armament = (mage_dir / "SevenJobArmamentM1.luau").read_bytes()
        header = b"blob " + str(len(armament)).encode() + bytes([0])
        self.assertEqual(hashlib.sha1(header + armament).hexdigest(), mage["source_origin"]["blob"])
        self.assertTrue(private_blobs.isdisjoint(route["after"] for route in mage["routes"].values()))
        water_dir = active / "features/active_mage_water"
        water = verify.data(water_dir / "source_lock.json")
        self.assertEqual(water["profile"], selection["active_profile"])
        for relative in ("server/Game.server.luau", "server/MusouHorde.luau"):
            self.assertEqual(water["routes"][relative]["before"], mage["routes"][relative]["after"])
        for relative in ("server/MatchRoleGrowth.luau", "client/HUD.client.luau"):
            self.assertEqual(water["routes"][relative]["before"], routes[relative]["after"])
        catalog = (water_dir / "MageWaterCatalog.luau").read_bytes()
        self.assertEqual(hashlib.sha256(catalog).hexdigest(), water["source_origin"]["selected_catalog_sha256"])
        self.assertTrue(private_blobs.isdisjoint(route["after"] for route in water["routes"].values()))
        blink_dir = active / "features/active_ninja_blink"
        blink = verify.data(blink_dir / "source_lock.json")
        self.assertEqual(blink["profile"], selection["active_profile"])
        for relative in ("server/Game.server.luau", "client/HUD.client.luau"):
            self.assertEqual(blink["routes"][relative]["before"], water["routes"][relative]["after"])
        blink_body = (blink_dir / "NinjaBlink.luau").read_bytes()
        blink_blob = hashlib.sha1(b"blob " + str(len(blink_body)).encode() + bytes([0]) + blink_body).hexdigest()
        self.assertEqual(blink_blob, blink["routes"]["server/NinjaBlink.luau"]["after"])
        self.assertTrue(private_blobs.isdisjoint(route["after"] for route in blink["routes"].values()))
        crowd = verify.data(active / "features/active_crowd_cap/source_lock.json")
        self.assertEqual(crowd["profile"], selection["active_profile"])
        horde = "server/MusouHorde.luau"
        self.assertEqual(set(crowd["routes"]), {horde})
        self.assertEqual(crowd["routes"][horde]["before"], water["routes"][horde]["after"])
        self.assertNotEqual(crowd["routes"][horde]["before"], crowd["routes"][horde]["after"])
        self.assertNotIn(crowd["routes"][horde]["after"], private_blobs)
        adapter = (active.parent / crowd["source_origin"]["adapter_path"]).read_bytes()
        header = b"blob " + str(len(adapter)).encode() + bytes([0])
        self.assertEqual(hashlib.sha1(header + adapter).hexdigest(), crowd["source_origin"]["adapter_blob"])
        chain_dir = active / "features/active_mage_chain"
        chain = verify.data(chain_dir / "source_lock.json")
        self.assertEqual(chain["profile"], selection["active_profile"])
        upstream = {
            "server/Game.server.luau": blink,
            "server/MusouHorde.luau": crowd,
            "server/MatchRoleGrowth.luau": water,
            "client/HUD.client.luau": blink,
        }
        for relative, previous in upstream.items():
            self.assertEqual(chain["routes"][relative]["before"], previous["routes"][relative]["after"])
        module = (chain_dir / "MageChain.luau").read_bytes()
        header = b"blob " + str(len(module)).encode() + bytes([0])
        self.assertEqual(chain["routes"]["server/MageChain.luau"]["after"],
                         hashlib.sha1(header + module).hexdigest())
        self.assertTrue(private_blobs.isdisjoint(route["after"] for route in chain["routes"].values()))
        packet = active / "features/active_sky_routes"
        sky = verify.data(packet / "source_lock.json")
        self.assertEqual(sky["profile"], selection["active_profile"])
        self.assertEqual(sky["source_commit"], selection["active_source_commit"])
        for relative, route in sky["routes"].items():
            with self.subTest(active_source=relative):
                source = (packet / Path(relative).name).read_bytes()
                blob = b"blob " + str(len(source)).encode() + b"\0" + source
                self.assertEqual(hashlib.sha1(blob).hexdigest(), route["after"])
                self.assertNotIn(route["after"], private_blobs,
                                 "ACTIVE rich51 geometry must stay outside the private companion")

    def test_hud_only_inverse_restores_current_rc_and_other68(self):
        parent_lock = compose.beast_parent_profile(before_guardian(self.lock))
        final = {p: (self.current / compose.BEAST_OFF / "sources" / p).read_bytes() for p in parent_lock["sources"]}
        before = compose.bot_parent_sources(final, parent_lock)
        restored = compose.hud_current_sources(before, parent_lock)
        self.assertEqual([p for p in before if before[p] != restored[p]], [compose.HUD_SOURCE])
        self.assertEqual(compose.identity(restored[compose.HUD_SOURCE]), parent_lock["followup_repair"]["current_hud"])
        self.assertNotEqual(parent_lock["followup_repair"]["current_place"], parent_lock["prior_place"])
        verified = verify.independent_scan(self.current / compose.BEAST_OFF, parent_lock, "after")
        self.assertEqual(len(verify.verify_hud_current_rollback(self.current, parent_lock, verified)), 71)

    def test_hud_only_inverse_payload_mutation_rejected(self):
        parent_lock = compose.beast_parent_profile(before_guardian(self.lock))
        changed = copy.deepcopy(parent_lock)
        changed["followup_repair"]["inverse"][0]["new"] += "-- wrong rollback\n"
        sources = {p: (self.current / compose.BEAST_OFF / "sources" / p).read_bytes() for p in parent_lock["sources"]}
        sources = compose.bot_parent_sources(sources, parent_lock)
        with self.assertRaisesRegex(ValueError, "HUNK_PAYLOAD_IDENTITY"):
            compose.hud_current_sources(sources, changed)

    def test_bot_only_inverse_restores_hud_parent_and_other68(self):
        parent_lock = compose.beast_parent_profile(before_guardian(self.lock))
        final = {p: (self.current / compose.BEAST_OFF / "sources" / p).read_bytes() for p in parent_lock["sources"]}
        parent = compose.bot_parent_sources(final, parent_lock)
        self.assertEqual([p for p in final if final[p] != parent[p]], [compose.BOT_SOURCE])
        self.assertEqual(compose.identity(parent[compose.BOT_SOURCE]), parent_lock["bot_followup_repair"]["parent_bot"])
        self.assertEqual(compose.identity(parent[compose.HUD_SOURCE]), parent_lock["followup_repair"]["repaired_hud"])
        verified = verify.independent_scan(self.current / compose.BEAST_OFF, parent_lock, "after")
        self.assertEqual(len(verify.verify_bot_parent_rollback(self.current, parent_lock, verified)), 71)

    def test_bot_inverse_rejects_wrong_source_before_restoring(self):
        parent_lock = compose.beast_parent_profile(before_guardian(self.lock))
        final = {p: (self.current / compose.BEAST_OFF / "sources" / p).read_bytes() for p in parent_lock["sources"]}
        router = "ServerScriptService/EGGRUMBLE_BotPathRouter.luau"
        self.assertIn(router, final)
        final[router] += b"\n-- unrelated router mutation\n"
        with self.assertRaisesRegex(ValueError, "BOT_PARENT_REQUIRES_EXACT_FINAL_SOURCES"):
            compose.bot_parent_sources(final, parent_lock)

    def test_bot_only_inverse_payload_mutation_rejected(self):
        parent_lock = compose.beast_parent_profile(before_guardian(self.lock))
        changed = copy.deepcopy(parent_lock)
        changed["bot_followup_repair"]["inverse"][0]["new"] += "-- wrong Bot rollback\n"
        changed["sources"][compose.BOT_SOURCE]["inverse"] = copy.deepcopy(changed["bot_followup_repair"]["inverse"])
        final = {p: (self.current / compose.BEAST_OFF / "sources" / p).read_bytes() for p in parent_lock["sources"]}
        with self.assertRaisesRegex(ValueError, "HUNK_PAYLOAD_IDENTITY"):
            compose.bot_parent_sources(final, changed)

    def test_bot_then_hud_rollback_order_required(self):
        parent_lock = compose.beast_parent_profile(before_guardian(self.lock))
        final = {p: (self.current / compose.BEAST_OFF / "sources" / p).read_bytes() for p in parent_lock["sources"]}
        with self.assertRaisesRegex(ValueError, "HUD_CURRENT_REQUIRES_EXACT_BOT_PARENT_SOURCES"):
            compose.hud_current_sources(final, parent_lock)
        parent = compose.bot_parent_sources(final, parent_lock)
        with self.assertRaisesRegex(ValueError, "BOT_PARENT_REQUIRES_EXACT_FINAL_SOURCES"):
            compose.bot_parent_sources(parent, parent_lock)
        restored = compose.hud_current_sources(parent, parent_lock)
        self.assertEqual(compose.identity(restored[compose.BOT_SOURCE]), parent_lock["bot_followup_repair"]["parent_bot"])
        self.assertEqual(compose.identity(restored[compose.HUD_SOURCE]), parent_lock["followup_repair"]["current_hud"])
        self.assertEqual(sorted(p for p in final if final[p] != restored[p]),
                         sorted([compose.BOT_SOURCE, compose.HUD_SOURCE]))

    def test_beast_only_inverse_restores_actual_h72_parent(self):
        on = {p: (self.current / "sources" / p).read_bytes() for p in self.lock["sources"]}
        vault_on, vault_lock = compose.castle_parent(*compose.score_parent(*compose.relay_presentation_parent(
            *restore_canyon(on, self.lock))))
        item_on, item_lock = compose.vault_parent(vault_on, vault_lock)
        guardian_on, guardian_lock = compose.item_parent(item_on, item_lock)
        final, beast = compose.guardian_parent(guardian_on, guardian_lock)
        self.assertEqual(beast, before_guardian(self.lock))
        self.assertEqual([p for p in guardian_on if guardian_on[p] != final[p]], [compose.GUARDIAN_SOURCE])
        self.assertEqual(compose.identity((self.current / compose.GUARDIAN_OFF / compose.PLACE).read_bytes()),
                         self.lock["guardian_followup_repair"]["parent_place"])
        parent_lock = compose.beast_parent_profile(beast)
        restored = compose.beast_parent_sources(final, beast, parent_lock)
        self.assertEqual([p for p in final if final[p] != restored[p]], [compose.BEAST_SOURCE])
        self.assertEqual(self.lock["beast_followup_repair"]["parent_head"], "72d620d86761f2aa5da80263a251cc5fa63fecbb")
        self.assertEqual(compose.identity(restored[compose.BEAST_SOURCE]), self.lock["beast_followup_repair"]["parent_combat"])
        self.assertEqual(compose.identity((self.current / compose.BEAST_OFF / compose.PLACE).read_bytes()),
                         self.lock["beast_followup_repair"]["parent_place"])

    def test_item_cleanup_only_inverse_restores_exact_guardian_parent(self):
        on = {p: (self.current / "sources" / p).read_bytes() for p in self.lock["sources"]}
        vault_on, vault_lock = compose.castle_parent(*compose.score_parent(*compose.relay_presentation_parent(
            *restore_canyon(on, self.lock))))
        item_ready, item_lock = compose.vault_parent(vault_on, vault_lock)
        restored, parent_lock = compose.item_parent(item_ready, item_lock)
        self.assertEqual([p for p in item_ready if item_ready[p] != restored[p]], [compose.ITEM_SOURCE])
        self.assertEqual(parent_lock["final_place"], self.lock["guardian_followup_repair"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.ITEM_OFF / compose.PLACE).read_bytes()),
                         parent_lock["final_place"])

    def test_empty_vault_inverse_keeps_item_and_rejects_wrong_archive(self):
        on = {p: (self.current / "sources" / p).read_bytes() for p in self.lock["sources"]}
        vault_on, vault_lock = compose.castle_parent(*compose.score_parent(*compose.relay_presentation_parent(
            *restore_canyon(on, self.lock))))
        restored, parent = compose.vault_parent(vault_on, vault_lock)
        self.assertEqual([p for p in vault_on if vault_on[p] != restored[p]], [compose.VAULT_SOURCE])
        self.assertEqual(parent["final_place"], self.lock["item_cleanup_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.VAULT_OFF / compose.PLACE).read_bytes()),
                         parent["final_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.ITEM_OFF_ARCHIVE, root / compose.VAULT_OFF_ARCHIVE)
        self.reject_core(root)

    def test_castle_release_and_stock_inverse_keeps_empty_vault_fix(self):
        on = {p: (self.current / "sources" / p).read_bytes() for p in self.lock["sources"]}
        parent_on, parent_lock = compose.score_parent(*compose.relay_presentation_parent(*restore_canyon(on, self.lock)))
        restored, parent = compose.castle_parent(parent_on, parent_lock)
        self.assertEqual([p for p in parent_on if parent_on[p] != restored[p]], [compose.VAULT_SOURCE])
        self.assertEqual(parent["final_place"], self.lock["empty_vault_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.CASTLE_OFF / compose.PLACE).read_bytes()),
                         parent["final_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.VAULT_OFF_ARCHIVE, root / compose.CASTLE_OFF_ARCHIVE)
        self.reject_core(root)

    def test_score_rollback_restores_exact_castle_parent_and_rejects_wrong_archive(self):
        on = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        parent, lock = compose.relay_presentation_parent(*restore_canyon(on, self.lock))
        actual, restored = compose.score_parent(parent, lock)
        self.assertEqual([name for name in parent if parent[name] != actual[name]], [compose.SCORE_SOURCE])
        self.assertEqual(restored["final_place"], self.lock["castle_release_stock_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.SCORE_OFF / compose.PLACE).read_bytes()),
                         restored["final_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.CASTLE_OFF_ARCHIVE, root / compose.SCORE_OFF_ARCHIVE)
        self.reject_core(root)

    def test_relay_presentation_off_restores_both_routes_and_rejects_previous_archive(self):
        on = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        on, post_relay = restore_canyon(on, self.lock)
        prior, lock = compose.relay_presentation_parent(on, post_relay)
        self.assertEqual({name for name in on if on[name] != prior[name]},set(compose.RELAY_PRESENTATION_SOURCES))
        self.assertEqual(lock["final_place"],self.lock["score_relay_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.RELAY_PRESENTATION_OFF / compose.PLACE).read_bytes()),
                         lock["final_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.SCORE_OFF_ARCHIVE, root / compose.RELAY_PRESENTATION_OFF_ARCHIVE)
        self.reject_core(root)

    def test_br_canyon_restores_exact_relay_parent_and_rejects_stale_pair(self):
        on = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        wall_off = compose.guardian_wall_parent(*restore_combat(on, self.lock))
        before_labels = compose.neutral_names_parent(*wall_off)
        on, post_canyon = compose.role_readability_parent(*compose.field_prompt_parent(*before_labels))
        prior, lock = compose.br_canyon_parent(on, post_canyon)
        self.assertEqual({name for name in on if on[name] != prior[name]}, set(compose.BR_CANYON_SOURCES))
        self.assertEqual(lock["final_place"], self.lock["relay_presentation_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.BR_CANYON_OFF / compose.PLACE).read_bytes()),
                         lock["final_place"])
        with self.assertRaisesRegex(ValueError, "BR_CANYON_SOURCE_PINS"):
            native.br_canyon_program(self.current / compose.BR_CANYON_OFF / "sources", self.lock, compose)
        root = self.current_copy()
        shutil.copyfile(root / compose.RELAY_PRESENTATION_OFF_ARCHIVE, root / compose.BR_CANYON_OFF_ARCHIVE)
        self.reject_core(root)

    def test_role_readability_parity_and_wrong_rollback_rejected(self):
        on = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        on, visual_lock = compose.guardian_wall_parent(*restore_combat(on, self.lock))
        neutral_off, neutral_lock = compose.neutral_names_parent(on, visual_lock)
        self.assertEqual({name for name in on if on[name] != neutral_off[name]}, set(compose.VISUAL_READABILITY_SOURCES))
        self.assertEqual(compose.identity((self.current / compose.NEUTRAL_NAMES_OFF / compose.PLACE).read_bytes()),
                         self.lock["field_prompt_followup"]["repaired_place"])
        prior, prior_lock = compose.field_prompt_parent(neutral_off, neutral_lock)
        self.assertEqual({name for name in neutral_off if neutral_off[name] != prior[name]}, {compose.VAULT_SOURCE})
        self.assertEqual(compose.identity((self.current / compose.FIELD_PROMPT_OFF / compose.PLACE).read_bytes()),
                         self.lock["role_readability_followup"]["repaired_place"])
        with self.assertRaisesRegex(ValueError, "FIELD_PROMPT_TWO_WAY|HUNK"):
            compose.field_prompt_parent(prior, neutral_lock)
        restored, lock = compose.role_readability_parent(prior, prior_lock)
        self.assertEqual({name for name in prior if prior[name] != restored[name]}, set(compose.ROLE_READABILITY_SOURCES))
        self.assertEqual(lock["final_place"], self.lock["br_canyon_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.ROLE_READABILITY_OFF / compose.PLACE).read_bytes()),
                         lock["final_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.BR_CANYON_OFF_ARCHIVE, root / compose.ROLE_READABILITY_OFF_ARCHIVE)
        self.reject_core(root)
        root = self.current_copy()
        shutil.copyfile(root / compose.ROLE_READABILITY_OFF_ARCHIVE, root / compose.FIELD_PROMPT_OFF_ARCHIVE)
        self.reject_core(root)
        root = self.current_copy()
        shutil.copyfile(root / compose.FIELD_PROMPT_OFF_ARCHIVE, root / compose.NEUTRAL_NAMES_OFF_ARCHIVE)
        self.reject_core(root)

    def test_shorefoam_inverse_changes_only_traversal_and_rejects_older_archive(self):
        final = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        cover_on, cover_lock = compose.mage_field_arcs_parent(final, self.lock)
        self.assertEqual({name for name in final if final[name] != cover_on[name]}, set(compose.MAGE_FIELD_ARCS_SOURCES))
        ground_on, ground_lock = compose.cover_orders_parent(cover_on, cover_lock)
        self.assertEqual({name for name in cover_on if cover_on[name] != ground_on[name]}, set(compose.COVER_ORDERS_SOURCES))
        return_on, return_lock = compose.ground_night_parent(ground_on, ground_lock)
        self.assertEqual({name for name in ground_on if ground_on[name] != return_on[name]},
                         set(compose.GROUND_NIGHT_SOURCES))
        field_on, field_lock = compose.return_convert_parent(return_on, return_lock)
        self.assertEqual({name for name in return_on if return_on[name] != field_on[name]},
                         set(compose.RETURN_CONVERT_SOURCES))
        wing_on, wing_lock = compose.field_loadouts_parent(field_on, field_lock)
        self.assertEqual({name for name in field_on if field_on[name] != wing_on[name]}, set(compose.FIELD_LOADOUTS_SOURCES))
        ninja_on, ninja_lock = compose.wing_warrior_parent(wing_on, wing_lock)
        self.assertEqual({name for name in wing_on if wing_on[name] != ninja_on[name]},
                         set(compose.WING_WARRIOR_SOURCES))
        water_on, water_lock = compose.ninja_s4_parent(ninja_on, ninja_lock)
        self.assertEqual({name for name in ninja_on if ninja_on[name] != water_on[name]}, set(compose.NINJA_S4_SOURCES))
        self.assertEqual(water_lock["final_place"], self.lock["mage_water_chain_followup"]["repaired_place"])
        projectile_on, projectile_on_lock = compose.mage_water_chain_parent(water_on, water_lock)
        self.assertEqual({name for name in water_on if water_on[name] != projectile_on[name]},
                         set(compose.MAGE_WATER_CHAIN_SOURCES))
        self.assertEqual(projectile_on_lock["final_place"], self.lock["mage_projectile_followup"]["repaired_place"])
        hp_on, hp_on_lock = compose.mage_projectile_parent(projectile_on, projectile_on_lock)
        self.assertEqual({name for name in projectile_on if projectile_on[name] != hp_on[name]},
                         set(compose.MAGE_PROJECTILES_SOURCES))
        self.assertEqual(hp_on_lock["final_place"], self.lock["fractional_hp_followup"]["repaired_place"])
        hp_parent, hp_lock = compose.fractional_hp_parent(hp_on, hp_on_lock)
        self.assertEqual({name for name in hp_on if hp_on[name] != hp_parent[name]}, {compose.HUD_SOURCE})
        self.assertEqual(hp_lock["final_place"], self.lock["team_win_rule_followup"]["repaired_place"])
        team_parent, team_lock = compose.team_win_rule_parent(hp_parent, hp_lock)
        self.assertEqual({name for name in hp_parent if hp_parent[name] != team_parent[name]}, {compose.VAULT_SOURCE})
        self.assertEqual(team_lock["final_place"], self.lock["shorefoam_followup"]["repaired_place"])
        parent, parent_lock = compose.shorefoam_parent(team_parent, team_lock)
        self.assertEqual({name for name in team_parent if team_parent[name] != parent[name]},
                         {compose.SHOREFOAM_SOURCE})
        self.assertEqual(parent_lock["final_place"], self.lock["portrait_followup"]["repaired_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.MAGE_PROJECTILES_OFF_ARCHIVE, root / compose.MAGE_WATER_CHAIN_OFF_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "ARCHIVE"):
            verify.verify_core(root, self.prior, self.reports, self.context)
        root = self.current_copy()
        shutil.copyfile(root / compose.FRACTIONAL_HP_OFF_ARCHIVE, root / compose.MAGE_PROJECTILES_OFF_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "ARCHIVE"):
            verify.verify_core(root, self.prior, self.reports, self.context)
        root = self.current_copy()
        shutil.copyfile(root / compose.TEAM_WIN_RULE_OFF_ARCHIVE, root / compose.FRACTIONAL_HP_OFF_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "ARCHIVE"):
            verify.verify_core(root, self.prior, self.reports, self.context)
        root = self.current_copy()
        shutil.copyfile(root / compose.SHOREFOAM_OFF_ARCHIVE, root / compose.TEAM_WIN_RULE_OFF_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "ARCHIVE"):
            verify.verify_core(root, self.prior, self.reports, self.context)
        root = self.current_copy()
        shutil.copyfile(root / compose.PORTRAIT_OFF_ARCHIVE, root / compose.SHOREFOAM_OFF_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "ARCHIVE"):
            verify.verify_core(root, self.prior, self.reports, self.context)

    def test_portrait_inverse_changes_only_policy_and_rejects_older_archive(self):
        final = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        previous, previous_lock = compose.shorefoam_parent(*restore_pre_team_gate(final, self.lock))
        parent, parent_lock = compose.portrait_parent(previous, previous_lock)
        self.assertEqual({name for name in previous if previous[name] != parent[name]}, {compose.PORTRAIT_SOURCE})
        self.assertEqual(parent_lock["final_place"], self.lock["private_touch_followup"]["repaired_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.PRIVATE_TOUCH_OFF_ARCHIVE, root / compose.PORTRAIT_OFF_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "ARCHIVE"):
            verify.verify_core(root, self.prior, self.reports, self.context)

    def test_private_touch_inverse_changes_only_hud_and_rejects_older_archive(self):
        final = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        previous, previous_lock = compose.portrait_parent(*compose.shorefoam_parent(*restore_pre_team_gate(final, self.lock)))
        parent, parent_lock = compose.private_touch_parent(previous, previous_lock)
        self.assertEqual({name for name in previous if previous[name] != parent[name]}, {compose.PRIVATE_TOUCH_SOURCE})
        self.assertEqual(parent_lock["final_place"], self.lock["moguron_followup"]["repaired_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.MOGURON_OFF_ARCHIVE, root / compose.PRIVATE_TOUCH_OFF_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "ARCHIVE"):
            verify.verify_core(root, self.prior, self.reports, self.context)
        self.assertFalse((root / "delivery").exists())

    def test_guardian_wall_inverse_restores_art_parent_and_rejects_stale_archive(self):
        final = {name: (self.current / "sources" / name).read_bytes() for name in self.lock["sources"]}
        shorefoam_off = compose.shorefoam_parent(*restore_pre_team_gate(final, self.lock))
        touch_off, touch_lock = compose.private_touch_parent(*compose.portrait_parent(*shorefoam_off))
        moguron_off, moguron_lock = compose.moguron_parent(touch_off, touch_lock)
        self.assertEqual({name for name in moguron_off if moguron_off[name] != touch_off[name]},
                         {compose.MOGURON_SOURCE})
        self.assertEqual(moguron_lock["final_place"], self.lock["relay_eligibility_followup"]["repaired_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.RELAY_ELIGIBILITY_OFF_ARCHIVE, root / compose.MOGURON_OFF_ARCHIVE)
        self.reject_core(root)
        eligibility_off, eligibility_lock = compose.relay_eligibility_parent(moguron_off, moguron_lock)
        self.assertEqual({name for name in eligibility_off if eligibility_off[name] != moguron_off[name]},
                         set(compose.RELAY_ELIGIBILITY_SOURCES))
        self.assertEqual(eligibility_lock["final_place"], self.lock["mage_contact_followup"]["repaired_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.MAGE_CONTACT_OFF_ARCHIVE, root / compose.RELAY_ELIGIBILITY_OFF_ARCHIVE)
        self.reject_core(root)
        mage_off, mage_lock = compose.mage_contact_parent(eligibility_off, eligibility_lock)
        self.assertEqual({name for name in mage_off if mage_off[name] != eligibility_off[name]},
                         set(compose.MAGE_CONTACT_SOURCES))
        self.assertEqual(mage_lock["final_place"], self.lock["art_polish_followup"]["repaired_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.ART_POLISH_OFF_ARCHIVE, root / compose.MAGE_CONTACT_OFF_ARCHIVE)
        self.reject_core(root)
        polish_off, polish_lock = compose.art_polish_parent(mage_off, mage_lock)
        self.assertEqual({name for name in polish_off if polish_off[name] != mage_off[name]},
                         set(compose.ART_POLISH_SOURCES))
        self.assertEqual(polish_lock["final_place"], self.lock["growth_musou_followup"]["repaired_place"])
        root = self.current_copy()
        shutil.copyfile(root / compose.GROWTH_MUSOU_OFF_ARCHIVE, root / compose.ART_POLISH_OFF_ARCHIVE)
        self.reject_core(root)
        final = polish_off
        growth_off, growth_lock = compose.growth_musou_parent(final, polish_lock)
        self.assertEqual({name for name in growth_off if growth_off[name] != final[name]},
                         set(compose.GROWTH_MUSOU_SOURCES))
        self.assertEqual(growth_lock["final_place"], self.lock["combat_visual_followup"]["repaired_place"])
        with self.assertRaisesRegex(ValueError, "HUNK|GROWTH_MUSOU_TWO_WAY"):
            compose.growth_musou_parent(growth_off, polish_lock)
        root = self.current_copy()
        shutil.copyfile(root / compose.COMBAT_VISUAL_OFF_ARCHIVE, root / compose.GROWTH_MUSOU_OFF_ARCHIVE)
        self.reject_core(root)
        final = growth_off
        on, combat_lock = compose.combat_visual_parent(final, growth_lock)
        self.assertEqual({name for name in on if on[name] != final[name]}, set(compose.COMBAT_VISUAL_SOURCES))
        self.assertEqual(combat_lock["final_place"], self.lock["guardian_wall_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.COMBAT_VISUAL_OFF / compose.PLACE).read_bytes()),
                         combat_lock["final_place"])
        with self.assertRaisesRegex(ValueError, "HUNK|COMBAT_VISUAL_TWO_WAY"):
            compose.combat_visual_parent(on, growth_lock)
        parent, lock = compose.guardian_wall_parent(on, combat_lock)
        guard = compose.GUARDIAN_SOURCE
        self.assertEqual({name for name in on if on[name] != parent[name]}, {guard})
        self.assertEqual(compose.identity(on[guard]), {
            "bytes": 15746, "sha256": "073c88a02e84d27c4f2cddd8ebd701c36e389f7050876b0551b4aa872301746c"})
        self.assertEqual(compose.identity(parent[guard]), self.lock["guardian_followup_repair"]["repaired_guardian"])
        self.assertEqual(lock["final_place"], self.lock["neutral_names_followup"]["repaired_place"])
        self.assertEqual(compose.identity((self.current / compose.GUARDIAN_WALL_OFF / compose.PLACE).read_bytes()),
                         lock["final_place"])
        with self.assertRaisesRegex(ValueError, "HUNK|GUARDIAN_WALL_TWO_WAY"):
            compose.guardian_wall_parent(parent, combat_lock)
        root = self.current_copy()
        shutil.copyfile(root / compose.GUARDIAN_WALL_OFF_ARCHIVE, root / compose.COMBAT_VISUAL_OFF_ARCHIVE)
        self.reject_core(root)
        root = self.current_copy()
        shutil.copyfile(root / compose.NEUTRAL_NAMES_OFF_ARCHIVE, root / compose.GUARDIAN_WALL_OFF_ARCHIVE)
        self.reject_core(root)

    def test_item_cleanup_inverse_rejects_old_guardian_off_archive(self):
        root = self.current_copy()
        shutil.copyfile(root / compose.GUARDIAN_OFF_ARCHIVE, root / compose.ITEM_OFF_ARCHIVE)
        self.reject_core(root)

    def test_guardian_matrix_binds_new_item_stage_and_rejects_wrong_parent(self):
        with patch.dict(sys.modules, {"run_profile": native}):
            guardian_spec = importlib.util.spec_from_file_location(
                "union22_guardian_item_boundary_tests", HERE / "native/run_guardian_diagnostic.py")
            guardian = importlib.util.module_from_spec(guardian_spec)
            guardian_spec.loader.exec_module(guardian)
        guardian.source_contract(self.current, self.lock, self.native_lock)
        for wrong, expected in (("source", "GUARDIAN_SOURCE69_CONTEXT"), ("place", "GUARDIAN_PLACE_PAIR")):
            with self.subTest(wrong=wrong):
                root = self.current_copy()
                path = "sources/" + compose.ITEM_SOURCE if wrong == "source" else compose.PLACE
                shutil.copyfile(root / path, root / compose.ITEM_OFF / path)
                with self.assertRaisesRegex(ValueError, expected):
                    guardian.source_contract(root, self.lock, self.native_lock)

    def test_beast_h72_parent_payload_or_swapped_archive_rejected(self):
        for mutation in ("source", "archive", "guardian_source", "guardian_archive"):
            with self.subTest(mutation=mutation):
                root = self.current_copy()
                if mutation == "source":
                    raw = root / compose.BEAST_OFF / "sources" / compose.BEAST_SOURCE
                    raw.write_bytes((root / "sources" / compose.BEAST_SOURCE).read_bytes())
                elif mutation == "archive":
                    shutil.copyfile(root / compose.BOT_OFF_ARCHIVE, root / compose.BEAST_OFF_ARCHIVE)
                elif mutation == "guardian_source":
                    raw = root / compose.GUARDIAN_OFF / "sources" / compose.GUARDIAN_SOURCE
                    raw.write_bytes((root / "sources" / compose.GUARDIAN_SOURCE).read_bytes())
                else:
                    shutil.copyfile(root / compose.BEAST_OFF_ARCHIVE, root / compose.GUARDIAN_OFF_ARCHIVE)
                self.reject_core(root)

    def test_bot_parent_payload_or_swapped_archive_rejected(self):
        for mutation in ("source", "archive"):
            with self.subTest(mutation=mutation):
                root = self.current_copy()
                if mutation == "source":
                    path = root / compose.BOT_OFF / "sources" / compose.HUD_SOURCE
                    path.write_bytes(path.read_bytes() + b"\n-- lost exact HUD parent\n")
                else:
                    shutil.copyfile(root / compose.HUD_OFF_ARCHIVE, root / compose.BOT_OFF_ARCHIVE)
                self.reject_core(root)

    def test_missing_or_reordered_bot_build_commands_rejected(self):
        for mutation, reason in (("missing", "CORE_COMMAND_COMPLETION"),
                                 ("order", "CORE_BUILD_STAGE_ORDER"),
                                 ("forged_reuse", "CORE_COMPILE_REUSE_PRIOR_BR_SET")):
            with self.subTest(mutation=mutation):
                root = self.current_copy()
                report = verify.data(root / "CORE_BUILD_REPORT.json")
                report["build_command_namespace"]["committed_root"] = str(root)
                commands = report["commands"]
                stage = Path(report["build_command_namespace"]["executed_stage"])
                bot_dir, hud_dir = stage / compose.BOT_OFF, stage / compose.HUD_OFF
                bot_compile = ["--text", str(bot_dir / "sources" / compose.BOT_SOURCE)]
                bot_index, = [index for index, row in enumerate(commands) if row["command"][1:] == bot_compile]
                self.assertEqual([row["command"][1:] for row in commands[bot_index:bot_index + 4]], [
                    bot_compile,
                    ["build", str(bot_dir / compose.PROJECT), "-o", str(bot_dir / compose.PLACE)],
                    ["--text", str(hud_dir / "sources" / compose.HUD_SOURCE)],
                    ["build", str(hud_dir / compose.PROJECT), "-o", str(hud_dir / compose.PLACE)],
                ])
                if mutation == "missing":
                    del commands[bot_index:bot_index + 2]
                elif mutation == "forged_reuse":
                    reused = report["compile_reuse_prior_br"]
                    self.assertTrue(reused)
                    reused.pop(next(iter(reused)))
                else:
                    commands[bot_index:bot_index + 4] = commands[bot_index + 2:bot_index + 4] + commands[bot_index:bot_index + 2]
                compose.write_json(root / "CORE_BUILD_REPORT.json", report)
                with self.assertRaisesRegex(ValueError, reason):
                    verify.verify_core(root, self.prior, self.reports, self.context)
                self.assertFalse((root / "delivery").exists())

    def test_bot_independent_programs_bind_current16_and_scenario_configuration(self):
        contract, _ = verify.independent_bot_contract(self.native_lock)
        programs = {}
        for item in contract["scenarios"]:
            scenario = item["scenario_id"]
            program, assembly = verify.independent_bot_generated(self.current, self.native_lock, scenario)
            self.assertEqual(assembly["scenario_id"], scenario)
            self.assertEqual(assembly["configuration_substitutions"], item["configuration_substitutions"])
            self.assertEqual(assembly["case_assembly"], item["case_assembly_identity"])
            self.assertEqual(len(assembly["full_body_byte_ranges"]), 16)
            for path, row in assembly["full_body_byte_ranges"].items():
                body = (self.current / "sources" / path).read_bytes()
                self.assertEqual(program[row["start"]:row["end"]], body)
                self.assertEqual(program.count(body), 1)
                self.assertEqual(compose.identity(body), self.native_lock["sources"][path])
            programs[scenario] = program
        self.assertEqual(len(set(programs.values())), 9)
        cases = {item["scenario_id"]: item for item in contract["scenarios"]}
        a, b = "candidate_route62_TEAM_normal", "candidate_route58_TEAM_normal"
        self.assertEqual(cases[a]["expected_ordered_CASE_names"], cases[b]["expected_ordered_CASE_names"])
        self.assertNotEqual(programs[a], programs[b])
        # These two additional bodies are absent from the original two programs.
        for suite in self.native_lock["suites"]:
            original, _, _ = verify.independent_generated(self.current, self.native_lock, suite)
            for path in (compose.BOT_SOURCE, "ServerScriptService/EGGRUMBLE_BotPathRouter.luau"):
                self.assertNotIn((self.current / "sources" / path).read_bytes(), original)

    def test_bot_source_reconstruction_rejects_stale_bot_wrong_router_or_truncated_host(self):
        for mutation in ("stale_bot", "wrong_router", "truncated_host"):
            with self.subTest(mutation=mutation):
                root = self.current_copy()
                if mutation == "stale_bot":
                    path = root / "sources" / compose.BOT_SOURCE
                    old = root / compose.COMBAT_VISUAL_OFF / "sources" / compose.BOT_SOURCE
                    path.write_bytes(old.read_bytes())
                    substituted = copy.deepcopy(self.native_lock)
                    substituted["sources"][compose.BOT_SOURCE] = compose.identity(old.read_bytes())
                    substituted["bot_vault_supplement"]["selected_sources"][compose.BOT_SOURCE] = (
                        substituted["sources"][compose.BOT_SOURCE])
                    with self.assertRaisesRegex(ValueError, "BOT_EXACT_DISPLAY_SOURCE"):
                        verify.independent_bot_contract(substituted)
                elif mutation == "wrong_router":
                    path = root / "sources/ServerScriptService/EGGRUMBLE_BotPathRouter.luau"
                    path.write_bytes(path.read_bytes() + b"\n-- wrong router\n")
                else:
                    path = root / "sources/ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau"
                    path.write_bytes(path.read_bytes()[:-20])
                with self.assertRaisesRegex(ValueError, "BOT_SOURCE_PROFILE"):
                    verify.independent_bot_generated(root, self.native_lock, "candidate_route62_TEAM_normal")

    def test_hud_only_rollback_other_source_mutation_rejected(self):
        root = self.current_copy()
        path = root / compose.HUD_OFF / "sources" / self.first
        path.write_bytes(path.read_bytes() + b"\n-- wrong current RC rollback\n")
        self.reject_core(root)

    def test_hud_only_rollback_archive_mutation_rejected(self):
        root = self.current_copy()
        # The full old BR archive is valid by itself, but is not a HUD-only inverse.
        shutil.copyfile(root / compose.OFF_ARCHIVE, root / compose.HUD_OFF_ARCHIVE)
        self.reject_core(root)

    def test_followup_provenance_mutation_rejected(self):
        root = self.current_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["followup_repair"]["claim_id"] = self.lock["claim_id"]
        compose.write_json(root / compose.RECEIPT, receipt)
        with self.assertRaisesRegex(ValueError, "FINAL_RECEIPT_FIELD_SET_OR_FACTS"):
            verify.verify_core(root, self.prior, self.reports, self.context)

    def test_original_39_workflow_step_payloads_byte_exact(self):
        workflow = (REPO / ".github/workflows/gq8-real63-source-composite.yml").read_bytes().decode("utf-8")
        # Only the reviewed original-input transport changes; invert it before
        # checking the unchanged historical 39-step contract.
        old_transport = (
            '          mkdir -p /tmp/gq863/{base55,hud59,trade62,formal62,formal63,viral56,counter56}\n'
            '          gh run download 44393525211 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL55-CANONICAL-PRIVATE-STUDIO --dir /tmp/gq863/base55\n'
            '          gh run download 44401178585 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL59-HUD-MAP-CANONICAL-PRIVATE-STUDIO --dir /tmp/gq863/hud59\n'
            '          gh run download 44402402944 --repo "$GITHUB_REPOSITORY" --name GQ8-REAL62-HUD59-TRADE3-PRIVATE-NOT-OFFICIAL --dir /tmp/gq863/trade62\n'
            '          gh run download 44404334603 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL62-HUD-TRADE-PRIVATE-STUDIO --dir /tmp/gq863/formal62\n'
            '          gh run download 44413796990 --repo "$GITHUB_REPOSITORY" --name P0D-EGGRUMBLE-V3-REAL63-BASIC-DODGE-CANONICAL-PRIVATE-STUDIO --dir /tmp/gq863/formal63\n'
            '          gh run download 44398710101 --repo "$GITHUB_REPOSITORY" --name GQ8-REAL56-VIRAL-CAPTURE-PRIVATE-NOT-OFFICIAL --dir /tmp/gq863/viral56\n'
            '          gh run download 44397387116 --repo "$GITHUB_REPOSITORY" --name GQ822-REAL56-CURRENT-FORMAL55-COUNTER-PRIVATE-NOT-OFFICIAL --dir /tmp/gq863/counter56\n'
        )
        new_transport = '          python3 -B quality_gameplay/gq8_real63_intake_20261119/restore_original_inputs.py --out /tmp/gq863\n'
        original = {"bytes": 106837,
                    "sha256": "0ab1ece54d56747dd655146ef3f4425ab2ad0346bd9843956a9d6dcd532cd039"}

        def check_original_prefix(candidate):
            self.assertEqual(candidate.count(new_transport), 1)
            self.assertNotIn(old_transport, candidate)
            prefix = candidate.split("    steps:\n", 1)[1].split(
                '      - name: "Union22: exact existing hunks after the unchanged BR-only prior boundary"\n', 1)[0]
            self.assertEqual(prefix.count(new_transport), 1)
            restored = prefix.replace(new_transport, old_transport, 1)
            self.assertEqual(compose.identity(restored.encode()), original)

        check_original_prefix(workflow)
        self.assertEqual(workflow.count("path: artifacts/real69_union22/delivery/"), 1)
        # Historical bytes, loader commands and multiplicity are exact; even a
        # physical LF-to-CRLF change must fail the inverse contract.
        mutations = {
            "historical_head": workflow.replace(
                "44393525211:a6020867fac80fa3b2ca47478625873fc6f3678e",
                "44393525211:b6020867fac80fa3b2ca47478625873fc6f3678e", 1),
            "loader_output": workflow.replace("--out /tmp/gq863\n", "--out /tmp/gq863x\n", 1),
            "duplicate_loader": workflow.replace(new_transport, new_transport * 2, 1),
            "prefix_crlf": workflow.replace("          set -euo pipefail\n", "          set -euo pipefail\r\n", 1),
        }
        for label, mutated in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(mutated, workflow)
                with self.assertRaises(AssertionError):
                    check_original_prefix(mutated)

    def test_actual_final_retention(self):
        result = verify.verify_core(self.current, self.prior, self.reports, self.context)
        reports = verify.retention_reports(self.current, result, self.context)
        self.assertEqual(reports["UNION22_FINAL_17_MARKER_RETENTION.json"]["source_family_marker_count"], 17)
        self.assertEqual(reports["UNION22_FINAL_ALL48_RAW.json"]["original_legacy_flags"], 48)

    def test_dynamic_actual_receipt_not_whole_hash_pinned(self):
        root = self.prior_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["test_only_distinct_receipt_metadata"] = "same exact prior profile"
        compose.write_json(root / compose.RECEIPT, receipt)
        result = compose.load_inputs(root, root)
        self.assertNotEqual(result["receipt_raw"], (self.prior / compose.RECEIPT).read_bytes())
        self.assertEqual(len(result["sources"]), 69)

    def test_unknown_prior_source_rejected(self):
        root = self.prior_copy()
        path = root / "sources" / self.first
        path.write_bytes(path.read_bytes() + b"\n-- unknown change\n")
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_extra_prior_source_rejected(self):
        root = self.prior_copy()
        (root / "sources/extra.luau").write_text("return {}\n")
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_unknown_prior_place_rejected(self):
        root = self.prior_copy()
        path = root / compose.PLACE
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_prior_root_symlink_rejected(self):
        link = self.temporary() / "link"
        link.symlink_to(self.prior, target_is_directory=True)
        with self.assertRaises(ValueError):
            compose.load_inputs(link, link)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            compose.strict_json(b'{"canonical_build":false,"canonical_build":true}')

    def test_receipt_source_lie_rejected(self):
        root = self.prior_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["source_hashes"][next(iter(receipt["source_hashes"]))] = "0" * 64
        compose.write_json(root / compose.RECEIPT, receipt)
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_canonical_string_rejected(self):
        root = self.prior_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["canonical_build"] = "true"
        compose.write_json(root / compose.RECEIPT, receipt)
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def test_context_false_formal_rejected(self):
        context = copy.deepcopy(self.context)
        context.update(kind="PR_CANDIDATE", canonical_build=True, official_build_head=context["build_head"])
        receipt = verify.data(self.prior / compose.RECEIPT)
        with self.assertRaises(ValueError):
            compose.validate_context(context, receipt)

    def test_cli_provenance_has_no_offline_fallback(self):
        receipt = verify.data(self.prior / compose.RECEIPT)
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            compose.live_context(receipt, receipt["build_head"])

    def test_hunk_removed_bytes_rejected(self):
        hunk = {"start": 0, "stop": 1, "old": "wrong\n", "new": "new\n",
                "old_identity": compose.identity(b"wrong\n"), "new_identity": compose.identity(b"new\n")}
        with self.assertRaises(ValueError):
            compose.apply_hunks(b"actual\n", [hunk])

    def test_hunk_overlap_rejected(self):
        hunk = {"start": 0, "stop": 1, "old": "old\n", "new": "new\n",
                "old_identity": compose.identity(b"old\n"), "new_identity": compose.identity(b"new\n")}
        with self.assertRaises(ValueError):
            compose.apply_hunks(b"old\n", [hunk, hunk])

    def test_double_application_rejected(self):
        root = self.current
        with self.assertRaises(ValueError):
            compose.load_inputs(root, root)

    def late_mutation_control(self, target):
        prior = self.prior_copy()
        output = self.temporary() / "candidate"
        commands = verify.data(self.current / "CORE_BUILD_REPORT.json")["commands"]
        last_call = len(commands)
        self.assertEqual(commands[-1]["command"][1], "build")
        compiler = Path(next(c["command"][0] for c in commands if c["command"][1] == "--text"))
        rojo = Path(next(c["command"][0] for c in commands if c["command"][1] == "build"))
        real_run = compose.run_checked
        calls = 0
        def mutate_after_last_real_build(command, logs, *args, **kwargs):
            nonlocal calls
            result = real_run(command, logs, *args, **kwargs)
            calls += 1
            if calls == last_call:
                self.assertEqual(command[1], "build")
                stage = Path(command[-1]).parent.parent
                path = ((stage / compose.BOT_OFF / "sources" / compose.BOT_SOURCE) if target == "bot_parent"
                        else (prior if target == "input" else stage) / "sources" / self.first)
                path.write_bytes(path.read_bytes() + b"\n-- reviewer late mutation control\n")
            return result
        expected = "PRIOR_SOURCE_IDENTITY" if target == "input" else "STAGED_OUTPUT_CHANGED_AFTER_BUILD"
        with patch.object(compose, "run_checked", mutate_after_last_real_build), self.assertRaisesRegex(ValueError, expected):
            compose.build_source_candidate(prior, prior, output, compiler, rojo, self.context)
        self.assertEqual(calls, last_call)
        self.assertFalse(output.exists())
        stages = list(output.parent.glob(output.name + ".building-*"))
        self.assertEqual(len(stages), 1)
        self.assertTrue((stages[0] / "FAILED.json").is_file())
        self.assertFalse((stages[0] / "CORE_BUILD_REPORT.json").exists())
        self.assertFalse((stages[0] / compose.RECEIPT).exists())
        self.assertFalse((stages[0] / "delivery").exists())

    def test_late_input_mutation_cannot_leave_success_report(self):
        self.late_mutation_control("input")

    def test_late_staged_source_mutation_cannot_commit(self):
        self.late_mutation_control("stage")

    def test_late_bot_parent_source_mutation_cannot_commit(self):
        self.late_mutation_control("bot_parent")

    def test_final_source_mutation_rejected(self):
        root = self.current_copy()
        p = root / "sources" / self.first
        p.write_bytes(p.read_bytes() + b"\n-- unknown final\n")
        self.reject_core(root)

    def test_final_non_source_property_mutation_rejected(self):
        root = self.current_copy()
        p = root / compose.PLACE
        p.write_bytes(p.read_bytes().replace(b'<roblox ', b'<roblox changed="1" ', 1))
        self.reject_core(root)

    def test_final_receipt_formal_lie_rejected(self):
        root = self.current_copy()
        receipt = verify.data(root / compose.RECEIPT)
        receipt["formal_rc_adoption_proven"] = not receipt["formal_rc_adoption_proven"]
        compose.write_json(root / compose.RECEIPT, receipt)
        self.reject_core(root)

    def test_immediate_prior_inverse_drift_rejected(self):
        root = self.current_copy()
        p = root / compose.OFF / "sources" / self.first
        p.write_bytes(p.read_bytes() + b"\n")
        self.reject_core(root)

    def test_opaque_prior_archive_drift_rejected(self):
        root = self.current_copy()
        p = root / "prior_boundary/legacy_rollbacks" / self.lock["prior_opaque_rollback_names"][0]
        p.write_bytes(p.read_bytes() + b"changed")
        self.reject_core(root)

    def test_archive_traversal_rejected(self):
        target = self.temporary() / "escape.tar.gz"
        with tarfile.open(target, "w:gz") as archive:
            info = tarfile.TarInfo(compose.OFF + "/../escape")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(ValueError):
            verify.verify_archive(target, {"escape": compose.identity(b"x")})

    def test_archive_duplicate_rejected(self):
        target = self.temporary() / "duplicate.tar.gz"
        with tarfile.open(target, "w:gz") as archive:
            for _ in range(2):
                info = tarfile.TarInfo(compose.OFF + "/one")
                info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(ValueError):
            verify.verify_archive(target, {"one": compose.identity(b"x"), "two": compose.identity(b"x")})

    def test_ordinary_readonly_payload_mode_accepted(self):
        root = self.temporary()
        path = root / "regular"
        path.write_bytes(b"x")
        path.chmod(0o444)
        self.assertEqual(compose.read_file(path), b"x")
        self.assertEqual(verify.files(root), {"regular": compose.identity(b"x")})

    def test_special_file_and_payload_directory_modes_rejected(self):
        root = self.temporary()
        path = root / "regular"
        path.write_bytes(b"x")
        path.chmod(0o4644)
        with self.assertRaises(ValueError):
            compose.read_file(path)
        with self.assertRaises(ValueError):
            verify.files(root)
        path.chmod(0o644)
        root.chmod(0o2755)
        with self.assertRaises(ValueError):
            verify.files(root)
        root.chmod(0o755)

    def test_archive_special_permission_bits_rejected(self):
        target = self.temporary() / "special-mode.tar.gz"
        with tarfile.open(target, "w:gz") as archive:
            info = tarfile.TarInfo(compose.OFF + "/one")
            info.size, info.mode = 1, 0o4644
            archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(ValueError):
            verify.verify_archive(target, {"one": compose.identity(b"x")})

    def test_missing_native_cannot_leave_delivery(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            verify.admit_delivery(self.current, self.prior, self.reports, self.temporary() / "missing", self.context)
        self.assertFalse((self.current / "delivery").exists())

    def test_original_vectors_exact_positive(self):
        for suite in self.native_lock["suites"].values():
            names = suite["expected_case_names"]
            stdout = "\n".join("CASE\t" + name + "\tPASS\tdetail" for name in names)
            self.assertTrue(native.exact_vector(stdout, names)[0])

    def test_revised_suite_is_separate_from_original_combined(self):
        self.assertEqual(set(self.native_lock["suites"]),
                         {"combined_clear_los", "objective_full_clear_los", "beast_target_selection"})
        self.assertEqual(self.native_lock["suites"]["beast_target_selection"]["input_variant"],
                         "GQ618_TARGET_ELIGIBILITY_CASES")
        self.assertEqual(len(self.native_lock["suites"]["beast_target_selection"]["expected_case_names"]), 12)
        self.assertEqual(self.native_lock["suites"]["combined_clear_los"]["input_variant"],
                         "BOUNDED_CLEAR_LOS_APPROACH_INPUT")
        self.assertEqual(self.native_lock["suites"]["objective_full_clear_los"]["input_variant"], "BOUNDED_CLEAR_LOS_MELEE_APPROACH_INPUT")
        with self.assertRaisesRegex(ValueError, "UNKNOWN_CASE_VARIANT"):
            native.assemble(self.current / "sources", self.native_lock, "original_combined")

    def test_clear_los_case_exact_inverse_preserves_original_assertions(self):
        original = (HERE / "native/fixtures/combined_cases.luau").read_bytes()
        revised = (HERE / "native/combined_cases_clear_los.luau").read_bytes()
        start = revised.index(b"local function clearNeutralApproach(neutral,target)\n")
        end = revised.index(b"local function neutralKO(session,label)\n", start)
        restored = revised[:start] + revised[end:]
        changed = b" rootPart.CFrame=clearNeutralApproach(neutral,target)\n"
        self.assertEqual(restored.count(changed), 1)
        restored = restored.replace(changed, b" rootPart.CFrame=CFrame.new(target-Vector3.new(0,-1,21),target)\n", 1)
        self.assertEqual(restored, original)

    def test_corrupt_new_case_rejected_before_execution(self):
        copied = self.temporary() / "native"
        shutil.copytree(HERE / "native", copied)
        p = copied / "combined_cases_clear_los.luau"
        p.write_bytes(p.read_bytes() + b"\n-- unknown case change\n")
        with patch.object(native, "HERE", copied), self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(self.native_lock)

    def test_old_case_pin_cannot_substitute_clear_los_case(self):
        altered = copy.deepcopy(self.native_lock)
        altered["suites"]["combined_clear_los"]["case"] = altered["fixtures"]["combined_cases.luau"]
        with self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(altered)

    def test_empty_missing_duplicate_extra_failed_case_rejected(self):
        names = self.native_lock["suites"]["objective_full_clear_los"]["expected_case_names"]
        lines = ["CASE\t" + name + "\tPASS\tdetail" for name in names]
        bad = [[], lines[:-1], lines + [lines[0]], lines + ["CASE\tEXTRA\tPASS\tdetail"],
               [lines[0].replace("\tPASS\t", "\tFAIL\t")] + lines[1:], list(reversed(lines))]
        for case in bad:
            self.assertFalse(native.exact_vector("\n".join(case), names)[0])

    def test_new_build_directory_preexisting_rejected(self):
        base = self.temporary()
        build = base / "existing-build"
        build.mkdir()
        with self.assertRaises(ValueError):
            native.run_profile(self.current / "sources", base / "source", build, base / "out",
                               Path("/missing-cmake"), Path("/missing-ninja"), Path("/missing-git"),
                               Path("/missing-cc"), Path("/missing-cxx"), self.context)
        self.assertFalse((base / "out").exists())

    def test_new_native_lock_cannot_accept_modified_fixture(self):
        altered = copy.deepcopy(self.native_lock)
        altered["fixtures"]["native_prefix.luau"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            native.fixture_snapshot(altered)

    def test_both_suites_assembly_full_body_exact(self):
        for suite in self.native_lock["suites"]:
            generated, _, ranges = native.assemble(self.current / "sources", self.native_lock, suite)
            self.assertEqual(len(ranges), 28)
            for rel, row in ranges.items():
                self.assertEqual(generated[row["start"]:row["end"]], (self.current / "sources" / rel).read_bytes())

    def test_objective_clear_los_case_inverse_preserves_original_assertions(self):
        original = (HERE / "native/objective_full_cases.luau").read_bytes()
        revised = (HERE / "native/objective_full_cases_clear_los.luau").read_bytes()
        first = b"-- OBJECTIVE_FULL_CLEAR_LOS_INPUT_BEGIN\n"
        last = b"-- OBJECTIVE_FULL_CLEAR_LOS_INPUT_END\n\n"
        self.assertEqual(revised.count(first), 1)
        self.assertEqual(revised.count(last), 1)
        start = revised.index(first)
        end = revised.index(last, start) + len(last)
        self.assertEqual(compose.identity(revised[start:end]), {"bytes": 768,
                         "sha256": "924c41396b10c0b31645f6edeefc456531671e5383e60510896091ae421daf30"})
        restored = revised[:start] + revised[end:]
        changed = (b" local beforeHealth=humanoid.Health\n local beforeWrites=#healthWrites\n"
                   b" local target=neutral.PrimaryPart.Position\n"
                   b" rootPart.CFrame=CFrame.new(clearMeleeApproach(neutral,character),target)\n"
                   b" local beforeRays=rayQueries\n")
        previous = (b" local beforeHealth=humanoid.Health\n local beforeWrites=#healthWrites\n"
                    b" local beforeRays=rayQueries\n local target=neutral.PrimaryPart.Position\n"
                    b" rootPart.CFrame=CFrame.new(target+Vector3.new(2,0,0),target)\n")
        self.assertEqual(restored.count(changed), 1)
        self.assertEqual(restored.replace(changed, previous, 1), original)

    def test_corrupt_objective_clear_los_case_rejected_before_execution(self):
        copied = self.temporary() / "native"
        shutil.copytree(HERE / "native", copied)
        p = copied / "objective_full_cases_clear_los.luau"
        p.write_bytes(p.read_bytes() + b"\n-- unknown objective case change\n")
        with patch.object(native, "HERE", copied), self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(self.native_lock)

    def test_original_objective_pin_cannot_substitute_clear_los_case(self):
        altered = copy.deepcopy(self.native_lock)
        original = altered["objective_case_amendment"]["original_case"]
        altered["suites"]["objective_full_clear_los"]["case"] = {k: original[k] for k in ("bytes", "sha256")}
        with self.assertRaisesRegex(ValueError, "CASE_MISMATCH"):
            native.fixture_snapshot(altered)

    def test_preserved_original_objective_drift_rejected_by_both_checks(self):
        copied = self.temporary() / "contract"
        shutil.copytree(HERE, copied)
        p = copied / "native/objective_full_cases.luau"
        p.write_bytes(p.read_bytes() + b"\n-- changed retained original\n")
        with patch.object(native, "HERE", copied / "native"), self.assertRaisesRegex(
                ValueError, "ORIGINAL_OBJECTIVE_CASE_NOT_PRESERVED"):
            native.fixture_snapshot(self.native_lock)
        with patch.object(verify, "HERE", copied), self.assertRaisesRegex(
                ValueError, "NATIVE_ORIGINAL_OBJECTIVE_NOT_PRESERVED"):
            verify.verify_native(copied / "missing-native-results", self.current, self.lock, self.context)


    def test_final_selected_hud_original_main_rejects_lost_anchor(self):
        historical_sources = self.current / compose.PORTRAIT_OFF / "sources"
        old_policy = self.lock["portrait_followup"]["rows"][compose.PORTRAIT_SOURCE]["parent"]["after"]
        old_traversal = self.lock["shorefoam_followup"]["rows"][compose.SHOREFOAM_SOURCE]["parent"]["after"]
        old_host = self.lock["team_win_rule_followup"]["rows"][compose.VAULT_SOURCE]["parent"]["after"]
        old_hud = self.lock["fractional_hp_followup"]["rows"][compose.HUD_SOURCE]["parent"]["after"]
        layout_lock = self.native_lock | {"sources": self.native_lock["sources"] | {
            compose.PORTRAIT_SOURCE: old_policy, compose.SHOREFOAM_SOURCE: old_traversal,
            compose.VAULT_SOURCE: old_host, compose.HUD_SOURCE: old_hud}}
        good = self.temporary() / "good-layout"
        prepared = native.prepare_selected_hud_layout(
            historical_sources, good, layout_lock)
        self.assertEqual(prepared["contract"]["condition_count"], 14)
        self.assertEqual((good / "generator.stderr.log").read_bytes(), b"")
        self.assertIn(b"GQ8_REAL63_UI_SQUARE_COLLISIONS_14_CASES_PASS",
                      (good / "generated.luau").read_bytes())
        copied = self.temporary() / "sources"
        shutil.copytree(historical_sources, copied)
        hud = copied / compose.HUD_SOURCE
        anchor = b"actions.ATTACK.Visible=actions.ATTACK.Visible and inMatch and not selecting"
        original = hud.read_bytes()
        self.assertEqual(original.count(anchor), 1)
        changed = original.replace(anchor, anchor.replace(b"inMatch", b"combatVisible"))
        hud.write_bytes(changed)
        revised = copy.deepcopy(layout_lock)
        revised["sources"][compose.HUD_SOURCE] = compose.identity(changed)
        rejected = self.temporary() / "rejected-layout"
        with self.assertRaisesRegex(ValueError, "GENERATOR_FAILED"):
            native.prepare_selected_hud_layout(copied, rejected, revised)
        self.assertFalse((rejected / "generated.luau").exists())
        self.assertIn(b"RED_REAL63_RUNTIME_LAYOUT_GATE",
                      (rejected / "generator.stderr.log").read_bytes())


class FinalAdmissionBoundary(unittest.TestCase):
    """Run explicitly after actual Native completion; no fixture or gate stubs."""
    ARTIFACT_STAGE = "final"

    @classmethod
    def setUpClass(cls):
        UnionBoundary.setUpClass.__func__(cls)
        _, paths = artifact_environment(cls.ARTIFACT_STAGE)
        cls.native = paths["UNION22_TEST_NATIVE"]
        verify.verify_native(cls.native, cls.current, cls.lock, cls.context)
        cls._core_snapshot = None

    def temporary(self):
        context = tempfile.TemporaryDirectory(prefix="union22-final-negative-")
        self.addCleanup(context.cleanup)
        return Path(context.name)

    def fresh_core(self):
        # One genuine build per interpreter; restore only to the original root.
        # Normal/-O remain separate. No receipt or executed path is rewritten.
        cls = type(self)
        if cls._core_snapshot is None:
            context = tempfile.TemporaryDirectory(prefix="union22-final-negative-core-")
            cls.addClassCleanup(context.cleanup)
            base = Path(context.name).resolve()
            work = base / "work"
            snapshot = base / "snapshot"
            output = work / "candidate"
            work.mkdir()
            self.addCleanup(shutil.rmtree, work)
            commands = verify.data(self.current / "CORE_BUILD_REPORT.json")["commands"]
            compiler = Path(next(c["command"][0] for c in commands if c["command"][1] == "--text"))
            rojo = Path(next(c["command"][0] for c in commands if c["command"][1] == "build"))
            compose.build_source_candidate(self.prior, self.reports, output, compiler, rojo, self.context)
            verify.verify_core(output, self.prior, self.reports, self.context)
            pin = verify.files(output)
            if (output / "delivery").exists():
                raise ValueError("RED_UNION22_NEGATIVE_SNAPSHOT_CONTAINS_DELIVERY")
            shutil.copytree(output, snapshot)
            if verify.files(snapshot) != pin:
                raise ValueError("RED_UNION22_NEGATIVE_SNAPSHOT_COPY_DRIFT")
            cls._core_snapshot = (base, pin)
            return output
        base, pin = cls._core_snapshot
        work = base / "work"
        snapshot = base / "snapshot"
        output = work / "candidate"
        if work.exists() or work.is_symlink():
            raise ValueError("RED_UNION22_NEGATIVE_WORK_NOT_CLEAN")
        if verify.files(snapshot) != pin:
            raise ValueError("RED_UNION22_NEGATIVE_SNAPSHOT_DRIFT")
        work.mkdir()
        self.addCleanup(shutil.rmtree, work)
        shutil.copytree(snapshot, output)
        if verify.files(output) != pin:
            raise ValueError("RED_UNION22_NEGATIVE_RESTORE_DRIFT")
        return output

    def check_failure(self, output, callback, native, reason):
        with callback, self.assertRaisesRegex(ValueError, reason):
            verify.admit_delivery(output, self.prior, self.reports, native, self.context)
        self.assertFalse((output / "delivery").exists())
        for stage in output.parent.glob(".union22-delivery-*"):
            self.assertTrue((stage / "FAILED.json").is_file())
            self.assertFalse((stage / "UNION22_FINAL_ADMISSION.json").exists())
            self.assertFalse((stage / "UNION22_DELIVERY_MANIFEST.json").exists())

    def phase_mutation(self, function_name, phase, mutation, copy_native=False):
        output = self.fresh_core()
        native = self.native
        if copy_native:
            native = self.temporary() / "native"
            shutil.copytree(self.native, native)
        original = getattr(verify, function_name)
        def after_real_check(*args, **kwargs):
            result = original(*args, **kwargs)
            mutation(output, native)
            return result
        self.check_failure(output, patch.object(verify, function_name, after_real_check), native,
                           "PAYLOAD_CHANGED_AFTER_" + phase)

    def bot_native_copy(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        return copied

    def test_score_regressions_reject_stale_score_with_fresh_receipt_hashes(self):
        copied = self.bot_native_copy()
        folder = copied / "score_relay"
        prefix = "EGGRUMBLE_RelayScoreRegression"
        runner = folder / (prefix + ".luau")
        on = (self.current / "sources" / compose.SCORE_SOURCE).read_bytes()
        off = (self.current / compose.SCORE_OFF / "sources" / compose.SCORE_SOURCE).read_bytes()
        self.assertEqual(runner.read_bytes().count(on), 1)
        runner.write_bytes(runner.read_bytes().replace(on, off, 1))
        receipt_path, aggregate_path = folder / "receipt.json", copied / "receipt.json"
        receipt, aggregate = verify.data(receipt_path), verify.data(aggregate_path)
        receipt["results"][prefix + ".spec.luau"]["program"] = compose.identity(runner.read_bytes())
        compose.write_json(receipt_path, receipt)
        aggregate["score_relay_regressions"] = compose.identity(receipt_path.read_bytes())
        compose.write_json(aggregate_path, aggregate)
        with self.assertRaisesRegex(ValueError, "SCORE_VERIFIED_EXACT_PROGRAM_AND_RUN"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_relay_presentation_rejects_stale_client_with_rebound_receipts(self):
        copied = self.bot_native_copy()
        evidence = copied / "relay_presentation"
        program_path = evidence / "generated.luau"
        client = (self.current / compose.RELAY_ELIGIBILITY_OFF / "sources" / compose.HUD_SOURCE).read_bytes()
        repair = self.lock["relay_presentation_followup"]
        mounted = client[repair["client_start"]:repair["client_end"]]
        self.assertEqual(program_path.read_bytes().count(mounted),1)
        program_path.write_bytes(program_path.read_bytes().replace(mounted,b"",1))
        receipt_path, aggregate_path = evidence / "receipt.json", copied / "receipt.json"
        receipt, aggregate = verify.data(receipt_path), verify.data(aggregate_path)
        receipt["generated"] = compose.identity(program_path.read_bytes())
        compose.write_json(receipt_path,receipt)
        aggregate["relay_presentation"] = compose.identity(receipt_path.read_bytes())
        compose.write_json(aggregate_path,aggregate)
        with self.assertRaisesRegex(ValueError,"RELAY_PRESENTATION_VERIFIED_PROGRAM_AND_RUN"):
            verify.verify_native(copied,self.current,self.lock,self.context)

    def rebind_mutated_bot_evidence(self, copied, scenario=None):
        # Negative controls refresh enclosing hashes so semantic checks, not a
        # stale outer digest, must reject the deliberately forged copy.
        folder = copied / "bot_vault"
        if scenario is not None:
            path = folder / scenario
            receipt = verify.data(path / "receipt.json")
            for key, name in (("generated", "generated.luau"), ("stdout", "stdout.log"), ("stderr", "stderr.log")):
                receipt[key] = compose.identity((path / name).read_bytes())
            compose.write_json(path / "receipt.json", receipt)
        summary = verify.data(folder / "receipt.json")
        summary["scenario_files"] = {name: pin for name, pin in verify.files(folder).items() if name != "receipt.json"}
        compose.write_json(folder / "receipt.json", summary)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["bot_vault_supplement"] = compose.identity((folder / "receipt.json").read_bytes())
        compose.write_json(copied / "receipt.json", aggregate)

    def test_place_changed_after_real_core_rejected(self):
        def mutate(root, _):
            p = root / compose.PLACE
            p.write_bytes(p.read_bytes() + b"\n<!-- after real core -->\n")
        self.phase_mutation("verify_core", "CORE", mutate)

    def test_project_changed_after_real_retention_rejected(self):
        def mutate(root, _):
            p = root / compose.PROJECT
            p.write_bytes(p.read_bytes() + b"\n")
        self.phase_mutation("retention_reports", "RETENTION", mutate)

    def test_place_changed_after_real_native_rejected(self):
        def mutate(root, _):
            p = root / compose.PLACE
            p.write_bytes(p.read_bytes() + b"\n<!-- after actual strong Native check -->\n")
        self.phase_mutation("verify_native", "NATIVE", mutate)

    def test_native_evidence_changed_after_real_native_rejected(self):
        def mutate(_, root):
            p = root / "objective_full_clear_los/stdout.log"
            p.write_bytes(p.read_bytes() + b"TRACE\tlate evidence drift\n")
        self.phase_mutation("verify_native", "NATIVE", mutate, copy_native=True)

    def test_bot_archive_changed_after_real_native_rejected(self):
        def mutate(root, _):
            shutil.copyfile(root / compose.HUD_OFF_ARCHIVE, root / compose.BOT_OFF_ARCHIVE)
        self.phase_mutation("verify_native", "NATIVE", mutate)

    def test_bot_route62_cannot_replace_route58_with_same_case_label(self):
        copied = self.bot_native_copy()
        source, target = "candidate_route62_TEAM_normal", "candidate_route58_TEAM_normal"
        folder = copied / "bot_vault"
        contract, _ = verify.independent_bot_contract(self.native_lock)
        items = {s["scenario_id"]: s for s in contract["scenarios"]}
        self.assertEqual(items[source]["expected_ordered_CASE_names"], items[target]["expected_ordered_CASE_names"])
        self.assertNotEqual((folder / source / "generated.luau").read_bytes(),
                            (folder / target / "generated.luau").read_bytes())
        shutil.copyfile(folder / source / "generated.luau", folder / target / "generated.luau")
        self.rebind_mutated_bot_evidence(copied, target)
        with self.assertRaisesRegex(ValueError, "BOT_GENERATED_PROGRAM_AND_RANGES"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_bot_missing_scenario_or_incomplete_duplicate_raw_vectors_rejected(self):
        scenario = "candidate_actors_TEAM_normal"
        for mutation, reason in (("scenario", "BOT_EVIDENCE_FILE_SET"),
                                 ("check", "BOT_RAW_CHECK_VECTOR"), ("duplicate", "BOT_RAW_CASE_VECTOR")):
            with self.subTest(mutation=mutation):
                copied = self.bot_native_copy()
                if mutation == "scenario":
                    shutil.rmtree(copied / "bot_vault/candidate_route58_TEAM_normal")
                    self.rebind_mutated_bot_evidence(copied)
                else:
                    path = copied / "bot_vault" / scenario / "stdout.log"
                    lines = path.read_bytes().splitlines(keepends=True)
                    if mutation == "check":
                        index = next(i for i, line in enumerate(lines) if line.startswith(b"CHECK\t"))
                        del lines[index]
                    else:
                        lines.append(next(line for line in lines if line.startswith(b"CASE\t")))
                    path.write_bytes(b"".join(lines))
                    self.rebind_mutated_bot_evidence(copied, scenario)
                with self.assertRaisesRegex(ValueError, reason):
                    verify.verify_native(copied, self.current, self.lock, self.context)

    def test_bot_forged_pass_stale_bot_wrong_router_or_truncated_program_rejected(self):
        scenario = "candidate_route62_TEAM_normal"
        for mutation in ("pass_marker", "stale_bot", "wrong_router", "truncated_host"):
            with self.subTest(mutation=mutation):
                copied = self.bot_native_copy()
                path = copied / "bot_vault" / scenario / "generated.luau"
                program = path.read_bytes()
                if mutation == "pass_marker":
                    changed = b'print("CASE\\tTEAM_normal\\tPASS\\tforged without game bodies")\n'
                else:
                    relative = (compose.BOT_SOURCE if mutation == "stale_bot" else
                                "ServerScriptService/EGGRUMBLE_BotPathRouter.luau" if mutation == "wrong_router" else
                                "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau")
                    body = (self.current / "sources" / relative).read_bytes()
                    self.assertEqual(program.count(body), 1)
                    if mutation == "stale_bot":
                        before_labels = self.current / compose.COMBAT_VISUAL_OFF / "sources" / relative
                        replacement = compose.apply_hunks(before_labels.read_bytes(), self.lock["bot_followup_repair"]["inverse"])
                    elif mutation == "wrong_router":
                        replacement = body + b"\n-- changed Router\n"
                    else:
                        replacement = body[:-20]
                    changed = program.replace(body, replacement, 1)
                path.write_bytes(changed)
                self.rebind_mutated_bot_evidence(copied, scenario)
                with self.assertRaisesRegex(ValueError, "BOT_GENERATED_PROGRAM_AND_RANGES"):
                    verify.verify_native(copied, self.current, self.lock, self.context)

    def test_bot_wrong_binary_build_context_and_command_rejected(self):
        scenario = "candidate_route62_TEAM_normal"
        for mutation, reason in (("binary", "BOT_SCENARIO_RECEIPT_BINDING"),
                                 ("build", "BOT_SCENARIO_RECEIPT_BINDING"),
                                 ("context", "BOT_SCENARIO_RECEIPT_BINDING"),
                                 ("source_receipt", "BOT_SCENARIO_RECEIPT_BINDING"),
                                 ("argv", "BOT_EXECUTED_COMMAND"), ("timeout", "BOT_EXECUTED_COMMAND"),
                                 ("exit", "BOT_PROCESS_EXIT_OR_STDERR")):
            with self.subTest(mutation=mutation):
                copied = self.bot_native_copy()
                path = copied / "bot_vault" / scenario / "receipt.json"
                receipt = verify.data(path)
                if mutation == "binary":
                    receipt["native"]["sha256"] = "0" * 64
                elif mutation == "build":
                    receipt["caller_fresh_build"]["target_build_started_ns"] -= 1
                elif mutation == "context":
                    receipt["execution_context"]["checkout_sha"] = "0" * 40
                elif mutation == "source_receipt":
                    receipt["source_receipt"]["sha256"] = "0" * 64
                elif mutation == "argv":
                    receipt["process"]["argv"][0] += "-different-vm"
                elif mutation == "timeout":
                    receipt["process"]["timed_out"] = True
                else:
                    receipt["process"]["exit_code"] = 1
                compose.write_json(path, receipt)
                self.rebind_mutated_bot_evidence(copied, scenario)
                with self.assertRaisesRegex(ValueError, reason):
                    verify.verify_native(copied, self.current, self.lock, self.context)

    def test_bot_aggregate_cannot_overclaim_body_coverage_or_process_count(self):
        for mutation in ("old28_scope", "server31", "omit_policy", "processes", "files"):
            with self.subTest(mutation=mutation):
                copied = self.bot_native_copy()
                path = copied / "receipt.json"
                aggregate = verify.data(path)
                if mutation == "old28_scope":
                    aggregate["source_count_executed_full_body_basis"] = "all_current_sources"
                elif mutation == "server31":
                    aggregate["full_body_coverage"]["distinct_server_union"] = 31
                elif mutation == "omit_policy":
                    aggregate["full_body_coverage"]["distinct_all_full_bodies"] = 30
                elif mutation == "processes":
                    aggregate["native_process_count"] = 11
                else:
                    aggregate["native_evidence_file_count"] = 62
                compose.write_json(path, aggregate)
                with self.assertRaisesRegex(ValueError, "NATIVE_AGGREGATE_BODY_AND_PROCESS_COVERAGE"):
                    verify.verify_native(copied, self.current, self.lock, self.context)

    def test_bot_log_changed_after_real_native_cannot_enter_delivery(self):
        def mutate(_, native_root):
            path = native_root / "bot_vault/candidate_parallel_TEAM_normal/stdout.log"
            path.write_bytes(path.read_bytes() + b"TRACE\tlate Bot log mutation\n")
        self.phase_mutation("verify_native", "NATIVE", mutate, copy_native=True)

    def test_bot_corpus_changed_after_real_native_cannot_enter_delivery(self):
        contract = self.temporary() / "contract"
        shutil.copytree(HERE, contract)
        def mutate(_, __):
            path = contract / "native/bot_vault_cases.json"
            path.write_bytes(path.read_bytes() + b"\n")
        # Mutate only an isolated contract copy, never the repository corpus.
        with patch.object(verify, "HERE", contract):
            self.phase_mutation("verify_native", "NATIVE", mutate)

    def test_unknown_file_in_delivery_stage_rejected(self):
        output = self.fresh_core()
        original = verify.shutil.copytree
        def mutate_stage_after_copy(src, dst, *args, **kwargs):
            result = original(src, dst, *args, **kwargs)
            if Path(dst).name == "native_evidence":
                (Path(dst).parent / "unexpected.txt").write_text("not part of the validated input or reports\n")
            return result
        self.check_failure(output, patch.object(verify.shutil, "copytree", mutate_stage_after_copy),
                           self.native, "DELIVERY_COPY_NOT_VALIDATED_STARTING_PAYLOAD")

    def test_original_case_tail_cannot_be_relabelled_as_clear_los(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        suite = copied / "combined_clear_los"
        program = (suite / "generated.luau").read_bytes()
        revised = (HERE / "native/combined_cases_clear_los.luau").read_bytes()
        original = (HERE / "native/fixtures/combined_cases.luau").read_bytes()
        self.assertTrue(program.endswith(revised))
        altered = program[:-len(revised)] + original
        (suite / "generated.luau").write_bytes(altered)
        receipt = verify.data(suite / "receipt.json")
        receipt["generated"] = compose.identity(altered)
        compose.write_json(suite / "receipt.json", receipt)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["combined_clear_los"] = compose.identity((suite / "receipt.json").read_bytes())
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_EXECUTED_PROGRAM_NOT_EXACT"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_unexecuted_original_combined_cannot_enter_aggregate(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["original_combined"] = dict(aggregate["suites"]["combined_clear_los"])
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_AGGREGATE_SUITE_SET"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_original_objective_tail_cannot_be_relabelled_as_clear_los(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        suite = copied / "objective_full_clear_los"
        program = (suite / "generated.luau").read_bytes()
        revised = (HERE / "native/objective_full_cases_clear_los.luau").read_bytes()
        original = (HERE / "native/objective_full_cases.luau").read_bytes()
        self.assertTrue(program.endswith(revised))
        altered = program[:-len(revised)] + original
        (suite / "generated.luau").write_bytes(altered)
        receipt = verify.data(suite / "receipt.json")
        receipt["generated"] = compose.identity(altered)
        compose.write_json(suite / "receipt.json", receipt)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["objective_full_clear_los"] = compose.identity((suite / "receipt.json").read_bytes())
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_EXECUTED_PROGRAM_NOT_EXACT"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_unexecuted_original_objective_cannot_enter_aggregate(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["suites"]["objective_full"] = dict(aggregate["suites"]["objective_full_clear_los"])
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_AGGREGATE_SUITE_SET"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_selected_layout_program_cannot_be_replaced_by_pass_marker(self):
        copied = self.temporary() / "native"
        shutil.copytree(self.native, copied)
        folder = copied / "selected_hud_layout"
        fake = b'print("GQ8_REAL63_UI_SQUARE_COLLISIONS_14_CASES_PASS")\n'
        (folder / "generated.luau").write_bytes(fake)
        receipt = verify.data(folder / "receipt.json")
        receipt["generated"] = compose.identity(fake)
        compose.write_json(folder / "receipt.json", receipt)
        aggregate = verify.data(copied / "receipt.json")
        aggregate["selected_hud_layout"] = compose.identity((folder / "receipt.json").read_bytes())
        compose.write_json(copied / "receipt.json", aggregate)
        with self.assertRaisesRegex(ValueError, "NATIVE_SELECTED_LAYOUT_GENERATED_PROGRAM"):
            verify.verify_native(copied, self.current, self.lock, self.context)

    def test_selected_layout_source_and_execution_forgery_rejected(self):
        for mutation, reason in [
            ("generator", "NATIVE_SELECTED_LAYOUT_GENERATOR_IDENTITY"),
            ("selected_hud", "NATIVE_SELECTED_LAYOUT_FINAL_SOURCE"),
            ("optimized_python", "NATIVE_SELECTED_LAYOUT_EXECUTED_COMMAND"),
            ("nonzero_native", "NATIVE_SELECTED_LAYOUT_EXECUTED_COMMAND"),
            ("missing_aggregate", "NATIVE_SELECTED_LAYOUT_AGGREGATE_BINDING"),
        ]:
            with self.subTest(mutation=mutation):
                copied = self.temporary() / "native"
                shutil.copytree(self.native, copied)
                folder = copied / "selected_hud_layout"
                receipt = verify.data(folder / "receipt.json")
                if mutation == "generator":
                    p = folder / "native_layout.py"
                    p.write_bytes(p.read_bytes() + b"\n# changed original gate\n")
                    receipt["generator"] = compose.identity(p.read_bytes())
                elif mutation == "selected_hud":
                    p = folder / "sources/EGGRUMBLE_HudIntelRuntime.client.luau"
                    p.write_bytes(p.read_bytes() + b"\n-- changed selected body\n")
                    receipt["selected_sources"][compose.HUD_SOURCE] = compose.identity(p.read_bytes())
                elif mutation == "optimized_python":
                    receipt["commands"]["generator"]["argv"].insert(1, "-O")
                elif mutation == "nonzero_native":
                    receipt["commands"]["native"]["exit_code"] = 1
                compose.write_json(folder / "receipt.json", receipt)
                aggregate = verify.data(copied / "receipt.json")
                aggregate["selected_hud_layout"] = compose.identity((folder / "receipt.json").read_bytes())
                if mutation == "missing_aggregate":
                    del aggregate["selected_hud_layout"]
                compose.write_json(copied / "receipt.json", aggregate)
                with self.assertRaisesRegex(ValueError, reason):
                    verify.verify_selected_hud_layout(
                        copied, self.current, self.native_lock,
                        verify.data(copied / "build_receipt.json"), aggregate, self.context)


class UnionOfflineContract(unittest.TestCase):
    """Repository-only checks; no artifact or runtime acceptance is claimed."""
    @classmethod
    def setUpClass(cls):
        cls.lock = compose.load_lock()
        cls.native_lock = native.load_lock()

    def test_guardian_hosted_sparse_donor_includes_and_checks_original_dependencies(self):
        with patch.object(sys, "path", [str(HERE / "native"), *sys.path]):
            guardian_spec = importlib.util.spec_from_file_location(
                "union22_guardian_sparse_tests", HERE / "native/run_guardian_diagnostic.py")
            guardian = importlib.util.module_from_spec(guardian_spec)
            guardian_spec.loader.exec_module(guardian)
        prefix = guardian.DONOR_PACKAGE + "/"
        contract_path = "stealth_target/INPUT_LOCK.json"
        missing_before = ("role_los/INPUT_LOCK.json", "role_session/apply_role_snapshot.py",
                          "role_session/INPUT_LOCK.json", "role_session/README.md",
                          "role_session/case.luau", "role_session/fixture_boundary.luau", "role_session/run.py")
        originals = set(missing_before) | {"role_los/README.md", "role_los/apply_existing_repairs.py",
                                           "role_los/case.luau", "role_los/fixture_boundary.luau", "role_los/run.py"}
        payload = {name: name.encode() for name in originals | set(guardian.STEALTH_INPUTS)}
        payload[contract_path] = json.dumps({
            "existing_pr_files": {prefix + name: native.identity(payload[name]) for name in sorted(originals)}
        }).encode()
        stealth = {name: (len(payload[name]), native.identity(payload[name])["sha256"])
                   for name in guardian.STEALTH_INPUTS}
        requests = []
        corrupted = set()

        def response(command, **kwargs):
            expected = f"repos/{compose.REPOSITORY}/contents/{prefix}"
            self.assertEqual(command[:4], ["gh", "api", "-H", "Accept: application/vnd.github.raw+json"])
            self.assertTrue(command[4].startswith(expected))
            relative, revision = command[4][len(expected):].split("?ref=")
            self.assertEqual(revision, guardian.DONOR_HEAD)
            requests.append(relative)
            body = payload[relative] + (b"altered" if relative in corrupted else b"")
            return subprocess.CompletedProcess(command, 0, body, b"")

        with tempfile.TemporaryDirectory(prefix="union22-sparse-donor-") as directory, \
                patch.dict(os.environ, {"GITHUB_REPOSITORY": compose.REPOSITORY, "GH_TOKEN": "unit-test"}), \
                patch.object(guardian, "STEALTH_INPUTS", stealth), patch.object(guardian.subprocess, "run", response):
            root = Path(directory)
            good = root / "good"
            guardian.load_hosted_donor(good)
            self.assertEqual(guardian.observe_donor(good)[1], {name: native.identity(raw) for name, raw in payload.items()})
            self.assertCountEqual(requests, payload.keys())
            corrupted.add("role_session/apply_role_snapshot.py")
            with self.assertRaisesRegex(ValueError, "GUARDIAN_PINNED_API_INPUT:role_session/apply_role_snapshot.py"):
                guardian.load_hosted_donor(root / "corrupt")

    def test_profile_and_native_lock_share_exact69(self):
        self.assertEqual(len(self.lock["sources"]), 69)
        self.assertEqual(self.native_lock["sources"],
                         {name: row["after"] for name, row in self.lock["sources"].items()})
        self.assertEqual(set(self.native_lock["suites"]),
                         {"combined_clear_los", "objective_full_clear_los", "beast_target_selection"})
        self.assertEqual(self.native_lock["suites"]["beast_target_selection"]["input_variant"],
                         "GQ618_TARGET_ELIGIBILITY_CASES")
        self.assertEqual(len(self.native_lock["suites"]["beast_target_selection"]["expected_case_names"]), 12)

    def test_followup_preserves_original_source_rows_phase_and_claim(self):
        repair = self.lock["followup_repair"]
        self.assertEqual(self.lock["claim_id"], "P0D-GQ470-UNION22-20261122-4B669")
        self.assertFalse(self.lock["author_origins"]["new_lua_authored"])
        self.assertTrue(repair["new_lua_authored"])
        self.assertEqual(repair["claim_id"], "P0D-GQ828-MOUNTED-HUD-20261123-79005A1F")
        self.assertEqual(repair["base_rc_head"], "dcb501673d7959e4904cf360ef0119917e6aa2e0")
        self.assertEqual(repair["grant_commit"], "9ed7b2af97de4ce32be89f6cf91450095188fcea")
        self.assertEqual(repair["grant_registry_blob"], "e0065fba728c65ab745edc0f4a5df0215f793484")
        self.assertEqual(repair["grant_comment"], 7088004228)
        self.assertEqual(repair["grant_status"], "GRANTED_SCOPE_4_NOT_ADOPTED")
        self.assertEqual(repair["grant_scope_version"], 4)
        self.assertEqual(repair["grant_expires_at"], "2026-11-23T03:51:42.000Z")
        self.assertEqual(repair["grant_independent_reviewer_context"], "/root/rules_audit")
        previous = repair["superseded_revision"]["followup_repair"]
        self.assertEqual(previous["grant_commit"], "b85eca5ce272daf3a63a7dba029a977a0effec79")
        self.assertEqual(repair["superseded_revision"]["published_head"],
                         "2e7d18df9102a7272caefe83e718cfa91c06fe12")
        self.assertEqual(previous["repaired_hud"],
                         {"bytes": 25338, "sha256": "d794669eb82ad8ff0804241879904c8e26e55d9c0f93fe5e771135f66651f001"})
        self.assertEqual(repair["prior_profile"]["sha256"], "826235327ba98bbde81242661d0929e81e8dda6d69550e1d040586414c7a0b60")
        # Restore H72 before removing the later Bot rows for the HUD-stage proof.
        parent_rows = copy.deepcopy(compose.beast_parent_profile(before_guardian(self.lock))["sources"])
        parent_rows[compose.BOT_SOURCE]["after"] = self.lock["bot_followup_repair"]["parent_bot"]
        parent_rows[compose.BOT_SOURCE]["forward"] = []
        parent_rows[compose.BOT_SOURCE]["inverse"] = []
        self.assertEqual(sum(len(row["forward"]) for row in parent_rows.values()), 169)
        remaining = {p: r for p, r in parent_rows.items() if p != compose.HUD_SOURCE}
        encode = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual(compose.identity(encode(remaining)), {'bytes': 272752, 'sha256': 'e2a6bcfd7d060f0da78b4a5971a2e887f26681b0477b1e5f70d99abbf80b6066'})
        prior_hud = self.lock["relay_presentation_followup"]["rows"][compose.HUD_SOURCE]["parent"]
        phase = prior_hud["forward"][0]
        self.assertEqual(compose.identity(encode(phase)), {'bytes': 997, 'sha256': '2ab2ddfd837f0ba1c78ebef579b54149c72c2c964730c3e1fcc36e4cc2cb17ec'})
        self.assertEqual(repair["current_hud"], {"bytes": 24779, "sha256": "3bf0d95802e1806d9167251417fd560673bd134c813d1cfb5407f163b322cf90"})
        self.assertEqual(repair["repaired_hud"], {"bytes": 25323, "sha256": "a5983ba5bfb8a3e743a767b59984ec7be6e48f46fa073c98a784b8afc0f674f4"})
        self.assertFalse(repair["hud_behavior_evidence"]["canonical_server28_suites_execute_hud"])
        self.assertFalse(self.native_lock["selected_hud_layout"]["hud_runtime_executed"])
        self.assertTrue(self.native_lock["selected_hud_layout"]["policy_full_body_executed"])
        self.assertEqual(self.native_lock["selected_hud_layout"]["condition_count"], 14)

    def test_bot_reuse_preserves_exact_parent_rows_and_registered_scope(self):
        beast = before_guardian(self.lock)
        h72 = compose.beast_parent_profile(beast)
        repair = h72["bot_followup_repair"]
        self.assertEqual(repair['grant_status'], 'GRANTED_SCOPE_1_NOT_ADOPTED')
        self.assertEqual(repair['claim_id'], 'P0D-GQ484-BOT-VAULT-20261123-0A2BA23F')
        self.assertEqual(repair['grant_commit'], 'b4a7601c8624160610a1211d63142b8794d64861')
        self.assertEqual(repair['grant_registry_blob'], '5aed02901d3d1bea7b6eaf06b2a55a8d65f7e375')
        self.assertEqual(repair['grant_comment'], 7091519547)
        self.assertEqual(repair['grant_scope_version'], 1)
        self.assertEqual(repair['grant_expires_at'], '2026-11-23T10:15:20.638570+00:00')
        self.assertEqual(repair['grant_independent_reviewer_context'], 'CODEX_ROOT_B8C8E7B756CD:/root/environment_audit')
        self.assertEqual(repair['source_publisher'], 'CODEX_ROOT_B8C8E7B756CD:/root')
        self.assertEqual(repair['actual_hud_parent_head'], '93a1147561a531610ac1609ebc68cc0ecf546623')
        self.assertEqual(repair['accepted_hud_parent_profile'], {'bytes': 306439, 'sha256': '2ceb3072c1e69a6575693f09027dd226a60cdf8da352b8533f01ae1e78a7c375'})
        self.assertEqual(repair['hud_preview_profile'], {'bytes': 306211, 'sha256': 'c7c58795e7974a7338cc46d10dfe2d8f2b4e226e9a05dbf624a10599295ace4a'})
        self.assertTrue(repair["hud_parent_is_accepted"])
        self.assertFalse(repair["new_lua_authored"])
        self.assertFalse(repair["native_admission_proven"])
        self.assertFalse(repair["studio_proven"])
        self.assertEqual(repair["rollback_order"], ["BOT_TO_HUD_PARENT", "HUD_PARENT_TO_FB5"])
        self.assertEqual((repair["changed_sources_from_hud_parent"], repair["unchanged_sources_from_hud_parent"]), (1, 68))
        self.assertEqual(repair["parent_bot"], {"bytes": 19070, "sha256": "b09627fd0995ba5938f8af5950a53462ab5df82ed91be776c9368da7a1164693"})
        self.assertEqual(repair["repaired_bot"], {"bytes": 19625, "sha256": "c38bcf82df581d2d9f105f9d7843eef0eff8e8bd6315b8520765ee646e1c5051"})
        self.assertEqual(repair["source_candidate_origin"]["source"], repair["repaired_bot"])
        row = h72["sources"][compose.BOT_SOURCE]
        self.assertEqual(row["before"], repair["parent_bot"])
        self.assertEqual(row["after"], repair["repaired_bot"])
        self.assertEqual(row["forward"], repair["forward"])
        self.assertEqual(row["inverse"], repair["inverse"])
        self.assertEqual(sum(len(r["forward"]) for r in h72["sources"].values()), 171)
        self.assertEqual(sum(r["before"] != r["after"] for r in h72["sources"].values()), 23)
        remaining = {p: r for p, r in h72["sources"].items() if p != compose.BOT_SOURCE}
        encoded = (json.dumps(remaining, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual(compose.identity(encoded), repair["preserved_parent_other68_rows"])
        self.assertEqual(repair["parent_place"], h72["followup_repair"]["repaired_place"])
        self.assertEqual(repair["repaired_place"], h72["final_place"])
        addition = self.lock["beast_followup_repair"]
        self.assertEqual(len(addition["forward"]), 2)
        self.assertEqual(sum(len(r["forward"]) for r in beast["sources"].values()), 173)
        self.assertEqual([path for path in beast["sources"]
                          if beast["sources"][path] != h72["sources"][path]], [compose.BEAST_SOURCE])
        self.assertEqual(addition["parent_place"], h72["final_place"])
        guardian = self.lock["guardian_followup_repair"]
        self.assertEqual(len(guardian["forward"]), 6)
        item = self.lock["item_cleanup_followup"]
        vault = self.lock["empty_vault_followup"]
        castle = self.lock["castle_release_stock_followup"]
        score = self.lock["score_relay_followup"]
        relay = self.lock["relay_presentation_followup"]
        canyon = self.lock["br_canyon_followup"]
        role = self.lock["role_readability_followup"]
        field = self.lock["field_prompt_followup"]
        neutral_names = self.lock["neutral_names_followup"]
        wall = self.lock["guardian_wall_followup"]
        combat = self.lock["combat_visual_followup"]
        growth = self.lock["growth_musou_followup"]
        polish = self.lock["art_polish_followup"]
        mage = self.lock["mage_contact_followup"]
        eligibility = self.lock["relay_eligibility_followup"]
        moguron = self.lock["moguron_followup"]
        private_touch = self.lock["private_touch_followup"]
        portrait = self.lock["portrait_followup"]
        relay_eligibility_sources = self.lock["sources"]
        shorefoam = self.lock["shorefoam_followup"]
        team_win = self.lock["team_win_rule_followup"]
        hp = self.lock["fractional_hp_followup"]
        for followup in (self.lock["mage_field_arcs_followup"], self.lock["cover_orders_followup"],
                         self.lock["ground_night_followup"],
                         self.lock["return_convert_followup"],
                         self.lock["field_loadouts_followup"],
                         self.lock["wing_warrior_followup"],
                         self.lock["ninja_s4_followup"],
                         self.lock["mage_water_chain_followup"],
                         self.lock["mage_projectile_followup"],
                         hp, team_win, shorefoam, portrait, private_touch, moguron):
            relay_eligibility_sources = relay_eligibility_sources | {
                name: row["parent"] for name, row in followup["rows"].items()}
        self.assertEqual(moguron["parent_place"], eligibility["repaired_place"])
        mage_sources = relay_eligibility_sources | {name: row["parent"] for name, row in eligibility["rows"].items()}
        polish_sources = mage_sources | {name: row["parent"] for name, row in mage["rows"].items()}
        growth_sources = polish_sources | {name: row["parent"] for name, row in polish["rows"].items()}
        combat_sources = growth_sources | {name: row["parent"] for name, row in growth["rows"].items()}
        wall_sources = combat_sources | {name: row["parent"] for name, row in combat["rows"].items()}
        visual_sources = wall_sources | {compose.GUARDIAN_SOURCE: wall["rows"][compose.GUARDIAN_SOURCE]["parent"]}
        field_sources = visual_sources | {name: row["parent"] for name, row in neutral_names["rows"].items()}
        role_sources = field_sources | {compose.VAULT_SOURCE: field["rows"][compose.VAULT_SOURCE]["parent"]}
        canyon_sources = role_sources | {name: row["parent"] for name, row in role["rows"].items()}
        relay_sources = canyon_sources | {name: row["parent"] for name, row in canyon["rows"].items()}
        score_sources = relay_sources | {name: row["parent"] for name,row in relay["rows"].items()}
        castle_sources = score_sources | {compose.SCORE_SOURCE: score["parent_score_row"]}
        vault_sources = castle_sources | {compose.VAULT_SOURCE: castle["parent_host_row"]}
        item_sources = castle_sources | {compose.VAULT_SOURCE: vault["parent_host_row"]}
        guardian_sources = item_sources | {compose.ITEM_SOURCE: item["parent_item_row"]}
        self.assertEqual(sum(len(r["forward"]) for r in guardian_sources.values()), 179)
        self.assertEqual([path for path in guardian_sources
                          if guardian_sources[path] != beast["sources"][path]], [compose.GUARDIAN_SOURCE])
        self.assertEqual(guardian["parent_place"], beast["final_place"])
        self.assertEqual(item["parent_place"], guardian["repaired_place"])
        self.assertEqual(len(item["forward"]), 4)
        self.assertEqual(sum(len(r["forward"]) for r in item_sources.values()), 182)
        self.assertEqual([path for path in item_sources
                          if item_sources[path] != guardian_sources[path]], [compose.ITEM_SOURCE])
        self.assertEqual(vault["parent_place"], item["repaired_place"])
        self.assertEqual(vault["repaired_place"], castle["parent_place"])
        self.assertEqual(len(vault["forward"]), 8)
        self.assertEqual(sum(len(r["forward"]) for r in vault_sources.values()), 187)
        self.assertEqual([path for path in item_sources
                          if item_sources[path] != vault_sources[path]], [compose.VAULT_SOURCE])
        self.assertEqual(castle["repaired_place"], score["parent_place"])
        self.assertEqual(score["repaired_place"], relay["parent_place"])
        self.assertEqual(relay["repaired_place"], canyon["parent_place"])
        self.assertEqual(canyon["repaired_place"], role["parent_place"])
        self.assertEqual(role["repaired_place"], field["parent_place"])
        self.assertEqual(field["repaired_place"], neutral_names["parent_place"])
        self.assertEqual(neutral_names["repaired_place"], wall["parent_place"])
        self.assertEqual(wall["repaired_place"], combat["parent_place"])
        self.assertEqual(combat["repaired_place"], growth["parent_place"])
        self.assertEqual(growth["repaired_place"], polish["parent_place"])
        self.assertEqual(polish["repaired_place"], mage["parent_place"])
        self.assertEqual(mage["repaired_place"], eligibility["parent_place"])
        self.assertEqual(moguron["repaired_place"], private_touch["parent_place"])
        self.assertEqual(private_touch["repaired_place"], portrait["parent_place"])
        self.assertEqual(portrait["repaired_place"], shorefoam["parent_place"])
        self.assertEqual(shorefoam["repaired_place"], team_win["parent_place"])
        self.assertEqual(team_win["repaired_place"], hp["parent_place"])
        projectiles = self.lock["mage_projectile_followup"]
        self.assertEqual(hp["repaired_place"], projectiles["parent_place"])
        water_chain = self.lock["mage_water_chain_followup"]
        self.assertEqual(projectiles["repaired_place"], water_chain["parent_place"])
        ninja_s4 = self.lock["ninja_s4_followup"]
        self.assertEqual(water_chain["repaired_place"], ninja_s4["parent_place"])
        wing_warrior = self.lock["wing_warrior_followup"]
        self.assertEqual(ninja_s4["repaired_place"], wing_warrior["parent_place"])
        field_loadouts = self.lock["field_loadouts_followup"]
        self.assertEqual(wing_warrior["repaired_place"], field_loadouts["parent_place"])
        return_convert = self.lock["return_convert_followup"]
        self.assertEqual(field_loadouts["repaired_place"], return_convert["parent_place"])
        ground_night = self.lock["ground_night_followup"]
        self.assertEqual(return_convert["repaired_place"], ground_night["parent_place"])
        cover_orders = self.lock["cover_orders_followup"]
        self.assertEqual(ground_night["repaired_place"], cover_orders["parent_place"])
        mage_field_arcs = self.lock["mage_field_arcs_followup"]
        self.assertEqual(cover_orders["repaired_place"], mage_field_arcs["parent_place"])
        self.assertEqual(mage_field_arcs["repaired_place"], self.lock["final_place"])
        self.assertEqual(set(mage_field_arcs["rows"]), set(compose.MAGE_FIELD_ARCS_SOURCES))
        self.assertEqual(set(cover_orders["rows"]), set(compose.COVER_ORDERS_SOURCES))
        self.assertEqual(set(ground_night["rows"]), set(compose.GROUND_NIGHT_SOURCES))
        self.assertEqual(set(return_convert["rows"]), set(compose.RETURN_CONVERT_SOURCES))
        self.assertEqual(set(field_loadouts["rows"]), set(compose.FIELD_LOADOUTS_SOURCES))
        self.assertEqual(set(wing_warrior["rows"]), set(compose.WING_WARRIOR_SOURCES))
        self.assertEqual(set(ninja_s4["rows"]), set(compose.NINJA_S4_SOURCES))
        self.assertEqual(set(water_chain["rows"]), set(compose.MAGE_WATER_CHAIN_SOURCES))
        self.assertEqual(set(projectiles["rows"]), set(compose.MAGE_PROJECTILES_SOURCES))
        self.assertEqual(set(hp["rows"]), {compose.HUD_SOURCE})
        self.assertEqual(len(hp["rows"][compose.HUD_SOURCE]["forward"]), 1)
        self.assertEqual(set(team_win["rows"]), {compose.VAULT_SOURCE})
        self.assertEqual(len(team_win["rows"][compose.VAULT_SOURCE]["forward"]), 1)
        self.assertEqual(set(shorefoam["rows"]), {compose.SHOREFOAM_SOURCE})
        self.assertEqual(set(portrait["rows"]), {compose.PORTRAIT_SOURCE})
        self.assertEqual(set(private_touch["rows"]), {compose.PRIVATE_TOUCH_SOURCE})
        self.assertEqual(set(eligibility["rows"]), set(compose.RELAY_ELIGIBILITY_SOURCES))
        self.assertEqual(set(mage["rows"]), set(compose.MAGE_CONTACT_SOURCES))
        self.assertEqual(set(polish["rows"]), set(compose.ART_POLISH_SOURCES))
        self.assertEqual(set(growth["rows"]), set(compose.GROWTH_MUSOU_SOURCES))
        self.assertEqual(set(combat["rows"]), set(compose.COMBAT_VISUAL_SOURCES))
        self.assertEqual(set(wall["rows"]), {compose.GUARDIAN_SOURCE})
        self.assertEqual(set(field["rows"]), {compose.VAULT_SOURCE})
        self.assertEqual(set(neutral_names["rows"]), set(compose.VISUAL_READABILITY_SOURCES))
        self.assertEqual([path for path in field_sources
                          if field_sources[path] != role_sources[path]], [compose.VAULT_SOURCE])
        self.assertEqual({path for path in visual_sources
                          if visual_sources[path] != field_sources[path]}, set(compose.VISUAL_READABILITY_SOURCES))
        self.assertEqual(len(castle["forward"]), 5)
        self.assertEqual(sum(len(r["forward"]) for r in castle_sources.values()), 190)
        self.assertEqual(sum(len(r["forward"]) for r in score_sources.values()), 191)
        self.assertEqual([path for path in vault_sources
                          if vault_sources[path] != castle_sources[path]], [compose.VAULT_SOURCE])

    def test_bot_immutable_template_corpus_and_adapter_drift_rejected(self):
        for name in verify.BOT_INPUTS:
            with self.subTest(file=name), tempfile.TemporaryDirectory(prefix="union22-bot-contract-") as directory:
                root = Path(directory)
                (root / "native").mkdir()
                for source in verify.BOT_INPUTS:
                    shutil.copyfile(HERE / "native" / source, root / "native" / source)
                path = root / "native" / name
                path.write_bytes(path.read_bytes() + b"\n")
                with patch.object(verify, "HERE", root), self.assertRaisesRegex(ValueError, "BOT_IMMUTABLE_INPUTS"):
                    verify.independent_bot_contract(self.native_lock)

    def test_bot_raw_parser_rejects_incomplete_forged_or_warning_vectors(self):
        # Protocol strings only; these checks do not execute or admit Native.
        contract, _ = verify.independent_bot_contract(self.native_lock)
        item = next(s for s in contract["scenarios"] if s["scenario_id"] == "candidate_actors_TEAM_normal")
        lines = [("CHECK\t" + name + "\tPASS\tprotocol control\n").encode()
                 for name in item["expected_ordered_CHECK_names"]]
        lines += [("CASE\t" + name + "\tPASS\tprotocol control\n").encode()
                  for name in item["expected_ordered_CASE_names"]]
        good = b"".join(lines)
        parsed = verify.independent_bot_vectors(item, good, b"", 0)
        self.assertEqual((len(parsed["case_rows"]), len(parsed["check_rows"])), (1, 13))
        mutations = [
            (b"", b"", 0), (b"".join(lines[1:]), b"", 0), (good + lines[0], b"", 0),
            (good + lines[-1], b"", 0), (good.replace(b"\tPASS\t", b"\tFAIL\t", 1), b"", 0),
            (good.replace(b"CHECK\t", b"CHECK_BAD\t", 1), b"", 0),
            (good + b" warning: swallowed runtime failure\n", b"", 0),
            (good, b"runtime stderr", 0), (good, b"", 1), (good, b"", False),
            (good + b"\xff\n", b"", 0),
        ]
        for index, (stdout, stderr, code) in enumerate(mutations):
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                verify.independent_bot_vectors(item, stdout, stderr, code)

    def test_original_fixture_and_case_bytes_remain_pinned(self):
        self.assertEqual(native.fixture_snapshot(self.native_lock), self.native_lock["fixtures"])

    def test_absent_partial_and_unknown_artifact_context_rejected(self):
        for environment in ({}, {"UNION22_TEST_PRIOR": "/missing"},
                            {"UNION22_TEST_STAGE": "final"}, {"UNION22_TEST_STAGE": "other"},
                            {"UNION22_TEST_UNKNOWN": "unexpected"}):
            with patch.dict(os.environ, environment, clear=True), self.assertRaises(ValueError):
                artifact_environment()

    def test_native_failure_observation_preserves_fail_and_success_contracts(self):
        # Python protocol controls only: subprocess, assembly and source reads
        # are mocked. No game, source-build, Native or CI acceptance is claimed.
        with tempfile.TemporaryDirectory(prefix="union22-diagnostic-protocol-") as directory:
            parent = Path(directory)
            binary = parent / "protocol-binary"
            binary.write_bytes(b"protocol-only; never executed")
            binary_pin = native.identity(binary.read_bytes())
            before = copy.deepcopy(self.native_lock["sources"])
            changed = copy.deepcopy(before)
            changed[next(iter(changed))]["sha256"] = "0" * 64
            expected = self.native_lock["suites"]["objective_full_clear_los"]["expected_case_names"]
            passed = ("\n".join("CASE\t" + name + "\tPASS\tprotocol-only" for name in expected) + "\n").encode()
            failed = passed.replace(b"\tPASS\t", b"\tFAIL\t", 1)
            controls = [
                ("process", subprocess.CompletedProcess([], 1, failed, b"original failure\n"), before, ValueError),
                ("vector", subprocess.CompletedProcess([], 0, failed, b""), before, ValueError),
                ("source", subprocess.CompletedProcess([], 0, passed, b""), changed, ValueError),
                ("timeout", subprocess.TimeoutExpired([], 60, output=b"partial output\n", stderr=b"partial error\n"), before, subprocess.TimeoutExpired),
                ("utf8", subprocess.CompletedProcess([], 0, b"\xff", b""), before, UnicodeDecodeError),
                ("success", subprocess.CompletedProcess([], 0, passed, b""), before, None),
            ]
            for name, response, snapshot, error_type in controls:
                with self.subTest(name=name):
                    output = parent / name
                    console = io.StringIO()
                    effect = {"side_effect": response} if isinstance(response, Exception) else {"return_value": response}
                    with patch.object(native, "assemble", return_value=(b"-- protocol only\n", {}, {})), \
                         patch.object(native.subprocess, "run", **effect), \
                         patch.object(native, "source_snapshot", return_value=snapshot), \
                         patch.object(native, "fixture_snapshot"), redirect_stdout(console):
                        arguments = (parent / "unused-source", output, binary, self.native_lock, "objective_full_clear_los", before,
                                     binary_pin, {"kind": "PROTOCOL_ONLY"}, native.identity(b"protocol-receipt"),
                                     native.identity(b"protocol-runner"))
                        if error_type is None:
                            result = native.run_suite(*arguments)
                        else:
                            with self.assertRaises(error_type) as caught:
                                native.run_suite(*arguments)
                    if error_type is None:
                        self.assertEqual(console.getvalue(), "objective_full_clear_los: 7/7 exact PASS cases\n")
                        self.assertEqual(result["schema"], "UNION22_FULL_RUNTIME_SUITE_V2")
                        self.assertEqual(result["status"], "PASS")
                        self.assertEqual({p.name for p in output.iterdir()},
                                         {"generated.luau", "stdout.log", "stderr.log", "receipt.json"})
                        self.assertEqual((output / "stdout.log").read_bytes(), passed)
                        continue
                    self.assertFalse((output / "receipt.json").exists())
                    diagnostic = verify.data(output / "FAILED.json")
                    stdout = response.stdout or b""
                    stderr = response.stderr or b""
                    self.assertEqual((output / "stdout.log").read_bytes(), stdout)
                    self.assertEqual((output / "stderr.log").read_bytes(), stderr)
                    self.assertEqual(diagnostic["stdout"], native.identity(stdout))
                    self.assertEqual(diagnostic["stderr"], native.identity(stderr))
                    self.assertEqual(diagnostic["native"], binary_pin)
                    self.assertEqual(diagnostic["generated"], native.identity(b"-- protocol only\n"))
                    self.assertEqual(diagnostic["status"], "FAIL_DIAGNOSTIC_ONLY")
                    self.assertFalse(diagnostic["native_admission"])
                    displayed = console.getvalue().splitlines()
                    self.assertEqual(len(displayed), 3)
                    self.assertEqual(json.loads(displayed[0].removeprefix("UNION22_NATIVE_FAILURE ")), diagnostic)
                    self.assertEqual(json.loads(displayed[1].removeprefix("UNION22_NATIVE_FAILURE_STDOUT ")),
                                     stdout.decode("utf-8", errors="backslashreplace"))
                    self.assertEqual(json.loads(displayed[2].removeprefix("UNION22_NATIVE_FAILURE_STDERR ")),
                                     stderr.decode("utf-8", errors="backslashreplace"))
                    if name in ("process", "vector", "source"):
                        self.assertIn("SUITE_FAILED_OR_SOURCE_MUTATED:objective_full_clear_los", str(caught.exception))
                        self.assertEqual(diagnostic["native_exit"], response.returncode)
                        self.assertEqual(diagnostic["source_inputs_unchanged"], name != "source")
                        self.assertEqual(diagnostic["exact_complete_pass_vector"], name == "source")
                        self.assertEqual(diagnostic["parse_reason"], "EXACT_PASS_VECTOR" if name == "source" else "NON_PASS_CASE")
                    elif name == "timeout":
                        self.assertIs(caught.exception, response)
                        self.assertTrue(diagnostic["timed_out"])
                        self.assertEqual(diagnostic["parse_reason"], "NOT_PARSED_TIMEOUT")
                    else:
                        self.assertEqual(diagnostic["parse_reason"], "INVALID_UTF8")

    test_original_39_workflow_step_payloads_byte_exact = UnionBoundary.test_original_39_workflow_step_payloads_byte_exact
    test_clear_los_case_exact_inverse_preserves_original_assertions = UnionBoundary.test_clear_los_case_exact_inverse_preserves_original_assertions
    test_objective_clear_los_case_inverse_preserves_original_assertions = UnionBoundary.test_objective_clear_los_case_inverse_preserves_original_assertions
    test_original_vectors_exact_positive = UnionBoundary.test_original_vectors_exact_positive
    test_empty_missing_duplicate_extra_failed_case_rejected = UnionBoundary.test_empty_missing_duplicate_extra_failed_case_rejected
    test_duplicate_json_keys_rejected = UnionBoundary.test_duplicate_json_keys_rejected
    test_hunk_removed_bytes_rejected = UnionBoundary.test_hunk_removed_bytes_rejected
    test_hunk_overlap_rejected = UnionBoundary.test_hunk_overlap_rejected


def integration_suite(loader):
    stage, _ = artifact_environment()
    case = FinalAdmissionBoundary if stage == "final" else UnionBoundary
    return checked_suite(loader, case, INTEGRATION_COUNTS[stage])


def load_tests(loader, standard_tests, pattern):
    # Only ordinary discovery with no union-specific context selects contracts.
    # A module/script entry or even a partial context must request real artifacts.
    has_context = any(key.startswith("UNION22_TEST_") for key in os.environ)
    if pattern is not None and not has_context:
        return checked_suite(loader, UnionOfflineContract, 17)
    return integration_suite(loader)


def main():
    if len(sys.argv) != 1:
        raise ValueError("RED_UNION22_COMPLETE_INTEGRATION_ENTRY_ONLY")
    stage, _ = artifact_environment()
    suite = integration_suite(unittest.defaultTestLoader)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun != INTEGRATION_COUNTS[stage] or result.skipped:
        raise ValueError("RED_UNION22_INCOMPLETE_INTEGRATION_EXECUTION")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
