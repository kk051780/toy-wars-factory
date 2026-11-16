# GQ V3 current-match ownership of own-castle egg deposit

FEATURE_ID: GQ-V3-OWN-DEPOSIT-CURRENT-SESSION-FENCE-20261116

A real source defect exists in original #482 single Host. Its OwnEggDeposit callback validates owner ID and non-nil match rules, but not that the player still belongs to this game mode and that the original session object is the current one. The patch adds those two required checks before the original Rules.depositEggs call. The existing sole Rules authority, deposit HUD refresh (#537), castle models, item pickups, bot routing, and score stay unchanged.

Immutable original #482 source HEAD: fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9
Exact original Host Git blob: 7162b209bf67b74a71553217f3f744e072a0365d
Official RC HEAD at initial branch creation: 62ee101ded97f8b2f9e983d846053a782e00df9e

Nonoverlap: not #537 egg-deposit GUI refresh, #523 egg topology, #583 roster hardcap, #571/#518 StoneGiant, #489/#517 item, #508 neutral KO, #581 receipt, #544 lobby timer or #568 balance median. One existing Host callback only; no added Game/Combat/Remote/Store/HP/XP/SCORE authority.

The GitHub workflow checks 12 Python negative/rollback tests, immutable #482 Git blob lock, changed Host Luau native compile and seven actual source-derived Luau cases: valid current player, old wrong-mode player, stale same-mode session, wrong castle owner, missing rules, valid return and departed player. Original predicate deliberately passes two stale-case negative differentials; new one must reject both. Inverse selection restores the original source byte-for-byte.

Status: DRAFT / isolated actual Luau source selector; no official RC write or Studio/Android/OWNER approval. After native tests pass, original's ACK is not a blocker; B #220, the sole authenticated RC writer, must re-fetch fresh official HEAD, source-select this delta in the accepted single Host after prior #537/#551/#523, prove 30/31 other original scripts exact, native/Rojo31 full source lock and rollback, nonforce expected-HEAD CAS, new same-HEAD Actions and Studio Place/ZIP receipts. If RED abort without forced merge. No main, Roblox publish, payment or Windows activity.

OFF: disable this selector, restore exact current accepted Host source; retain all unrelated 30 canonical scripts.