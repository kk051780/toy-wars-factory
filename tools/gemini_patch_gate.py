#!/usr/bin/env python3
"""Independent, fail-closed review of an AI-generated patch. No data is uploaded in offline mode.

Online review is blocked by incident TWF-0006. The old direct provider transport bypassed
the shared budget ledger and has been removed. Offline parser tests do not approve a patch.
This is NOT the official gh-aw built-in threat detection; do not claim equivalence.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

MODEL="gemini-3.8-flash"
ONLINE_HOLD="LIVE_REVIEW_BLOCKED_TWF_0006_UNVERIFIED_INPUT_BOUND_AND_SHARED_BUDGET"
MAX_PATCH_BYTES=120000
ALLOWED_PREFIX=("src/","tests/","studio/","evidence/")
ALLOWED_EXACT={"docs/EXPERIMENT_LOG.md"}
FORBIDDEN_PATTERNS=(
    (r"(?i)(gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})","GitHub credential material"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----","Private key"),
    (r"(?i)\b(?:curl|wget)\b[^\n]{0,100}\|\s*(?:sh|bash)\b","Download and execute"),
    (r"(?i)\brm\s+-rf\s+(?:/|\$HOME|~)","Destructive shell"),
    (r"(?i)\b(?:GH_AW_DEFAULT_DETECTION|COPILOT_GITHUB_TOKEN|GEMINI_API_KEY)\s*=\s*['\"][^'\"]+","Hardcoded workflow credential"),
)

def _approved_path(path):
    """Reject traversal and ambiguous patch paths before prefix allowlisting."""
    if not path or "\\" in path or "\x00" in path or path.startswith("/"):
        return False
    if any(part in ("", ".", "..") for part in path.split("/")):
        return False
    return path.startswith(ALLOWED_PREFIX) or path in ALLOWED_EXACT


def check_patch(patch):
    if not isinstance(patch,str) or not patch.strip():
        return ["Missing/empty patch"]
    if len(patch.encode("utf-8"))>MAX_PATCH_BYTES:
        return ["Patch exceeds maximum reviewed size"]
    issues=[]
    if "GIT binary patch" in patch or "Binary files " in patch:
        issues.append("Binary diff not reviewable")

    # Git applies the --- / +++ file headers, not just the diff --git summary.
    # Validate every section and require these paths to agree before allowing it.
    blocks=re.split(r"(?=^diff --git )",patch,flags=re.MULTILINE)
    if not any(block.startswith("diff --git ") for block in blocks):
        issues.append("Missing diff file headers")
    for block in blocks:
        if not block.startswith("diff --git "):
            if block.strip():
                issues.append("Unexpected content outside diff sections")
            continue
        header=block.splitlines()[0]
        match=re.fullmatch(r"diff --git a/(\S+) b/(\S+)",header)
        if not match:
            issues.append("Malformed diff file header")
            continue
        src,dest=match.groups()
        if src!=dest:
            issues.append("Rename/move requires separate review")
        if not _approved_path(src) or not _approved_path(dest):
            issues.append("Change to unapproved path")
        lines=block.splitlines()
        for marker,expected in (("--- ","a/"+src),("+++ ","b/"+dest)):
            declared=[line[len(marker):] for line in lines if line.startswith(marker)]
            if len(declared)!=1 or declared[0] not in (expected,"/dev/null"):
                issues.append("Inconsistent patch file path")
        if any(line.startswith(("rename from ","rename to ","copy from ","copy to ")) for line in lines):
            issues.append("Rename/move requires separate review")

    plus_lines="\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++ "))
    for pattern,label in FORBIDDEN_PATTERNS:
        if re.search(pattern,plus_lines):
            issues.append(label)
    return issues

def scan_online(patch,api_key,transport=None):
    """Terminal compatibility entry point; arguments cannot unlock provider access."""
    raise RuntimeError(ONLINE_HOLD)


def parse_model_verdict(raw):
    """Validate synthetic/captured response bytes without transport or authorization."""
    obj=json.loads(raw)
    texts=[part.get("text","") for item in obj.get("candidates",[]) for part in item.get("content",{}).get("parts",[])]
    if len(texts)!=1:
        raise RuntimeError("MISSING_OR_AMBIGUOUS_SECURITY_VERDICT")
    try: verdict=json.loads(texts[0])
    except (ValueError,TypeError): raise RuntimeError("INVALID_SECURITY_VERDICT")
    if not isinstance(verdict,dict) or type(verdict.get("safe")) is not bool or not isinstance(verdict.get("reasons"),list):
        raise RuntimeError("INVALID_SECURITY_VERDICT_SCHEMA")
    if verdict["safe"] and verdict["reasons"]:
        raise RuntimeError("CONTRADICTORY_SECURITY_VERDICT")
    if any(not isinstance(reason,str) for reason in verdict["reasons"]):
        raise RuntimeError("INVALID_REASONS")
    return verdict

def save_safe_verdict(directory):
    """Emit gh-aw threat-detect-compatible host-side verdict only after both checks PASS."""
    target=Path(directory)/"detection_result.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    result={"prompt_injection":False,"secret_leak":False,"malicious_patch":False,"reasons":[]}
    tmp=target.with_suffix(".json.tmp")
    with tmp.open("w",encoding="utf-8") as fp:
        json.dump(result,fp,separators=(",",":"))
        fp.write("\n")
    os.chmod(tmp,0o600)
    tmp.replace(target)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--patch-dir",default="/tmp/gh-aw/threat-detection")
    parser.add_argument("--online",action="store_true")
    args=parser.parse_args()
    root=Path(args.patch_dir)
    # A verdict left by an earlier attempt must never survive this invocation.
    try:
        for name in ("detection_result.json","detection_result.json.tmp"):
            (root/name).unlink(missing_ok=True)
    except OSError:
        print("FAIL: cannot invalidate previous independent verdict")
        return 1
    if args.online:
        # Stop before opening the patch, reading a credential, or selecting transport.
        print("BLOCKED: "+ONLINE_HOLD)
        return 2
    file=root/"aw.patch"
    if not file.is_file():
        print("FAIL: expected patch artifact not found")
        return 1
    try: patch=file.read_text(encoding="utf-8")
    except (OSError,UnicodeError):
        print("FAIL: cannot read patch")
        return 1
    findings=check_patch(patch)
    if findings:
        print("FAIL static-review: "+", ".join(sorted(set(findings))))
        return 1
    print("PASS static-review: allowed diff paths and no obvious credential patterns")
    print("HOLD: static test alone is insufficient for publish; no provider call was made")
    return 0

if __name__=="__main__": sys.exit(main())
