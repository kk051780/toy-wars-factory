#!/usr/bin/env python3
"""Strict existing-hunk union after the unchanged BR-only REAL69 boundary.

The CLI requires the real Actions event/live-RC provenance guard. The separately
named local_source_context is for explicit offline source QA through the Python
API; it never asserts canonical/formal execution. No delivery is admitted here.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LOCK_SHA256 = "6f76962b33682de03d951ac72c3670f935505a914397f54f65b6062b082a5703"
FORMAL = "rc/p0d-s1-kids-rc01"
REPOSITORY = "kk051780/toy-wars-factory"
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
OFF = "off69_union22_prior_br"
OFF_ARCHIVE = "OFF69_UNION22_PRIOR_BR_ROLLBACK.tar.gz"
HUD_SOURCE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau"
HUD_OFF = "off69_hud_context_current_rc"
HUD_OFF_ARCHIVE = "OFF69_HUD_CONTEXT_CURRENT_RC_ROLLBACK.tar.gz"
BOT_SOURCE = "ServerScriptService/EGGRUMBLE_BotActors.luau"
BOT_OFF = "off69_bot_vault_hud_parent"
BOT_OFF_ARCHIVE = "OFF69_BOT_VAULT_HUD_PARENT_ROLLBACK.tar.gz"
BEAST_SOURCE = "ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau"
BEAST_OFF = "off69_beast_h72_parent"
BEAST_OFF_ARCHIVE = "OFF69_BEAST_H72_PARENT_ROLLBACK.tar.gz"
GUARDIAN_SOURCE = "ServerScriptService/EGGRUMBLE_CastleGuardianRuntime.luau"
GUARDIAN_OFF = "off69_guardian_beast_parent"
GUARDIAN_OFF_ARCHIVE = "OFF69_GUARDIAN_BEAST_PARENT_ROLLBACK.tar.gz"
ITEM_SOURCE = "ServerScriptService/EGGRUMBLE_EncounterReadabilityArt.server.luau"
ITEM_OFF = "off69_item_cleanup_guardian_parent"
ITEM_OFF_ARCHIVE = "OFF69_ITEM_CLEANUP_GUARDIAN_PARENT_ROLLBACK.tar.gz"
VAULT_SOURCE = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau"
VAULT_OFF = "off69_empty_vault_item_parent"
VAULT_OFF_ARCHIVE = "OFF69_EMPTY_VAULT_ITEM_PARENT_ROLLBACK.tar.gz"
CASTLE_OFF = "off69_castle_release_stock_vault_parent"
CASTLE_OFF_ARCHIVE = "OFF69_CASTLE_RELEASE_STOCK_VAULT_PARENT_ROLLBACK.tar.gz"
SCORE_SOURCE = "ServerScriptService/EGGRUMBLE_ScoreBalance.luau"
SCORE_OFF = "off69_score_relay_castle_parent"
SCORE_OFF_ARCHIVE = "OFF69_SCORE_RELAY_CASTLE_PARENT_ROLLBACK.tar.gz"
SCORE_REGRESSION_DONOR = "quality_gameplay/gq487_relay_score_real69_20261122"
RELAY_PRESENTATION_OFF = "off69_relay_presentation_score_parent"
RELAY_PRESENTATION_OFF_ARCHIVE = "OFF69_RELAY_PRESENTATION_SCORE_PARENT_ROLLBACK.tar.gz"
RELAY_PRESENTATION_SOURCES = (VAULT_SOURCE, HUD_SOURCE)
BR_CANYON_OFF = "off69_br_canyon_relay_parent"
BR_CANYON_OFF_ARCHIVE = "OFF69_BR_CANYON_RELAY_PARENT_ROLLBACK.tar.gz"
BR_CANYON_SOURCES = (
    "ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes.server.luau",
    "ServerScriptService/EGGRUMBLE_RealmBattleCore.server.luau",
)
ROLE_READABILITY_OFF = "off69_role_readability_canyon_parent"
ROLE_READABILITY_OFF_ARCHIVE = "OFF69_ROLE_READABILITY_CANYON_PARENT_ROLLBACK.tar.gz"
FIELD_PROMPT_OFF = "off69_field_prompt_role_parent"
FIELD_PROMPT_OFF_ARCHIVE = "OFF69_FIELD_PROMPT_ROLE_PARENT_ROLLBACK.tar.gz"
ROLE_MOTION_SOURCE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills.client.luau"
ROLE_WEAPON_SOURCE = "ServerScriptService/EGGRUMBLE_WeaponSilhouettes.luau"
ROLE_READABILITY_SOURCES = (ROLE_WEAPON_SOURCE, ROLE_MOTION_SOURCE)
SHA = re.compile(r"[0-9a-f]{40}\Z")
CLASSES = {"ModuleScript": 47, "Script": 12, "LocalScript": 10}


class GateError(ValueError):
    pass


def need(condition, reason):
    if not condition:
        raise GateError("RED_UNION22_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read_file(path):
    path = Path(path)
    need(not path.is_symlink() and path.is_file(), "NOT_REGULAR_FILE:" + str(path))
    need(stat.S_ISREG(path.stat().st_mode), "NOT_REGULAR_FILE:" + str(path))
    need(not path.stat().st_mode & 0o7000, "SPECIAL_FILE_MODE:" + str(path))
    return path.read_bytes()


def strict_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            need(key not in value, "DUPLICATE_JSON_KEY")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def safe(root, relative):
    need(isinstance(relative, str) and relative and "\\" not in relative,
         "INVALID_RELATIVE_PATH")
    rel = PurePosixPath(relative)
    need(not rel.is_absolute() and ".." not in rel.parts, "ESCAPED_PATH")
    path = Path(root) / relative
    need(path.resolve().is_relative_to(Path(root).resolve()), "ESCAPED_PATH")
    need(not any(p.is_symlink() for p in [path, *path.parents]
                 if p == Path(root) or p.is_relative_to(Path(root))), "SYMLINK_PATH")
    return path


def load_lock():
    raw = read_file(HERE / "profile_lock.json")
    need(identity(raw)["sha256"] == LOCK_SHA256, "PROFILE_LOCK_MISMATCH")
    lock = strict_json(raw)
    need(lock["schema"] == "GQ470_UNION22_PRODUCTION_PROFILE_V1"
         and len(lock["sources"]) == 69, "PROFILE_SCHEMA_OR_COUNT")
    return lock


def source_class(path):
    if path.endswith(".server.luau"):
        return "Script"
    if path.endswith(".client.luau"):
        return "LocalScript"
    need(path.endswith(".luau"), "SOURCE_EXTENSION")
    return "ModuleScript"


def project_inventory(raw):
    tree = strict_json(raw)["tree"]
    need(tree.get("$className") == "DataModel", "PROJECT_ROOT_CLASS")
    result = {}
    def walk(node, route):
        need(isinstance(node, dict), "PROJECT_NODE")
        if "$path" in node:
            name = node["$path"]
            need(isinstance(name, str) and name.startswith("sources/"), "PROJECT_PATH")
            relative = name.removeprefix("sources/")
            need(relative not in result and route, "DUPLICATE_PROJECT_SOURCE")
            result[relative] = {"route": route, "class": source_class(relative)}
        for name, child in node.items():
            if not name.startswith("$"):
                walk(child, route + "/" + name if route else name)
    walk(tree, "")
    need(len(result) == 69 and Counter(x["class"] for x in result.values()) == CLASSES,
         "PROJECT_INVENTORY")
    return result


def place_inventory(raw):
    tree = ET.fromstring(raw)
    sources, routes = {}, set()
    def walk(item, parent=""):
        props = item.find("Properties")
        need(props is not None, "PLACE_PROPERTIES")
        names = props.findall("string[@name='Name']")
        need(len(names) == 1 and names[0].text, "PLACE_NAME")
        route = parent + "/" + names[0].text if parent else names[0].text
        need(route not in routes, "DUPLICATE_INSTANCE_ROUTE")
        routes.add(route)
        nodes = [x for x in props if x.get("name") == "Source"]
        need(len(nodes) <= 1, "DUPLICATE_SOURCE_PROPERTY")
        if nodes:
            node = nodes[0]
            need(node.tag in ("string", "ProtectedString"), "SOURCE_ENCODING")
            sources[route] = {"class": item.get("class"),
                              "raw": (node.text or "").encode()}
            node.text = "__SOURCE_OMITTED_FOR_NON_SOURCE_COMPARISON__"
        for child in item.findall("Item"):
            walk(child, route)
    for item in tree.findall("Item"):
        walk(item)
    need(len(sources) == 69 and Counter(x["class"] for x in sources.values()) == CLASSES,
         "PLACE_SOURCE_INVENTORY")
    need(len(routes) == 75, "PLACE_INSTANCE_COUNT")
    return sources, ET.tostring(tree, encoding="utf-8")


def load_inputs(base, reports, lock=None):
    lock = lock or load_lock()
    for value in (base, reports):
        path = Path(value).absolute()
        need(not any(p.is_symlink() for p in [path, *path.parents]), "INPUT_ROOT_SYMLINK")
    base, reports = Path(base).resolve(), Path(reports).resolve()
    need(reports in (base, base / "delivery"), "PRIOR_REPORT_DIRECTORY")
    project = read_file(base / PROJECT)
    place = read_file(base / PLACE)
    need(identity(project) == lock["project"], "PRIOR_PROJECT_IDENTITY")
    need(identity(place) == lock["prior_place"], "PRIOR_PLACE_IDENTITY")
    inventory = project_inventory(project)
    need(inventory == {p: {"route": row["route"], "class": row["class"]}
                       for p, row in lock["sources"].items()}, "PRIOR_PROJECT_ROUTE_CLASS")
    source_root = safe(base, "sources")
    found = set()
    for path in source_root.rglob("*"):
        need(not path.is_symlink(), "SOURCE_SYMLINK")
        if path.is_file():
            found.add(path.relative_to(source_root).as_posix())
        else:
            need(path.is_dir(), "SOURCE_SPECIAL_FILE")
    need(found == set(lock["sources"]), "PRIOR_SOURCE_INVENTORY")
    sources = {}
    for name, row in lock["sources"].items():
        raw = read_file(safe(source_root, name))
        need(identity(raw) == row["before"], "PRIOR_SOURCE_IDENTITY:" + name)
        sources[name] = raw
    embedded, non_source = place_inventory(place)
    for name, row in lock["sources"].items():
        need(embedded[row["route"]] == {"class": row["class"], "raw": sources[name]},
             "PRIOR_EMBEDDED_SOURCE:" + name)
    receipt_raw = read_file(base / RECEIPT)
    receipt = strict_json(receipt_raw)
    need(receipt.get("official_branch") == FORMAL and receipt.get("source_profile") == "REAL69"
         and receipt.get("selected_source_count") == 69, "PRIOR_RECEIPT_PROFILE")
    need(receipt.get("source_hashes") == {r["route"]: r["before"]["sha256"] for r in lock["sources"].values()}
         and receipt.get("source_classes") == {r["route"]: r["class"] for r in lock["sources"].values()},
         "PRIOR_RECEIPT_SOURCE_IDENTITY")
    need(receipt.get("private_place_bytes") == len(place)
         and receipt.get("private_place_sha256") == identity(place)["sha256"],
         "PRIOR_RECEIPT_PLACE_IDENTITY")
    need(type(receipt.get("canonical_build")) is bool
         and isinstance(receipt.get("build_head"), str) and SHA.fullmatch(receipt["build_head"])
         and receipt.get("legacy_48_all_ported") is False, "PRIOR_RECEIPT_CONTEXT")
    evidence = {name: read_file(reports / name) for name in lock["prior_report_names"]}
    r17, r48, art = [strict_json(evidence[n]) for n in lock["prior_report_names"]]
    need(r17.get("build_head") == receipt["build_head"]
         and r17.get("source_family_marker_count") == 17
         and r17.get("selected_luau_sources") == 69
         and r17.get("source_route_class_hash_receipt") == "PASS_69_OF_69"
         and r17.get("private_place_sha256") == lock["prior_place"]["sha256"]
         and r17.get("private_place_bytes") == lock["prior_place"]["bytes"], "PRIOR_17_REPORT")
    need(r48.get("official_head") == receipt["build_head"] and r48.get("source_count") == 69
         and r48.get("original_legacy_flags") == 48 and len(r48.get("flags", [])) == 48
         and r48.get("all_48_semantic_parity") == "NOT_PROVEN"
         and r48.get("summary") == {"EVIDENCE_GAP": 4, "MARKER_SOURCE_PRESENT": 15,
                                   "NON_RUNTIME_LEGACY_FLAG": 2, "SOURCE_ANALOGUE_ONLY": 27},
         "PRIOR_48_REPORT")
    expected_kind = "OFFICIAL" if receipt["canonical_build"] else "PR_CANDIDATE"
    need(art.get("candidate_build_head") == receipt["build_head"]
         and art.get("receipt_provenance") == expected_kind
         and art.get("formal_rc_adoption_proven") is receipt["canonical_build"]
         and art.get("official_build_head") == (receipt["build_head"] if receipt["canonical_build"] else None)
         and art.get("private_place_sha256") == lock["prior_place"]["sha256"]
         and art.get("private_place_bytes") == lock["prior_place"]["bytes"]
         and art.get("source_gate", {}).get("status") == "PASS_SOURCE_ONLY"
         and art["source_gate"].get("actual_place_scripts") == 69
         and art["source_gate"].get("verified_visual_feature_sources") == 3
         and art.get("art_gate") == "ART_NO_GO" and art.get("product_gate") == "PRODUCT_NO_GO"
         and art.get("owner_accepted") is False, "PRIOR_ART_REPORT")
    archives = {p.name for p in reports.glob("OFF*.tar.gz")}
    need(archives == set(lock["prior_opaque_rollback_names"]), "PRIOR_ROLLBACK_INVENTORY")
    for name in sorted(archives):
        evidence["legacy_rollbacks/" + name] = read_file(reports / name)
    evidence[RECEIPT] = receipt_raw
    snapshot = {"sources/" + name: identity(raw) for name, raw in sources.items()}
    snapshot.update({PROJECT: identity(project), PLACE: identity(place), RECEIPT: identity(receipt_raw)})
    snapshot.update({"reports/" + name: identity(raw) for name, raw in evidence.items()})
    return {"base": base, "reports": reports, "project": project, "place": place,
            "sources": sources, "non_source": non_source, "receipt": receipt,
            "receipt_raw": receipt_raw, "evidence": evidence, "snapshot": snapshot}


def live_context(receipt, head):
    need(os.environ.get("GITHUB_ACTIONS") == "true"
         and os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "REAL_ACTIONS_CONTEXT_REQUIRED")
    need(head == os.environ.get("GITHUB_SHA") == receipt.get("build_head"), "BUILD_HEAD_MISMATCH")
    checkout = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                       env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"},
                                       text=True, timeout=30).strip()
    need(checkout == head, "ACTUAL_CHECKOUT_HEAD_MISMATCH")
    need(all(os.environ.get(key, "").isdigit() and int(os.environ[key]) > 0
             for key in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")), "ACTUAL_RUN_ID_ATTEMPT_REQUIRED")
    sys.path.insert(0, str(REPO))
    from quality_gameplay.gq470_art_pr_provenance_20261121.guard import verify_receipt
    event = strict_json(read_file(Path(os.environ["GITHUB_EVENT_PATH"])))
    live = subprocess.check_output(
        ["gh", "api", f"repos/{REPOSITORY}/git/ref/heads/{FORMAL}", "--jq", ".object.sha"],
        text=True, timeout=30).strip()
    kind = verify_receipt(receipt, dict(os.environ), event, live)
    need(kind in ("OFFICIAL", "PR_CANDIDATE"), "UNSUPPORTED_PRODUCTION_CONTEXT")
    return {"kind": kind, "build_head": head, "canonical_build": kind == "OFFICIAL",
            "checkout_sha": checkout,
            "official_build_head": head if kind == "OFFICIAL" else None,
            "observed_live_rc": live, "event": os.environ["GITHUB_EVENT_NAME"],
            "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT")}


def local_source_context(receipt):
    """Explicit offline Python-API QA. CLI admission cannot select this mode."""
    checkout = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                       env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"},
                                       text=True, timeout=30).strip()
    return {"kind": "LOCAL_SOURCE_REVIEW", "build_head": receipt["build_head"],
            "checkout_sha": checkout,
            "canonical_build": False, "official_build_head": None,
            "observed_live_rc": None, "event": None, "run_id": None, "run_attempt": None}


def validate_context(context, receipt):
    need(set(context) == {"kind", "build_head", "checkout_sha", "canonical_build", "official_build_head",
                          "observed_live_rc", "event", "run_id", "run_attempt"}, "CONTEXT_FIELD_SET")
    need(context.get("kind") in ("OFFICIAL", "PR_CANDIDATE", "LOCAL_SOURCE_REVIEW"),
         "CONTEXT_KIND")
    official = context["kind"] == "OFFICIAL"
    need(context.get("build_head") == receipt["build_head"]
         and context.get("canonical_build") is official
         and context.get("official_build_head") == (receipt["build_head"] if official else None),
         "CONTEXT_CLASSIFICATION")
    if context["kind"] != "LOCAL_SOURCE_REVIEW":
        need(receipt["canonical_build"] is official and context["checkout_sha"] == context["build_head"]
             and all(isinstance(context[k], str) and context[k].isdigit() and int(context[k]) > 0
                     for k in ("run_id", "run_attempt")), "PARENT_CONTEXT_CLASSIFICATION")
    else:
        need(isinstance(context["checkout_sha"], str) and SHA.fullmatch(context["checkout_sha"])
             and all(context[k] is None for k in ("observed_live_rc", "event", "run_id", "run_attempt")),
             "LOCAL_CONTEXT_CANNOT_CLAIM_CI")


def apply_hunks(raw, hunks):
    lines = raw.decode().splitlines(keepends=True)
    result, cursor, previous = [], 0, None
    need(hunks == sorted(hunks, key=lambda h: (h["start"], h["stop"])), "HUNK_ORDER")
    for hunk in hunks:
        start, stop = hunk["start"], hunk["stop"]
        need(type(start) is int and type(stop) is int and cursor <= start <= stop <= len(lines),
             "HUNK_RANGE_OR_OVERLAP")
        need(previous != (start, stop), "DUPLICATE_HUNK")
        need(identity(hunk["old"].encode()) == hunk["old_identity"]
             and identity(hunk["new"].encode()) == hunk["new_identity"], "HUNK_PAYLOAD_IDENTITY")
        need("".join(lines[start:stop]) == hunk["old"], "HUNK_REMOVED_TEXT")
        result.extend(lines[cursor:start])
        result.append(hunk["new"])
        cursor, previous = stop, (start, stop)
    result.extend(lines[cursor:])
    return "".join(result).encode()


def transform(inputs, lock):
    on, off = {}, {}
    for name, row in lock["sources"].items():
        on[name] = apply_hunks(inputs["sources"][name], row["forward"])
        need(identity(on[name]) == row["after"], "FINAL_SOURCE_IDENTITY:" + name)
        off[name] = apply_hunks(on[name], row["inverse"])
        need(off[name] == inputs["sources"][name] and identity(off[name]) == row["before"],
             "INVERSE_NOT_EXACT:" + name)
    need(sum(on[p] != inputs["sources"][p] for p in on) == 26, "CHANGED_SOURCE_COUNT")
    return on, off


def single_source_parent(on, lock, name, repair, parent_row, prior_place, reason):
    row = lock["sources"][name]
    need(repair["source_path"] == name and repair["repaired_place"] == lock["final_place"]
         and repair["parent_place"] == prior_place
         and parent_row["before"] == row["before"], reason + "_PARENT_PROFILE")
    restored = apply_hunks(on[name], repair["inverse"])
    need(identity(restored) == parent_row["after"] and restored != on[name]
         and apply_hunks(restored, repair["forward"]) == on[name], reason + "_EXACT_TWO_WAY")
    return on | {name: restored}, lock | {
        "sources": lock["sources"] | {name: parent_row}, "final_place": repair["parent_place"],
    }


def score_parent(on, lock):
    repair = lock["score_relay_followup"]
    need(len(repair["forward"]) == 1 and repair["forward"][0]["old"] == ""
         and repair["forward"][0]["new_identity"] == repair["fragment"], "SCORE_ORIGINAL_FRAGMENT")
    return single_source_parent(on, lock, SCORE_SOURCE, repair, repair["parent_score_row"],
                                lock["castle_release_stock_followup"]["repaired_place"], "SCORE_RELAY")


def paired_source_parent(on, lock, repair, names, prior_place, reason):
    need(set(repair["rows"]) == set(names)
         and repair["repaired_place"] == lock["final_place"]
         and repair["parent_place"] == prior_place, reason + "_PARENT")
    old = dict(on)
    parent = {**lock, "sources": dict(lock["sources"]), "final_place": repair["parent_place"]}
    for name, row in repair["rows"].items():
        restored = apply_hunks(on[name], row["inverse"])
        need(identity(restored) == row["parent"]["after"] and restored != on[name]
             and row["parent"]["before"] == lock["sources"][name]["before"]
             and apply_hunks(restored, row["forward"]) == on[name], reason + "_TWO_WAY:" + name)
        old[name] = restored
        parent["sources"][name] = row["parent"]
    return old, parent


def relay_presentation_parent(on, lock):
    return paired_source_parent(on, lock, lock["relay_presentation_followup"], RELAY_PRESENTATION_SOURCES,
                                lock["score_relay_followup"]["repaired_place"], "RELAY_PRESENTATION")


def br_canyon_parent(on, lock):
    return paired_source_parent(on, lock, lock["br_canyon_followup"], BR_CANYON_SOURCES,
                                lock["relay_presentation_followup"]["repaired_place"], "BR_CANYON")


def role_readability_parent(on, lock):
    return paired_source_parent(on, lock, lock["role_readability_followup"], ROLE_READABILITY_SOURCES,
                                lock["br_canyon_followup"]["repaired_place"], "ROLE_READABILITY")


def field_prompt_parent(on, lock):
    return paired_source_parent(on, lock, lock["field_prompt_followup"], (VAULT_SOURCE,),
                                lock["role_readability_followup"]["repaired_place"], "FIELD_PROMPT")


def castle_parent(on, lock):
    repair = lock["castle_release_stock_followup"]
    return single_source_parent(on, lock, VAULT_SOURCE, repair, repair["parent_host_row"],
                                lock["empty_vault_followup"]["repaired_place"], "CASTLE_RELEASE_STOCK")


def vault_parent(on, lock):
    repair = lock["empty_vault_followup"]
    return single_source_parent(on, lock, VAULT_SOURCE, repair, repair["parent_host_row"],
                                lock["item_cleanup_followup"]["repaired_place"], "VAULT")


def item_parent(on, lock):
    repair = lock["item_cleanup_followup"]
    row = lock["sources"][ITEM_SOURCE]
    parent_row = repair["parent_item_row"]
    need(repair["source_path"] == ITEM_SOURCE and repair["repaired_place"] == lock["final_place"]
         and repair["parent_place"] == lock["guardian_followup_repair"]["repaired_place"]
         and parent_row["before"] == row["before"], "ITEM_CLEANUP_PARENT_PROFILE")
    restored = apply_hunks(on[ITEM_SOURCE], repair["inverse"])
    need(identity(restored) == parent_row["after"] and restored != on[ITEM_SOURCE]
         and apply_hunks(restored, repair["forward"]) == on[ITEM_SOURCE], "ITEM_CLEANUP_EXACT_TWO_WAY")
    return on | {ITEM_SOURCE: restored}, lock | {
        "sources": lock["sources"] | {ITEM_SOURCE: parent_row}, "final_place": repair["parent_place"],
    }


def guardian_parent(on, lock):
    repair = lock["guardian_followup_repair"]
    row = lock["sources"][GUARDIAN_SOURCE]
    need(repair["source_path"] == GUARDIAN_SOURCE and repair["repaired_place"] == lock["final_place"]
         and repair["parent_place"] == lock["beast_followup_repair"]["repaired_place"]
         and repair["repaired_guardian"] == row["after"]
         and repair["parent_guardian_row"]["after"] == repair["parent_guardian"]
         and repair["parent_guardian_row"]["before"] == row["before"],
         "GUARDIAN_PARENT_PROFILE")
    restored = apply_hunks(on[GUARDIAN_SOURCE], repair["inverse"])
    need(identity(restored) == repair["parent_guardian"] and restored != on[GUARDIAN_SOURCE]
         and apply_hunks(restored, repair["forward"]) == on[GUARDIAN_SOURCE], "GUARDIAN_EXACT_TWO_WAY")
    return on | {GUARDIAN_SOURCE: restored}, lock | {
        "sources": lock["sources"] | {GUARDIAN_SOURCE: repair["parent_guardian_row"]},
        "final_place": repair["parent_place"],
    }


def beast_parent_profile(lock):
    repair = lock["beast_followup_repair"]
    need(repair["source_path"] == BEAST_SOURCE and repair["repaired_place"] == lock["final_place"]
         and repair["parent_place"] == lock["bot_followup_repair"]["repaired_place"]
         and repair["parent_combat_row"]["after"] == repair["parent_combat"]
         and lock["sources"][BEAST_SOURCE]["after"] == repair["repaired_combat"]
         and repair["changed_sources_from_h72_parent"] == 1
         and repair["unchanged_sources_from_h72_parent"] == 68,
         "BEAST_PARENT_PROFILE")
    return lock | {
        "sources": lock["sources"] | {BEAST_SOURCE: repair["parent_combat_row"]},
        "final_place": repair["parent_place"],
    }


def beast_parent_sources(on, lock, parent_lock):
    repair = lock["beast_followup_repair"]
    parent = on | {BEAST_SOURCE: apply_hunks(on[BEAST_SOURCE], repair["inverse"])}
    need(set(parent) == set(parent_lock["sources"])
         and all(identity(raw) == parent_lock["sources"][p]["after"] for p, raw in parent.items())
         and parent[BEAST_SOURCE] != on[BEAST_SOURCE]
         and apply_hunks(parent[BEAST_SOURCE], repair["forward"]) == on[BEAST_SOURCE],
         "BEAST_H72_PARENT_INVERSE")
    return parent


def bot_parent_sources(on, lock):
    """Undo only BotActors, yielding the recorded HUD parent."""
    repair = lock["bot_followup_repair"]
    row = lock["sources"][BOT_SOURCE]
    need(repair["source_path"] == BOT_SOURCE and set(on) == set(lock["sources"])
         and repair["changed_sources_from_hud_parent"] == 1
         and repair["unchanged_sources_from_hud_parent"] == 68, "BOT_PARENT_SOURCE_SET")
    need(all(identity(raw) == lock["sources"][p]["after"] for p, raw in on.items()),
         "BOT_PARENT_REQUIRES_EXACT_FINAL_SOURCES")
    need(repair["parent_bot"] == row["before"] and repair["repaired_bot"] == row["after"]
         and repair["forward"] == row["forward"] and repair["inverse"] == row["inverse"]
         and repair["parent_place"] == lock["followup_repair"]["repaired_place"]
         and repair["repaired_place"] == lock["final_place"], "BOT_PARENT_CONTRACT")
    parent = dict(on)
    parent[BOT_SOURCE] = apply_hunks(on[BOT_SOURCE], repair["inverse"])
    need(identity(parent[BOT_SOURCE]) == repair["parent_bot"]
         and apply_hunks(parent[BOT_SOURCE], repair["forward"]) == on[BOT_SOURCE],
         "BOT_PARENT_INVERSE_NOT_EXACT")
    need([p for p in on if on[p] != parent[p]] == [BOT_SOURCE], "BOT_PARENT_CHANGE_SCOPE")
    return parent


def hud_current_sources(on, lock):
    """Undo HUD only after the Bot-only inverse has restored the HUD parent."""
    repair = lock["followup_repair"]
    need(repair["source_path"] == HUD_SOURCE and set(on) == set(lock["sources"]),
         "HUD_CURRENT_SOURCE_SET")
    need(all(identity(raw) == (lock["bot_followup_repair"]["parent_bot"] if p == BOT_SOURCE
                              else lock["sources"][p]["after"]) for p, raw in on.items()),
         "HUD_CURRENT_REQUIRES_EXACT_BOT_PARENT_SOURCES")
    current = dict(on)
    current[HUD_SOURCE] = apply_hunks(on[HUD_SOURCE], repair["inverse"])
    need(identity(current[HUD_SOURCE]) == repair["current_hud"]
         and identity(on[HUD_SOURCE]) == repair["repaired_hud"]
         and apply_hunks(current[HUD_SOURCE], repair["forward"]) == on[HUD_SOURCE],
         "HUD_CURRENT_INVERSE_NOT_EXACT")
    need([p for p in on if on[p] != current[p]] == [HUD_SOURCE], "HUD_CURRENT_CHANGE_SCOPE")
    return current


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def run_checked(command, log, timeout=60, quiet_stdout=False):
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(x) for x in command], stdout=subprocess.DEVNULL if quiet_stdout else subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout)
    row = {"command": [str(x) for x in command], "started_at_utc": started,
           "exit": result.returncode, "stderr": result.stderr.decode(errors="replace"),
           "stdout": None if quiet_stdout else result.stdout.decode(errors="replace")}
    log.append(row)
    need(result.returncode == 0, "COMMAND_FAILED:" + str(command[0]))
    return row


def make_archive(root, destination, prefix=OFF):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for file in sorted(p for p in root.rglob("*") if p.is_file()):
            relative = prefix + "/" + file.relative_to(root).as_posix()
            content = read_file(file)
            info = tarfile.TarInfo(relative)
            info.size, info.mode, info.mtime, info.uid, info.gid = len(content), 0o644, 0, 0, 0
            archive.addfile(info, io.BytesIO(content))
    with destination.open("wb") as output:
        with gzip.GzipFile(fileobj=output, filename="", mode="wb", mtime=0) as zipped:
            zipped.write(raw.getvalue())


def staged_payload(stage):
    need(not stage.stat().st_mode & 0o7000, "STAGED_DIRECTORY_SPECIAL_MODE")
    result = {}
    for path in sorted(stage.rglob("*")):
        need(not path.is_symlink(), "STAGED_OUTPUT_SYMLINK")
        if path.is_file():
            result[path.relative_to(stage).as_posix()] = identity(read_file(path))
        else:
            need(path.is_dir(), "STAGED_OUTPUT_SPECIAL_FILE")
            need(not path.stat().st_mode & 0o7000, "STAGED_DIRECTORY_SPECIAL_MODE")
    return result


def build_source_candidate(base, reports, output, compiler, rojo, context):
    """Build exact source identities; final verifier alone may create delivery."""
    lock = load_lock()
    producer_before = read_file(Path(__file__))
    profile_before = read_file(HERE / "profile_lock.json")
    output = Path(output).absolute()
    need(not output.exists() and not output.is_symlink(), "OUTPUT_ALREADY_EXISTS")
    inputs = load_inputs(base, reports, lock)
    base = inputs["base"]
    need(not output.resolve().is_relative_to(base) and not base.is_relative_to(output.resolve()),
         "OUTPUT_OVERLAPS_INPUT")
    validate_context(context, inputs["receipt"])
    on, off = transform(inputs, lock)
    field_off, field_off_lock = field_prompt_parent(on, lock)
    role_off, role_off_lock = role_readability_parent(field_off, field_off_lock)
    canyon_off, canyon_off_lock = br_canyon_parent(role_off, role_off_lock)
    relay_off, relay_off_lock = relay_presentation_parent(canyon_off, canyon_off_lock)
    score_off, score_off_lock = score_parent(relay_off, relay_off_lock)
    castle_off, castle_off_lock = castle_parent(score_off, score_off_lock)
    vault_off, vault_off_lock = vault_parent(castle_off, castle_off_lock)
    item_off, item_off_lock = item_parent(vault_off, vault_off_lock)
    guardian_off, guardian_off_lock = guardian_parent(item_off, item_off_lock)
    parent_lock = beast_parent_profile(guardian_off_lock)
    h72 = beast_parent_sources(guardian_off, guardian_off_lock, parent_lock)
    bot_parent = bot_parent_sources(h72, parent_lock)
    hud_off = hud_current_sources(bot_parent, parent_lock)
    compiler, rojo = Path(compiler).resolve(), Path(rojo).resolve()
    compiler_before, rojo_before = identity(read_file(compiler)), identity(read_file(rojo))
    need(os.access(compiler, os.X_OK) and os.access(rojo, os.X_OK), "TOOL_NOT_EXECUTABLE")
    need(rojo_before == {k: lock["rojo"][k] for k in ("bytes", "sha256")}, "ROJO_IDENTITY")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output.name + ".building-", dir=output.parent))
    logs = []
    try:
        builds = ((stage, on, lock["final_place"], None),
                  (stage / OFF, off, lock["prior_place"], None),
                  (stage / BOT_OFF, bot_parent, lock["bot_followup_repair"]["parent_place"], BOT_SOURCE),
                  (stage / HUD_OFF, hud_off, lock["followup_repair"]["current_place"], HUD_SOURCE),
                  (stage / BEAST_OFF, h72, parent_lock["final_place"], BEAST_SOURCE),
                  (stage / GUARDIAN_OFF, guardian_off, guardian_off_lock["final_place"], GUARDIAN_SOURCE),
                  (stage / ITEM_OFF, item_off, item_off_lock["final_place"], ITEM_SOURCE),
                  (stage / VAULT_OFF, vault_off, vault_off_lock["final_place"], VAULT_SOURCE),
                  (stage / CASTLE_OFF, castle_off, castle_off_lock["final_place"], VAULT_SOURCE),
                  (stage / SCORE_OFF, score_off, score_off_lock["final_place"], SCORE_SOURCE),
                  (stage / RELAY_PRESENTATION_OFF, relay_off, relay_off_lock["final_place"], RELAY_PRESENTATION_SOURCES),
                  (stage / BR_CANYON_OFF, canyon_off, canyon_off_lock["final_place"], BR_CANYON_SOURCES),
                  (stage / ROLE_READABILITY_OFF, role_off, role_off_lock["final_place"], ROLE_READABILITY_SOURCES),
                  (stage / FIELD_PROMPT_OFF, field_off, field_off_lock["final_place"], VAULT_SOURCE))
        for folder, sources, wanted, changed_source in builds:
            folder.mkdir(exist_ok=True)
            (folder / PROJECT).write_bytes(inputs["project"])
            for name, raw in sources.items():
                path = folder / "sources" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                if (changed_source is None or name == changed_source
                        or isinstance(changed_source, tuple) and name in changed_source):
                    run_checked([compiler, "--text", path], logs, quiet_stdout=True)
            run_checked([rojo, "build", folder / PROJECT, "-o", folder / PLACE], logs)
            place = read_file(folder / PLACE)
            need(identity(place) == wanted, "BUILT_PLACE_IDENTITY")
            embedded, non_source = place_inventory(place)
            need(non_source == inputs["non_source"], "NON_SOURCE_PROPERTY_DRIFT")
            for name, row in lock["sources"].items():
                need(embedded[row["route"]] == {"class": row["class"], "raw": sources[name]},
                     "BUILT_EMBEDDED_SOURCE:" + name)
        (stage / OFF / RECEIPT).write_bytes(inputs["receipt_raw"])
        for name, raw in inputs["evidence"].items():
            path = stage / "prior_boundary" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            if name in lock["prior_report_names"]:
                (stage / OFF / name).write_bytes(raw)
        make_archive(stage / OFF, stage / OFF_ARCHIVE)
        archive_identity = identity(read_file(stage / OFF_ARCHIVE))
        make_archive(stage / HUD_OFF, stage / HUD_OFF_ARCHIVE, HUD_OFF)
        hud_archive_identity = identity(read_file(stage / HUD_OFF_ARCHIVE))
        make_archive(stage / BOT_OFF, stage / BOT_OFF_ARCHIVE, BOT_OFF)
        bot_archive_identity = identity(read_file(stage / BOT_OFF_ARCHIVE))
        make_archive(stage / BEAST_OFF, stage / BEAST_OFF_ARCHIVE, BEAST_OFF)
        beast_archive_identity = identity(read_file(stage / BEAST_OFF_ARCHIVE))
        make_archive(stage / GUARDIAN_OFF, stage / GUARDIAN_OFF_ARCHIVE, GUARDIAN_OFF)
        field_archive_identity = identity(read_file(stage / GUARDIAN_OFF_ARCHIVE))
        make_archive(stage / ITEM_OFF, stage / ITEM_OFF_ARCHIVE, ITEM_OFF)
        item_archive_identity = identity(read_file(stage / ITEM_OFF_ARCHIVE))
        make_archive(stage / VAULT_OFF, stage / VAULT_OFF_ARCHIVE, VAULT_OFF)
        vault_archive_identity = identity(read_file(stage / VAULT_OFF_ARCHIVE))
        make_archive(stage / CASTLE_OFF, stage / CASTLE_OFF_ARCHIVE, CASTLE_OFF)
        castle_archive_identity = identity(read_file(stage / CASTLE_OFF_ARCHIVE))
        make_archive(stage / SCORE_OFF, stage / SCORE_OFF_ARCHIVE, SCORE_OFF)
        score_archive_identity = identity(read_file(stage / SCORE_OFF_ARCHIVE))
        make_archive(stage / RELAY_PRESENTATION_OFF, stage / RELAY_PRESENTATION_OFF_ARCHIVE, RELAY_PRESENTATION_OFF)
        relay_archive_identity = identity(read_file(stage / RELAY_PRESENTATION_OFF_ARCHIVE))
        make_archive(stage / BR_CANYON_OFF, stage / BR_CANYON_OFF_ARCHIVE, BR_CANYON_OFF)
        canyon_archive_identity = identity(read_file(stage / BR_CANYON_OFF_ARCHIVE))
        make_archive(stage / ROLE_READABILITY_OFF, stage / ROLE_READABILITY_OFF_ARCHIVE, ROLE_READABILITY_OFF)
        role_archive_identity = identity(read_file(stage / ROLE_READABILITY_OFF_ARCHIVE))
        make_archive(stage / FIELD_PROMPT_OFF, stage / FIELD_PROMPT_OFF_ARCHIVE, FIELD_PROMPT_OFF)
        field_prompt_archive_identity = identity(read_file(stage / FIELD_PROMPT_OFF_ARCHIVE))
        expected_stage = {"sources/" + name: identity(raw) for name, raw in on.items()}
        expected_stage.update({OFF + "/sources/" + name: identity(raw) for name, raw in off.items()})
        expected_stage.update({PROJECT: lock["project"], PLACE: lock["final_place"],
                               OFF + "/" + PROJECT: lock["project"], OFF + "/" + PLACE: lock["prior_place"],
                               OFF + "/" + RECEIPT: identity(inputs["receipt_raw"]), OFF_ARCHIVE: archive_identity})
        expected_stage.update({"prior_boundary/" + name: identity(raw) for name, raw in inputs["evidence"].items()})
        expected_stage.update({OFF + "/" + name: identity(inputs["evidence"][name]) for name in lock["prior_report_names"]})
        expected_stage.update({HUD_OFF + "/sources/" + name: identity(raw) for name, raw in hud_off.items()})
        expected_stage.update({HUD_OFF + "/" + PROJECT: lock["project"],
                               HUD_OFF + "/" + PLACE: lock["followup_repair"]["current_place"],
                               HUD_OFF_ARCHIVE: hud_archive_identity})
        expected_stage.update({BOT_OFF + "/sources/" + name: identity(raw) for name, raw in bot_parent.items()})
        expected_stage.update({BOT_OFF + "/" + PROJECT: lock["project"],
                               BOT_OFF + "/" + PLACE: lock["bot_followup_repair"]["parent_place"],
                               BOT_OFF_ARCHIVE: bot_archive_identity})
        expected_stage.update({BEAST_OFF + "/sources/" + name: identity(raw) for name, raw in h72.items()})
        expected_stage.update({BEAST_OFF + "/" + PROJECT: lock["project"],
                               BEAST_OFF + "/" + PLACE: parent_lock["final_place"],
                               BEAST_OFF_ARCHIVE: beast_archive_identity})
        expected_stage.update({GUARDIAN_OFF + "/sources/" + name: identity(raw) for name, raw in guardian_off.items()})
        expected_stage.update({GUARDIAN_OFF + "/" + PROJECT: lock["project"],
                               GUARDIAN_OFF + "/" + PLACE: guardian_off_lock["final_place"],
                               GUARDIAN_OFF_ARCHIVE: field_archive_identity})
        expected_stage.update({ITEM_OFF + "/sources/" + name: identity(raw) for name, raw in item_off.items()})
        expected_stage.update({ITEM_OFF + "/" + PROJECT: lock["project"],
                               ITEM_OFF + "/" + PLACE: item_off_lock["final_place"],
                               ITEM_OFF_ARCHIVE: item_archive_identity})
        expected_stage.update({VAULT_OFF + "/sources/" + name: identity(raw) for name, raw in vault_off.items()})
        expected_stage.update({VAULT_OFF + "/" + PROJECT: lock["project"],
                               VAULT_OFF + "/" + PLACE: vault_off_lock["final_place"],
                               VAULT_OFF_ARCHIVE: vault_archive_identity})
        expected_stage.update({CASTLE_OFF + "/sources/" + name: identity(raw) for name, raw in castle_off.items()})
        expected_stage.update({CASTLE_OFF + "/" + PROJECT: lock["project"],
                               CASTLE_OFF + "/" + PLACE: castle_off_lock["final_place"],
                               CASTLE_OFF_ARCHIVE: castle_archive_identity})
        expected_stage.update({SCORE_OFF + "/sources/" + name: identity(raw) for name, raw in score_off.items()})
        expected_stage.update({SCORE_OFF + "/" + PROJECT: lock["project"],
                               SCORE_OFF + "/" + PLACE: score_off_lock["final_place"],
                               SCORE_OFF_ARCHIVE: score_archive_identity})
        expected_stage.update({RELAY_PRESENTATION_OFF + "/sources/" + name: identity(raw) for name, raw in relay_off.items()})
        expected_stage.update({RELAY_PRESENTATION_OFF + "/" + PROJECT: lock["project"],
                               RELAY_PRESENTATION_OFF + "/" + PLACE: relay_off_lock["final_place"],
                               RELAY_PRESENTATION_OFF_ARCHIVE: relay_archive_identity})
        expected_stage.update({BR_CANYON_OFF + "/sources/" + name: identity(raw) for name, raw in canyon_off.items()})
        expected_stage.update({BR_CANYON_OFF + "/" + PROJECT: lock["project"],
                               BR_CANYON_OFF + "/" + PLACE: canyon_off_lock["final_place"],
                               BR_CANYON_OFF_ARCHIVE: canyon_archive_identity})
        expected_stage.update({ROLE_READABILITY_OFF + "/sources/" + name: identity(raw) for name, raw in role_off.items()})
        expected_stage.update({ROLE_READABILITY_OFF + "/" + PROJECT: lock["project"],
                               ROLE_READABILITY_OFF + "/" + PLACE: role_off_lock["final_place"],
                               ROLE_READABILITY_OFF_ARCHIVE: role_archive_identity})
        expected_stage.update({FIELD_PROMPT_OFF + "/sources/" + name: identity(raw) for name, raw in field_off.items()})
        expected_stage.update({FIELD_PROMPT_OFF + "/" + PROJECT: lock["project"],
                               FIELD_PROMPT_OFF + "/" + PLACE: field_off_lock["final_place"],
                               FIELD_PROMPT_OFF_ARCHIVE: field_prompt_archive_identity})
        final_receipt = {
            "schema": "GQ470_UNION22_CURRENT_SOURCE_RECEIPT_V1",
            "feature_id": lock["feature_id"], "source_profile": "REAL69",
            "private_companion_profile": "REAL69_UNION22", "official_branch": FORMAL,
            "build_head": context["build_head"], "canonical_build": context["canonical_build"],
            "execution_context": context,
            "receipt_provenance": context["kind"], "official_build_head": context["official_build_head"],
            "formal_rc_adoption_proven": context["kind"] == "OFFICIAL",
            "selected_source_count": 69, "changed_source_count": 26, "unchanged_source_count": 43,
            "source_hashes": {row["route"]: row["after"]["sha256"] for row in lock["sources"].values()},
            "source_classes": {row["route"]: row["class"] for row in lock["sources"].values()},
            "private_place_bytes": lock["final_place"]["bytes"],
            "private_place_sha256": lock["final_place"]["sha256"],
            "prior_place": lock["prior_place"], "prior_receipt": identity(inputs["receipt_raw"]),
            "profile_lock": identity(read_file(HERE / "profile_lock.json")),
            "prior_evidence": {name: identity(raw) for name, raw in inputs["evidence"].items()},
            "runtime_rollback_archive": archive_identity,
            "followup_repair": lock["followup_repair"],
            "hud_only_current_rc_rollback_archive": hud_archive_identity,
            "bot_followup_repair": lock["bot_followup_repair"],
            "bot_only_hud_parent_rollback_archive": bot_archive_identity,
            "beast_followup_repair": lock["beast_followup_repair"],
            "beast_only_h72_parent_rollback_archive": beast_archive_identity,
            "guardian_followup_repair": lock["guardian_followup_repair"],
            "guardian_only_beast_parent_rollback_archive": field_archive_identity,
            "item_cleanup_followup": lock["item_cleanup_followup"],
            "item_cleanup_only_rollback_archive": item_archive_identity,
            "empty_vault_followup": lock["empty_vault_followup"],
            "empty_vault_only_rollback_archive": vault_archive_identity,
            "castle_release_stock_followup": lock["castle_release_stock_followup"],
            "castle_release_stock_rollback_archive": castle_archive_identity,
            "score_relay_followup": lock["score_relay_followup"],
            "score_relay_rollback_archive": score_archive_identity,
            "relay_presentation_followup": lock["relay_presentation_followup"],
            "relay_presentation_rollback_archive": relay_archive_identity,
            "br_canyon_followup": lock["br_canyon_followup"],
            "br_canyon_rollback_archive": canyon_archive_identity,
            "role_readability_followup": lock["role_readability_followup"],
            "role_readability_rollback_archive": role_archive_identity,
            "field_prompt_followup": lock["field_prompt_followup"],
            "field_prompt_rollback_archive": field_prompt_archive_identity,
            "legacy_48_all_ported": False, "owner_accepted": False,
            "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO",
            "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
            "android_15min": "NOT_TESTED", "fun": "NOT_TESTED",
            "roblox_publish": False, "paid_trade": False,
            "identity_receipt_is_not_final_delivery_admission": True,
            **lock["runtime_labels"],
        }
        core_report = {
            "schema": "GQ470_UNION22_CORE_BUILD_V1", "status": "PASS_SOURCE_BUILD_ONLY",
            "final_delivery_created": False, "context": context,
            "source_count": 69, "changed_sources": 26, "unchanged_sources": 43,
            "compile_count": 153, "rojo_build_count": 14, "instances": 75,
            "item_cleanup_only_parent_place": item_off_lock["final_place"],
            "empty_vault_only_parent_place": vault_off_lock["final_place"],
            "castle_release_stock_parent_place": castle_off_lock["final_place"],
            "score_relay_parent_place": score_off_lock["final_place"],
            "relay_presentation_parent_place": relay_off_lock["final_place"],
            "br_canyon_parent_place": canyon_off_lock["final_place"],
            "role_readability_parent_place": role_off_lock["final_place"],
            "field_prompt_parent_place": field_off_lock["final_place"],
            "guardian_only_compile_count": 1, "guardian_only_rojo_build_count": 1,
            "guardian_only_beast_parent_place": guardian_off_lock["final_place"],
            "changed_sources_from_beast_parent": 1, "unchanged_sources_from_beast_parent": 68,
            "beast_only_compile_count": 1, "beast_only_rojo_build_count": 1,
            "beast_only_h72_parent_place": parent_lock["final_place"],
            "changed_sources_from_h72_parent": 1, "unchanged_sources_from_h72_parent": 68,
            "historical_on_br_compile_count": 138, "historical_on_br_rojo_build_count": 2,
            "hud_only_compile_count": 1, "hud_only_rojo_build_count": 1,
            "hud_only_off_place": lock["followup_repair"]["current_place"],
            "hud_stage_changed_sources_from_current_rc": 1, "hud_stage_unchanged_sources_from_current_rc": 68,
            "bot_only_compile_count": 1, "bot_only_rojo_build_count": 1,
            "bot_only_parent_place": lock["bot_followup_repair"]["parent_place"],
            "changed_sources_from_hud_parent": 1, "unchanged_sources_from_hud_parent": 68,
            "prior_snapshot": inputs["snapshot"], "final_place": lock["final_place"],
            "off_place": lock["prior_place"], "actual_inverse_source_and_place_exact": True,
            "non_source_property_identity": identity(inputs["non_source"]),
            "compiler": compiler_before, "rojo": rojo_before,
            "build_command_namespace": {"executed_stage": str(stage), "committed_root": str(output),
                                        "commands_are_actual_pre_rename_paths": True},
            "profile_lock": identity(read_file(HERE / "profile_lock.json")),
            "composer": identity(producer_before),
            "commands": logs, "original_receipt_preserved_byte_exact": True}
        need(load_inputs(base, reports, lock)["snapshot"] == inputs["snapshot"], "INPUT_CHANGED_DURING_BUILD")
        need(identity(read_file(compiler)) == compiler_before and identity(read_file(rojo)) == rojo_before,
             "TOOL_CHANGED_DURING_BUILD")
        need(read_file(Path(__file__)) == producer_before
             and read_file(HERE / "profile_lock.json") == profile_before, "PRODUCER_OR_PROFILE_CHANGED_DURING_BUILD")
        need(staged_payload(stage) == expected_stage, "STAGED_OUTPUT_CHANGED_AFTER_BUILD")
        core_report["staged_payload_verified_after_all_commands"] = True
        core_report["staged_payload"] = expected_stage
        need(not (stage / "delivery").exists(), "PREMATURE_DELIVERY")
        write_json(stage / RECEIPT, final_receipt)
        write_json(stage / "CORE_BUILD_REPORT.json", core_report)
        stage.rename(output)
        return output
    except Exception as error:
        # A failed private stage cannot retain an apparently successful report.
        for name in (RECEIPT, "CORE_BUILD_REPORT.json"):
            (stage / name).unlink(missing_ok=True)
        write_json(stage / "FAILED.json", {"status": "FAIL_NO_DELIVERY", "reason": str(error), "commands": logs})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--prior-reports", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--luau-compile", type=Path, required=True)
    parser.add_argument("--rojo", type=Path, required=True)
    args = parser.parse_args()
    inputs = load_inputs(args.base, args.prior_reports)
    context = live_context(inputs["receipt"], args.head)
    result = build_source_candidate(args.base, args.prior_reports, args.out,
                                    args.luau_compile, args.rojo, context)
    print("UNION22_EXACT_SOURCE_BUILD_ONLY_NO_DELIVERY", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
