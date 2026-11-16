# GQ-V3 stale-avatar carrier Died fence — 2026-11-16
Author fixed source #482 `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`; exact original Host Git blob `7162b209bf67b74a71553217f3f744e072a0365d`.

## Source-confirmed unique bug
During the SAME active TEAM or BR match, the Host subscribes to every successive Humanoid.Died on CharacterAdded. A delayed Died on an obsolete character can call `session.dropCarrierEggs` against the **new live avatar's owner-held eggs**, because the original listener checks only `joined[player.UserId]~=mode`. Egg token conservation cannot distinguish which avatar died.

## Minimal real behavior correction
Exactly one existing original Host callback is modified *only in an isolated composer*, without changing #482 author code in Git. Require current mode, session identity, exact current `player.Character==character`, and ACTIVE phase; otherwise do not drop. Original other20 mapped Luau remain byte-identical. OFF selects exact original Host blob.

Not duplicated with #509 (post-FINISHED egg token mutations), #540 (Assassin stealth inherited on respawn), #506 (respawn forcefield), #515 (field egg ground recovery), #543 (DASH expiry), #544 (lobby queue) or #547/#539 (world text).

## Independent hard evidence
Run 12 source/negative Python regressions, **native Luau executing actual Host Died callback** over seven cases, all 21 original sources Native parse, and checksum-pinned Rojo original21 Source/Class exact private Place. Same-HEAD workflow must complete SUCCESS before marking source candidate ready. No new Game/Remote/Score/Store/HP/Items/AI/Art authority.

## Integration
#220 is the sole authenticated CAS RC writer. Recheck latest official 31-source V3 companion and source-lock, compose only this Died callback with original #484/#531/#537/#540/#544 changes, preserving all other 8 domains, rerun same-HEAD Native/Rojo/Place/ZIP and ledger ACK. Individual old-author replies are not a stop condition; the exclusive authentic RC writer and RED gates are mandatory.

**State**: DRAFT / source-only private / #218 SOFT_CLAIM_NOT_GRANTED / official RC uptake 0 / Studio+Android+#420+OWNER NO_GO. No main, unauthorized merge, Publish, Windows, or spending.
