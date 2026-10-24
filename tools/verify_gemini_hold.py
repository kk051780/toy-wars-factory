#!/usr/bin/env python3
"""Check a literal incident hold in authored and compiler-validated workflow files.

This narrow, standard-library check is not a general YAML parser or financial-cap
certification. The pinned official compiler independently validates the workflow.
"""
import argparse
import json
from pathlib import Path
import re


def verify_hold(root):
    workflows = Path(root) / ".github/workflows"
    source = (workflows / "twf-gemini-free-trial.md").read_text(encoding="utf-8")
    compiled = (workflows / "twf-gemini-free-trial.lock.yml").read_text(encoding="utf-8")
    frontmatter = source.split("---", 2)[1]
    if re.findall(r"^if:\s*(.*?)\s*$", frontmatter, re.MULTILINE) != ["${{ false }}"]:
        raise ValueError("authored workflow must contain one literal false hold")
    jobs_text = compiled.split("\njobs:\n", 1)[1]
    headers = list(re.finditer(r"^  ([a-z_]+):\s*$", jobs_text, re.MULTILINE))
    jobs = {match[1]: jobs_text[match.end():headers[i + 1].start() if i + 1 < len(headers) else len(jobs_text)] for i, match in enumerate(headers)}
    if set(jobs) != {"pre_activation", "activation", "agent", "detection", "safe_outputs", "conclusion"}:
        raise ValueError("unexpected compiled jobs require independent hold review")
    if re.findall(r"^    if:\s*(.*?)\s*$", jobs["pre_activation"], re.MULTILINE) != ["${{ false }}"]:
        raise ValueError("pre_activation must contain one literal false hold")
    # Existing downstream needs/conditions must remain. No provider job is independent.
    for name, parent in (("activation", "pre_activation"), ("agent", "activation")):
        if not re.search(r"^    needs: " + parent + r"\s*$", jobs[name], re.MULTILINE):
            raise ValueError(name + " must depend on held " + parent)
        conditions = re.findall(r"^    if:\s*(.*?)\s*$", jobs[name], re.MULTILINE)
        if len(conditions) != 1 or re.search(r"\b(?:always|cancelled|failure)\s*\(", conditions[0]) or "||" in conditions[0]:
            raise ValueError(name + " must preserve dependency success gating")
        if name == "activation" and "needs.pre_activation.outputs.activated == 'true'" not in conditions[0]:
            raise ValueError("activation must require a successful held pre_activation")
    for name in ("detection", "safe_outputs"):
        if not re.search(r"^      - agent\s*$", jobs[name], re.MULTILINE):
            raise ValueError(name + " must depend on held agent")
        conditions = re.findall(r"^    if:\s*(.*?)\s*$", jobs[name], re.MULTILINE)
        if len(conditions) != 1 or "needs.agent.result != 'skipped'" not in conditions[0]:
            raise ValueError(name + " must reject a skipped agent")
    if "GEMINI_API_KEY" in jobs["conclusion"]:
        raise ValueError("conclusion must not have Gemini credential access")
    return {"status": "PASS_OFFLINE_HOLD_ONLY", "workflow_pre_activation": "LITERAL_FALSE", "provider_calls": 0, "live_authorized": False, "financial_cap_certified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(verify_hold(args.root), indent=2))
