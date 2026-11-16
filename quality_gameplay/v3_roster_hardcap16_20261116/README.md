# Unique GQ V3: original 16-player roster hard cap

Existing original-author [#482](https://github.com/kk051780/toy-wars-factory/pull/482)
CastleMatchRules defines MAX_HERO_SLOTS=16, and the 16-player TEAM/BR mode is
specified in #219/#470. However, the same original Luau allowed maxSlots<=32
in makeRoster and #roster<=32 in new. A 17/32-player scenario could therefore
bypass the declared cap (AI/individual castle/performance and fairness drift).

This isolated source selector locks immutable #482 HEAD
fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9 and original Git blob
27da5ca1e9e6d9a7afe0674030e387f094ee7492.
It changes exactly two guards in the SAME CastleMatchRules ModuleScript:
both become <=M.MAX_HERO_SLOTS. Existing 1-16 player behavior, TEAM/BR,
egg, castle, neutral, item, combat and lobby implementations are unmodified.
The selector never introduces another Game, Remote, Store, or service.

Dedicated real Luau differential executes original and patched sources:
a valid 16-slot TEAM roster and 16 individual BR castles both still start,
while the original allows and the patch rejects 17 and 32 makeRoster slots
and a 17-person Royale new() call. Python mutation regression tests,
exact changed-source pinning, and inverse rollback are included.

Current status is SOURCE candidate, NOT official RC adoption. It is not a
second feature writer, not an owner-approved test, not full RC31 Rojo proof.
B #220 must source-select this one existing CastleMatchRules module only,
preserve 30 other canonical sources byte-exact, verify actual current
31-source native+Rojo/project/Place and latest HEAD nonforce CAS, then
Studio/Android/#420 FUN/OWNER acceptance. Original author ACK is not needed.

Rollback: selector OFF is bit-exact original #482 CastleMatchRules;
delete only scoped source-selection QA/workflow files for full branch rollback.
main, ordinary merge, Roblox publish, paid operations and Windows untouched.
