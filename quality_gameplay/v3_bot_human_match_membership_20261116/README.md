# GQ-V3-BOT-HUMAN-MEMBERSHIP — isolated unique product fix

**Scope:** #470 product-quality writer; #218 soft-claim request **PENDING**, #482 original-author ACK **PENDING**, #220 only officially authenticated RC writer. No main, author PR, official RC, payment or Roblox publish edits.

## Real, source-derived defect / not a duplicate

Frozen original [#482](https://github.com/kk051780/toy-wars-factory/pull/482) HEAD
`fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`:
- `EGGRUMBLE_BotActors.luau`, Git blob `fa38f24a26a619238e4c6a62b3ee582dc14cfe7a`.
- `EGGRUMBLE_LobbyCastleModesPreview.server.luau`, Git blob `7162b209bf67b74a71553217f3f744e072a0365d`.

In `tryHeroAttack`, a bot checks target UserId in its match's **castle roster**, alive castle, team, actual distance, wall LOS and stealth. It does **not** check whether this **currently connected Player is still a human participant of this session and mode**. In the author host a disconnected human castle can remain alive under bot takeover; if that UserId reconnects or joins the other mode and physically enters the old arena, an original bot can wrongly damage the nonparticipant because a stale castle ID still exists. This is a **session-membership/fairness** guard, not new attack damage, combat power or an extra bot.

Specific distinct source scopes already owned by other chats:
- #525 item mode/ownership; #529 assassin human combat; #502 carried-egg bot targeting;
- #527 siege pacing; #508 neutral KO attribution; #516 DOT expiry; #489 item balance;
- #482 owns all game systems, #484 composites original AI, #485 ART, #487 score.
**This change only guards the existing bot-to-human HP hit when targeting a Player.** It never alters other authors' Luau directly.

## Exact implementation

`compose.py` loads original **two real Luau source files** by file content, verifies their frozen Git blob SHA1, and applies exactly:
1. Host adds `session.isCurrentHuman(player)` callback reading its own **server-only** `joined[UserId]`, exact session reference, ACTIVE phase, live Player parent and current castle roster.
2. Bot `tryHeroAttack` rejects any human target failing that callback before hit range/LOS/stealth/damage.
3. Generated output contains the original authored two source files plus ONLY the additions, written to isolated build output. No alternative Game, Remote, humanoid system or lobby.

The two files must be integrated as **one atomic source-selective overlay** by the real owner/#220. Bot without Host intentionally fails closed for player damage. Original source remains unmodified. If owner changes one source, this composer **REFUSES to patch** until reviewed/re-pinned; no silent ancient fallback.

## Negative QA / proof boundary

- `test_compose.py`: original byte reverse check, insertion exactly once, no double application, strict Luau, Git blob, frozen-source E2E QA.
- `make_native_membership_harness.py`: extracts the **exact patched host Luau callback** and runs 9 negative/positive cases in official open-source native Luau CLI. Tests active/same mode; disconnect; opposite mode; detached Player; FINISHED; waiting; replaced session; missing castle; valid participant restored.
- Dedicated [workflow](../../.github/workflows/p0d-gq-v3-bot-human-membership.yml): fetch pinned #482 Git source, generate overlay with immutable source lock, run Python QA, native compile **both real patched scripts**, native membership behavior, artifact.

**Native Luau and source exact are NOT a Roblox Studio/Android gameplay test**. Real distance, hit/raycast, 2-client/stale-rejoin and mobile performance still require Studio QA. An ACTIONS green status does not make this an official RC or OWNER accepted.

## Balanced release impact, 8 areas (no duplication)

| Domain | Effect on existing real gameplay |
| --- | --- |
| Characters | Preserves seven roles, stealth, health; protects nonparticipants |
| Field | No map copy; membership required even if someone enters stale arena physically |
| Battle | Removes invalid bot-to-human PvP hit; human PVP untouched |
| Castle | Keeps AI takeover castle state; prevents stale castle ownership from acting as player-authority |
| Neutrals | Does not alter swarm/boss kill counting, pacing, or spawn |
| Items | Does not modify item mode guard (#525) or pickup grants |
| Lobby | Source-owned joined-mode ledger stays sole authority; never trust player movement as session membership |
| Balance/score | Enemy bot damage remains exactly 13/1.15s for valid participants; no score or rank spoof |

## RC integration path and gates

`SOURCE_WIP → CLAIM_GRANTED+ORIGINAL_AUTHOR_ACK → NATIVE+SOURCE_EXACT_GREEN → PRIVATE_21_SOURCE_ROJO → #220 AUTH_CAS → OFFICIAL_RC_SAME_HEAD_CI+ZIP/PLACE → STUDIO_2CLIENT+ANDROID → #420/#470 PRODUCT_GO → OWNER_ACCEPTED`.

**Current facts at source creation:** Official RC HEAD `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34`. #482 original source HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`. Official candidate adoption 0. Studio/Android/OWNER 0. No authorized RC write.

P0 failure conditions: wrong-mode user takes bot HP damage; any valid participant loses bot combat unexpectedly; newly selected PLAYER still receives attacks after changing mode; bot and host half-adopted; change in native owner SHA without replay; same-HEAD test/byte lock missing. For a **YELLOW** optional warning, record owner, repro, flag-OFF, rollback; for a **RED** stop adoption.

Rollback: remove the exact callback from generated Host **and** target clause from generated Bot in one authorized source-selective revert; original SHA-pinned sources become byte-exact. Do not revert #482, #484 or other owners wholesale.
