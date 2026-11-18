# BATTLE-LEVEL-ITEMS / #765 lane 4 — isolated PREP

FEATURE_ID: BATTLE_LEVEL_ITEMS_20261118
CLAIM: #765 comment 6968380109. Base formal RC 261b75d0a7093db5c13db3b95dad9a2911f78689.
This is a REAL Luau server-side gameplay rule, **NOT YET wired to official V3 Host/Item and NOT RC-adopted**.

Seven real #482 role IDs receive a free usable Lv1 basic element with no gacha/payment:
WARRIOR=FIRE, MAGE=ICE, NINJA=WIND, TRAPPER=LIGHTNING, BUILDER=EARTH, BEAST=WATER, ZOMBIE=EARTH.
Lv milestones unlock distinct free elements. WARRIOR DIVINE Lv25 and ZOMBIE CURSE Lv20 are not instant permanent power. Temporary free world pickups grant one of eight elements: 24 seconds/two casts regular or 10 seconds/one cast DIVINE/CURSE. No paid dependency, no unrestricted upper-element superiority; actual damage math remains #766.

## Server hook contract for #220 ONLY
Existing authoritative Host+Item must create all context (serverOwned, activeMatch, currentAvatar, current session, role, level, monotonic now); it must NOT pass client-provided context, pickup registry or grants. Existing Item spawn must create registry[pickupId]={available=true,element=...,sessionId=...} on server; authenticated real touch calls issuePickup; it atomically marks that object consumed. Existing Combat must first accept a real skill cast and map a trusted skill ID to an attribute, then call authorizeAndConsume just once. Server maintains grants per player and clears them at round/leave/respawn boundaries; level progression remains under existing progression authority. No Remote/Store/HP/damage/score side channel; a policy flag OFF simply omits this module and preserves all original31 sources.

## QA and admission
Native workflow compiles the source and executes 7-role free starter tests, level final forms, pickup provenance, exactly-once use, cross-round/current-avatar, <= expiry and upper-item limits. Deliberate `<=` → `<` mutation MUST go RED. Negative engine/Android Studio runtime, true Item/Combat wiring and objective fairness remain separate.

**No permission to merge into main / publish / spend / write official RC.** Only authenticated #220 writer may combine this with #764/#775/#777/#778, reconcile future role/skill IDs, use expected-SHA nonforce CAS against latest official HEAD, run same-HEAD real31→32+ Native/Rojo Source-Class and OFF31 31 byte-exact, then verify readback. If another lane4 claim was created concurrently, reconcile by SOURCE/FEATURE_ID first and do not duplicate.
