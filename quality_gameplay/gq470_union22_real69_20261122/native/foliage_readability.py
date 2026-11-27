"""Execute and validate the existing full-body Native foliage cases."""

import importlib.util
import json
from pathlib import Path


FIXTURE = Path(__file__).with_name("foliage_native_cases.py")


def source_paths(root, compose):
    return {"official": root.parent / compose.NEUTRAL_NAMES_OFF / "sources" / compose.FOLIAGE_LOD_SOURCE,
            "candidate": root / compose.FOLIAGE_LOD_SOURCE}


def check(root, output, native, context, profile, compose):
    record = profile["neutral_names_followup"]["foliage"]
    pin = compose.identity(compose.read_file(FIXTURE))
    compose.need(pin == record["native_fixture"], "FOLIAGE_NATIVE_FIXTURE_PIN")
    report = json.loads(compose.read_file(output / "receipt.json"))
    expected = {"official": record["native_before"], "candidate": record["native_after"]}
    compose.need(set(report) == {"native", "context", "fixture", "scope", "cases"}
                 and report["native"] == native and report["context"] == context
                 and report["fixture"] == pin and set(report["cases"]) == set(expected)
                 and report["scope"] == "Full LocalScript with deterministic Roblox geometry/event mocks",
                 "FOLIAGE_NATIVE_RECEIPT_BINDING")
    for mode, path in source_paths(root, compose).items():
        observed, wanted = report["cases"][mode], expected[mode]
        selected = compose.identity(compose.read_file(path))
        compose.need(set(observed) == set(wanted)
                     and selected == {"bytes": wanted["source_bytes"], "sha256": wanted["source_sha256"]}
                     and all(observed[k] == v for k, v in wanted.items() if k != "cases"),
                     "FOLIAGE_NATIVE_SOURCE_OR_COUNTS")
        # Exception file paths may differ between the hosted and Windows Luau binaries.
        actual_cases = [line.split("\t", 2)[:2] for line in observed["cases"]]
        expected_cases = [line.split("\t", 2)[:2] for line in wanted["cases"]]
        compose.need(actual_cases == expected_cases and len(actual_cases) == 14, "FOLIAGE_NATIVE_CASE_VECTOR")
    compose.need(report["cases"]["candidate"]["passed"] == 14 and report["cases"]["candidate"]["unexpected"] == 0,
                 "FOLIAGE_FULL_BODY_REGRESSION")
    return report


def run(root, output, binary, native, context, profile, compose):
    raw = compose.read_file(FIXTURE)
    compose.need(compose.identity(raw) == profile["neutral_names_followup"]["foliage"]["native_fixture"],
                 "FOLIAGE_NATIVE_FIXTURE_PIN")
    spec = importlib.util.spec_from_file_location("union22_original_foliage", FIXTURE)
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    tested = {mode: harness.run(binary, compose.read_file(path), mode, mode == "candidate")
              for mode, path in source_paths(root, compose).items()}
    output.mkdir()
    report = {"native": native, "context": context, "fixture": compose.identity(raw),
              "scope": "Full LocalScript with deterministic Roblox geometry/event mocks", "cases": tested}
    (output / "receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    check(root, output, native, context, profile, compose)
    print("foliage_readability: 14 full body cases; visible triangle and exact exit restoration PASS", flush=True)
