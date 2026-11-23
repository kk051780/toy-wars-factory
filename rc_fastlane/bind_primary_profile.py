#!/usr/bin/env python3
"""Offline A2 binding audit; never selects a runtime or executes a quality gate.

Inputs are caller-supplied evidence, not remotely authenticated by this module.
The synthetic mode preserves Native history in a separate, explicit namespace.
No canonical producer/verifier is imported and no GitHub environment is read.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET


CONTEXT_FIELDS = frozenset(("kind", "build_head", "checkout_sha", "canonical_build",
                            "official_build_head", "observed_live_rc", "event",
                            "run_id", "run_attempt"))
TARGET = "REAL69_UNION22"
SYNTHETIC_SELECTOR = "eggrumble_v3_real69_union22_private_studio"
MANIFEST = "UNION22_DELIVERY_MANIFEST.json"
PROFILE = "UNION22_PROFILE_LOCK.json"
SOURCE_RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
CORE = "CORE_BUILD_REPORT.json"
ADMISSION = "UNION22_FINAL_ADMISSION.json"
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
HOST = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
CLASS_COUNTS = {"Script": 12, "LocalScript": 10, "ModuleScript": 47}
GAPS = frozenset(("SIX_SKILL_DURABLE", "SAVED_PVE_MASTERY",
                  "SAVED_BEAST_EVOLUTION", "SCOUT_SPECIES_V1"))
SUMMARY = {"EVIDENCE_GAP": 4, "MARKER_SOURCE_PRESENT": 15,
           "NON_RUNTIME_LEGACY_FLAG": 2, "SOURCE_ANALOGUE_ONLY": 27}
SUITES = {
    "combined_clear_los": (
        "SHARED_MODULES", "FIRST_READY", "FIRST_GUARDIAN_INCOMING", "FIRST_SWARM_KO",
        "FINISH_AND_CLOSE", "NEXT_READY", "OLD_GENERATION_RETIRED",
        "SECOND_GUARDIAN_INCOMING", "SECOND_SWARM_KO", "COMBINED_HOST_RUNTIME"),
    "objective_full_clear_los": (
        "WHOLE_HOST_READY", "REAL_TOOL_REAL_SWARM_AWAKEN", "AWAKENED_SIEGE_DENIED",
        "AWAKENED_VAULT_DENIED", "AWAKENED_FIELD_DENIED",
        "EXPIRY_PICKUP_DEPOSIT_RESTORED", "WHOLE_HOST_OBJECTIVE_CROSS"),
}
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
LONG_BRACKET = re.compile(r"\[(=*)\[")
PRIOR_REPORTS = frozenset(("ART_CHECK_REPORT.json", "RC85_RC86_REAL69_ALL48_FEATURE_TRUTH.json",
                           "REAL69_LEGACY17_NONLOSS_AUDIT.json"))
PRIOR_ROLLBACKS = frozenset("OFF69_" + name + "_ROLLBACK.tar.gz" for name in (
    "BOT_ART", "DISCOVERY", "FB019", "FORTRESS", "GQ470_P0", "HUD_DISPLAY", "OBJECTIVE", "REEF_SCULPT"))
ROLLBACK = "OFF69_UNION22_PRIOR_BR_ROLLBACK.tar.gz"


class BindingError(ValueError):
    """A rejection with a stable public error family."""

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def _need(condition, code, detail):
    if not condition:
        raise BindingError(code, detail)


def _pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _is_pin(value):
    return (isinstance(value, dict) and set(value) == {"bytes", "sha256"}
            and type(value["bytes"]) is int and value["bytes"] >= 0
            and isinstance(value["sha256"], str) and SHA64.fullmatch(value["sha256"]))


def _json(raw, label):
    def pairs(items):
        result = {}
        for key, value in items:
            _need(key not in result, "BIND_JSON", f"duplicate key in {label}: {key}")
            result[key] = value
        return result

    def constant(value):
        raise BindingError("BIND_JSON", f"nonfinite value in {label}: {value}")

    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                            parse_constant=constant)
    except BindingError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise BindingError("BIND_JSON", f"invalid JSON: {label}") from exc
    _need(isinstance(result, dict), "BIND_JSON", f"object required: {label}")
    # Overflowing exponents (1e999) do not use parse_constant.
    def finite(value):
        if isinstance(value, float):
            import math
            _need(math.isfinite(value), "BIND_JSON", f"nonfinite number: {label}")
        elif isinstance(value, dict):
            for item in value.values():
                finite(item)
        elif isinstance(value, list):
            for item in value:
                finite(item)
    try:
        finite(result)
    except RecursionError as exc:
        raise BindingError("BIND_JSON", f"excessively nested JSON: {label}") from exc
    return result


def _absolute(path, code="BIND_PATH"):
    try:
        path = Path(path)
        _need(".." not in path.parts and "\x00" not in str(path), code, "unsafe path")
        return Path(os.path.abspath(path))
    except (TypeError, ValueError, OSError) as exc:
        if isinstance(exc, BindingError):
            raise
        raise BindingError(code, "invalid path") from exc


def _safe_existing(path, directory=False, code="BIND_PATH"):
    """Reject links in every component, including a symlinked parent."""
    path = _absolute(path, code)
    for item in (*reversed(path.parents), path):
        try:
            info = item.lstat()
        except OSError as exc:
            raise BindingError("BIND_IO" if code == "BIND_PATH" else code,
                               f"unreadable path: {item}") from exc
        _need(not stat.S_ISLNK(info.st_mode), code, f"symlink: {item}")
        expected_dir = item != path or directory
        _need(stat.S_ISDIR(info.st_mode) if expected_dir else stat.S_ISREG(info.st_mode),
              code, f"unexpected file type: {item}")
    return path


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns)


def _read(path):
    path = _safe_existing(path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            _need(stat.S_ISREG(before.st_mode), "BIND_PATH", "nonregular input")
            raw = stream.read()
            after = os.fstat(stream.fileno())
        _need(_identity(before) == _identity(after) == _identity(path.lstat()),
              "BIND_INPUT_CHANGED", f"changed while reading: {path}")
        return raw, _identity(after)
    except OSError as exc:
        raise BindingError("BIND_IO", f"cannot read: {path}") from exc


def _member(name):
    _need(isinstance(name, str) and name and "\\" not in name and "\x00" not in name,
          "BIND_MANIFEST_FILES", "invalid member name")
    path = PurePosixPath(name)
    _need(not path.is_absolute() and str(path) == name
          and all(part not in (".", "..", "") for part in path.parts),
          "BIND_MANIFEST_FILES", f"unsafe member: {name}")
    return name


def _tree(root):
    root = _safe_existing(root, directory=True)
    files, directories = {}, set()
    try:
        for directory, dirs, names in os.walk(root, followlinks=False):
            dp = Path(directory)
            _safe_existing(dp, directory=True)
            directories.add(str(dp.relative_to(root)))
            for name in dirs:
                _safe_existing(dp / name, directory=True)
            for name in names:
                path = dp / name
                relative = _member(path.relative_to(root).as_posix())
                raw, identity = _read(path)
                files[relative] = (raw, identity)
    except OSError as exc:
        raise BindingError("BIND_IO", f"cannot inventory: {root}") from exc
    return files, frozenset(directories)


class _Inputs:
    def __init__(self):
        self.files = {}
        self.trees = {}

    def file(self, path):
        path = _absolute(path)
        raw, identity = _read(path)
        if path in self.files:
            _need(self.files[path] == (raw, identity), "BIND_INPUT_CHANGED", str(path))
        self.files[path] = (raw, identity)
        return raw

    def tree(self, path):
        path = _absolute(path)
        files, directories = _tree(path)
        if path in self.trees:
            _need(self.trees[path] == (files, directories), "BIND_INPUT_CHANGED", str(path))
        self.trees[path] = (files, directories)
        return {name: value[0] for name, value in files.items()}

    def recheck(self):
        try:
            for path, previous in self.files.items():
                _need(_read(path) == previous, "BIND_INPUT_CHANGED", str(path))
            for path, previous in self.trees.items():
                _need(_tree(path) == previous, "BIND_INPUT_CHANGED", str(path))
        except BindingError as exc:
            if exc.code == "BIND_INPUT_CHANGED":
                raise
            raise BindingError("BIND_INPUT_CHANGED", "input safety or bytes changed") from exc


def _context(value, *, synthetic=None):
    _need(isinstance(value, Mapping) and set(value) == CONTEXT_FIELDS,
          "BIND_CONTEXT", "exact nine-field context required")
    context = dict(value)
    for key in ("build_head", "checkout_sha"):
        _need(isinstance(context[key], str) and SHA40.fullmatch(context[key]),
              "BIND_CONTEXT", f"invalid {key}")
    kind = context["kind"]
    _need(kind in ("OFFICIAL", "PR_CANDIDATE", "LOCAL_SOURCE_REVIEW"),
          "BIND_CONTEXT", "unsupported context kind")
    official = kind == "OFFICIAL"
    _need(context["canonical_build"] is official
          and context["official_build_head"] == (context["build_head"] if official else None),
          "BIND_CONTEXT", "context classification")
    if kind == "LOCAL_SOURCE_REVIEW":
        _need(all(context[k] is None for k in ("observed_live_rc", "event", "run_id", "run_attempt")),
              "BIND_CONTEXT", "local context cannot claim CI")
    else:
        _need(context["checkout_sha"] == context["build_head"]
              and isinstance(context["observed_live_rc"], str)
              and SHA40.fullmatch(context["observed_live_rc"])
              and context["event"] == ("push" if official else "pull_request")
              and all(isinstance(context[k], str) and re.fullmatch(r"[0-9]+", context[k])
                      and context[k].lstrip("0") for k in ("run_id", "run_attempt")),
              "BIND_CONTEXT", "archived run context")
        if official:
            _need(context["observed_live_rc"] == context["build_head"],
                  "BIND_CONTEXT", "official RC context")
    if synthetic is not None:
        _need((kind == "LOCAL_SOURCE_REVIEW") is synthetic,
              "BIND_CONTEXT", "input kind/context mismatch")
    return context


def _eq_context(document, key, context):
    _need(_context(document.get(key)) == context, "BIND_CONTEXT", f"{key} mismatch")


def _provenance(document, context, *, source=False):
    _need(document.get("build_head" if source else "candidate_build_head") == context["build_head"]
          and document.get("official_build_head") == context["official_build_head"]
          and document.get("receipt_provenance") == context["kind"]
          and document.get("formal_rc_adoption_proven") is context["canonical_build"],
          "BIND_CONTEXT", "head/provenance/adoption mismatch")
    if source:
        _need(document.get("canonical_build") is context["canonical_build"],
              "BIND_CONTEXT", "source canonical flag")


def _engine_claims(document, *, required=False):
    expected = {"studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
                "studio_2client": "NOT_TESTED", "android_15min": "NOT_TESTED",
                "fun": "NOT_TESTED", "owner_accepted": False, "owner_acceptance": "NO_GO",
                "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO",
                "roblox_publish": False, "paid_trade": False,
                "studio_executed": False, "native_executed": False,
                "fresh_ci_executed": False, "current_native_admission_proven": False}
    if required:
        _need({"studio_solo", "studio_two_client", "android_15min", "fun", "owner_accepted",
               "art_gate", "product_gate"} <= set(document), "BIND_ENGINE_CLAIM", "engine boundaries missing")
    for key, value in expected.items():
        if key in document:
            actual = document[key]
            _need(actual is value if isinstance(value, bool) else actual == value,
                  "BIND_ENGINE_CLAIM", f"unsupported {key}")


def _labels(document, labels):
    _need({k: document.get(k) for k in labels} == labels,
          "BIND_RUNTIME_CLAIM", "runtime labels differ")
    if "legacy_48_all_ported" in document:
        _need(document["legacy_48_all_ported"] is False, "BIND_RUNTIME_CLAIM", "legacy parity claim")
    if "all_48_semantic_parity" in document:
        _need(document["all_48_semantic_parity"] == "NOT_PROVEN", "BIND_RUNTIME_CLAIM", "semantic parity claim")
    _engine_claims(document)


def _strip_luau_comments(text):
    """Keep strings intact; comment text cannot supply the Host's executable guard."""
    result, index = [], 0
    while index < len(text):
        comment = text.startswith("--", index)
        start = index + 2 if comment else index
        bracket = LONG_BRACKET.match(text, start)
        if bracket:
            close = "]" + bracket.group(1) + "]"
            end = text.find(close, start + len(bracket.group(0)))
            _need(end >= 0, "BIND_AUTHORITY", "unclosed long string/comment")
            end += len(close)
            result.append("\n" if comment else text[index:end])
            index = end
        elif comment:
            end = text.find("\n", index)
            index = len(text) if end < 0 else end
            result.append("\n")
        elif text[index] in ("'", '"', "`"):
            quote, end = text[index], index + 1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                elif text[end] == quote:
                    end += 1
                    break
                else:
                    end += 1
            result.append(text[index:end])
            index = end
        else:
            result.append(text[index])
            index += 1
    return "".join(result)


