"""Run the #928 cap and fade regressions on the pinned ImpactFeedback bodies."""

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


EXPECTED = ["KO_SECOND_BOUNDARY\t1\t24", "KO_SECOND_BOUNDARY\t2\t12", "KO_RECLAIM_FULL_PAIR_ONLY\t12"]
FADE_CASES = ["KO_GEOMETRY_AND_DELAYED_FADE\t12", "KO_CROSS_SECOND_PARTIAL_PAIR_SUPPRESSED\t12",
              "KO_RECLAIM_AND_REFILL\t12", "KO_TEARDOWN_NO_RESIDUE\t0"]
ROUTE = "ServerScriptService/EGGRUMBLE_ImpactFeedback.luau"


def expected(root, native_pin, context, lock, compose):
    group = lock["combat_visual_followup"]
    earlier = root.parent / compose.COMBAT_VISUAL_OFF / "sources" / ROUTE
    selected = root / ROUTE
    test_path = compose.REPO / group["ko_fixture"]["path"]
    fade_path = compose.REPO / group["ko_fade_fixture"]["path"]
    original = compose.identity(compose.read_file(earlier))
    patched = compose.identity(compose.read_file(selected))
    fixture = compose.identity(compose.read_file(test_path))
    fade_fixture = compose.read_file(fade_path)
    compose.need(fixture == group["ko_fixture"]["identity"]
                 and compose.identity(fade_fixture) == group["ko_fade_fixture"]["identity"]
                 and original == group["rows"][ROUTE]["parent"]["after"]
                 and patched == lock["sources"][ROUTE]["after"], "COMBAT_VISUAL_NATIVE_INPUT_PIN")
    data = {"context": context, "vm": native_pin, "scope": "Exact #928 live cap and delayed fade",
            "original": original, "selected": patched, "fixture": fixture, "cases": EXPECTED,
            "fade_fixture": compose.identity(fade_fixture), "fade_cases": FADE_CASES,
            "immediate_fade_rejection": "short AddItem lifetime"}
    return data, test_path, earlier, selected, fade_fixture


def run(root, output, binary, native_pin, context, lock, compose):
    required, fixture, before, after, fade_fixture = expected(root, native_pin, context, lock, compose)
    from verify_union22 import visual_author

    row = lock["combat_visual_followup"]["ko_fade"]
    fade = visual_author(row["path"], row["identity"], "COMBAT_VISUAL_KO_FADE")
    selected = compose.read_file(after)
    capped = fade.inverse(selected)
    with TemporaryDirectory(prefix="union22-ko-fade-") as directory:
        intermediate = Path(directory) / "capped.luau"
        intermediate.write_bytes(capped)
        result = subprocess.run([sys.executable, "-B", str(fixture), "--luau", str(binary),
                                 "--official-source", str(before), "--selected-source", str(intermediate)],
                                capture_output=True, timeout=60, check=True)
        program = Path(directory) / "timed.luau"
        for body, delayed in ((selected, True), (capped, False)):
            compose.need(b"]=]" not in body, "COMBAT_VISUAL_NATIVE_QUOTE")
            program.write_bytes(fade_fixture + b"\ntimedBurst([=[" + body + b"]=])\n")
            tested = subprocess.run([str(binary), str(program)], capture_output=True, timeout=45, check=False)
            if delayed:
                compose.need(tested.returncode == 0 and not tested.stderr
                             and tested.stdout.decode().splitlines() == FADE_CASES, "COMBAT_VISUAL_FADE_CASES")
            else:
                compose.need(tested.returncode == 1 and not tested.stdout
                             and b"timed.luau:24: assertion failed" in tested.stderr
                             and b"function AddItem" in tested.stderr,
                             "COMBAT_VISUAL_FADE_BASELINE_MUST_FAIL")
    lines = result.stdout.replace(b"\r\r\n", b"\r\n").decode().splitlines()
    compose.need(not result.stderr and lines == EXPECTED,
                 "COMBAT_VISUAL_NATIVE_CASES")
    output.mkdir()
    (output / "receipt.json").write_text(json.dumps(required, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("combat_visual: #928 live cap, delayed fade and expected immediate-fade rejection PASS", flush=True)
