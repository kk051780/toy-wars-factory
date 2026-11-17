#!/usr/bin/env python3
"""Execute the *actual* pure Luau module with standalone Luau CLI (no mocked Roblox)."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_ElementAffinityPolicy.module.luau"
ELEMENTS = ("FIRE", "WATER", "LIGHTNING", "WIND", "EARTH", "ICE", "DIVINE", "CURSE")
CYCLE = {
    "FIRE": "ICE", "ICE": "WIND", "WIND": "EARTH",
    "EARTH": "LIGHTNING", "LIGHTNING": "WATER", "WATER": "FIRE",
}


def oracle(a: str, d: str) -> tuple[float, str]:
    # Independent spec oracle, deliberately not extracted from the ModuleScript.
    if a == d:
        return (0.65, "STRONG_RESISTANCE")
    if {a, d} == {"DIVINE", "CURSE"}:
        return (1.25, "MUTUAL_COUNTER")
    if CYCLE.get(a) == d:
        return (1.25, "ADVANTAGE")
    if CYCLE.get(d) == a:
        return (0.80, "RESISTED")
    return (1.00, "NEUTRAL")


def build(mutant: bool = False) -> str:
    original = SOURCE.read_text(encoding="utf-8")
    marker = "\nreturn Policy\n"
    if original.count(marker) != 1:
        raise ValueError("RED_EXPECT_EXACT_ONE_POLICY_RETURN")
    if mutant:
        target = "if CYCLE[attack] == defend then"
        if original.count(target) != 1:
            raise ValueError("RED_MUTANT_TARGET_NOT_UNIQUE")
        original = original.replace(target, "if false and CYCLE[attack] == defend then", 1)
    body = original.replace(marker, "\nlocal P = Policy\n", 1)
    lines = ["-- Source-derived native 64 matchups + adversarial behavior tests"]
    for a in ELEMENTS:
        for d in ELEMENTS:
            mult, outcome = oracle(a, d)
            lines.extend([
                "do",
                f'  local m, label = P.resolve("{a}", "{d}")',
                f'  assert(m == {mult:.2f} and label == "{outcome}", "MATCHUP_FAIL_{a}_{d}")',
                "end",
            ])
    lines += [
        'assert(P.VERSION == "GQ8_ELEMENT_POLICY_V1", "VERSION_FAIL")',
        'assert(P.isKnown("FIRE") and P.isKnown("DIVINE"), "KNOWN_FAIL")',
        'assert(not P.isKnown("fire") and not P.isKnown(nil), "UNKNOWN_FAIL")',
        'local absent, neutral = P.resolve(nil, nil)',
        'assert(absent == 1 and neutral == "NEUTRAL", "LEGACY_NIL_FAIL")',
        'local empty, neutral2 = P.resolve("NONE", "FIRE")',
        'assert(empty == 1 and neutral2 == "NEUTRAL", "NONE_NEUTRAL_FAIL")',
        'local badA, whyA = P.resolve("fire", "ICE")',
        'assert(badA == nil and whyA == "INVALID_ATTACK_ELEMENT", "FORGED_ATTACK_FAIL")',
        'local badD, whyD = P.resolve("FIRE", {})',
        'assert(badD == nil and whyD == "INVALID_DEFENSE_ELEMENT", "FORGED_DEFENSE_FAIL")',
        'local n, tag = P.scaleDamage(20, "FIRE", "ICE")',
        'assert(n == 25 and tag == "ADVANTAGE", "DAMAGE_SCALE_FAIL")',
        'local same, sameTag = P.scaleDamage(20, "FIRE", "FIRE")',
        'assert(same == 13 and sameTag == "STRONG_RESISTANCE", "SAME_RESIST_FAIL")',
        'local zero = P.scaleDamage(0, "DIVINE", "CURSE")',
        'assert(zero == 0, "NO_FORCED_MINIMUM_DAMAGE_FAIL")',
        'local nan = 0/0',
        'local invalid1, reason1 = P.scaleDamage(nan, "FIRE", "ICE")',
        'assert(invalid1 == nil and reason1 == "INVALID_BASE_DAMAGE", "NAN_FAIL")',
        'local invalid2, reason2 = P.scaleDamage(-5, "FIRE", "ICE")',
        'assert(invalid2 == nil and reason2 == "INVALID_BASE_DAMAGE", "NEGATIVE_FAIL")',
        'local invalid3, reason3 = P.scaleDamage(100001, "FIRE", "ICE")',
        'assert(invalid3 == nil and reason3 == "INVALID_BASE_DAMAGE", "OVERSIZE_FAIL")',
        'local invalid4, reason4 = P.scaleDamage(10, "FIRE", "fake")',
        'assert(invalid4 == nil and reason4 == "INVALID_DEFENSE_ELEMENT", "SCALE_SPOOF_FAIL")',
        'print("BATTLE_ELEMENT_RULES_NATIVE_64_MATCHUPS_PLUS_NEGATIVE_PASS")',
    ]
    return body + "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--mutant", required=True)
    args = parser.parse_args()
    Path(args.out).write_text(build(), encoding="utf-8")
    Path(args.mutant).write_text(build(mutant=True), encoding="utf-8")


if __name__ == "__main__":
    main()