def _source_inventory(files, profile):
    sources = profile.get("sources")
    _need(isinstance(sources, dict) and len(sources) == 69, "BIND_SOURCE", "69 source entries required")
    actual = {name[len("sources/"):]: raw for name, raw in files.items() if name.startswith("sources/")}
    _need(set(actual) == set(sources), "BIND_SOURCE", "exact source file set")
    routes, classes = {}, Counter()
    for name, entry in sources.items():
        _member(name)
        _need(isinstance(entry, dict), "BIND_SOURCE", "source entry")
        kind, route = entry.get("class"), entry.get("route")
        _need(kind in CLASS_COUNTS and isinstance(route, str) and route not in routes,
              "BIND_SOURCE", "duplicate route or unknown class")
        suffix = {"Script": ".server.luau", "LocalScript": ".client.luau", "ModuleScript": ".luau"}[kind]
        _need(name == route + suffix, "BIND_SOURCE", f"source class/path: {name}")
        _need(_is_pin(entry.get("after")) and _pin(actual[name]) == entry["after"],
              "BIND_SOURCE", f"source body: {name}")
        _need(not re.search(r"TrapRaiders|PersistentHatchStore|(?:^|/)Game$", route),
              "BIND_AUTHORITY", f"mixed legacy authority: {route}")
        routes[route] = (kind, actual[name])
        classes[kind] += 1
    _need(dict(classes) == CLASS_COUNTS, "BIND_SOURCE", "source class counts")
    _need(HOST in routes and routes[HOST][0] == "Script", "BIND_AUTHORITY", "one canonical Host required")
    try:
        executable = _strip_luau_comments(routes[HOST][1].decode("utf-8"))
    except UnicodeError as exc:
        raise BindingError("BIND_SOURCE", "source UTF-8") from exc
    prefix = (r"\A\s*local\s+Players\s*=\s*game:GetService\([\"']Players[\"']\)\s*"
              r"local\s+RunService\s*=\s*game:GetService\([\"']RunService[\"']\)\s*"
              r"local\s+Debris\s*=\s*game:GetService\([\"']Debris[\"']\)\s*"
              r"if\s+not\s+RunService:IsStudio\(\)\s+then\s+return\s+end(?:\s|$)")
    _need(re.match(prefix, executable) is not None, "BIND_AUTHORITY", "executable early Studio guard required")
    return actual, routes


