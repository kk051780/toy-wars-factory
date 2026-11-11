#!/usr/bin/env python3
"""S1 independent current 28-file game candidate gate: native Luau + real assembly.

Read-only against immutable source. No Studio, no Roblox Place deployment.
The Python and native compiler are independent validators: no fake engine PASS.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SOURCE_ROOT = REPO / "handoffs/P0D-S1-D07D08-SPATIAL-LOBBY-COMPOSITE-20261112-01"
SOURCE = SOURCE_ROOT / "candidate"
PLAN = SOURCE_ROOT / "SOURCE_PLAN_LOBBY.json"
EXPECTED_RECEIPT = SOURCE_ROOT / "CHAT_RC_RECEIPT.json"
ASSEMBLER = REPO / "handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/tools/chat_rc_assemble.py"
VENDOR = ROOT / "vendor"
sys.path.insert(0, str(VENDOR))
import verify_rc_wiring as vr
import verify_source_snapshot as vs

GAME_SHA = "9de6496282c7bd4dcea586563f75da71d08d77ec"
LUAU_SHA = "f46d879e28302a430029304f7f6a162aed66f103"
EXPECTED_MANIFEST = 28
EXPECTED_UNITS = 19
EXPECTED_SOURCES = 18


def require(ok: bool, why: str) -> None:
    if not ok:
        raise RuntimeError("INDEPENDENT_28_SOURCE_GATE_FAIL:" + why)


def reject(name, call, prefix):
    try:
        call()
    except vr.QAError as exc:
        require(str(exc).startswith(prefix), name + " wrong reason: " + str(exc))
        print("EXPECTED_NEGATIVE_PASS:" + name + ":" + str(exc), flush=True)
        return
    raise RuntimeError("FAIL_OPEN_NEGATIVE:" + name)


def compile_one(compiler: Path, file: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(compiler), "-O0", str(file)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        text=True, timeout=45, check=False)


def native_compile(compiler: Path) -> None:
    require(compiler.is_file(), "official Luau compiler missing")
    luau = sorted((SOURCE / "src").rglob("*.luau"))
    require(len(luau) == EXPECTED_SOURCES, "native source count mismatch")
    require(all(p.is_file() and not p.is_symlink() for p in luau),
            "nonregular Luau input")
    with tempfile.TemporaryDirectory(prefix="p0d_native_controls_") as d:
        good, bad = Path(d) / "good.luau", Path(d) / "bad.luau"
        good.write_text("local function f(x: number): number\n  return x + 1\nend\nreturn f(1)\n")
        bad.write_text("local =\n")
        require(compile_one(compiler,good).returncode == 0, "official good control failed")
        require(compile_one(compiler,bad).returncode != 0, "official invalid control incorrectly passed")
        print("P0D_NATIVE_LUAU_POSITIVE_NEGATIVE_CONTROLS_PASS",flush=True)
    for n, f in enumerate(luau, 1):
        result = compile_one(compiler, f)
        require(result.returncode == 0,
                "native compile failure " + str(f.relative_to(SOURCE)) + ": " +
                result.stderr[-1700:])
        print(f"NATIVE_LUAU_PASS:{n}/{EXPECTED_SOURCES}:{f.relative_to(SOURCE)}",flush=True)


def main(args: list[str]) -> int:
    require(len(args) == 1, "usage runner.py <official-luau-compile>")
    require(SOURCE.is_dir() and PLAN.is_file() and EXPECTED_RECEIPT.is_file(),
            "missing pinned candidate")
    public = vs.audit_source(SOURCE)
    require(public["studio_2client_mobile"] == "NOT_TESTED",
            "false engine status in source")
    manifest = json.loads((SOURCE / "BUILD_MANIFEST.json").read_text("utf-8"))
    plan = json.loads(PLAN.read_text("utf-8"))
    require(len(manifest["files"]) == EXPECTED_MANIFEST, "manifest count changed")
    require(len(plan["units"]) == EXPECTED_UNITS, "source unit count changed")
    game = (SOURCE / "src/server/Game.server.luau").read_text("utf-8")
    lobby = (SOURCE / "src/server/LobbyTeamRecovery.luau").read_text("utf-8")
    require('require(script.Parent:WaitForChild("LobbyTeamRecovery"))' in game,
            "lobby module not wired")
    require("rebalanceLobbyTeams" in game and "LobbyTeamRecovery" in lobby,
            "team deadlock recovery not retained")
    require("CANONICAL_S1_ENABLED = false" in game and
            "D07_D08_RELEASE_REVIEW_APPROVED = false" in game,
            "canonical gameplay enabled without review")
    require(game.count("remote.OnServerEvent:Connect(") == 1,
            "more than one client authority")
    host = (SOURCE / "src/server/S1CanonicalRoundHost.luau").read_text("utf-8")
    binding = (SOURCE / "src/server/S1GoroganLiveBindings.luau").read_text("utf-8")
    require('self.reason == "EVENT_FINISHED"' in host and
            'playerId:match("^%-?%d+$")' in binding,
            "reviewed D08 and Studio test ID fixes missing")
    authority = [x for x in plan["units"] if x.get("authorities")]
    require(len(authority) == 1 and
            set(authority[0]["authorities"]) == {"round","event_chooser","damage"} and
            authority[0]["target_path"] == "src/server/Game.server.luau",
            "second round/event/damage source declared")
    print("P0D_PUBLIC_SOURCE_28_OF_28_PASS",flush=True)

    # Native syntax/bytecode compilation of the real 18-game-source candidate.
    native_compile(Path(args[0]).resolve())

    with tempfile.TemporaryDirectory(prefix="p0d_independent_28_") as name:
        work = Path(name)
        assembled = work / "assembly"
        p = subprocess.run([sys.executable, str(ASSEMBLER),
                            "--plan", str(PLAN), "--source-root", str(SOURCE),
                            "--out", str(assembled)],
                           cwd=str(REPO), capture_output=True, text=True,
                           timeout=120, check=False)
        require(p.returncode == 0, "original assembler error: " +
                p.stderr[-1500:] + p.stdout[-1500:])
        receipt = (assembled / "CHAT_RC_RECEIPT.json").read_bytes()
        require(receipt == EXPECTED_RECEIPT.read_bytes(), "receipt exact bytes mismatch")
        report = vr.audit(assembled, PLAN)
        require(report["result"] == "PASS_SOURCE_WIRING_ONLY" and
                report["source_files_verified"] == EXPECTED_UNITS and
                report["studio_2client_mobile"] == "NOT_TESTED",
                "native source/receipt auditor rejected actual assembly")
        print("P0D_REAL_PYTHON_19_UNIT_ASSEMBLY_RECEIPT_PASS",
              hashlib.sha256(receipt).hexdigest(),flush=True)

        broken = work / "tampered"
        shutil.copytree(assembled, broken)
        with (broken / "src/server/Game.server.luau").open("ab") as f:
            f.write(b"\n-- mutated source\n")
        reject("tamper_game", lambda: vr.audit(broken, PLAN), "CONTENT_BYTES_MISMATCH")

        fake = work / "false_studio"
        shutil.copytree(assembled, fake)
        file = fake / "CHAT_RC_RECEIPT.json"
        d = json.loads(file.read_text("utf-8"))
        d["studio_status"] = "PASS"
        file.write_text(json.dumps(d) + "\n", "utf-8")
        reject("false_studio_pass",lambda: vr.audit(fake, PLAN),
               "STUDIO_OR_LIVE_RELEASE_CLAIM_FORBIDDEN")

        bogus_plan = work / "duplicate_authority_plan.json"
        duplicate = work / "duplicate_authority"
        shutil.copytree(assembled,duplicate)
        doc=json.loads(PLAN.read_text("utf-8"))
        sole = next(u for u in doc["units"] if u.get("authorities"))
        sole["authorities"]=["round","round","damage"]
        raw=(json.dumps(doc,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
        bogus_plan.write_bytes(raw)
        file=duplicate/"CHAT_RC_RECEIPT.json"
        receipt_fake=json.loads(file.read_text("utf-8"))
        receipt_fake["source_plan_sha256"]=hashlib.sha256(raw).hexdigest()
        file.write_text(json.dumps(receipt_fake)+"\n","utf-8")
        reject("duplicate_round",lambda: vr.audit(duplicate,bogus_plan),
               "DUPLICATE_AUTHORITY_IN_UNIT")

        bad_manifest=work/"false_source_manifest"
        shutil.copytree(SOURCE,bad_manifest)
        file=bad_manifest/"BUILD_MANIFEST.json"
        manifest_fake=json.loads(file.read_text("utf-8"))
        manifest_fake["studio_status"]="PASS"
        file.write_text(json.dumps(manifest_fake)+"\n","utf-8")
        try:
            vs.audit_source(bad_manifest)
        except Exception as exc:
            require("PUBLIC_SOURCE_MANIFEST_SCHEMA_MISMATCH" in str(exc),
                    "unexpected manifest rejection " + str(exc))
            print("EXPECTED_NEGATIVE_PASS:extra_public_manifest_status",flush=True)
        else:
            raise RuntimeError("FAIL_OPEN_EXTRA_PUBLIC_STATUS")

        print(json.dumps({
            "format":"P0D_S1_28_SOURCE_NATIVE_AND_INDEPENDENT_ASSEMBLY_V1",
            "result":"PASS_NATIVE_LUAU_18_AND_SOURCE_28_ASSEMBLY_19",
            "source_game_commit":GAME_SHA,
            "official_luau_source_commit":LUAU_SHA,
            "luau_compiled":EXPECTED_SOURCES,
            "manifest_sha256_verified":EXPECTED_MANIFEST,
            "assembler_units":EXPECTED_UNITS,
            "negative_faults_rejected":4,
            "receipt_sha256":hashlib.sha256(receipt).hexdigest(),
            "real_studio_2client":"NOT_TESTED",
            "gameplay_release_approved":False,
            "official_release_rc_updated":False
        },sort_keys=True),flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
