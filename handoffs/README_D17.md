# P0-D D17 Cosmetic Catalog: encrypted ChatGPT reference handoff

Packet: `P0D-D17-COSMETIC-CATALOG-20261110-01` | game: `TRAP_RAIDERS` | work: `p0d-siege-v19`

## One feature slice, no overlap
This independent ChatGPT packet implements a **preview-only visual cosmetic catalog and server-trusted equip guard**, not the privacy metrics from earlier D17 claim `P0D-D17-PRIVACY-METRICS-20261110-A` (other chat). It does not grant stamps, XP, game access or product purchases. Previous D17 engagement-metrics claim from this chat was explicitly withdrawn.

Five whitelisted entries: starter banner (free), amber egg glow and jade lobby plinth (server-entitlement-gated placeholders), and future victory-petals/emote examples (permanently PREVIEW_ONLY in this prototype). No arbitrary assets, price tags, Robux, buying, catalog external network calls, combat effects or user telemetry. Session-only memory capped at 256 equipped player entries; on leaving/entitlement revocation the effect is gone. Future UI/3D rendering itself remains unimplemented.

## Actual artifact and scope
- **AES-256-GCM encrypted** JSON: `TRAP_RAIDERS_D17_encrypted.json` (no private source or decryption key in this repository).
- ZIP archive (restored locally only): `TRAP_RAIDERS_D17_CosmeticCatalog.zip`, **17,509 bytes**.
- Original ZIP SHA256: `abd8efebae089b40c6837ceccc9fc152b2309ffa6a5b01eaf2dba497bac7e065`.
- Manifest SHA256: `9a84e06ef487083f03f0492b45fe0a35aebd27f338e3ad3e422fe9ccc3dcbf3e`.
- 15 listed files plus `BUILD_MANIFEST.json`.
- Encrypted JSON SHA256: `85c69f7efbc1d1c288d02d3c5df0306f8a7c7ef78b2677fd28c0a366a4561d4e`.
- Ciphertext SHA256: `699787579f46f7c8aed49368a3674d167367ff62209816358140fa8a3c03ee67`.
- Python reference unit / randomized scenarios and negative transport tests: **67/67 PASS**. ZIP per-file SHA/size and encryption/decryption byte identity PASS.
- **Luau syntax/semantics, Windows PC restore, Studio, 2/3-client, iPhone, player engagement, Robux revenue are NOT_TESTED.** Nothing was integrated into the owner's unpublished game.

## Owner Windows Codex restoration later (NOT automatic)
1. Read GitHub issue #218 current claims and #213 PC QA; ensure D17 privacy-metrics from other chat remains a separate packet.
2. Verify the immutable GitHub commit and remote encrypted JSON SHA, then obtain the private key **from the owner's ChatGPT conversation only**, never from GitHub or logs.
3. Use the safe restore utility at immutable [v2 restore tool](https://github.com/kk051780/toy-wars-factory/blob/d37eec1b653d060ae27568ddcd5f501da9662081/tools/restore_handoff_safe.py) with the owner's protected directory and exact expected packet/work ID + ZIP SHA. Its argument form:

```powershell
py restore_handoff_safe.py TRAP_RAIDERS_D17_encrypted.json --out TRAP_RAIDERS_D17_CosmeticCatalog.zip --expect-zip-sha256 abd8efebae089b40c6837ceccc9fc152b2309ffa6a5b01eaf2dba497bac7e065 --expect-work-id p0d-siege-v19 --expect-game-id TRAP_RAIDERS --expect-packet-id P0D-D17-COSMETIC-CATALOG-20261110-01
```

Use `CHAT_CODEX_HANDOFF_KEY` env var privately. Do not print or commit it. On mismatch, STOP without overwrite. Run `python tools/verify_packet.py` and `python -m unittest discover -s tests -q` **only after verifying and extracting safely in an isolated local folder**.

4. Prerequisite: v37 final SHA QA, then v39-H1 proper server-granted stamp entitlement if available. Import one catalog **preview** to existing lobby UI in an unpublished isolated Roblox Studio; don't grant or equip without server ownership resolver. Confirm visibility on iPhone emulator and 2 clients. No new payment or purchase endpoints.
5. Preserve local source/place SHA, Studio save/normal exit and PID evidence, then report separately to #213/#218. GitHub delivery does NOT prove Studio or owner PC QA.

## Safety boundary
This repository is PUBLIC. Do not upload plaintext game Luau/Place/ZIP, keys, personal information or private data. No direct `main` edits, merges, Roblox publishing, real money transactions or extra spending. P0-A/B/C writer/CAS/review gates and existing automations are unchanged. This file is transport documentation, not an instruction to run Windows Codex automatically.