def _project_and_place(files, profile, routes):
    _need(_pin(files[PROJECT]) == profile.get("project"), "BIND_PROJECT", "project pin")
    project = _json(files[PROJECT], PROJECT)
    _need(isinstance(project.get("tree"), dict) and project["tree"].get("$className") == "DataModel",
          "BIND_PROJECT", "DataModel project required")
    inventory = {}

    def visit(node, route=""):
        _need(isinstance(node, dict), "BIND_PROJECT", "project node")
        allowed = {"$path"} if "$path" in node else {"$className"}
        _need(all(not key.startswith("$") or key in allowed for key in node),
              "BIND_PROJECT", "unexpected project properties")
        if route:
            if "$path" in node:
                _need(set(node) == {"$path"} and route in routes, "BIND_PROJECT", "source project node")
                expected = next(name for name, value in profile["sources"].items() if value["route"] == route)
                _need(node["$path"] == "sources/" + expected, "BIND_PROJECT", "source path binding")
                inventory[route] = routes[route][0]
            else:
                inventory[route] = node.get("$className", route if "/" not in route else None)
        for name, child in node.items():
            if not name.startswith("$"):
                _need(isinstance(name, str) and name and "/" not in name and "\\" not in name,
                      "BIND_PROJECT", "node name")
                visit(child, f"{route}/{name}".lstrip("/"))
    visit(project["tree"])
    _need(len(inventory) == 75 and {r for r, c in inventory.items() if c in CLASS_COUNTS} == set(routes),
          "BIND_PROJECT", "project inventory")
    _need(_pin(files[PLACE]) == profile.get("final_place"), "BIND_PLACE", "Place pin")
    _need(b"<!DOCTYPE" not in files[PLACE].upper() and b"<!ENTITY" not in files[PLACE].upper(),
          "BIND_PLACE", "DTD/entities forbidden")
    try:
        xml = ET.fromstring(files[PLACE])
    except ET.ParseError as exc:
        raise BindingError("BIND_PLACE", "invalid Place XML") from exc
    _need(xml.tag == "roblox" and xml.get("version") == "4", "BIND_PLACE", "Place root")
    found, referents = {}, set()

    def items(parent, prefix=""):
        for item in parent.findall("Item"):
            properties = item.findall("Properties")
            _need(len(properties) == 1, "BIND_PLACE", "unique Properties required")
            props = {}
            for prop in properties[0]:
                key = prop.get("name")
                _need(key and key not in props, "BIND_PLACE", "duplicate Place property")
                props[key] = prop
            _need("Name" in props and props["Name"].tag == "string", "BIND_PLACE", "instance Name")
            name = props["Name"].text
            _need(isinstance(name, str) and name and "/" not in name and "\\" not in name,
                  "BIND_PLACE", "unsafe instance Name")
            route = f"{prefix}/{name}".lstrip("/")
            kind = item.get("class")
            _need(route not in found, "BIND_AUTHORITY", "duplicate instance route")
            ref = item.get("referent")
            _need(ref and ref not in referents, "BIND_PLACE", "duplicate/missing referent")
            referents.add(ref)
            found[route] = kind
            _need(kind not in ("RemoteEvent", "RemoteFunction", "UnreliableRemoteEvent"),
                  "BIND_AUTHORITY", "unlisted prebuilt Remote authority")
            if kind in CLASS_COUNTS:
                _need(route in routes and routes[route][0] == kind, "BIND_PLACE", "source route/class")
                source = props.get("Source")
                _need(source is not None and source.tag in ("string", "ProtectedString")
                      and (source.text or "").encode("utf-8") == routes[route][1],
                      "BIND_PLACE", f"Place source body: {route}")
                if route == HOST:
                    _need(set(props) <= {"Name", "Source", "RunContext", "Disabled", "Enabled"},
                          "BIND_AUTHORITY", "unexpected Host properties")
                    _need("RunContext" not in props or (props["RunContext"].tag == "token"
                          and props["RunContext"].text == "0"), "BIND_AUTHORITY", "Host RunContext")
                    _need("Disabled" not in props or (props["Disabled"].tag == "bool"
                          and props["Disabled"].text == "false"), "BIND_AUTHORITY", "Host disabled")
                    _need("Enabled" not in props or (props["Enabled"].tag == "bool"
                          and props["Enabled"].text == "true"), "BIND_AUTHORITY", "Host enabled")
                # The existing canonical Place has no extra script properties.
                allowed = {"Name", "Source", "RunContext"} if kind == "Script" else {"Name", "Source"}
                _need(set(props) == allowed, "BIND_AUTHORITY", f"unexpected source property: {route}")
                if kind == "Script":
                    _need(props["RunContext"].tag == "token" and props["RunContext"].text == "0",
                          "BIND_AUTHORITY", "unexpected server RunContext")
            else:
                _need(set(props) == {"Name"}, "BIND_AUTHORITY", "unexpected non-script property")
            items(item, route)
    items(xml)
    _need(found == inventory and len(list(xml.iter("Item"))) == 75,
          "BIND_PLACE", "complete project/Place inventory differs")


