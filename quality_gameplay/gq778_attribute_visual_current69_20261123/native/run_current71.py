#!/usr/bin/env python3
"""Fresh native/compile/Rojo evidence for a fixed #778 SOURCE candidate.

No Studio, Android, visual quality, or formal-RC acceptance is inferred here.
Every expected failure is retained as a failure observation, not a passing game.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODULE_PATH = "handoffs/EGGRUMBLE-ATTR-VFX-20261118/ElementVisuals.luau"
CLIENT_PATH = "handoffs/EGGRUMBLE-ATTR-VFX-20261118/EGGRUMBLE_AttributeCue.client.luau"
ORIGINAL_HEAD = "a8391a94ea1cbf7fe069fc34fb77b95c5a846cfb"
MARKER = b"-- GQ778_INSERT_SOURCE_BODIES_HERE"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError("GQ778_RED_" + message)


def git(directory, *args):
    return subprocess.run(["git", "-C", str(directory), *args], check=True, capture_output=True).stdout


def command(args, output, name, *, cwd=None):
    result = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True)
    output.mkdir(parents=True, exist_ok=True)
    (output / (name + ".stdout.log")).write_bytes(result.stdout)
    (output / (name + ".stderr.log")).write_bytes(result.stderr)
    return {
        "name": name, "argv": [str(a) for a in args], "returncode": result.returncode,
        "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
        "stdout_bytes": len(result.stdout), "stderr_bytes": len(result.stderr),
    }, result


def assemble(template, bodies, expectation):
    require(template.count(MARKER) == 1, "FIXTURE_MARKER")
    prefix, suffix = template.split(MARKER)
    program = prefix
    spans = {}
    for label, loader in (("module", "loadActualModule"), ("client", "loadActualClient")):
        program += ("\n" + loader + "=function(script)\n").encode()
        start = len(program)
        program += bodies[label]
        spans[label] = {"start": start, "end": len(program), "sha256": sha(bodies[label])}
        program += b"\nend\n"
    program += ("\nlocal expectation=" + json.dumps(expectation) + "\n").encode() + suffix
    for label, span in spans.items():
        require(program[span["start"]:span["end"]] == bodies[label], "ALTERED_FULL_SOURCE_BODY")
    return program, spans


def fresh_native(source, output, lock):
    source = source.resolve(strict=True)
    require(git(source, "rev-parse", "HEAD").decode().strip() == lock["commit"], "LUAU_SOURCE_COMMIT")
    require(git(source, "rev-parse", "HEAD^{tree}").decode().strip() == lock["tree"], "LUAU_SOURCE_TREE")
    require(not git(source, "status", "--porcelain", "--untracked-files=all"), "LUAU_DIRTY_SOURCE")
    manifest = []
    for row in git(source, "ls-files", "-s", "-z").split(b"\0"):
        if not row:
            continue
        meta, raw_path = row.split(b"\t", 1)
        mode, expected_blob, stage = meta.decode().split()
        path = raw_path.decode()
        require(mode in ("100644", "100755") and stage == "0", "LUAU_UNSUPPORTED_SOURCE_ENTRY")
        file = source / path
        require(file.is_file() and not file.is_symlink(), "LUAU_SOURCE_FILE")
        body = file.read_bytes()
        require(blob(body) == expected_blob, "LUAU_TRACKED_BYTES")
        manifest.append({"path": path, "blob": expected_blob, "bytes": len(body), "sha256": sha(body)})
    output.mkdir(parents=True, exist_ok=False)
    (output / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    build = output / "build"
    commands = []
    for name, args in (
        ("configure", ["cmake", "-S", source, "-B", build, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                       "-DLUAU_BUILD_TESTS=OFF", "-DLUAU_BUILD_WEB=OFF"]),
        ("build", ["cmake", "--build", build, "--target", "Luau.Repl.CLI", "Luau.Compile.CLI", "--parallel", "2"]),
    ):
        record, result = command(args, output, name)
        commands.append(record)
        require(result.returncode == 0, "FRESH_LUAU_" + name.upper())
    require(not git(source, "status", "--porcelain", "--untracked-files=all"), "LUAU_SOURCE_CHANGED_DURING_BUILD")
    for entry in manifest:
        require(sha((source / entry["path"]).read_bytes()) == entry["sha256"], "LUAU_BYTES_CHANGED_DURING_BUILD")
    binaries = {name: {"path": str(build / name), "sha256": sha((build / name).read_bytes())}
                for name in ("luau", "luau-compile")}
    receipt = {"source_commit": lock["commit"], "source_tree": lock["tree"], "tracked_source_files": len(manifest),
               "source_manifest_sha256": sha((output / "source_manifest.json").read_bytes()),
               "build_directory_was_absent": True, "commands": commands, "binaries": binaries}
    (output / "BUILD_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return build / "luau", build / "luau-compile", receipt


def run(args, ownership=None):
    ownership = {} if ownership is None else ownership
    output = args.out_dir.resolve()
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    lock_bytes = (HERE / "INPUT_LOCK.json").read_bytes()
    lock = json.loads(lock_bytes)
    require(lock["schema"] == "GQ778_FULL_BODY_NATIVE_INPUT_V1", "NATIVE_LOCK_SCHEMA")
    fixture = (HERE / "fixture.luau").read_bytes()
    require(sha(fixture) == lock["fixture_sha256"], "FIXTURE_HASH")
    spec = importlib.util.spec_from_file_location("gq778_composer", HERE.parent / "compose_current71.py")
    composer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(composer)
    source_lock = (HERE.parent / "source_lock.json").read_bytes()
    require(sha(source_lock) == lock["source_lock_sha256"], "OFFICIAL_LOCK_HASH")
    official = composer.read_official_artifact(args.artifact)
    require(sha(args.rojo.read_bytes()) == lock["rojo_binary_sha256"], "ROJO_BINARY_HASH")
    if args.diagnostic_original_root:
        source_head = None
        originals = {label: (args.diagnostic_original_root / path).read_bytes()
                     for label, path in (("module", MODULE_PATH), ("client", CLIENT_PATH))}
    else:
        source_head = git(ROOT, "rev-parse", "HEAD").decode().strip()
        require(not git(ROOT, "status", "--porcelain", "--untracked-files=no"), "CANDIDATE_TRACKED_DIRTY")
        originals = {label: git(ROOT, "show", ORIGINAL_HEAD + ":" + path)
                     for label, path in (("module", MODULE_PATH), ("client", CLIENT_PATH))}
    candidate = {"module": (ROOT / MODULE_PATH).read_bytes(), "client": (ROOT / CLIENT_PATH).read_bytes()}
    for label, body in originals.items():
        require(blob(body) == lock["originals"][label]["git_blob"] and sha(body) == lock["originals"][label]["sha256"],
                "ORIGINAL_BODY_" + label.upper())
    for path, expected in lock["immutable_original_paths"].items():
        require(blob((ROOT / path).read_bytes()) == expected, "FROZEN_ORIGINAL_PATH")
    output.mkdir(parents=True)
    owned_stat = output.stat()
    ownership.update(path=output, device=owned_stat.st_dev, inode=owned_stat.st_ino)
    print("GQ778_INPUTS_VERIFIED_FRESH_LUAU_BUILD_START", flush=True)
    cli, compiler, native_build = fresh_native(args.luau_source, output / "native_build", lock["luau"])
    print("GQ778_FRESH_LUAU_BUILD_COMPLETE", flush=True)
    native = output / "native"
    native.mkdir()
    records = []
    programs = {}

    def execute(name, bodies, expectation, *, expected_failure=None):
        program, spans = assemble(fixture, bodies, expectation)
        file = native / (name + ".luau")
        file.write_bytes(program)
        record, result = command([cli, file], native, name)
        records.append(record)
        programs[name] = {"program_sha256": sha(program), "full_body_spans": spans}
        if expected_failure:
            require(result.returncode != 0 and expected_failure.encode() in result.stderr + result.stdout,
                    "EXPECTED_NEGATIVE_DID_NOT_REJECT_" + name)
        else:
            require(result.returncode == 0, "NATIVE_" + name)
            text = result.stdout.decode()
            require(text.splitlines()[-1] == lock["terminal_markers"][expectation], "NATIVE_TERMINAL_" + name)
            rows = [line for line in text.splitlines() if line.startswith("OBS ")]
            require(len(rows) == lock["observation_count"] and len(set(rows)) == len(rows), "NATIVE_CASE_ACCOUNTING")
            require(result.stderr == b"", "NATIVE_UNEXPECTED_STDERR")
        return result

    execute("original_observations", originals, "original")
    execute("original_against_new_contract", originals, "proposal", expected_failure=lock["baseline_contract_failure"])
    execute("candidate", candidate, "proposal")
    require(len(lock["mutants"]) >= 4, "MISSING_TARGETED_MUTANTS")
    for mutant in lock["mutants"]:
        bodies = dict(candidate)
        old, new = mutant["old"].encode(), mutant["new"].encode()
        require(bodies[mutant["target"]].count(old) == 1, "MUTANT_ANCHOR_" + mutant["name"])
        bodies[mutant["target"]] = bodies[mutant["target"]].replace(old, new, 1)
        execute("mutant_" + mutant["name"], bodies, "proposal", expected_failure=mutant["failure_contains"])
    print("GQ778_FULL_BODY_BASELINE_CANDIDATE_MUTANTS_COMPLETE", flush=True)

    # The original descriptor generator is retained byte-for-byte and remains
    # a separate historical contract; it cannot replace actual renderer execution.
    legacy = output / "legacy"
    record, result = command([sys.executable, "-B", ROOT / "handoffs/EGGRUMBLE-ATTR-VFX-20261118/make_native_tests.py",
                              "--out", legacy], output, "legacy_generator")
    records.append(record)
    require(result.returncode == 0, "LEGACY_GENERATOR")
    for name, failure in (("good", None), ("mutant", "RED_BUDGET")):
        record, result = command([cli, legacy / (name + ".luau")], legacy, name)
        records.append(record)
        if failure:
            require(result.returncode != 0 and failure.encode() in result.stderr, "LEGACY_BUDGET_MUTANT")
        else:
            require(result.returncode == 0 and result.stdout.strip() == b"GQ8_ATTR_VFX_NATIVE_SHAPES_BUDGET_CONTRACT_PASS",
                    "LEGACY_DESCRIPTOR_CONTRACT")

    compositions = {}
    compile_records = []
    for profile, enabled in (("ON71", True), ("OFF69", False)):
        target = output / profile
        compositions[profile] = composer.compose(args.artifact, target, args.rojo, enabled=enabled)
        project = composer.read_json((target / compositions[profile]["project"]["path"]).read_bytes())
        for index, (route, path) in enumerate(sorted(composer.project_inventory(project).items())):
            record, result = command([compiler, "--text", target / path], output / "compile" / profile, str(index))
            record["route"] = route
            require(result.returncode == 0 and result.stderr == b"", "COMPILE_" + route)
            compile_records.append(record)
    require(len(compile_records) == 140, "COMPILE_COUNT")

    # Run the real tests with artifact required; normal discovery has a separate
    # artifact-free contract suite and explicit skips for unavailable external input.
    env_before = os.environ.get("GQ778_ARTIFACT")
    os.environ["GQ778_ARTIFACT"] = str(args.artifact.resolve())
    try:
        record, result = command([sys.executable, "-B", ROOT / "tests/test_gq778_attribute_visual_current69_20261123.py",
                                  "--require-artifact"], output, "artifact_contract_tests")
    finally:
        if env_before is None:
            os.environ.pop("GQ778_ARTIFACT", None)
        else:
            os.environ["GQ778_ARTIFACT"] = env_before
    records.append(record)
    require(result.returncode == 0 and b"skipped=" not in result.stderr + result.stdout, "ARTIFACT_CONTRACT_TESTS")
    require((HERE / "INPUT_LOCK.json").read_bytes() == lock_bytes and (HERE / "fixture.luau").read_bytes() == fixture,
            "NATIVE_INPUTS_CHANGED")
    require((HERE.parent / "source_lock.json").read_bytes() == source_lock, "OFFICIAL_LOCK_CHANGED")
    for label, path in (("module", MODULE_PATH), ("client", CLIENT_PATH)):
        require((ROOT / path).read_bytes() == candidate[label], "CANDIDATE_CHANGED")
    if source_head:
        require(git(ROOT, "rev-parse", "HEAD").decode().strip() == source_head and
                not git(ROOT, "status", "--porcelain", "--untracked-files=no"), "CANDIDATE_HEAD_OR_BYTES_CHANGED")
    report = {
        "schema": "GQ778_CURRENT71_SOURCE_QA_V1", "status": "LOCAL_NATIVE_COMPILE_ROJO_EVIDENCE_COMPLETE",
        "source_head": source_head, "diagnostic_proposal_only": bool(args.diagnostic_original_root),
        "official_rc_sha": official[0]["official_rc_sha"], "official_artifact": official[0]["artifact"],
        "candidate": {k: {"bytes": len(v), "sha256": sha(v), "git_blob": blob(v)} for k, v in candidate.items()},
        "native_build": native_build, "programs": programs, "commands": records,
        "original_known_gap_checks": lock["known_gap_checks"],
        "original_contract_rejected": True, "candidate_contract_passed": True,
        "targeted_mutants_rejected": [x["name"] for x in lock["mutants"]],
        "compile": compile_records, "compositions": compositions,
        "source_acceptance": False, "formal_rc_adoption": False,
        "studio": "NOT_TESTED", "android": "NOT_TESTED", "art": "NOT_TESTED", "fun": "NOT_TESTED",
        "limitations": lock["limitations"],
    }
    (output / "REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    print("GQ778_CURRENT71_FULL_BODY_NATIVE_140_COMPILE_ON71_OFF69_EVIDENCE_COMPLETE_NOT_RC", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--luau-source", type=Path, required=True)
    parser.add_argument("--rojo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--diagnostic-original-root", type=Path,
                        help="Isolated proposal only; prevents a source-head evidence claim.")
    args = parser.parse_args()
    ownership = {}
    try:
        run(args, ownership)
    except Exception as error:
        # Only this invocation's exclusively created directory may receive a
        # failure record. Never alter a directory rejected by the initial guard.
        # A descriptor pins that owned directory even if its path is replaced.
        if ownership:
            directory_fd = None
            try:
                directory_fd = os.open(ownership["path"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                observed = os.fstat(directory_fd)
                if (observed.st_dev, observed.st_ino) == (ownership["device"], ownership["inode"]):
                    failure_fd = os.open("FAILURE.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                                         0o600, dir_fd=directory_fd)
                    with os.fdopen(failure_fd, "w", encoding="utf-8") as handle:
                        handle.write(json.dumps({"status": "REJECTED", "error": str(error)}, indent=2) + "\n")
            except OSError:
                pass  # Preserve the original failure and any existing file.
            finally:
                if directory_fd is not None:
                    os.close(directory_fd)
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
