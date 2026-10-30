# A14 alternate bridge — Roblox XML Saved test place (not deployment)

This is an **independent adapter** for the already-produced, current-main `.rbxlx` candidate from Issue #117, not a new XML place builder, not the pending PR143 Rojo binary builder and not the PR144 GitHub Actions artifact consumer. It intentionally does not change any protected GitHub Actions workflow.

## Why it matters

Roblox official Place Publishing endpoint accepts **both `.rbxl` and `.rbxlx`**. For `.rbxlx`, the HTTP request content-type is `application/xml`. The `versionType=Saved` selector means **save without public publishing**. The response contains a positive `versionNumber`. This can, after separate protected authorization and credential provisioning, be handed to the existing v2 Luau Execution session API against the same private place version. An XML file that parses is *not* proof Roblox Studio accepted it or that the game boots.

Authoritative specification:
- https://create.roblox.com/docs/cloud/guides/usage-place-publishing
- https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/cloud/universes-api/v1.json
- https://create.roblox.com/docs/cloud/reference/features/luau-execution

## Implementation

- `tools/roblox_private_xml_saved.py`: nonpublishing XML file gate + one-shot Saved API transport. Exact known four source digests/current accepted main SHA, 10 structural instances, 4 unchanged Luau scripts and RemoteEvent. Rejects extra/changed scripts, DTDs/entities, bad hashes, symlinks, wrong universes and production-target overlap. No source or branch writes. Supplied metadata, GitHub-style environment strings and test responses are never trusted as provider attestation.
- `tools/stage_private_xml_saved.py`: **safe PLAN_ONLY by default**, zero network or credentials. Optional `--live` requires a legitimately protected host; syntactic checks alone are **NOT** authority.
- `tests/test_system_private_xml_saved.py`: 25 cases using the four real accepted game source files. Offline fake transport; no actual Roblox call.

## Real execution prerequisite — not met

1. A real accepted `main` source commit plus accepted GitHub artifact provenance for `.rbxlx` must be authenticated through a read-only trusted connector, including all four exact script bytes. The other chat's XML file only exists as a conversation artifact, not a GitHub Actions binary; this module cannot attest its provenance by itself.
2. A separately created **private** Roblox Universe and Place and a different production Universe/Place must exist and be authoritatively verified, not guessed. A narrowly scoped `universe-places:write` API key for the test universe is required. Do not publish the key in chat or GitHub source.
3. An independently reviewed, protected GitHub Actions workflow must verify exact source and artifact, the secret's real protection controls and test-target binding; manual-only, one-shot. If supported private-repo environment approvals are unavailable, **STOP** rather than silently use an unprotected secret.
4. Only then a single no-retry POST is permitted: `https://apis.roblox.com/universes/v1/{TEST_UNIVERSE}/places/{TEST_PLACE}/versions?versionType=Saved` with `Content-Type: application/xml`. If network response is lost, outcome UNKNOWN, no automatic retry.
5. Separately verify provider `versionNumber`, actual saved place version and originating artifact with platform evidence. Only then use the v2 separate Luau Execution credential to test **that exact version** and retrieve all logs. This does not prove mobile, two-player, PvE gameplay quality or any public release.

All output proof flags are `false`. Engine, Studio, hosted Roblox place and active credentials are **NOT VERIFIED**, automatic publishing/spending/Gemini remain HOLD.
