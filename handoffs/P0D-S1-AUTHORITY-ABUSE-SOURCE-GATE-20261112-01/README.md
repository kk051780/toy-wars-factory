# P0-D S1: Server authority and abuse regression gate

- **Game:** TRAP_RAIDERS / p0d-siege-v19 / P0D-S1-KIDS-RC01.
- **Lane:** CHAT-QA-S1-AUTHORITY-ABUSE-SOURCE-GATE-20261112-01, no overlap with independent source/assembler compiler owner.
- **Pinned game candidate:** \`b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc\`, candidate root \`handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/candidate\`.
- **Scope:** actual four authoritative Luau source files at pinned SHA, not a rewrite. Source blobs are strictly checked before any assertions, so retargeting requires an explicit source review and repin.
- **Run (on any complete local Git checkout):** \`python handoffs/P0D-S1-AUTHORITY-ABUSE-SOURCE-GATE-20261112-01/audit_authority.py --repo .\`
- **Test semantics:** 19 fail-closed static source assertions and 8 deliberately weakened-source mutation controls, including forged client damage, replayed commands, skipped carrier ownership, castle wall bypass, fake boss STOMP event, duplicate hit and disabling the owner review gate.
- **PASS limits:** proves only that **these precise safety patterns are present in the four pinned texts** and that the named mutations are detected. It does not prove the active runtime invokes those checks, Roblox physics/Remote delivery, race freedom, player enjoyment, replay retention, native Luau parser, or Studio performance. Additional dynamic/no-publish gates remain necessary.
- **No producer changes:** do not edit the sole integrator's \`rc/p0d-s1-kids-rc01\`, Game sources, existing QA branches, main, authorization/CAS, Automations, Roblox release or billing.
- **Next:** sole #220 integrator may use this check as a targeted gate on its **actual final** candidate after independently refreshing the pinned SHA and testing 2 real clients in owner-directed Windows Studio. A match against an older 30-file candidate is not final RC approval.
