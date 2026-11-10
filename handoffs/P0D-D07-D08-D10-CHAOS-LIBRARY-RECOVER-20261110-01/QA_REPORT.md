# P0-D v40-v41-v42 alternative standalone packet — QA

- Mode: CHAT_LEAD_QUOTA / owner-supplied Codex limit.
- Tests: 69/69 Python unittest PASS, `python -m unittest discover -s tests -q`.
- Covered: 0..99 category weighting, 4-stage boss choice, short-match suppression, single event, telegraph/expiry/cleanup, invalid rolls, boss team/relic/capture concurrency and expiry, time-safe snapshot/egg carrying/collision validator, XP/mastery thresholds and 512-match replay/ledger caps, AES-256-GCM tamper/recovery and ZIP Slip and manifest integrity.
- All pure gameplay Luau functions manually authored. **Luau compiler/Roblox Studio/real Place/2 or 3-client, mobile and real player KPI: NOT_TESTED.**
- Cryptographic transport validation uses Python `cryptography` and SHA256, but receiving through Windows Codex/PC GitHub and app integration are separate gates.
- Existing v42.2 historical ZIP is not present. The new fallback **does not preserve historical v42.2 binary hash** and is not an authorized migration or replacement. v42.3 reference `RoundEvidenceGate` is still a separate external artifact.
- Server authority remains dependent on a genuine MatchCoordinator/roster/clock/physical floor validator; a forged `serverRosterConfirmed=true` dictionary is not a secure token.
- Not licensed to production/public Roblox, Robux monetization or unexpected costs.
