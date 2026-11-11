#!/usr/bin/env python3
"""Independent actual 27-file composite source+assembler QA, source ONLY.

Uses unchanged SHA-pinned static auditors from independent QA commit
c65d2d5caecf1052c15951dedbf3959684d3dc59. No external dependencies,
no Studio, no Roblox publish, no Git mutations, and no false game-ready flag.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
VENDOR = ROOT / "vendor"
sys.path.insert(0, str(VENDOR))
import verify_rc_wiring as vr
import verify_source_snapshot as vs

SOURCE_COMMIT = "ff291d7a5e6dc53e841552d1abc3cbdf9a805f48"
AUDITOR_COMMIT = "c65d2d5caecf1052c15951dedbf3959684d3dc59"
GAME = REPO / "handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01"
SRC = GAME / "candidate"
PLAN = GAME / "SOURCE_PLAN_CORRECTED.json"
AUTH_RECEIPT = GAME / "CHAT_RC_RECEIPT.json"
ASSEMBLER = REPO / "handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/tools/chat_rc_assemble.py"

def force(condition: bool, detail: str) -> None:
    if not condition:
        raise RuntimeError("INDEPENDENT_SOURCE_GATE_FAIL:" + detail)

def expect_rejected(name: str, func, expected_prefix: str) -> None:
    try:
        func()
    except vr.QAError as err:
        force(str(err).startswith(expected_prefix),
              name + ":unexpected_error:" + str(err))
        print("EXPECTED_NEGATIVE_PASS:" + name + ":" + str(err), flush=True)
    else:
        raise RuntimeError("FAIL_OPEN_NEGATIVE_TEST:" + name)

def manifest_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def main() -> int:
    force(SRC.is_dir() and PLAN.is_file() and AUTH_RECEIPT.is_file(),
          "missing actual fixed candidate files")
    source_summary = vs.audit_source(SRC)
    force(source_summary["studio_2client_mobile"] == "NOT_TESTED",
          "source lied about studio")
    manifest = json.loads((SRC / "BUILD_MANIFEST.json").read_text("utf-8"))
    force(len(manifest["files"]) == 27, "expected exact 27-game-source manifest entries")
    plan = json.loads(PLAN.read_text("utf-8"))
    force(len(plan["units"]) == 18, "expected exact 18 real source units")
    named_roles = [u for u in plan["units"] if u.get("authorities")]
    force(len(named_roles) == 1 and
          set(named_roles[0]["authorities"]) == {"round", "event_chooser", "damage"} and
          named_roles[0]["target_path"] == "src/server/Game.server.luau",
          "more than one actual round/event/damage authority")
    source_luau = (SRC / "src/server/S1CanonicalRoundHost.luau").read_text("utf-8")
    binding_luau = (SRC / "src/server/S1GoroganLiveBindings.luau").read_text("utf-8")
    force('self.reason == "EVENT_FINISHED"' in source_luau and
          'self.bridge.retired[key] ~= true' in source_luau,
          "corrected D08 terminal handling absent")
    force('playerId:match("^%-?%d+$")' in binding_luau and
          'tostring(player.UserId) == playerId' in binding_luau,
          "corrected Studio negative UserId handling absent")
    game_script = (SRC / "src/server/Game.server.luau").read_text("utf-8")
    force("local CANONICAL_S1_ENABLED = false" in game_script and
          "local D07_D08_RELEASE_REVIEW_APPROVED = false" in game_script,
          "unauthorized gameplay activation or changed safety flags")
    force(game_script.count("remote.OnServerEvent:Connect(") == 1,
          "duplicate client-authoritative Roblox remote listeners")

    with tempfile.TemporaryDirectory(prefix="p0d_s1_independent_") as name:
        tmp = Path(name)
        output = tmp / "actual_assembled"
        result = subprocess.run(
            [sys.executable, str(ASSEMBLER), "--plan", str(PLAN),
             "--source-root", str(SRC), "--out", str(output)],
            cwd=str(REPO), capture_output=True, text=True, timeout=120)
        force(result.returncode == 0, "real Python assembler failed:" +
              result.stdout[-1600:] + result.stderr[-1600:])
        print("P0D_INDEPENDENT_REAL_PYTHON_ASSEMBLY_COMPLETED", flush=True)
        rec_content = (output / "CHAT_RC_RECEIPT.json").read_bytes()
        force(rec_content == AUTH_RECEIPT.read_bytes(),
              "actual receipt bytes differ from immutable author's receipt")
        print("P0D_INDEPENDENT_RECEIPT_BYTE_EQUAL_SHA256=" +
              manifest_hash(rec_content), flush=True)
        rc_report = vr.audit(output, PLAN)
        force(rc_report["result"] == "PASS_SOURCE_WIRING_ONLY",
              "actual independently assembled project static gate failed")
        force(rc_report["source_files_verified"] == 18,
              "source count differs from exact plan")
        force(rc_report["studio_2client_mobile"] == "NOT_TESTED",
              "false studio PASS")

        # Negative 1: actual Game byte tampering must be rejected by source QA.
        evil = tmp / "mutated_game"
        shutil.copytree(output, evil)
        with (evil / "src/server/Game.server.luau").open("ab") as out:
            out.write(b"\n-- unauthorized source edit\n")
        expect_rejected("tampered_Game_source",
                        lambda: vr.audit(evil, PLAN),
                        "CONTENT_BYTES_MISMATCH")

        # Negative 2: forge a studio-successful receipt without actual engine.
        forged = tmp / "forged_studio"
        shutil.copytree(output, forged)
        receipt_path = forged / "CHAT_RC_RECEIPT.json"
        receipt = json.loads(receipt_path.read_text("utf-8"))
        receipt["studio_status"] = "PASS"
        receipt_path.write_text(json.dumps(receipt) + "\n", "utf-8")
        expect_rejected("fake_Studio_PASS",
                        lambda: vr.audit(forged, PLAN),
                        "STUDIO_OR_LIVE_RELEASE_CLAIM_FORBIDDEN")

        # Negative 3: a forged duplicate role must fail even after an attacker
        # recalculates the advertised source-plan SHA256 in the receipt.
        bad_plan = tmp / "forged_plan.json"
        bad_receipt = tmp / "forged_authority"
        shutil.copytree(output, bad_receipt)
        plan_fake = json.loads(PLAN.read_text("utf-8"))
        one_owner = next(u for u in plan_fake["units"]
                         if u.get("authorities"))
        one_owner["authorities"] = ["round", "round", "damage"]
        bad_plan_bytes = (json.dumps(plan_fake, indent=2, ensure_ascii=False) +
                          "\n").encode("utf-8")
        bad_plan.write_bytes(bad_plan_bytes)
        receipt_path = bad_receipt / "CHAT_RC_RECEIPT.json"
        fake_rec = json.loads(receipt_path.read_text("utf-8"))
        fake_rec["source_plan_sha256"] = manifest_hash(bad_plan_bytes)
        receipt_path.write_text(json.dumps(fake_rec) + "\n", "utf-8")
        expect_rejected("duplicate_round_writer_authority",
                        lambda: vr.audit(bad_receipt, bad_plan),
                        "DUPLICATE_AUTHORITY_IN_UNIT")

        # Negative 4: true original PUBLIC_SOURCE_V1 forbids extra root keys.
        bad_source = tmp / "forged_source_manifest"
        shutil.copytree(SRC, bad_source)
        manifest_path = bad_source / "BUILD_MANIFEST.json"
        fake_manifest = json.loads(manifest_path.read_text("utf-8"))
        fake_manifest["studio_status"] = "PASS"
        manifest_path.write_text(json.dumps(fake_manifest) + "\n", "utf-8")
        expect_rejected("fake_manifest_extra_status",
                        lambda: vs.audit_source(bad_source),
                        "PUBLIC_SOURCE_MANIFEST_SCHEMA_MISMATCH")

        print(json.dumps({
            "format": "P0D_S1_INDEPENDENT_ACTUAL_COMPOSITE_QA_V1",
            "candidate_sha": SOURCE_COMMIT,
            "independent_checker_sha": AUDITOR_COMMIT,
            "result": "PASS_27_SOURCE_MANIFEST_18_ASSEMBLED_4_NEGATIVE_TESTS",
            "public_source_count": 27,
            "actual_assembled_source_units": 18,
            "negative_tamper_probes": 4,
            "authority_owners": rc_report["authority_declarations"],
            "rojo_mappings": rc_report["project_path_mappings_verified"],
            "receipt_sha256": manifest_hash(rec_content),
            "luau_native_parser": "NOT_TESTED",
            "real_2client_mobile_studio": "NOT_TESTED",
            "actual_release_rc_branch": "NOT_UPDATED_BY_THIS_TEST",
            "publish_approved": False
        }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
