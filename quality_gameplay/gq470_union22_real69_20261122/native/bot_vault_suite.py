"""Reuse the frozen Bot16 predicates with the caller's current pinned sources.

Public API:
  load_contract() -> immutable-input data, checked against the fixed file pins.
  assemble(source_root, expected_profile, scenario_id) -> (bytes, assembly dict).
  parse_result(scenario_id, stdout, stderr, exit_code) -> ordered PASS vectors.
  summarize_results(receipts) -> exact nine-scenario/13 CASE/43 CHECK totals.
  run_supplement(...keyword inputs...) -> nine real subprocess receipts.

run_profile remains responsible for authenticating the source/CI context and
building F46 once. This adapter accepts only that caller's fresh-build record
and binary; it neither builds/downloads/selects a VM nor synthesizes CI context.
Historical sources/results in the data file are provenance, never fallbacks.
The two original dual28 programs are not imported, modified or rerun here.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time

HERE = Path(__file__).resolve().parent
CASES_PIN = {"bytes": 71446, "sha256": "aaca8180579291218bc5e119ecb38c2d291aba094d9081cc1032189c3b17d4fa"}
TEMPLATE_PIN = {"bytes": 39786, "sha256": "1f74ccb6b1061a333f25e1012c9c8faa1298265d74a40217d1fcb63fa83ad1ee"}
BOT_OBJECTIVE_TAG_PIN = {"bytes": 20012, "sha256": "06e5197b826d1cd279d27ce019a92d9dcc5b9b651c6933587e69a6ecff5cdc23"}
F46_COMMIT = "f46d879e28302a430029304f7f6a162aed66f103"
F46_TREE = "2432c996fc9fa73680b5e2cfe172d36114fe3746"
SCENARIO_IDS = (
    "candidate_route62_TEAM_normal", "candidate_route62_TEAM_slow",
    "candidate_route62_BATTLE_ROYALE_normal", "candidate_route62_BATTLE_ROYALE_slow",
    "candidate_route58_TEAM_normal", "candidate_contracts_TEAM_normal",
    "candidate_actors_TEAM_normal", "candidate_eggs_TEAM_normal", "candidate_parallel_TEAM_normal",
)
TOKEN = re.compile(rb"@@[A-Za-z0-9_]+@@")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, reason):
    if not condition:
        raise ValueError("RED_BOT_VAULT_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def safe_path(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), "SYMLINK_PATH")
    return path.resolve()


def read(path):
    path = safe_path(path)
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), "REGULAR_FILE_REQUIRED")
    return path.read_bytes()


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique)


def valid_pin(pin):
    return (isinstance(pin, dict) and set(pin) == {"bytes", "sha256"}
            and type(pin["bytes"]) is int and pin["bytes"] >= 0
            and isinstance(pin["sha256"], str) and bool(SHA.fullmatch(pin["sha256"])))


def package_pins():
    return {name: identity(read(HERE / name)) for name in
            ("bot_vault_base.template.luau", "bot_vault_cases.json", "bot_vault_suite.py")}


def load_contract():
    raw = read(HERE / "bot_vault_cases.json")
    require(identity(raw) == CASES_PIN, "FROZEN_CASES_FILE")
    contract = strict_json(raw)
    require(identity(read(HERE / "bot_vault_base.template.luau")) == TEMPLATE_PIN, "FROZEN_TEMPLATE")
    require(contract["schema"] == "BOT_VAULT_NATIVE_SUPPLEMENT_CASES_V1"
            and tuple(s["scenario_id"] for s in contract["scenarios"]) == SCENARIO_IDS
            and len(contract["modules_in_load_order"]) == 16
            and len({m["module"] for m in contract["modules_in_load_order"]}) == 16,
            "FROZEN_CONTRACT")
    require(len(contract["corpora"]) == 6
            and len({c["id"] for c in contract["corpora"]}) == 6, "CORPUS_SET")
    for corpus in contract["corpora"]:
        require(identity(corpus["raw_text"].encode("utf-8")) == corpus["identity"], "CORPUS_BYTES")
    require(sum(s["expected_CASE_count"] for s in contract["scenarios"]) == 13
            and sum(s["expected_CHECK_count"] for s in contract["scenarios"]) == 43,
            "FROZEN_VECTOR_TOTALS")
    return contract


def source_snapshot(root):
    root = safe_path(root)
    require(root.is_dir(), "SOURCE_DIRECTORY")
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "SOURCE_SYMLINK")
        if path.is_file():
            require(path.suffix == ".luau", "EXTRA_SOURCE_FILE")
            result[path.relative_to(root).as_posix()] = identity(read(path))
        else:
            require(path.is_dir(), "SPECIAL_SOURCE_ENTRY")
    return result


def source_inputs(root, expected_profile, contract):
    require(isinstance(expected_profile, dict) and len(expected_profile) == 69, "PINNED_69_PROFILE_REQUIRED")
    for name, pin in expected_profile.items():
        require(isinstance(name, str), "SOURCE_PATH_TYPE")
        path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts and "\\" not in name
                and path.as_posix() == name and path.suffix == ".luau"
                and valid_pin(pin) and pin["bytes"] > 0, "PINNED_SOURCE_ENTRY")
    require(source_snapshot(root) == expected_profile, "SOURCE_PROFILE_MISMATCH")
    result = {}
    for module in contract["modules_in_load_order"]:
        name = module["relative_source_path"]
        require(name in expected_profile, "FULL_BODY_NOT_IN_PROFILE")
        raw = read(Path(root) / name)
        raw.decode("utf-8")
        require(identity(raw) == expected_profile[name], "FULL_BODY_PIN_MISMATCH")
        if module["module"] == "BotActors":
            require(identity(raw) in (module["historical_candidate"], BOT_OBJECTIVE_TAG_PIN),
                    "EXACT_BOT_SOURCE_REQUIRED")
        if module["module"] == "BotPathRouter":
            require(identity(raw) == module["historical_candidate"], "ORIGINAL_ROUTER_REQUIRED")
        result[name] = raw
    return result


def scenario(contract, scenario_id):
    matches = [s for s in contract["scenarios"] if s["scenario_id"] == scenario_id]
    require(len(matches) == 1, "UNKNOWN_OR_DUPLICATE_SCENARIO")
    return matches[0]


def assemble_inputs(contract, template, sources, item):
    corpora = {c["id"]: c["raw_text"].encode("utf-8") for c in contract["corpora"]}
    case = b"".join(corpora[p["corpus_id"]] if "corpus_id" in p else p["literal_utf8"].encode("utf-8")
                    for p in item["case_assembly_order"])
    require(identity(case) == item["case_assembly_identity"], "CASE_CONCATENATION")
    replacements = {key.encode(): value.encode() for key, value in item["configuration_substitutions"].items()}
    replacements[item["case_token"].encode()] = case
    source_tokens = {m["token"].encode(): m for m in contract["modules_in_load_order"]}
    for token, module in source_tokens.items():
        replacements[token] = sources[module["relative_source_path"]]
    matches = list(TOKEN.finditer(template))
    require(len(matches) == len(replacements) == 20
            and {m.group() for m in matches} == set(replacements), "TEMPLATE_TOKEN_SET_OR_DUPLICATE")
    require([m.group() for m in matches if m.group() in source_tokens] == list(source_tokens), "FULL_BODY_ORDER")
    parts, byte_ranges, cursor, size = [], {}, 0, 0
    for match in matches:
        prefix, token = template[cursor:match.start()], match.group()
        parts.append(prefix)
        size += len(prefix)
        replacement = replacements[token]
        if token in source_tokens:
            module = source_tokens[token]
            byte_ranges[module["relative_source_path"]] = {
                "module": module["module"], "start": size, "end": size + len(replacement), **identity(replacement)}
        parts.append(replacement)
        size += len(replacement)
        cursor = match.end()
    parts.append(template[cursor:])
    generated = b"".join(parts)
    require(not TOKEN.search(generated) and len(byte_ranges) == 16, "UNRESOLVED_TOKEN_OR_BODY_COUNT")
    line_ranges = {}
    for name, row in byte_ranges.items():
        body = sources[name]
        require(generated[row["start"]:row["end"]] == body and generated.count(body) == 1, "FULL_BODY_EXACT_ONCE")
        first = generated[:row["start"]].count(b"\n") + 1
        line_ranges[row["module"]] = {"first": first, "last": first + body.count(b"\n")}
    return generated, {"scenario_id": item["scenario_id"], "configuration_substitutions": item["configuration_substitutions"],
                       "case_assembly": identity(case), "full_body_byte_ranges": byte_ranges,
                       "source_line_ranges": line_ranges, "generated": identity(generated)}


def assemble(source_root, expected_profile, scenario_id):
    contract = load_contract()
    sources = source_inputs(source_root, expected_profile, contract)
    return assemble_inputs(contract, read(HERE / "bot_vault_base.template.luau"), sources, scenario(contract, scenario_id))


def parse_output(item, stdout, stderr, exit_code):
    require(type(stdout) is bytes and type(stderr) is bytes, "RAW_PROCESS_BYTES_REQUIRED")
    require(type(exit_code) is int and exit_code == 0, "NATIVE_EXIT_NONZERO")
    require(stderr == b"", "NATIVE_STDERR_NOT_EMPTY")
    rows = {"CASE": [], "CHECK": []}
    for line in stdout.decode("utf-8").splitlines():
        require(not line.lstrip().upper().startswith("WARN"), "NATIVE_WARNING")
        key = line.split("\t", 1)[0].strip()
        if key.startswith(("CASE", "CHECK")):
            parts = line.split("\t", 3)
            require(len(parts) == 4 and parts[0] in rows and parts[2] == "PASS", "MALFORMED_OR_NONPASS_VECTOR_ROW")
            rows[parts[0]].append(parts)
    for kind in rows:
        require([p[1] for p in rows[kind]] == item["expected_ordered_" + kind + "_names"], kind + "_NAME_OR_ORDER")
    return {"case_rows": rows["CASE"], "check_rows": rows["CHECK"], "warning_rows": [],
            "exit_code": exit_code, "stderr_bytes": 0, "exact_complete_pass_vectors": True}


def parse_result(scenario_id, stdout, stderr, exit_code):
    return parse_output(scenario(load_contract(), scenario_id), stdout, stderr, exit_code)


def summarize_results(receipts):
    contract = load_contract()
    require(isinstance(receipts, list) and tuple(r.get("scenario_id") for r in receipts) == SCENARIO_IDS,
            "MISSING_DUPLICATE_OR_REORDERED_SCENARIO")
    cases = checks = 0
    for receipt, item in zip(receipts, contract["scenarios"]):
        result = receipt.get("result", {})
        require(receipt.get("status") == "PASS"
                and receipt.get("configuration_substitutions") == item["configuration_substitutions"]
                and receipt.get("case_assembly") == item["case_assembly_identity"], "SCENARIO_CONFIG_OR_CASE_BINDING")
        for key, expected in (("case_rows", item["expected_ordered_CASE_names"]),
                              ("check_rows", item["expected_ordered_CHECK_names"])):
            rows = result.get(key, [])
            require(all(isinstance(p, list) and len(p) == 4 and p[0] == key.split("_")[0].upper()
                        and p[2] == "PASS" for p in rows) and [p[1] for p in rows] == expected, "RESULT_VECTOR")
        require(result.get("exact_complete_pass_vectors") is True and result.get("exit_code") == 0
                and result.get("stderr_bytes") == 0 and result.get("warning_rows") == [], "RESULT_PROCESS_GATE")
        cases += len(result["case_rows"])
        checks += len(result["check_rows"])
    require((cases, checks) == (13, 43), "RESULT_TOTALS")
    return {"scenarios": 9, "CASE_rows": cases, "CHECK_rows": checks, "warning_rows": 0,
            "full_bodies_per_scenario": 16, "distinct_full_bodies_with_existing_dual28": 30}


def validate_build(binary, built, context, source_receipt):
    binary = safe_path(binary)
    require(valid_pin(source_receipt) and isinstance(context, dict)
            and set(context) == {"kind", "build_head", "checkout_sha", "canonical_build", "official_build_head",
                                 "observed_live_rc", "event", "run_id", "run_attempt"}, "CALLER_CONTEXT_REQUIRED")
    require(context["kind"] in ("OFFICIAL", "PR_CANDIDATE", "LOCAL_SOURCE_REVIEW")
            and re.fullmatch(r"[0-9a-f]{40}", context["build_head"] or "")
            and re.fullmatch(r"[0-9a-f]{40}", context["checkout_sha"] or "")
            and context["canonical_build"] is (context["kind"] == "OFFICIAL")
            and context["official_build_head"] == (context["build_head"] if context["kind"] == "OFFICIAL" else None),
            "CALLER_CONTEXT_CLASSIFICATION")
    if context["kind"] == "LOCAL_SOURCE_REVIEW":
        require(all(context[k] is None for k in ("observed_live_rc", "event", "run_id", "run_attempt")), "LOCAL_CONTEXT_IS_NOT_CI")
    else:
        require(context["checkout_sha"] == context["build_head"]
                and all(isinstance(context[k], str) and context[k].isdigit() and int(context[k]) > 0
                        for k in ("run_id", "run_attempt")), "CALLER_RUN_BINDING")
    require(built.get("schema") == "UNION22_F46_REPL_BUILD_V1" and built.get("status") == "PASS_NEW_BUILD"
            and built.get("source_commit") == F46_COMMIT and built.get("source_tree") == F46_TREE
            and built.get("tracked_file_count") == 2336 and built.get("source_tree_clean_before_after") is True
            and built.get("build_directory_absent_initially") is True and built.get("binary_absent_before_build") is True
            and built.get("configure_exit") == 0 and built.get("build_exit") == 0
            and built.get("execution_context") == context and built.get("source_receipt") == source_receipt,
            "SAME_CALLER_FRESH_F46_BUILD_REQUIRED")
    pin = built.get("binary_before_suites")
    require(valid_pin(pin) and identity(read(binary)) == pin and os.access(binary, os.X_OK)
            and safe_path(built["binary_path"]) == binary
            and binary == safe_path(built["build_directory"]) / "luau"
            and binary.stat().st_mtime_ns == built["binary_mtime_ns"] >= built["target_build_started_ns"] > 0,
            "SAME_FRESH_BINARY_IDENTITY")
    return binary, pin


def write_json(path, data):
    path.write_bytes((json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def clean_environment():
    keep = ("PATH", "HOME", "TMPDIR", "SYSTEMROOT", "LD_LIBRARY_PATH")
    env = {name: os.environ[name] for name in keep if name in os.environ}
    env.update({"LC_ALL": "C", "LANG": "C"})
    return env


def run_one(root, output, binary, pin, profile, package, item, generated, assembly, common):
    output.mkdir(exist_ok=False)
    program = output / "generated.luau"
    program.write_bytes(generated)
    stdout, stderr = b"", b""
    receipt = {**deepcopy(common), **assembly, "schema": "BOT_VAULT_NATIVE_SCENARIO_V1",
               "status": "FAIL_NO_NATIVE_ADMISSION", "native": pin,
               "process": {"argv": [str(binary), str(program)], "exit_code": None, "timed_out": False,
                           "started_at_utc": datetime.now(timezone.utc).isoformat()}}
    started = time.monotonic_ns()
    try:
        require(identity(read(binary)) == pin and package_pins() == package, "INPUT_CHANGED_BEFORE_PROCESS")
        result = subprocess.run([str(binary), str(program)], env=clean_environment(), capture_output=True, timeout=60)
        stdout, stderr = result.stdout, result.stderr
        receipt["process"]["exit_code"] = result.returncode
        receipt["result"] = parse_output(item, stdout, stderr, result.returncode)
        require(source_snapshot(root) == profile and identity(read(binary)) == pin
                and read(program) == generated and package_pins() == package, "INPUT_CHANGED_DURING_PROCESS")
        receipt.update(status="PASS", source_inputs_unchanged=True, generated_and_binary_unchanged=True)
    except Exception as error:
        if isinstance(error, subprocess.TimeoutExpired):
            stdout, stderr = error.stdout or b"", error.stderr or b""
            receipt["process"]["timed_out"] = True
        receipt.update(exception_type=type(error).__name__, exception=str(error))
        raise
    finally:
        receipt["process"]["elapsed_ns"] = time.monotonic_ns() - started
        receipt["process"]["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        receipt.update(stdout=identity(stdout), stderr=identity(stderr))
        (output / "stdout.log").write_bytes(stdout)
        (output / "stderr.log").write_bytes(stderr)
        write_json(output / "receipt.json", receipt)
    return receipt


def run_supplement(*, source_root, expected_profile, binary, build_receipt,
                   execution_context, source_receipt, output):
    """Run all nine once using run_profile's existing fresh binary and evidence.

    Successful output is exactly nine directories with generated.luau,
    stdout.log, stderr.log and receipt.json, plus the aggregate receipt.json.
    On failure raw process evidence is retained and the exception propagates;
    missing/unrun scenarios never receive fabricated PASS receipts.
    """
    contract = load_contract()
    package = package_pins()
    root, output = safe_path(source_root), safe_path(output)
    profile, context, source_receipt = deepcopy(expected_profile), deepcopy(execution_context), deepcopy(source_receipt)
    sources = source_inputs(root, profile, contract)
    binary, pin = validate_build(binary, build_receipt, context, source_receipt)
    require(not output.exists(), "OUTPUT_MUST_BE_NEW")
    for protected in (root, HERE, binary.parent):
        require(not output.is_relative_to(protected) and not protected.is_relative_to(output), "OUTPUT_OVERLAPS_INPUT")
    template = read(HERE / "bot_vault_base.template.luau")
    programs = [assemble_inputs(contract, template, sources, item) for item in contract["scenarios"]]
    common = {"execution_context": context, "source_receipt": source_receipt, "input_files": package,
              "source_count_pinned": 69, "source_count_executed_full_body": 16,
              "caller_fresh_build": {k: deepcopy(build_receipt[k]) for k in
                  ("schema", "source_commit", "source_tree", "binary_before_suites", "target_build_started_ns")},
              "source_only": True, "formal_rc_adoption_proven": False, "engine_boundary": contract["engine_boundary"]}
    output.mkdir(parents=True, exist_ok=False)
    receipts = []
    try:
        for item, (generated, assembly) in zip(contract["scenarios"], programs):
            receipts.append(run_one(root, output / item["scenario_id"], binary, pin, profile, package,
                                    item, generated, assembly, common))
        totals = summarize_results(receipts)
        require(source_snapshot(root) == profile and package_pins() == package
                and identity(read(binary)) == pin, "INPUT_CHANGED_AFTER_SCENARIOS")
        names = [f"{name}/{filename}" for name in SCENARIO_IDS
                 for filename in ("generated.luau", "stdout.log", "stderr.log", "receipt.json")]
        require(sorted(p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()) == sorted(names),
                "SCENARIO_EVIDENCE_FILE_SET")
        aggregate = {**common, "schema": "BOT_VAULT_NATIVE_SUPPLEMENT_V1", "status": "PASS", "totals": totals,
                     "ordered_scenarios": list(SCENARIO_IDS), "source_profile": profile,
                     "source_inputs_unchanged": True, "native": pin, "output_files_including_this_receipt": 37,
                     "scenario_files": {name: identity(read(output / name)) for name in names}}
        write_json(output / "receipt.json", aggregate)
        return aggregate
    except Exception as error:
        write_json(output / "receipt.json", {**common, "schema": "BOT_VAULT_NATIVE_SUPPLEMENT_V1",
                   "status": "FAIL_NO_NATIVE_ADMISSION", "completed_scenarios": [r["scenario_id"] for r in receipts],
                   "exception_type": type(error).__name__, "exception": str(error)})
        raise
