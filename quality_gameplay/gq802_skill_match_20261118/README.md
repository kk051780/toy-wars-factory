# GQ802 | Skill matchmaking policy only (no queuing/teleport)
Spec #802; existing lobby owner #220. Unique component: pure native Luau server-verified cohort and balanced party assignment. This is not a new lobby, queue, teleport system or per-client PRNG.

- When >=16 valid candidate human tickets in same trusted mode/region and acceptable skill band, try 16 (8vs8), otherwise 8 (4vs4); match party as unit (up to4), preserve novices <=5 matches and <=12 level as separate band, compare authoritative rating and mild level/experience, widen waiting band after queue age. Find two balanced teams <=10% rating gap initially or <=16% after 45secs.
- After <8 eligible or no fair whole-party bracket, return fallbacks; existing ordinary lobby/bots remain default. This module never creates servers, persists ratings, accesses unverified client data, teleports or blocks onboarding. Tickets are only validated as service-side receipts; existing lobby MUST enforce idempotent atomic queue claims and match epoch.
- Current stage randomizer #803 is separate; matchmaking does not pick physical map, weather or seed. No existing Host, Game, Combat, Store or Realm changes.

Native tests cover 8/16, deterministic ordering, same-party teams, newcomer segregation, sparse servers, wide rating separation, fake server ticket, duplicate account and invalid region/mode. Exact OFF=module omitted; no actual MemoryStoreService/TeleportService nor Studio/player sessions. Even if CI passes, real match routing is NOT implemented.

Roblox Creator official refs for the actual adapter: https://create.roblox.com/docs/cloud-services/memory-stores/queue ; https://create.roblox.com/docs/matchmaking ; https://create.roblox.com/docs/projects/teleport-private-servers . Real player queue and failure recovery requires separately reviewed connected integration through #220, same-head Native/Rojo, source LOCK, OFF and rollback.