def _native_binding(files, profile, source, context, admission):
    """Link archived evidence and raw vectors; do not claim a new Native execution."""
    native_names = {name[len("native_evidence/"):] for name in files if name.startswith("native_evidence/")}
    expected = {"receipt.json", "build_receipt.json", "source_tree_manifest.json", "CMakeCache.txt",
                "build.ninja", "build.stdout.log", "build.stderr.log", "configure.stdout.log",
                "configure.stderr.log"}
    expected |= {f"{suite}/{name}" for suite in SUITES for name in ("receipt.json", "generated.luau", "stdout.log", "stderr.log")}
    _need(native_names == expected, "BIND_ADMISSION", "exact archived Native file set")
    nfiles = {name: files["native_evidence/" + name] for name in expected}
    aggregate = _json(nfiles["receipt.json"], "native receipt")
    build = _json(nfiles["build_receipt.json"], "native build receipt")
    _need(aggregate.get("schema") == "UNION22_NATIVE_BOTH_SUITES_V3" and aggregate.get("status") == "PASS"
          and build.get("schema") == "UNION22_F46_REPL_BUILD_V1" and build.get("status") == "PASS_NEW_BUILD",
          "BIND_ADMISSION", "archived Native schemas/status")
    pins = {name: entry["after"] for name, entry in profile["sources"].items()}
    for document in (aggregate, build):
        _eq_context(document, "execution_context", context)
        _need(document.get("source_receipt") == _pin(files[SOURCE_RECEIPT]),
              "BIND_ADMISSION", "Native source receipt namespace")
    _need(aggregate.get("source_profile") == pins and aggregate.get("source_count_pinned") == 69
          and aggregate.get("source_count_executed_full_body") == 28
          and aggregate.get("source_inputs_unchanged") is True and aggregate.get("source_only") is True
          and aggregate.get("formal_rc_adoption_proven") is False,
          "BIND_ADMISSION", "Native scope")
    _need(aggregate.get("build_receipt") == _pin(nfiles["build_receipt.json"])
          and admission.get("native_build_receipt") == _pin(nfiles["build_receipt.json"]),
          "BIND_ADMISSION", "Native build receipt links")
    _need(build.get("source_commit") == profile["luau_source"]["commit"]
          and build.get("source_tree") == profile["luau_source"]["tree"]
          and build.get("binary_before_suites") == build.get("binary_after_suites")
          and _is_pin(build.get("binary_before_suites"))
          and all(build.get(key) is True for key in ("binary_absent_before_build", "build_directory_absent_initially", "source_tree_clean_before_after"))
          and type(build.get("configure_exit")) is int and build["configure_exit"] == 0
          and type(build.get("build_exit")) is int and build["build_exit"] == 0,
          "BIND_ADMISSION", "archived fresh-build linkage")
    evidence = build.get("evidence_files")
    _need(isinstance(evidence, dict) and set(evidence) == expected - {"receipt.json", "build_receipt.json"} -
          {f"{suite}/{name}" for suite in SUITES for name in ("receipt.json", "generated.luau", "stdout.log", "stderr.log")},
          "BIND_ADMISSION", "build evidence set")
    for name, pin in evidence.items():
        _need(_is_pin(pin) and pin == _pin(nfiles[name]), "BIND_ADMISSION", f"build evidence: {name}")
    commands = build.get("commands")
    _need(isinstance(commands, dict) and set(commands) == {"configure", "build"}, "BIND_ADMISSION", "build commands")
    for name, command in commands.items():
        _need(isinstance(command, dict) and type(command.get("exit_code")) is int and command["exit_code"] == 0
              and isinstance(command.get("argv"), list) and command["argv"], "BIND_ADMISSION", "archived build command")
        for stream in ("stdout", "stderr"):
            _need(command.get(stream) == _pin(nfiles[f"{name}.{stream}.log"]), "BIND_ADMISSION", "build stream link")
    _need(set(aggregate.get("suites", {})) == set(SUITES) and set(admission.get("native_suites", {})) == set(SUITES),
          "BIND_ADMISSION", "Native suite set")
    for suite, names in SUITES.items():
        receipt = _json(nfiles[f"{suite}/receipt.json"], suite)
        _eq_context(receipt, "execution_context", context)
        _need(receipt.get("schema") == "UNION22_FULL_RUNTIME_SUITE_V2" and receipt.get("status") == "PASS"
              and receipt.get("suite") == suite and receipt.get("source_receipt") == _pin(files[SOURCE_RECEIPT])
              and receipt.get("source_profile") == pins and receipt.get("source_count_pinned") == 69
              and receipt.get("source_count_executed_full_body") == 28
              and receipt.get("source_inputs_unchanged") is True
              and receipt.get("native") == build["binary_before_suites"]
              and receipt.get("input_lock") == aggregate.get("input_lock") == build.get("input_lock")
              and receipt.get("runner") == aggregate.get("runner") == build.get("runner"),
              "BIND_ADMISSION", f"Native source/build link: {suite}")
        _need(aggregate["suites"][suite] == _pin(nfiles[f"{suite}/receipt.json"])
              and admission["native_suites"][suite] == {"case_count": len(names), "receipt": _pin(nfiles[f"{suite}/receipt.json"])},
              "BIND_ADMISSION", "suite receipt link")
        for key, filename in (("generated", "generated.luau"), ("stdout", "stdout.log"), ("stderr", "stderr.log")):
            _need(receipt.get(key) == _pin(nfiles[f"{suite}/{filename}"]), "BIND_ADMISSION", "suite raw-file link")
        try:
            lines = nfiles[f"{suite}/stdout.log"].decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise BindingError("BIND_ADMISSION", "Native stdout encoding") from exc
        cases = [line for line in lines if line.startswith("CASE\t")]
        vectors = [line.split("\t") for line in cases]
        _need([row[1] for row in vectors if len(row) >= 4] == list(names)
              and all(len(row) >= 4 and row[2] == "PASS" for row in vectors)
              and receipt.get("cases") == cases and receipt.get("expected_case_names") == list(names)
              and receipt.get("exact_complete_pass_vector") is True
              and type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0
              and nfiles[f"{suite}/stderr.log"] == b""
              and not any(re.search(r"warning|\bFAIL\b|\bERROR\b", line, re.I) for line in lines),
              "BIND_ADMISSION", "archived raw Native result differs")
        ranges = receipt.get("full_body_byte_ranges")
        _need(isinstance(ranges, dict) and len(ranges) == 28, "BIND_ADMISSION", "full-body range set")
        intervals = []
        generated = nfiles[f"{suite}/generated.luau"]
        for path, span in ranges.items():
            _need(path in pins and isinstance(span, dict) and type(span.get("start")) is int
                  and type(span.get("end")) is int and 0 <= span["start"] < span["end"] <= len(generated),
                  "BIND_ADMISSION", "full-body range")
            raw = generated[span["start"]:span["end"]]
            _need(raw == files["sources/" + path] and {k: span.get(k) for k in ("bytes", "sha256")} == pins[path],
                  "BIND_ADMISSION", "complete historical body differs")
            intervals.append((span["start"], span["end"]))
        intervals.sort()
        _need(all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:])),
              "BIND_ADMISSION", "overlapping source ranges")


