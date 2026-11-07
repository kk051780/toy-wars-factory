#!/usr/bin/env python3
"""Deterministic policy/character QA. Does not claim Studio runtime coverage."""
from pathlib import Path
import json
import subprocess
import sys
import hashlib
from verify_status import status_ok
from system_character_pipeline import catalog_errors

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def record(label, ok):
    checks.append((label,bool(ok)))

state=json.loads((ROOT/"PROJECT_STATE.json").read_text(encoding="utf-8"))
chars=json.loads((ROOT/"config/characters.json").read_text(encoding="utf-8"))
policy=json.loads((ROOT/"config/quality_policy.json").read_text(encoding="utf-8"))
units=chars["characters"]
ids=[u["id"] for u in units]
character_failures=catalog_errors(chars,(ROOT/"src/ToyWarsBalance.lua").read_text(),policy["character_required"])
record("character_roster",not character_failures)
for key in policy["character_required"]:
    record("character_has_"+key,all(key in u and u[key] not in (None,"",[]) for u in units))
for key in ("combat_class","shape","color"):
    record("character_distinct_"+key,len(set(u[key] for u in units))==len(units))
record("policy_holds_release_unverified",policy["unverified_means_hold"] and policy["never_claim_studio_pass_without_evidence"])
record("state_does_not_claim_runtime_pass",state["verification"]["roblox_studio"]=="NOT_RUN")
record("state_does_not_claim_autonomous_worker",status_ok(state["autonomous_coding"],state["github"]["repository"]))
record("no_incorrect_game_completion",state["game"]["pvp"]=="NOT_IMPLEMENTED" and state["game"]["coop"]=="NOT_IMPLEMENTED")
record("canonical_balance_present",(ROOT/"src/ToyWarsBalance.lua").is_file())
record("original_balance_test_present",(ROOT/"tests/balance_spec.lua").is_file())
git=subprocess.run(["git","ls-files","-z"],cwd=ROOT,capture_output=True,check=True)
paths=[p.decode() for p in git.stdout.split(b"\0") if p]
interesting=[p for p in paths if p.endswith((".lua",".luau",".py",".json",".md",".yml",".yaml"))]
metrics={"tracked_files":len(paths),"tracked_source_and_docs":len(interesting),"tracked_bytes":sum((ROOT/p).stat().st_size for p in paths if (ROOT/p).is_file()),"balance_sha256":hashlib.sha256((ROOT/"src/ToyWarsBalance.lua").read_bytes()).hexdigest()}
failures=[n for n,ok in checks if not ok]
report={"status":"PASS_POLICY_ONLY" if not failures else "FAIL","checks":len(checks),"failed":failures,"metrics":metrics,"unverified":["Roblox Studio","Multiplayer","Visual character quality","Player fun/retention","Autonomous coding agent"]}
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(1 if failures else 0)
