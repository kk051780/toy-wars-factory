# GQ8 LSS detached-world lifecycle — independent source candidate

FEATURE_ID=GQ8_LSS_SCENE_DETACH_RETIRE_20261118
OWNER_SCOPE=One existing Studio-only optional32 LandSeaSkyTraversal Script
STACKED_AFTER=PR #772 (idle craft lease + latest high-air dismount rescue)
PARENT_SHA_RECHECK=d2c01ff5b6a7c90e9ee93ad268e689580781d16a
PARENT_LSS_BLOB=440bf7fb00b4a67d565603d973d1e84de5c30f4d
COMPOSED_LSS_BLOB=c0b6b420ae588e2facb22caa793397356c2e8246
NO_DUPLICATE_RUNTIME_SCRIPT=YES
FORMAL_RC_ADOPTED=NO; P0D_PREP_READY_V1=SOURCE_QA_PENDING
SOURCE_LOCK=Update both optional32 JSON source blob references to current candidate
ROLLBACK=Omit optional32 for exact canonical31, or revert ONLY this lifecycle hunk

## Verified code defect
The pre-fix Heartbeat disconnected itself when the arena world was unparented,
while PlayerAdded, PlayerRemoving and per-player attribute listeners remained
alive. scenes[world] continued to claim ownership and the visual scene remained
attached to the world. Later reparenting could leave stale visuals and prevent
clean reinstall. Destroying cleans these, but reparenting is not Destroying.

## Actual patch
One idempotent retireScene function shared by world.Destroying and the detached
world/scene Heartbeat edge. It releases observer connections, player state,
craft activity and scenes[world]; on detach (not wholesale world Destroying)
it also destroys the obsolete visual child. Guard rejects parent-not-LOBBY,
not-descendant-of-Workspace and detached scene. No new Game, Combat, HP,
Store, Remote, KO, XP, boss, field-item or AI writer. Optional32 still
Studio-only; none of 31 canonical source files changed.

## Gates
Actual Luau helper extracted into native 7-case harness with 3 deliberately
broken guard mutants required RED, full optional32 native syntax, Python source
tests, and latest original31->optional32+OFF31 Rojo before #220 can intake.
Any original-source drift, failed test, or newer formal head invalidates older
receipt. Studio 2 clients, low-end Android 15m, art and fun remain NOT_TESTED.
#220 is the sole authenticated nonforce expected-SHA formal RC writer.
No main, release, purchases, billing changes or force pushes.

## Residual world signal repair
Detached worlds also disconnect the original world.Destroying connection itself,
so old reparented worlds cannot retain per-round observation closures.
