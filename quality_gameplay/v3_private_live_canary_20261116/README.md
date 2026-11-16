# EGGRUMBLE V3 — 21→22 SOURCE-EXACT private-live activation canary

**Ownership:** dedicated new path `quality_gameplay/v3_private_live_canary_20261116/**`. Claim is SOFT_REQUEST_NOT_GRANTED at #218. All canonical author sources #482, spatial #484, ART #485, SCORE #487, other QA, `main`, and official RC stay **unchanged**.

## Confirmed source gap

Pinned author #482 `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9` contains **21 V3 source scripts**; **17 `RunService:IsStudio()` checks in 12 files** prevent normal-server runtime for the preview host, AI, seven-role combat, field items, neutral boss/horde, replay, result, visuals, and client FX. The current composite has no proven safe path to a non-Studio private Android trial. This does **not** imply that simply bypassing Studio guards is sufficient to release.

## Implemented isolated correction

`compose.py` uses the **exact pinned original Git commit** for all 21 source bytes. It fails closed if one source differs, changes the guard count, or changes the project mappings. It copies all 21 sources into an output directory **outside the repository**; unguarded sources stay byte-identical. In the *temporary copies only*, each Studio guard is replaced by `PrivateGate.allowed()`, the main host uses `PrivateGate.advertiseServerReady()`, and client scripts use `PrivateGate.waitAllowed(8)`. Adds one independently named `ReplicatedStorage/EGGRUMBLE_PrivateLiveGate` module for a separate 22-source Rojo test Place. Outputs a per-source `SOURCE_RECEIPT.json`.

**Authorization defaults OFF:** Studio stays allowed in the dedicated development Place. A genuine non-Studio process is allowed **only** when `game.PrivateServerId` is nonempty **and** the independent *private test Place* has a server-controlled `ServerStorage` attribute `EGGRUMBLE_V3_EXPLICIT_PRIVATE_CANARY=true`. Ordinary/public server cannot opt in. Clients require the server's replicated `EGGRUMBLE_V3_PRIVATE_SERVER_READY` acknowledgement (bounded 8-second wait); client input cannot enable the server. Explicit attribute must be set in the isolated, access-controlled test environment by the authorized owner; the composer never sets it. Build a **separate PRIVATE Place**, never paste into a production Place or merge the author host on top of original Game/Store/Remote.

Run `python3 -m unittest discover -s quality_gameplay/v3_private_live_canary_20261116/tests -v` followed by `python3 quality_gameplay/v3_private_live_canary_20261116/compose.py --out /tmp/eggrumble-v3-private-canary`. Must have `git` with full commit history (GitHub Actions checkout `fetch-depth: 0`).

## RC integration / risk ledger

- **Source-local**: original 21 SHA256s fixed, 17 known conditions gated, 22 mappings, no author code edit. Candidate not yet same-HEAD native Luau or Rojo verified until CI/tools provide them.
- **RED release blockers**: Studio-only original code remains the real formal source; new Place is not an official RC adoption; production Game/Store/Remote coexistence and client readiness have not been tested in Roblox engine; no verified private-server deployment or Android; official SOURCE_LOCK/CAS approval absent. Do not publicly deploy.
- **YELLOW optional issues**: additional Studio assumptions may fail in actual private server even when guards pass; measure in engine with 2 clients and mobile. Disable by clearing private opt-in and use older approved private Place.
- **B #220 only**: author/coordinator authorization; compose latest #482/#484/#485/#487 and source-identical production host, check competing authority and all 8 domains, source-selective nonforce CAS against latest `rc/p0d-s1-kids-rc01`, same-HEAD native/Rojo/source-lock, official ZIP/Place sizes, adoption ACK, Studio/Android/#420/#470/OWNER checks. Never merge this whole branch into official RC or main.
- **Progress**: this slice code work is SOURCE_CANDIDATE, formal RC integrated **0/1**, actual gameplay/ART/FUN/OWNER acceptance **0/1**. The earlier V3 umbrella 3/6 candidate preparation is separate and not increased by local scripts.

**Prohibitions:** no direct `main` edits, ordinary merge, Publish, new payment, Windows/Studio remote control, or production activation.
