#!/usr/bin/env python3
"""Reversible *single Combat file* patch. Requires #531's host callback.

Do not edit #482/#529 author branches, #531 BotActors/Host or official RC.
"""
import argparse
import hashlib
import json
from pathlib import Path

AUTHOR_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
AUTHOR_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"
AUTHOR_PATH = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau"
HOST_DEPENDENCY = "#531 session.isCurrentHuman(player)"
COMBAT_NAME = "EGGRUMBLE_SevenRoleCombat.luau"

HELPER_ANCHOR = "local function hitHumanHeroes("
HELPER = '''-- #531 is the *only* host-side session-membership authority. Fail closed
-- if the prerequisite callback is absent, invalid, or throws.
local function currentHumanMember(session:any,player:Player):boolean
 if not session or not player then return false end
 local verify=session.isCurrentHuman
 if type(verify)~="function" then return false end
 local ok,allowed=pcall(verify,player)
 return ok and allowed==true
end
'''
HIT_OLD = "  if enemyPlayer~=p and enemyState and enemyState.alive\n"
HIT_NEW = HIT_OLD + "   and currentHumanMember(session,enemyPlayer)\n"
STATUS_OLD = "  if targetPlayer~=p and target and target.alive and enemyChar and enemyRoot and hum\n"
STATUS_NEW = STATUS_OLD + "   and currentHumanMember(session,targetPlayer)\n"
HEAL_OLD = "  if c and c.alive and char and otherRoot and h\n"
HEAL_NEW = HEAL_OLD + "   and currentHumanMember(session,other)\n"
CAST_OLD = ''' local owner=session.rules.castles[tostring(p.UserId)]
 if not owner or not owner.alive then return end
 if p:GetAttribute("EGGRUMBLE_Eliminated")==true then return end'''
CAST_NEW = ''' local owner=session.rules.castles[tostring(p.UserId)]
 if not owner or not owner.alive then return end
 if not currentHumanMember(session,p) then return end
 if p:GetAttribute("EGGRUMBLE_Eliminated")==true then return end'''

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def one(src: str, old: str, new: str, label: str) -> str:
    amount = src.count(old)
    if amount != 1:
        raise ValueError(f"RED {label}: expected one exact anchor, got {amount}")
    # A reverse patch's shorter replacement may already occur as a substring of
    # the longer exact anchor. The unique-anchor check above is authoritative.
    out = src.replace(old, new, 1)
    if out.replace(new, old, 1) != src:
        raise AssertionError(f"RED {label}: nonreversible")
    return out

CHANGES = (
    (HIT_OLD, HIT_NEW, "human damage"),
    (STATUS_OLD, STATUS_NEW, "human status"),
    (HEAL_OLD, HEAL_NEW, "mage human heal"),
    (CAST_OLD, CAST_NEW, "caster current session"),
)

def patch(original: str) -> str:
    if not original.startswith("--!strict\n"):
        raise ValueError("RED original must be strict Luau")
    if "local function currentHumanMember(" in original:
        raise ValueError("RED existing membership overlay: do not double-add")
    fixed = one(original, HELPER_ANCHOR, HELPER + HELPER_ANCHOR, "helper")
    for old, new, label in CHANGES:
        fixed = one(fixed, old, new, label)
    if fixed.count("currentHumanMember(") != 5:
        raise AssertionError("RED exactly one helper and four call sites required")
    if fixed.count("local function hitHumanHeroes(") != 1 or fixed.count("local function execute(") != 1:
        raise AssertionError("RED duplicate Combat implementation")
    if undo(fixed) != original:
        raise AssertionError("RED overlay fails byte-for-byte rollback")
    return fixed

def undo(fixed: str) -> str:
    out = fixed
    for old, new, label in reversed(CHANGES):
        out = one(out, new, old, f"rollback {label}")
    out = one(out, HELPER + HELPER_ANCHOR, HELPER_ANCHOR, "rollback helper")
    return out

def run(original_path: Path, out_dir: Path):
    data = original_path.read_bytes()
    observed = git_blob(data)
    if observed != AUTHOR_BLOB:
        raise ValueError(f"RED original Combat blob drift {observed}; expected {AUTHOR_BLOB}")
    raw = data.decode("utf-8")
    fixed = patch(raw)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / COMBAT_NAME
    target.write_bytes(fixed.encode("utf-8"))
    report = {
        "source_author_head": AUTHOR_HEAD,
        "source_author_blob": AUTHOR_BLOB,
        "patched_blob": git_blob(target.read_bytes()),
        "patched_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "original_recovered_by_off": undo(fixed) == raw,
        "changed_gameplay_files": [COMBAT_NAME],
        "dependent_host_callback": HOST_DEPENDENCY,
        "requires_source_selective_author_reconciliation": ["#529", "#531", "#510", "#516", "#524"],
        "official_rc_adopted": False,
        "studio_engine": "NOT_TESTED",
        "android_engine": "NOT_TESTED",
        "owner_accepted": False,
    }
    (out_dir / "GQ_HUMAN_COMBAT_LOCK.json").write_text(json.dumps(report, indent=2) + "\n")
    return report

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(run(args.original, args.out), ensure_ascii=False))
