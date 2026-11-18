# GQ8_SUBSEA_LEVIATHAN_MELEE_LOS_20261118

## True source defect / exclusive nonoverlap

Original author #764 Core34 / current formal private Core36 exact Realm
`EGGRUMBLE_RealmBattleCore.server.luau` loop has a 6HP melee attack by
SubseaLeviathan when a human diver is within 13 studs, but checks only distance.
No server LOS check precedes `h:TakeDamage(6)`, allowing the creature to
hit through solid coral, underwater walls and nearby castle geometry.
That violates distinct underground fight readability and low-HP fairness.

This is **not** #792 server LOS for dive/rise/fighter *station prompts*, #795
Realm client HUD, #788 LSS live bridge, original #518 StoneGiant shockwave,
#541 canonical ground Swarm or #775 natural player HP regen.

## Isolated game-source overlay

- Upstream #764 immutable HEAD `c51de1ed4feb7a7500ada95d21282402053ef988`.
- Locked original Git blob `1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1`.
- Patch ONE existing RealmBattleCore server source only. Before 6HP melee
  the server traces from the Leviathan to the diver's HumanoidRootPart;
  exclude creature and the diver avatar only, respect solid collision.
  Solid wall/reef blocks damage, and blocked melee **does not spend the
  2-second hit cooldown**, so it can connect after an obstacle clears.
- Preserves all boats, aircraft, storm, realm weapons, seven roles, castle,
  egg, ITEM, neutral Swarm, Combat, Remote, Store and score ownership.
- OFF reverses exactly to locked author file, no alternative Realm controller.

## Actual regression QA

The workflow tests exact pinned original source; 10 Python source-drifts and
negative mutations; generates and executes native Luau harness incorporating
the **actual selected helper and original-source melee branch**, including
coral/stone obstruction, cooldown, clear-space damage and missing avatar.
Compile original/selected/OFF native Luau; pinned Rojo 7.7.1 builds one
Script-class source ON/OFF with exact Source readback.

Native VM and Rojo are **not** 2-client Studio/Android/FUN evidence.

## Canonical integration protocol

Only B #220 authenticated CAS writer can compose this original-server
source overlay into the current official Core36; DO NOT separately replace
the #792 server prompt LOS change if B selected that parallel lane. Apply both
as **nonoverlapping anchored transformations of the same immutable original**
or ask for a composite source-locked candidate; preserve original31 and
original Realm other2 scripts, all Regen2 and Host, source+class exact,
Core36 ON/OFF31, same-head official CI and nonforce expected-SHA CAS.

No author ACK wait, no main merge/Publish/spend/Windows. Original Core36
contains 36 private sources; this patch replaces **one** existing source,
so source count stays **36**, FEATURE_CATALOG RC adoption remains unchanged.

Studio 2client, mobile 15min, first-play FUN, art are NOT_TESTED / NO_GO.
Rollback this one realm-server overlay to the original #764 author source
while retaining other accepted B features and original31 OFF profile.
