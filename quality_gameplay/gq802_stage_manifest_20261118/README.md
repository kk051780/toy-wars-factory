# GQ802 | Dynamic World Stage Manifest — SOURCE-ONLY PREP
Feature: DW_STAGE_FACTORY_V1 | Owner requirement #802 | Upstream world #222 / local gravity #223 / Realm #764 | official intake #220

## What is **actually implemented**
- Pure server-side Luau function: validated 31-bit positive RNG seed, reproducible six-slot tile selection across center, two full land bypasses, sea, sky, fantasy pocket; 25 named prefab identifiers total, plus three seeded weather phases. No client reroll/seed selection API.
- Materialized **manifest data**, NOT a rendered 3D stage. Requires artist-authored compatible modular Roblox models and hookup to the current authoritative Host map builder and Realm weather. Existing egg/castle source remains untouched.
- Three full ground corridors, fixed upstream castles/eggs, recovery exit and no paid-only routes. Local gravity/time are **hints** only for existing/upcoming authority; no world clock or workspace.Gravity mutation.
- Deterministic test of 180 seeds, >=90 distinct layouts, all six fantastic themes, warning cues, replay determinism, invalid request rejection, hostile mutations, BR/TEAM, simultaneous human population cap 16.
- Source owns ZERO HP, status effect, weather physics, spawns, Remote, teleport, persistence or cosmetic models. "Server-side" means ONLY existing server can call build and keep the result; validation is not a cryptographic signature.

## Stage cell contract for next #220 integration
- Existing Host owns current Castle/Egg/round epoch and chooses stage seed once per match (not client-supplied); reserve/ticket maps to exactly one manifest.
- Existing MapBuilder owns pivot/real 3D prefab deployment and collision checks; no fall-through, overlap or objective-blocking; confirm **same** castle and egg positions/route distance for BOTH sides. Force legacy stage on failed asset lookup.
- CENTER/NORTH/SOUTH must have continuous ground traversal, SEA/SKY optional connectors and WONDER at edge; sky/sea never required to win. Map assets use StreamingEnabled/LOD and low-end Android VFX budget. Prefer artist geometry over piles of neon primitive parts.
- Existing Realm weather is one true controller. Seeded schedule is input, not a second storm server. Only #223 owns local gravity, and neither the player cooldown nor round clock is accelerated inside TIME.
- Rollback: Feature flag OFF means no module loaded or new tiles spawned; original Core36 and 31 sources remain byte-exact. No direct RC CAS from this candidate branch.

## Source and acceptance progress
A Pure Luau policy: authored; Native CI to verify after PR.
B Physical tile prefab assembly: NOT IMPLEMENTED.
C Sole #220 official RC integration and same HEAD Luau/Rojo/source-lock/OFF: NOT IMPLEMENTED.
D Real matchmaking: NOT IMPLEMENTED; issue #802 specification only.
E Player status VFX/control and F item model/drops/long-fight gameplay: NOT IMPLEMENTED in this PR; existing #765/#801/#764 lanes are kept separate.
G Studio/2player Android15m/retention/FUN: NOT TESTED.
Do not present this isolated policy as a live in-game stage or 1/7 finished gameplay.
