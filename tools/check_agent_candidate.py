"""Guardrail checker for pre-activation agentic workflow (no model inference)."""
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/".github/workflows/twf-autonomous-developer.md").read_text(encoding="utf-8")
lock=(ROOT/".github/workflows/twf-autonomous-developer.lock.yml").read_text(encoding="utf-8")
checks={
    "gh_aw_generated":lock.startswith("# gh-aw-metadata:"),
    "scheduler_20_minutes":'8,28,48 * * * *' in source and '8,28,48 * * * *' in lock,
    "max_run_ai_credits":re.search(r"(?m)^max-ai-credits:\s*25\s*$",source) is not None and 'GH_AW_MAX_AI_CREDITS: "25"' in lock,
    "daily_ai_credits":re.search(r"(?m)^max-daily-ai-credits:\s*100\s*$",source) is not None and 'GH_AW_MAX_DAILY_AI_CREDITS: "100"' in lock,
    "max_turns":re.search(r"(?m)^max-turns:\s*20\s*$",source) is not None,
    "timeout":re.search(r"(?m)^timeout-minutes:\s*16\s*$",source) is not None,
    "draft_pr":re.search(r"(?m)^\s+draft:\s*true\s*$",source) is not None,
    "max_one_pr":re.search(r"(?m)^\s+max:\s*1\s*$",source) is not None,
    "protected_files_blocked":re.search(r"(?m)^\s+protected-files:\s*blocked\s*$",source) is not None,
    "no_main_qa_rule_write":all(x in source for x in ["allowed-files:","src/**","tests/**","studio/**","evidence/**"]),
    "no_main_security_write":all(x not in source for x in ["- '.github/**'","- 'config/quality_policy.json'","- 'AGENTS.md'"]),
    "explicit_no_publishing":("never merge, release, monetize" in source)
}
for k,v in checks.items():
    print(("PASS " if v else "FAIL ")+k)
if not all(checks.values()):
    sys.exit(1)
print("GUARD_PASS",len(checks),"static criteria; no AI model invoked")
