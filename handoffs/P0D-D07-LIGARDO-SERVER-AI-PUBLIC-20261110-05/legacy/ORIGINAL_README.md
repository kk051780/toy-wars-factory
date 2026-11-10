# TRAP RAIDERS — D07 LIGARDO server AI reference

`packet_id=P0D-D07-LIGARDO-SERVER-AI-20261110-04`; `work_id=p0d-siege-v19`.

**What exists:** Two new standalone Luau modules, one independent Python oracle, 90 offline regression/static/safe archive tests (see QA_REPORT), immutable integrity manifest and restore instructions. S2/S4 Ligardo has a target selector, leash-bounded MOVE_INTENT, 2-second lightning TELEGRAPH, maximum three attack attempts and exactly-once `LIGHTNING_INTENT` authorization against a fresh authoritative server round snapshot and LOS.

**What does not exist:** a live Roblox boss rig, physics/PathfindingService, damage application to Humanoids, multiplayer gameplay integration, Studio compile/Play/Stop, or finished boss AI. `damageCap=7` is a bounded *intention*, never a real attack. Do not claim a fight is playable from this pack alone.

## Integration contract (OWNER Windows Codex only)

1. Re-read GitHub #218/#213/#217 and PC's *latest actual* game sources, Studio-saved Place SHA, CHECKPOINT, RESUME, and v39-H1 QA. The recent PC report shows v39-H1 **scoped** Studio PASS, overall game still PARTIAL_NOT_READY. Do not downgrade new PC sources to old `v37`.
2. Compare with canonical **one** v40 server event chooser, stage S2/S4 names, real team strings, and D07 Ligardo client reference `bd1c4fcc...` before changing any live code. `LIGARDO`, `RAIDERS`, `S2`, `S4` are **reference interface names**; map them from the real trusted server, not from untrusted RemoteEvent data. Do not start another event picker or overlap Gorogan S1/S3 server AI.
3. The true server's snapshot factory must populate `roundId`, `eventId`, `stage`, `bossId`, `authorized=true`, `running=true`, `bossAlive=true`, *authoritative* roster (<=16), monotonically increasing clock/sequence. Only call `Policy.begin(...)` for the chosen canonical boss event and `Policy.tick(...)` on true server update. No RemoteEvent from the client may call either with client-owned values.
4. `MOVE_INTENT` and `TELEGRAPH` are proposals only. Real boss physical motion, collision, spawn origin, PathfindingService and visual broadcast must be integrated separately by Codex in an unpublished isolated Studio. The model's `s.pos` is a simulated intent position, not evidence of an NPC's actual location. Fail-closed if physical boss position diverges.
5. Before real damage, call `Adapter.authorizeLightning(intent, *fresh* true server snapshot, lineOfSightCallback, persistentPerEventLedger)`. Adapter checks event/round, live boss position within 2 studs of intent, attack index<=3, true enemy alive and unshielded within 12 studs and server LOS, then marks the attempt consumed. Damage applier must independently check an atomic once-only attack transaction keyed `(roundId,eventId,bossId,attackNo,targetId)` and apply <=7 through the existing trusted damage pipeline. Do not call `Humanoid:TakeDamage` directly from this reference; never trust client-side position or team.
6. Real Studio acceptance needs S2/S4 2-client combat against Ligardo, visible 2s warning, blocked-LOS => zero damage, telegraph interruption, stale/duplicate commands rejected, 3-client race, mobile landscape FPS, S1/S3 Gorogan no regression, egg/7jobs/4 stages/round end/replay. Correct Studio instance Play→Stop→Edit→save→normal app quit→PID disappearance.
7. Do not merge/force-push main, publish/charge, overwrite P0-A/C, upload private game Luau/Place or passwords to PUBLIC GitHub. Log exact SHA and statuses to #213/#218 without leaking code or key.

## Read-only test

```powershell
python -m unittest discover -s tests -q
python tools/verify_packet.py  # no CLI; import verify(blob) from Python
```

Actual ZIP SHA and manifest digest are in the publicly safe encrypted handoff README. P0-D restore uses the reviewed `restore_handoff_safe.py` at `d37eec1b653d060ae27568ddcd5f501da9662081`; key is privately provided by OWNER and **must never be logged, stored on GitHub, or run in a CI env**.