def _packet(files, context, *, synthetic=False, history=None):
    required = {MANIFEST, PROFILE, SOURCE_RECEIPT, CORE, ADMISSION, PROJECT, PLACE,
                "UNION22_FINAL_17_MARKER_RETENTION.json", "UNION22_FINAL_ALL48_ENVELOPE.json",
                "UNION22_FINAL_ALL48_RAW.json", "UNION22_FINAL_ART_SOURCE_RETENTION.json"}
    # Parse all JSON before semantic checks: strict input validation is not bypassed by
    # a stale outer hash, and duplicate keys in preserved prior evidence are rejected.
    documents = {name: _json(raw, name) for name, raw in files.items() if name.endswith(".json")}
    _need(required <= set(files), "BIND_MANIFEST_FILES", "required delivery files missing")
    manifest = documents[MANIFEST]
    members = manifest.get("files")
    _need(manifest.get("schema") == "UNION22_DELIVERY_FILES_V1"
          and manifest.get("manifest_self_excluded") is True and manifest.get("current_place") == PLACE
          and isinstance(members, dict), "BIND_MANIFEST_FILES", "manifest contract")
    for name in members:
        _member(name)
    _need(set(members) == set(files) - {MANIFEST}, "BIND_MANIFEST_FILES", "manifest/file-set closure")
    for name, pin in members.items():
        _need(_is_pin(pin) and pin == _pin(files[name]), "BIND_MANIFEST_PIN", f"member pin: {name}")
    profile = documents[PROFILE]
    _need(profile.get("schema") == "GQ470_UNION22_PRODUCTION_PROFILE_V1"
          and profile.get("source_count") == 69 and profile.get("instance_count") == 75
          and profile.get("class_counts") == CLASS_COUNTS
          and profile.get("project_name") == PROJECT and profile.get("place_name") == PLACE
          and profile.get("receipt_name") == SOURCE_RECEIPT
          and profile.get("formal_branch") == "rc/p0d-s1-kids-rc01",
          "BIND_PROFILE", "canonical profile contract")
    labels = profile.get("runtime_labels")
    expected_labels = {"ACTIVE_RUNTIME": SYNTHETIC_SELECTOR if synthetic else "rich51",
                       "PRIVATE_COMPANION": TARGET, "RUNTIME_UNIFIED": "NO"}
    _need(labels == expected_labels, "BIND_RUNTIME_CLAIM", "profile runtime labels")
    sources, routes = _source_inventory(files, profile)
    _need(set(profile.get("prior_report_names", [])) == PRIOR_REPORTS
          and set(profile.get("prior_opaque_rollback_names", [])) == PRIOR_ROLLBACKS,
          "BIND_PROFILE", "supported prior report/rollback contract")
    prior_names = PRIOR_REPORTS | {SOURCE_RECEIPT} | {"legacy_rollbacks/" + name for name in PRIOR_ROLLBACKS}
    expected_members = required | {ROLLBACK} | {"prior_boundary/" + name for name in prior_names}
    expected_members |= {"sources/" + name for name in sources}
    expected_members |= {name for name in files if name.startswith("native_evidence/")}
    _need(set(files) == expected_members and {name for name in files if name.endswith(".rbxlx")} == {PLACE},
          "BIND_MANIFEST_FILES", "unexpected delivery member or current Place")
    _project_and_place(files, profile, routes)
    source, core, admission = (documents[name] for name in (SOURCE_RECEIPT, CORE, ADMISSION))
    _need(source.get("schema") == "GQ470_UNION22_CURRENT_SOURCE_RECEIPT_V1"
          and source.get("source_profile") == "REAL69" and source.get("private_companion_profile") == TARGET
          and source.get("selected_source_count") == 69
          and source.get("source_hashes") == {r: _pin(raw)["sha256"] for r, (_, raw) in routes.items()}
          and source.get("source_classes") == {r: c for r, (c, _) in routes.items()},
          "BIND_SOURCE", "source receipt inventory")
    _eq_context(source, "execution_context", context)
    _provenance(source, context, source=True)
    _eq_context(core, "context", context)
    _provenance(admission, context)
    for document in (source, admission):
        _labels(document, labels)
        _engine_claims(document, required=True)
    _need(source.get("roblox_publish") is False and source.get("paid_trade") is False
          and admission.get("roblox_publish", False) is False,
          "BIND_ENGINE_CLAIM", "source Publish/trade boundary")
    _need(source.get("profile_lock") == _pin(files[PROFILE])
          and core.get("profile_lock") == _pin(files[PROFILE])
          and admission.get("profile_lock") == _pin(files[PROFILE]), "BIND_PROFILE", "profile links")
    place_pin = _pin(files[PLACE])
    _need({"bytes": source.get("private_place_bytes"), "sha256": source.get("private_place_sha256")} == place_pin
          and core.get("final_place") == place_pin and admission.get("current_place") == place_pin,
          "BIND_PLACE", "receipt Place links")
    _need(core.get("schema") == "GQ470_UNION22_CORE_BUILD_V1" and core.get("status") == "PASS_SOURCE_BUILD_ONLY"
          and core.get("source_count") == 69 and core.get("instances") == 75
          and core.get("actual_inverse_source_and_place_exact") is True
          and core.get("staged_payload_verified_after_all_commands") is True
          and core.get("final_delivery_created") is False,
          "BIND_ADMISSION", "source build admission")
    prior_pins = {name: _pin(files["prior_boundary/" + name]) for name in prior_names}
    _need(source.get("prior_evidence") == prior_pins
          and source.get("prior_receipt") == prior_pins[SOURCE_RECEIPT]
          and source.get("runtime_rollback_archive") == _pin(files[ROLLBACK])
          and source.get("identity_receipt_is_not_final_delivery_admission") is True,
          "BIND_ADMISSION", "preserved prior/rollback receipt links")
    staged = core.get("staged_payload")
    _need(isinstance(staged, dict) and all(staged.get(name) == _pin(files[name])
          for name in ({PROJECT, PLACE, ROLLBACK} | {"sources/" + name for name in sources})),
          "BIND_ADMISSION", "current staged payload links")
    commands = core.get("commands")
    _need(isinstance(commands, list) and type(core.get("compile_count")) is int
          and type(core.get("rojo_build_count")) is int
          and core["compile_count"] >= 138 and core["rojo_build_count"] >= 2
          and len(commands) == core["compile_count"] + core["rojo_build_count"]
          and all(isinstance(row, dict) and type(row.get("exit")) is int and row["exit"] == 0
                  and isinstance(row.get("command"), list) and row["command"] for row in commands),
          "BIND_ADMISSION", "archived source command closure")
    counts = (profile.get("changed_sources"), profile.get("unchanged_sources"))
    _need(all(type(n) is int and n >= 0 for n in counts) and sum(counts) == 69
          and counts == (source.get("changed_source_count"), source.get("unchanged_source_count"))
          and counts == (core.get("changed_sources"), core.get("unchanged_sources"))
          and counts == (admission.get("changed_sources"), admission.get("unchanged_sources")),
          "BIND_ADMISSION", "source change counts")
    _need(admission.get("schema") == "UNION22_FINAL_DELIVERY_ADMISSION_V1"
          and admission.get("status") == ("LOCAL_SYNTHETIC_SOURCE_SELECTION_ONLY" if synthetic else "PASS_SOURCE_AND_NATIVE_ONLY")
          and admission.get("source_count") == 69 and admission.get("instances") == 75
          and admission.get("legacy_48_all_ported") is False
          and admission.get("fresh_final_marker_retention") == 17
          and admission.get("unchanged_all48_auditor_executed_on_final") == 48
          and admission.get("visual_source_retention") == 3,
          "BIND_ADMISSION", "final admission contract")
    for name in ("UNION22_FINAL_17_MARKER_RETENTION.json", "UNION22_FINAL_ALL48_ENVELOPE.json",
                 "UNION22_FINAL_ART_SOURCE_RETENTION.json"):
        document = documents[name]
        _provenance(document, context)
        _labels(document, labels)
        _need(document.get("private_place") == place_pin, "BIND_PLACE", "retention Place link")
    marker = documents["UNION22_FINAL_17_MARKER_RETENTION.json"]
    family = marker.get("historic_source_family_evidence")
    _need(marker.get("source_family_marker_count") == 17 and isinstance(family, dict) and len(family) == 17
          and set(family.values()) == {"SOURCE_PRESENT_ENGINE_NOT_TESTED"}
          and marker.get("full_original_nonloss_gate_executed_on_union22") is False,
          "BIND_ADMISSION", "17-family retention boundary")
    raw48, envelope = documents["UNION22_FINAL_ALL48_RAW.json"], documents["UNION22_FINAL_ALL48_ENVELOPE.json"]
    flags = raw48.get("flags")
    _need(raw48.get("official_head") == context["build_head"]
          and raw48.get("official_branch") == "rc/p0d-s1-kids-rc01"
          and envelope.get("raw_official_head_field_is_build_head_only") is True
          and envelope.get("raw_report_name") == "UNION22_FINAL_ALL48_RAW.json",
          "BIND_CONTEXT", "raw all48 build-head provenance")
    _need(raw48.get("product_quality") == "NO_GO", "BIND_ENGINE_CLAIM", "raw all48 product boundary")
    _need(raw48.get("all_48_semantic_parity") == "NOT_PROVEN"
          and envelope.get("all_48_semantic_parity") == "NOT_PROVEN"
          and raw48.get("original_legacy_flags") == 48 and raw48.get("source_count") == 69
          and raw48.get("summary") == envelope.get("summary") == SUMMARY
          and isinstance(flags, list) and len(flags) == 48
          and all(isinstance(flag, dict) for flag in flags), "BIND_RUNTIME_CLAIM", "48 truth contract")
    _need(len({flag.get("feature_id") for flag in flags}) == 48
          and dict(Counter(flag.get("current_evidence") for flag in flags)) == SUMMARY
          and {flag.get("feature_id") for flag in flags if flag.get("current_evidence") == "EVIDENCE_GAP"} == GAPS,
          "BIND_RUNTIME_CLAIM", "legacy gap classifications")
    for flag in flags:
        _need(flag.get("original_rc85_rc86_full_semantic_parity") == "NOT_PROVEN",
              "BIND_RUNTIME_CLAIM", "legacy feature parity claim")
        _engine_claims(flag)
        if flag.get("feature_id") in GAPS:
            _need(flag.get("current_routes") == [] and flag.get("source_sha256") == {},
                  "BIND_RUNTIME_CLAIM", "gap cannot claim integrated routes")
        route_pins = flag.get("source_sha256")
        _need(isinstance(route_pins, dict) and all(r in routes and h == _pin(routes[r][1])["sha256"]
              for r, h in route_pins.items()), "BIND_RUNTIME_CLAIM", "legacy route-source link")
    art = documents["UNION22_FINAL_ART_SOURCE_RETENTION.json"]
    _engine_claims(art, required=True)
    _need(art.get("screenshots_received") == 0 and art.get("prior_fixed_sha_art_gate_reused_as_final_pass") is False
          and art.get("exact_locked_source_class_route_place") is True,
          "BIND_ENGINE_CLAIM", "ART source-only boundary")
    if synthetic:
        _need(history is not None, "BIND_HISTORY", "explicit history required")
        old_files, old_profile, old_context = history
        new_native = {n: raw for n, raw in files.items() if n.startswith("native_evidence/")}
        old_native = {n: raw for n, raw in old_files.items() if n.startswith("native_evidence/")}
        _need(new_native == old_native and files[PLACE] == old_files[PLACE] and files[PROJECT] == old_files[PROJECT]
              and sources == {n[len("sources/"):]: raw for n, raw in old_files.items() if n.startswith("sources/")},
              "BIND_HISTORY", "historical Native/source/Place bytes must stay exact")
        _native_binding(old_files, old_profile, _json(old_files[SOURCE_RECEIPT], "historical source"),
                        old_context, admission)
    else:
        _native_binding(files, profile, source, context, admission)
    return profile, routes


