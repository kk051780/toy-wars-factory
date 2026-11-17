# BATTLE-HP-REGEN / GQ8 | nonoverlap candidate
OWNER: #765 lane 7. Source: PassiveRegenPolicy.luau (pure ModuleScript candidate).
Based on official private RC `261b75d0a7093db5c13db3b95dad9a2911f78689`. No modifications to existing Game, Combat, Host, Score, Store, Remote, Swarm, BotActors or RealmCore.

## Behavior
- Seven free starting classes, HP: WARRIOR 250, MAGE 195, NINJA (Assassin) 185, TRAPPER 205, BUILDER 225, BEAST_TAMER 220, ZOMBIE_MASTER 230.
- After seven continuous seconds without **actual server-observed HP decrease** and while alive, in current match, not downed, and without active DOT: passive recovery at 0.7% MaxHP per second. Frames are capped to 0.5 s to prevent AFK/lag catchup.
- Round ID, health cap change, stale clock or lobby transition cannot carry regen into a new session. Incoming heal never counts as incoming damage. Natural regen does **not** implement Mage burst heal or revival.
- The policy only computes heal delta. Existing canonical HP authority must call `step` with server-owned clock, current-match token, HP/MaxHP and DOT/downed flags and apply the returned delta in its **existing** health write path. No new RemoteEvents, Health writers, Store, Game, or Role identifiers.

## Gate
`python3 -m unittest discover -v -s handoffs/EGGRUMBLE-HP-REGEN-20261118` then pinned native Luau good + forced 0s-delay mutant (must RED). Original31/RC untouched. Studio/Android not claimed.
Required adoption next: original31 exact rehydrate; one-owned Game/Combat/Host adapter, ON/OFF byte-identical rollback, real Native + Rojo classes/sources, feature flag default ON in *private gameplay*; #220 authenticated expectedSHA nonforce CAS; same-HEAD RC success. Until then SOURCE_PREP and RC_NOT_INTEGRATED.
RED: duplicate HP authority, client provided clock, stale session, source overwrite, failed CI.
YELLOW: untested 30fps/15min Android FUN, character balancing and attacks-to-kill; keep tracker tickets.
main, publish and paid actions forbidden.
