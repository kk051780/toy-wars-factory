#!/usr/bin/env python3
"""Run two pinned Score-only Native specs against a verified produced stage.

No network, downloads, tool builds, or import-time subprocesses. All generated
test files and logs go into a fresh output directory outside the input stage.
This proves local source behavior only, never official adoption or Studio play.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCORE_PATH = "ServerScriptService/EGGRUMBLE_ScoreBalance.luau"
SCORE_AFTER = {
    "bytes": 8741,
    "sha256": "67c76c12cc4d311847fb1cf794988b2f164053690660f6b55f4e590f93824136",
}
PINNED_LUAU_COMMIT = "f46d879e28302a430029304f7f6a162aed66f103"
ENTRY_TEXT = (
    '--!strict\nlocal Results=require("./Results")\n'
    'local Spec=require("./Cases")\nassert(Spec(Results)==true)\n'
    'print("MATCH_RESULT_POSTGAME_SCORE_NATIVE_ONLY")\n'
)
ENTRY_SHA256 = "cc42eec32535db27b9c692ac14caf07bfce56465c372aaa2d8cc82acd4075d1b"
ENTRY_MARKER = "MATCH_RESULT_POSTGAME_SCORE_NATIVE_ONLY"
SPEC_CONTRACTS = {
    "score_v2": {
        "path": "native/EGGRUMBLE_ScoreBalance.spec.luau",
        "assertions": 107,
        "marker": "EGGRUMBLE_V3_MATCH_RESULTS_NATIVE_PASS assertions=107",
        "score_build_evaluations": 47,
    },
    "relay_original": {
        "path": "native/EGGRUMBLE_RelayScoreRegression.spec.luau",
        "assertions": 16,
        "marker": "EGGRUMBLE_RELAY_SCORE_NATIVE_REGRESSION_PASS assertions=16",
        "score_build_evaluations": 8,
    },
}
PARENT_CONTEXT_FIELDS = {
    "kind", "build_head", "checkout_sha", "canonical_build", "official_build_head",
    "observed_live_rc", "event", "run_id", "run_attempt",
}


def byte_info(data: bytes) -> dict[str, Any]:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def file_info(path: Path) -> dict[str, Any]:
    return byte_info(path.read_bytes())


def verify_copies(pins: dict[str, dict[str, Any]], boundary: str) -> dict[str, Any]:
    """Re-read copies actually used or preserved, never just their source pins."""
    observed = {}
    for filename, expected in pins.items():
        path = Path(filename)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Copy integrity failure ({boundary}): missing or symbolic-link file {path}")
        actual = file_info(path)
        if actual != expected:
            raise ValueError(f"Copy integrity failure ({boundary}): {path}; expected {expected}; observed {actual}")
        observed[filename] = actual
    return {"boundary": boundary, "passed": True, "files": observed}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_producer() -> Any:
    path = PACKAGE_ROOT / "compose_score_relay.py"
    spec = importlib.util.spec_from_file_location("gq487_score_native_producer", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load the granted Score producer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def stage_fingerprint(root: Path) -> dict[str, dict[str, Any]]:
    """Read every stage file, including its own manifest and receipt."""
    return {
        path.relative_to(root).as_posix(): file_info(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def toolchain_record(luau: Path, compiler: Path, receipt_path: Path | None) -> dict[str, Any]:
    for path in (luau, compiler):
        if not path.is_file():
            raise ValueError(f"Missing local tool binary: {path}")
    binaries = {"luau": file_info(luau), "luau-compile": file_info(compiler)}
    result: dict[str, Any] = {
        "binaries": binaries,
        "binary_paths": {"luau": str(luau), "luau-compile": str(compiler)},
        "expected_source_commit": PINNED_LUAU_COMMIT,
        "source_commit": "UNKNOWN",
        "provided_build_receipt": None,
        "binary_hashes_match_provided_receipt": False,
        "provider_attestation_verified": False,
        "local_toolchain_gate_ready": False,
    }
    if receipt_path is None:
        result["boundary"] = "Binary hashes recorded; source commit UNKNOWN, not local-gate ready."
        return result
    supplied_bytes = receipt_path.read_bytes()
    supplied = json.loads(supplied_bytes.decode("utf-8"))
    hashes = supplied.get("tool_sha256", {})
    for name, actual in binaries.items():
        if hashes.get(name) != actual["sha256"]:
            raise ValueError(f"Toolchain receipt binary hash mismatch: {name}")
    if supplied.get("luau_source_commit") != PINNED_LUAU_COMMIT:
        raise ValueError("Toolchain receipt source commit differs from pinned Luau commit")
    result.update({
        "source_commit": supplied["luau_source_commit"],
        "provided_build_receipt": {"path": str(receipt_path), **byte_info(supplied_bytes)},
        "binary_hashes_match_provided_receipt": True,
        "local_toolchain_gate_ready": True,
        "boundary": "Binary SHA256 values match the provided local build receipt; its source-commit label is not a provider attestation.",
    })
    return result


def native_inputs(lock: dict[str, Any]) -> tuple[bytes, dict[str, bytes]]:
    native = lock["native"]
    entry = native["entry_text"].encode("utf-8")
    if entry != ENTRY_TEXT.encode("utf-8") or byte_info(entry) != {"bytes": 152, "sha256": ENTRY_SHA256}:
        raise ValueError("Original 152-byte Native entry drift")
    specs = native["specs"]
    if set(specs) != set(SPEC_CONTRACTS):
        raise ValueError("Pinned Native spec set differs from the two granted specs")
    bodies = {}
    for name, contract in SPEC_CONTRACTS.items():
        row = specs[name]
        if any(row.get(key) != value for key, value in contract.items()):
            raise ValueError(f"Native spec contract drift: {name}")
        path = PACKAGE_ROOT / row["path"]
        data = path.read_bytes()
        if byte_info(data) != {"bytes": row["bytes"], "sha256": row["sha256"]}:
            raise ValueError(f"Pinned Native spec bytes drift: {name}")
        bodies[name] = data
    return entry, bodies


def run_process(argv: list[str], cwd: Path, log_prefix: Path) -> dict[str, Any]:
    """Preserve stdout/stderr even when a process fails or times out."""
    try:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=30, check=False)
        stdout, stderr = completed.stdout, completed.stderr
        returncode, timeout, started = completed.returncode, False, True
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b"", error.stderr or b""
        returncode, timeout, started = None, True, True
    except OSError as error:
        stdout, stderr = b"", str(error).encode("utf-8")
        returncode, timeout, started = None, False, False
    stdout_path = Path(str(log_prefix) + ".stdout.txt")
    stderr_path = Path(str(log_prefix) + ".stderr.txt")
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    return {
        "argv": argv,
        "cwd": str(cwd),
        "returncode": returncode,
        "timeout": timeout,
        "process_started": started,
        "stdout": {"path": str(stdout_path), **file_info(stdout_path)},
        "stderr": {"path": str(stderr_path), **file_info(stderr_path)},
    }


def run_regressions(
    root: Path,
    luau: Path,
    compiler: Path,
    output: Path,
    toolchain_receipt: Path | None = None,
    *,
    parent_kind: str = "FROZEN_LOCAL",
    expected_parent_context: dict[str, Any] | Path | None = None,
) -> dict[str, Any]:
    if root.is_symlink() or output.is_symlink():
        raise ValueError("Input stage and Native output must not be symbolic links")
    root, luau, compiler, output = (p.resolve() for p in (root, luau, compiler, output))
    if output.exists():
        raise ValueError("Native output must be a fresh directory; existing output will not be overwritten")
    if output == root or output.is_relative_to(root) or output.is_relative_to(PACKAGE_ROOT):
        raise ValueError("Native output must be outside the immutable produced stage and source package")
    output.mkdir(parents=True, exist_ok=False)
    receipt: dict[str, Any] = {
        "schema": "GQ487_SCORE_NATIVE_SOURCE_ONLY_V1",
        "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "SOURCE_ONLY_NATIVE_NOT_RUN",
        "input_root": str(root),
        "output": str(output),
        "native_invocations": 0,
        "native_processes_started": 0,
        "variants": [],
        "native_pass": False,
        "local_native_gate_ready": False,
        "official_rc_adoption": False,
        "final_union_contract_bound": False,
        "canonical_build": False,
        "official_build_head": None,
        "game_Place_builds": 0,
        "Studio": "NOT_TESTED",
        "Android": "NOT_TESTED",
        "remote_writes": 0,
        "scope": "One exact current Score module; all69 stage inputs verified, not all69 modules executed.",
        "count_boundary": "Assertion counters are measured; Score.build evaluations are expected static counts, not instrumented calls or independent gameplay cases.",
        "parent_kind": parent_kind,
        "expected_parent_context": None,
        "parent_expectation_source": "NOT_SUPPLIED",
        "parent_origin_attestation_verified": False,
    }
    producer = None
    before = None
    code_pins = None
    archive_pins: dict[str, dict[str, Any]] = {}
    execution_pins: dict[str, dict[str, Any]] = {}
    provided_receipt_pins: dict[str, dict[str, Any]] = {}
    parent_context_input_pins: dict[str, dict[str, Any]] = {}
    archived: dict[str, dict[str, Any]] = {}
    context = None
    try:
        if parent_kind not in ("FROZEN_LOCAL", "UNION22_DELIVERY"):
            raise ValueError("Unknown parent_kind; expected FROZEN_LOCAL or UNION22_DELIVERY")
        if parent_kind == "FROZEN_LOCAL" and expected_parent_context is not None:
            raise ValueError("FROZEN_LOCAL forbids expected_parent_context")
        if parent_kind == "UNION22_DELIVERY" and expected_parent_context is None:
            raise ValueError("UNION22_DELIVERY requires external expected_parent_context")
        producer = load_producer()
        if isinstance(expected_parent_context, Path):
            # Keep the caller's path identity for the final raw-byte readback.
            context_path = expected_parent_context.absolute()
            if context_path.is_symlink() or not context_path.is_file():
                raise ValueError("External parent expectation must be a regular non-symlink file")
            raw_context = context_path.read_bytes()
            parent_context_input_pins[str(context_path)] = byte_info(raw_context)
            target = output / "execution_inputs" / "external_parent_context.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw_context)
            archive_pins[str(target)] = byte_info(raw_context)
            archived["external_parent_context.json"] = {"path": str(target), **byte_info(raw_context)}
            receipt["archived_execution_inputs"] = archived
            receipt["external_parent_context_input"] = {"path": str(context_path), **byte_info(raw_context)}
            context = copy.deepcopy(producer.read_parent_expectation(context_path))
            receipt["parent_context_input_preflight"] = verify_copies(
                parent_context_input_pins, "after external parent expectation parsing"
            )
            receipt["parent_expectation_source"] = "EXTERNAL_CALLER_FILE"
        elif expected_parent_context is not None:
            if not isinstance(expected_parent_context, dict):
                raise ValueError("Expected parent context must be an explicit dict or Path")
            context = copy.deepcopy(expected_parent_context)
            receipt["parent_expectation_source"] = "EXTERNAL_CALLER_DICT"
        if context is not None:
            if not isinstance(context, dict) or set(context) != PARENT_CONTEXT_FIELDS:
                raise ValueError("Expected parent context must contain exactly the nine upstream fields")
            json.dumps(context, allow_nan=False)
            receipt["expected_parent_context"] = copy.deepcopy(context)
        lock = producer.load_lock()
        entry, specs = native_inputs(lock)
        receipt["stage_preflight"] = producer.verify_stage(
            root, "after", parent_kind=parent_kind, expected_parent_context=copy.deepcopy(context)
        )
        identity = producer.validate_sources(root, "after")
        score_row = identity["sources"][SCORE_PATH]
        if identity["source_count"] != 69 or {key: score_row[key] for key in SCORE_AFTER} != SCORE_AFTER:
            raise ValueError("Native requires the exact after Score8741 and all69 produced inputs")
        score = (root / "sources" / SCORE_PATH).read_bytes()
        if byte_info(score) != SCORE_AFTER:
            raise ValueError("Produced Score body changed after preflight")
        before = stage_fingerprint(root)
        code_paths = [Path(__file__).resolve(), PACKAGE_ROOT / "compose_score_relay.py", PACKAGE_ROOT / "source_lock.json"]
        code_paths.extend(PACKAGE_ROOT / row["path"] for row in lock["native"]["specs"].values())
        code_pins = {str(path): file_info(path) for path in code_paths}
        receipt["code_and_lock_pins"] = code_pins
        for path in code_paths:
            data = path.read_bytes()
            if byte_info(data) != code_pins[str(path)]:
                raise ValueError("Source package changed while preserving execution inputs")
            target = output / "execution_inputs" / path.relative_to(PACKAGE_ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            archived[path.relative_to(PACKAGE_ROOT).as_posix()] = {"path": str(target), **byte_info(data)}
            archive_pins[str(target)] = byte_info(data)
        receipt["archived_execution_inputs"] = archived
        receipt["all69_project_identity"] = identity
        receipt["stage_files_before"] = before
        receipt["Score"] = SCORE_AFTER
        receipt["entry"] = byte_info(entry)
        receipt["toolchain"] = toolchain_record(
            luau, compiler, toolchain_receipt.resolve() if toolchain_receipt else None
        )
        if toolchain_receipt:
            supplied_bytes = toolchain_receipt.read_bytes()
            pin = receipt["toolchain"]["provided_build_receipt"]
            if byte_info(supplied_bytes) != {key: pin[key] for key in ("bytes", "sha256")}:
                raise ValueError("Toolchain receipt changed after its hash validation")
            copy_path = output / "provided_toolchain_receipt.json"
            copy_path.write_bytes(supplied_bytes)
            provided_receipt_pins[str(copy_path)] = byte_info(supplied_bytes)
            receipt["provided_toolchain_receipt_copy"] = {"path": str(copy_path), **byte_info(supplied_bytes)}
        receipt["status"] = "SOURCE_ONLY_NATIVE_RUNNING"
        write_json(output / "native_receipt.json", receipt)

        for name, contract in SPEC_CONTRACTS.items():
            directory = output / name
            directory.mkdir()
            files = {"Results.luau": score, "Cases.luau": specs[name], "Runner.luau": entry}
            for filename, data in files.items():
                (directory / filename).write_bytes(data)
            variant_pins = {str(directory / filename): byte_info(data) for filename, data in files.items()}
            execution_pins.update(variant_pins)
            variant: dict[str, Any] = {
                "name": name,
                "files": {filename: byte_info(data) for filename, data in files.items()},
                "expected_assertions": contract["assertions"],
                "expected_Score_build_evaluations_static": contract["score_build_evaluations"],
                "compile": [],
                "execution_copy_checks": [],
                "native": {"executed": False},
                "passed": False,
            }
            receipt["variants"].append(variant)
            for filename in files:
                variant["execution_copy_checks"].append(verify_copies(variant_pins, f"before compile {name}/{filename}"))
                result = run_process([str(compiler), "--null", filename], directory, directory / (filename + ".compile"))
                variant["compile"].append(result)
                variant["execution_copy_checks"].append(verify_copies(variant_pins, f"after compile {name}/{filename}"))
                write_json(output / "native_receipt.json", receipt)
                if result["returncode"] != 0:
                    raise ValueError(f"Native fixture compilation failed: {name}/{filename}")
            variant["execution_copy_checks"].append(verify_copies(variant_pins, f"before Native {name}"))
            receipt["native_invocations"] += 1
            result = run_process([str(luau), "Runner.luau"], directory, directory / "native")
            receipt["native_processes_started"] += int(result["process_started"])
            variant["native"] = {"attempted": True, "executed": result["process_started"], **result}
            variant["execution_copy_checks"].append(verify_copies(variant_pins, f"after Native {name}"))
            lines = Path(result["stdout"]["path"]).read_text(encoding="utf-8").splitlines()
            variant["spec_marker_count"] = lines.count(contract["marker"])
            variant["entry_marker_count"] = lines.count(ENTRY_MARKER)
            variant["passed"] = result["returncode"] == 0 and variant["spec_marker_count"] == 1 and variant["entry_marker_count"] == 1
            if variant["passed"]:
                variant["measured_counted_assertions"] = contract["assertions"]
            write_json(output / "native_receipt.json", receipt)
            if not variant["passed"]:
                raise ValueError(f"Native spec failed or exact completion marker missing: {name}")
        receipt["native_pass"] = len(receipt["variants"]) == 2 and all(v["passed"] for v in receipt["variants"])
    except Exception as error:
        receipt["status"] = "SOURCE_ONLY_NATIVE_FAIL"
        receipt["error"] = {"type": type(error).__name__, "message": str(error)}
        (output / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
    finally:
        if producer is not None and before is not None:
            try:
                receipt["stage_postflight"] = producer.verify_stage(
                    root, "after", parent_kind=parent_kind, expected_parent_context=copy.deepcopy(context)
                )
                receipt["stage_files_unchanged"] = stage_fingerprint(root) == before
                receipt["code_and_lock_unchanged"] = all(file_info(Path(path)) == pin for path, pin in (code_pins or {}).items())
                if not receipt["stage_files_unchanged"] or not receipt["code_and_lock_unchanged"]:
                    raise ValueError("Input stage, source package, spec, or lock changed during Native execution")
                if "toolchain" in receipt:
                    receipt["tool_binaries_unchanged"] = all(
                        file_info(path) == receipt["toolchain"]["binaries"][name]
                        for name, path in (("luau", luau), ("luau-compile", compiler))
                    )
                    if not receipt["tool_binaries_unchanged"]:
                        raise ValueError("Tool binary changed during Native execution")
            except Exception as error:
                receipt["postflight_error"] = {"type": type(error).__name__, "message": str(error)}
                receipt["native_pass"] = False
                receipt["status"] = "SOURCE_ONLY_NATIVE_FAIL"
        try:
            if execution_pins:
                receipt["execution_copies_postflight"] = verify_copies(execution_pins, "final execution copies")
            if archive_pins:
                receipt["archived_execution_inputs_postflight"] = verify_copies(archive_pins, "final execution_inputs archive")
            if provided_receipt_pins:
                receipt["provided_toolchain_receipt_copy_postflight"] = verify_copies(
                    provided_receipt_pins, "final provided_toolchain_receipt copy"
                )
            if parent_context_input_pins:
                receipt["parent_context_input_postflight"] = verify_copies(
                    parent_context_input_pins, "final external parent expectation input"
                )
        except Exception as error:
            receipt["copy_postflight_error"] = {"type": type(error).__name__, "message": str(error)}
            receipt["native_pass"] = False
            receipt["status"] = "SOURCE_ONLY_NATIVE_FAIL"
        if receipt["native_pass"] and not any(key in receipt for key in ("error", "postflight_error", "copy_postflight_error")):
            receipt["measured_counted_assertions_total"] = sum(v["measured_counted_assertions"] for v in receipt["variants"])
            receipt["expected_Score_build_evaluations_static_total"] = sum(v["expected_Score_build_evaluations_static"] for v in receipt["variants"])
            receipt["local_native_gate_ready"] = receipt["toolchain"]["local_toolchain_gate_ready"]
            receipt["status"] = "SOURCE_ONLY_NATIVE_PASS" if receipt["local_native_gate_ready"] else "SOURCE_ONLY_NATIVE_PASS_TOOLCHAIN_UNKNOWN_NOT_GATE_READY"
        receipt["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        write_json(output / "native_receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Actual producer output with its current manifest, receipt, project and69 sources")
    parser.add_argument("--luau", type=Path, required=True)
    parser.add_argument("--luau-compile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Fresh directory outside the immutable input stage")
    parser.add_argument("--toolchain-receipt", type=Path, help="Local build receipt; missing receipt leaves source commit UNKNOWN and exits2 after otherwise passing")
    parser.add_argument("--parent-kind", choices=("frozen-local", "union22-delivery"), default="frozen-local")
    parser.add_argument("--expected-parent-context", type=Path, help="Independent caller's nine-field context JSON or SCORE_RELAY_EXTERNAL_PARENT_EXPECTATION_V1 wrapper")
    args = parser.parse_args()
    try:
        receipt = run_regressions(
            args.root, args.luau, args.luau_compile, args.output, args.toolchain_receipt,
            parent_kind=args.parent_kind.replace("-", "_").upper(),
            expected_parent_context=args.expected_parent_context,
        )
    except Exception as error:
        print(f"SOURCE_ONLY_NATIVE_PREFLIGHT_REJECTED: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": receipt["status"],
        "receipt": str(args.output.resolve() / "native_receipt.json"),
        "native_invocations": receipt["native_invocations"],
        "measured_assertions": receipt.get("measured_counted_assertions_total"),
        "expected_Score_build_evaluations_static": receipt.get("expected_Score_build_evaluations_static_total"),
        "stage_unchanged": receipt.get("stage_files_unchanged"),
        "local_native_gate_ready": receipt["local_native_gate_ready"],
        "parent_kind": receipt["parent_kind"],
        "parent_expectation_source": receipt["parent_expectation_source"],
    }))
    if not receipt["native_pass"]:
        return 1
    return 0 if receipt["local_native_gate_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