def _selection(active, context, synthetic):
    _need(active.get("schema") == "P0D_FAST_RC_V1" and isinstance(active.get("source_profiles"), dict),
          "BIND_SELECTION", "ACTIVE selection schema")
    selected = active.get("active_profile")
    rows = active["source_profiles"]
    _need(isinstance(selected, str) and selected in rows and isinstance(rows[selected], dict),
          "BIND_SELECTION", "registered active profile required")
    head = active.get("active_source_commit")
    _need(isinstance(head, str) and SHA40.fullmatch(head) and rows[selected].get("source_commit") == head,
          "BIND_SELECTION", "selector/source lineage mismatch")
    _need(active.get("production_publish_authorized") is False, "BIND_ENGINE_CLAIM", "Publish unauthorized")
    target_rows = [name for name, row in rows.items() if isinstance(row, dict)
                   and (row.get("source_profile") == TARGET or row.get("source_manifest") ==
                        "quality_gameplay/gq470_union22_real69_20261122/profile_lock.json")]
    _need(len(target_rows) <= 1, "BIND_SELECTION", "ambiguous REAL69 mapping")
    if synthetic:
        expected = {"source_profile": TARGET,
                    "source_manifest": "quality_gameplay/gq470_union22_real69_20261122/profile_lock.json",
                    "build_workflow": ".github/workflows/gq8-real63-source-composite.yml",
                    "source_count": 69, "expected_script_count": 69,
                    "release_place": PLACE, "selected_for_roblox_publish": False,
                    "source_commit": context["build_head"]}
        _need(selected == SYNTHETIC_SELECTOR and target_rows == [selected]
              and all(rows[selected].get(key) == value and (not isinstance(value, bool) or rows[selected][key] is value)
                      for key, value in expected.items()) and head == context["build_head"],
              "BIND_SELECTION", "synthetic target mapping")
    else:
        _need(selected == "rich51" and not target_rows and rows[selected].get("source_count") == 51,
              "BIND_SELECTION", "A2 archived mode supports current unselected companion only")
    return selected, bool(target_rows)


