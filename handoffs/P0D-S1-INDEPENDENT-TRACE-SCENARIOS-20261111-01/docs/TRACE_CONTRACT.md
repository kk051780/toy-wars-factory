# QA_S1_TRACE_V1 integration contract

- Each event must include `seq` (starting 1, contiguous), `epoch` (round epoch), `t` (monotonic seconds), `kind`.
- `meta`: `schema=p0d.s1.trace.v1`, `match_id`, initial `epoch`, `capture_mode=SYNTHETIC|STUDIO_CAPTURE`. `--release` additionally requires nonempty `studio_session`, `place_id`, `source_commit` (40-hex).
- Server source only for `JOIN actor/team`, `START`, `TAKE actor`, `DROP actor`, `SCORE actor/home_team`, `DAMAGE actor/target/amount/after_hp/receipt_id`, `CASTLE_DAMAGE actor/target_team/amount/after_hp/receipt_id`, `BOSS_WARN event_id/deadline`, `BOSS_HIT event_id/target/amount/after_hp/receipt_id`, `BOSS_CLEAR event_id`, `REMOTE_REJECT actor/reason/receipt_id`, `LEAVE actor`, `END winner/reason`, `RESET next_epoch`, `DONE`.
- Two clients' visual telemetry is represented by `WARN_VISIBLE viewer/event_id/shown_remaining`. The captured `t` value **must already be projected into the authoritative server synchronized time domain**. Never let a client report gameplay damage or success via this QA instrumentation.
- `BOSS_WARN` deadline must be 1.8–2.2 s after event. `WARN_VISIBLE.shown_remaining` must equal `max(0, deadline-t)` within 0.1 s and be >=1.5 s for each of red/blue in a full scenario. `BOSS_HIT` occurs at or after deadline and while uncleared.
- HP starts at 100 in this **test contract**. The actual RC must document whether its HP settings are 100; if not, adapt contract **explicitly** or send a new version, never silently force the game to fit.
- Egg scores require the same carrier on own team; opponent's castle at 0 is the only cause for a `castle` win; a previously scored egg for `egg` win; opponent quit for `forfeit` win.
- A full scenario includes 2 team entrants, start, egg score, at least 1 HP change, at least 1 server fake-remote reject, 1 boss hit, two warning views (one per team), end/reset/DONE.
- `REMOTE_REJECT` logging is evidence of the check running, **not** independently authenticated evidence that the forged remote could not influence the game. In final Studio QA force actual attack/replay from a second client and reconcile HP via server authoritative state.
- Important: `RESET` is included with old epoch and `next_epoch`; following event uses new epoch. Trace is a single scenario test; replay across game server sessions is outside this validator's scope.
