# Security & data lifecycle

- **Authenticator external:** the Python/Luau pure function rejects invalid shapes, not forged but well-formed values. Do not create `trusted=true` on client or infer verified authority from `kind`. Server-side game state is the authority for player roster, match identity, winner, active seconds, and action evidence.
- **Idempotence:** a state-local ledger tracks awarded and zero-reward finalized matches. It is bounded to 512 matches. A replay with a fresh invented match ID can only be ruled out by the authoritative MatchCoordinator. A disconnected player's new session is not durable; no guarantee of lifetime persistence.
- **Fail closed:** wrong user ID, malformed timestamps, stage/job outside S1-S4/7 free jobs, invalid match ID, unfinished round, malformed action count, and ledger capacity are rejected.
- **No DataStore:** `saved=false` and the view label are compulsory. Owner must explicitly request persistent schema design and test retries separately from v42.2/42.3.
- **No pay-to-win:** milestones are cosmetic preview IDs only. No HP/ATK/DEF, speed, cooldown, egg carry, summon cap, or boss control stat changes.
- **GitHub transfer:** the private artifact is uploaded only as AES-GCM encrypted ciphertext into a separate branch. The 256-bit key is supplied outside GitHub. Public metadata and generic restoration utility do not reveal source, Place or assets.