class ValidatedBinding:
    """Detached public report, private validation snapshots, no implicit publication."""

    __slots__ = ("_serialized", "_inputs")

    def __init__(self, report, inputs, *, _token=None):
        _need(_token is _VALIDATION_TOKEN, "BIND_ADMISSION", "use validate_binding")
        self._serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        self._inputs = inputs

    def as_dict(self):
        return json.loads(self._serialized)


_VALIDATION_TOKEN = object()


def _validate_binding(*, active: Path, profile: Path, delivery: Path, expected_context: Mapping,
                     input_kind: str = "ARCHIVED_ARTIFACT", historical_delivery: Path | None = None) -> ValidatedBinding:
    """Validate supplied offline evidence without changing selection or executing it."""
    _need(input_kind in ("ARCHIVED_ARTIFACT", "LOCAL_SYNTHETIC"), "BIND_INPUT_KIND", "unsupported input kind")
    synthetic = input_kind == "LOCAL_SYNTHETIC"
    context = _context(expected_context, synthetic=synthetic)
    _need((historical_delivery is not None) is synthetic, "BIND_HISTORY", "history required only for synthetic mode")
    inputs = _Inputs()
    active_raw, profile_raw = inputs.file(active), inputs.file(profile)
    active_data, reference_profile = _json(active_raw, "ACTIVE"), _json(profile_raw, "reference profile")
    files = inputs.tree(delivery)
    # Strict JSON rejection is observable even for incomplete rejection-only inputs.
    for name, raw in files.items():
        if name.endswith(".json"):
            _json(raw, name)
    _need(MANIFEST in files and PROFILE in files, "BIND_MANIFEST_FILES", "delivery manifest/profile missing")
    history, history_context = None, None
    if synthetic:
        _need(_absolute(historical_delivery) != _absolute(delivery), "BIND_HISTORY", "history must be separate")
        try:
            historical = inputs.tree(historical_delivery)
            _need(SOURCE_RECEIPT in historical, "BIND_HISTORY", "historical source receipt missing")
            historical_source = _json(historical[SOURCE_RECEIPT], "historical source receipt")
            history_context = _context(historical_source.get("execution_context"), synthetic=False)
            history_profile, _ = _packet(historical, history_context)
            history = historical, history_profile, history_context
        except BindingError as exc:
            raise BindingError("BIND_HISTORY", f"invalid historical reference ({exc.code})") from exc
    _need(PROFILE in files and files[PROFILE] == profile_raw, "BIND_PROFILE", "reference/package profile bytes differ")
    selected, registered = _selection(active_data, context, synthetic)
    actual_profile, routes = _packet(files, context, synthetic=synthetic, history=history)
    _need(reference_profile == actual_profile, "BIND_PROFILE", "profile object mismatch")
    pins = {"active": _pin(active_raw), "profile": _pin(profile_raw)}
    for key, name in (("packaged_profile", PROFILE), ("manifest", MANIFEST), ("source_receipt", SOURCE_RECEIPT),
                      ("core", CORE), ("admission", ADMISSION), ("project", PROJECT), ("place", PLACE)):
        pins[key] = _pin(files[name])
    if synthetic:
        pins["historical_manifest"] = _pin(history[0][MANIFEST])
        pins["historical_source_receipt"] = _pin(history[0][SOURCE_RECEIPT])
    report = {
        "schema": "GQ866_PRIMARY_BINDING_VALIDATION_V1", "status": "PASS_READ_ONLY_BINDING",
        "selection_status": "LOCAL_SYNTHETIC_SELECTION_ONLY" if synthetic else "COMPANION_NOT_SELECTED",
        "validator_execution": "LOCAL_READ_ONLY", "input_kind": input_kind,
        "input_evidence_context": context, "observed_primary_profile": selected, "target_profile": TARGET,
        "target_registered": registered, "configuration_selects_target": synthetic,
        "source_count": 69, "instances": 75, "class_counts": CLASS_COUNTS,
        "host": {"route": HOST, "class": "Script", **_pin(routes[HOST][1]), "studio_guard_preserved": True},
        "inputs": pins, "delivery_file_count": len(files), "runtime_labels": actual_profile["runtime_labels"],
        "legacy_48_all_ported": False, "all_48_semantic_parity": "NOT_PROVEN",
        "default_selection_changed": False, "fresh_ci_executed": False, "native_executed": False,
        "formal_rc_adoption_performed": False, "studio_executed": False, "roblox_publish": False,
        "native_evidence_scope": "HISTORICAL_ONLY" if synthetic else "ARCHIVED_ADMISSION_BINDING",
        "current_native_admission_proven": False, "archived_native_admission_bound": not synthetic,
        "historical_native_bytes_preserved": True if synthetic else None,
        "historical_input_evidence_context": history_context, "upstream_authentication_performed": False,
    }
    inputs.recheck()
    return ValidatedBinding(report, inputs, _token=_VALIDATION_TOKEN)


