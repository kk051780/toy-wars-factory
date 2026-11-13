# EGG RAID RUMBLE — RUMBLE LINK visual cue candidate
2026-11-13 JST · `game_id=TRAP_RAIDERS` · `work_id=p0d-siege-v19`

Parent original IDEA_CARD: https://github.com/kk051780/toy-wars-factory/issues/219#issuecomment-6844560612
Approval/adoption: https://github.com/kk051780/toy-wars-factory/issues/250
Sole game RC writer / official progress: https://github.com/kk051780/toy-wars-factory/issues/220

## Source scope
Separate branch and folder only: `GAME-DESIGN-COOPERATIVE-RUMBLE-LINK-CLIENT-PREVIEW-20261113-01`.
- Four distinct Japanese child-legible display cues, shown by a pure lightweight policy.
- Validates event shape, local team, expired/future times, monotonically increasing sequence and a global display cooldown.
- A Studio-only LocalScript builds one compact accessible banner in an EMPTY isolated preview Place. It sends synthetic local display events, not genuine game events.
- Standalone Rojo `default.project.json`, Python source/negative contract tests.

## Not claimed
This is **NOT integrated** into #282 source, #220 official RC, or original H1 game. No real coop-server signal producer is written; no new/changed game Remote, score, egg, inventory, save, XP, ability, or payment. No native Luau compile, Roblox Studio, Android, 2client or human FUN run has been measured in this lane. Python source assertions are not native Luau tests.

## Test and private preview
1. Run `python -m unittest discover -s tests -v` locally (static+reference oracle only).
2. In a clean, unpublished Studio Place, load standalone project with trusted local Rojo, or import these two scripts into the `ReplicatedStorage` and `StarterPlayerScripts` destinations. Save/exit normally.
3. Four cues display only in Studio from synthetic local packets. Check mobile landscape clipping and zero effect on touch controls.
4. **Before real integration** #250 must select the feature and sole #220 owner must select a frozen authentic game SHA (e.g., newer than #282). A trusted authoritative server producer must emit a read-only cue in the existing server->client state protocol; this library does NOT authenticate events or certify teamwork. Explicitly forbid client self-award and additional Remote. H0/H1 compare score, XP, round, egg, saved profile **byte-equivalence** against no-cue baseline; 2client/Android/human FUN test required.

## Rollback / guardrails
If cues distract a child, obscure the egg, alter gameplay, show erroneous enemy-only data, worsen phone load or fail H0 parity, disable/omit this package. No direct-main push, automatic merge, live publish, payments, PC Codex invocation, P0 A/B/C or automation change.
