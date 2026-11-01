# A14 — Roblox Cloud v2 target metadata preflight (read-only, protected draft)

Scope: issue [#151](https://github.com/kk051780/toy-wars-factory/issues/151), exact main source base \`e5deff4d5681bca4823a3da0f848e01bc089ae6e\`. This candidate only checks metadata for **an already-existing** nonpublic sandbox Universe/Place. It does not create a Roblox game, upload source, run Luau, or publish. It is independent of draft #145 XML Saved upload, #175 Luau task, #167 Studio MCP and #143 Rojo build.

## Files and smoke test
- \`tools/twf_roblox_target_metadata_probe.py\`: fixed Roblox host, exact Universe/Place paths, at most two GETs, status/content type/path checks, bounded 8-second requests, 64 KiB response, no redirects, no implicit proxy, no retries and no POST.
- \`tests/test_twf_roblox_target_metadata_probe.py\`: 18 mock-only regression methods. Run \`python -m unittest discover -s tests -p 'test_twf_roblox_target_metadata_probe.py' -v\` with no Roblox key or network.
- The original local candidate's byte-exact Git blob IDs are \`43b8f01ce9efe4fe687a7e22041304a7d238b340\` for source and \`6041783c8e38d047a18b2d2491f135c1a811e011\` for tests.

## Safety boundaries

A matching response \`path\` is untrusted metadata, **not** evidence of Roblox credential provenance, private status, ownership, real provider connection, Saved version, real engine test, Play session, multiplayer or smartphone QA. All authority/grant flags are false. An injected test opener makes fixture tests pass without any provider request. The independent reviewer must confirm official Roblox request/response contracts, accepted CI at the exact PR HEAD and separate real target/provider attestation before any live dispatch is proposed. Never paste secrets into issues, repo, logs or chat.

A known production Universe/Place may be optionally supplied for **collision rejection**. Production IDs cannot be fabricated when no production game exists. Live calls are not made by CI or a registered worker from this PR.

Official API documentation:
- https://create.roblox.com/docs/cloud/reference/features/universes
- https://create.roblox.com/docs/cloud/reference/features/places

## Coordination
Manual owner-delegated CONTROLLER isolated candidate, coordinator epoch 378 owner \`39359777-3362-4170-8a74-88b4060e6e3f\`, original nonforced CAS claim \`44d96793e7a2518cfaf2e2779c9588363409427c\`; protected review and merge are separate decisions. No Roblox API traffic, test environment, token, production publish, merge, external inference or spending authorization was exercised.