def validate_binding(*, active: Path, profile: Path, delivery: Path, expected_context: Mapping,
                     input_kind: str = "ARCHIVED_ARTIFACT", historical_delivery: Path | None = None) -> ValidatedBinding:
    """Public offline validator; malformed nested input types fail with stable errors."""
    try:
        return _validate_binding(active=active, profile=profile, delivery=delivery,
                                 expected_context=expected_context, input_kind=input_kind,
                                 historical_delivery=historical_delivery)
    except BindingError:
        raise
    except (TypeError, KeyError, IndexError, AttributeError, RecursionError) as exc:
        raise BindingError("BIND_JSON", "malformed nested input structure") from exc


def _unlink_owned(path, identity):
    """Never adopt the identity of a replacement as our temporary/report file."""
    try:
        info = Path(path).lstat()
    except FileNotFoundError:
        return
    if (info.st_dev, info.st_ino) == identity:
        os.unlink(path)


def write_report(validated: ValidatedBinding, out: Path) -> Path:
    """Publish one new external file atomically; never replace inputs or outputs."""
    _need(type(validated) is ValidatedBinding, "BIND_ADMISSION", "validated binding required")
    out = _absolute(out, "BIND_OUTPUT_PATH")
    _need(out not in validated._inputs.files, "BIND_OUTPUT_PATH", "output is an input")
    _need(not any(out == root or root in out.parents for root in validated._inputs.trees),
          "BIND_OUTPUT_PATH", "output lies inside immutable delivery")
    _safe_existing(out.parent, directory=True, code="BIND_OUTPUT_PATH")
    _need(not os.path.lexists(out), "BIND_OUTPUT_EXISTS", "output already exists")
    validated._inputs.recheck()
    temporary = None
    owned_identity = None
    linked = False
    try:
        fd, temporary = tempfile.mkstemp(prefix=".primary-binding-", suffix=".tmp", dir=out.parent)
        with os.fdopen(fd, "wb") as stream:
            info = os.fstat(stream.fileno())
            owned_identity = (info.st_dev, info.st_ino)
            stream.write(validated._serialized.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        _safe_existing(out.parent, directory=True, code="BIND_OUTPUT_PATH")
        validated._inputs.recheck()
        try:
            os.link(temporary, out, follow_symlinks=False)
        except FileExistsError as exc:
            raise BindingError("BIND_OUTPUT_EXISTS", "output appeared during publication") from exc
        linked = True
        published = out.lstat()
        _need((published.st_dev, published.st_ino) == owned_identity,
              "BIND_OUTPUT_PATH", "published report was replaced")
        # A final check also rejects an input changed during the atomic link.
        validated._inputs.recheck()
        return out
    except OSError as exc:
        if linked:
            try:
                _unlink_owned(out, owned_identity)
            except OSError:
                pass
        raise BindingError("BIND_IO", "cannot publish report") from exc
    except BindingError:
        if linked:
            try:
                _unlink_owned(out, owned_identity)
            except OSError:
                pass
        raise
    finally:
        if temporary is not None and owned_identity is not None:
            try:
                _unlink_owned(temporary, owned_identity)
            except OSError as exc:
                if linked:
                    try:
                        _unlink_owned(out, owned_identity)
                    except OSError:
                        pass
                raise BindingError("BIND_IO", "cannot remove owned temporary report") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("active", "profile", "delivery", "expected-context", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--input-kind", choices=("ARCHIVED_ARTIFACT", "LOCAL_SYNTHETIC"), default="ARCHIVED_ARTIFACT")
    parser.add_argument("--historical-delivery", type=Path)
    args = parser.parse_args(argv)
    try:
        context_inputs = _Inputs()
        context_raw = context_inputs.file(args.expected_context)
        result = validate_binding(active=args.active, profile=args.profile, delivery=args.delivery,
                                  expected_context=_json(context_raw, "expected context"), input_kind=args.input_kind,
                                  historical_delivery=args.historical_delivery)
        # The CLI context file joins the same late-mutation/output-intersection checks.
        for path, value in context_inputs.files.items():
            if path in result._inputs.files:
                _need(result._inputs.files[path] == value, "BIND_INPUT_CHANGED", "context input changed")
            result._inputs.files[path] = value
        path = write_report(result, args.out)
        print(json.dumps({"status": "PASS_READ_ONLY_BINDING", "report": str(path),
                          "validator_execution": "LOCAL_READ_ONLY"}, sort_keys=True))
        return 0
    except BindingError as exc:
        print(json.dumps({"status": "REJECTED", "code": exc.code, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
