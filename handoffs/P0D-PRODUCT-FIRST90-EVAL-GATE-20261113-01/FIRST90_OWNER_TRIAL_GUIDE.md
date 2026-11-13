# P0D PRODUCT FIRST90: OWNER PRIVATE FUN GATE v1
2026-11-13 JST | Owner: PRODUCT_STUDIO_219 | Scope: evidence/QA instructions only

## Truth / provenance
- Game: TRAP_RAIDERS / p0d-siege-v19, PRELAUNCH; source/publication policy #218 V4.
- Product case: P0D-FUN-H1-001, #219 / #250; sole *official* RC writer: #220.
- **B42 First90** source commit `837853e66278e38bb79f6399c3e8bfc9a2403be6`: **selected for OWNER private trial, NOT official RC adoption**.
- **A40 V6** source commit `4b09de3eb70abb2e79268ce41bdecc4b614d39df`: **comparison candidate only**.
- Per #218/#219/#220/#250: published S1 release score **75/100**, `FUN_NO_GO`. Owner real 2client, Android and human FUN **NOT_TESTED** for these candidates. Scores may change only with actual evidence and #220 audit.
- This kit **does not provide / validate a Place file, native Studio QA, or release approval**. Record a local Place file hash from each candidate before running it. Do not assume a source commit identifies a unique .rbxlx file.

## Objective
Measure whether a first-time child can identify the red/blue sides, understand egg stealing, experience a fun, fair fight, and want to rematch. Prior 8-safe owner test was reported as visually/plainly unexciting. Avoid new speculative feature proliferation until a concrete playable difference is measured.

## Trial setup (OWNER manually in isolated unpublished Roblox Studio)
1. Confirm Place is **local unpublished private** and backed up; note filename, SHA-256, build recipe/source commit, device, date/time and tester; never touch main/public game. Keep B42/A40 as two isolated sessions, not scripts combined.
2. Open **B42 first**; do a single solo Play for first90 observation. Then run two Studio test clients on the same candidate for adversarial checks. Separately assess Android actual mobile if available, do not infer from PC window resizing.
3. Repeat identical checks on A40. Do **not** equate native Rojo/source CI PASS with Roblox runtime, 2client, Android or owner enjoyment.
4. If Studio cannot run or Place cannot be matched to a source SHA, mark `NOT_TESTED` / `BLOCKED`, not PASS. Stop/close only the specific Studio instance you started, preserving other projects.
5. Enter results in `TRIAL_RESULT_TEMPLATE.json` copy. Source hashes are references, **not proof** of inspected local Place contents.

## Owner first90 timed observational prompts (each candidate)
- **00–15 s (recognition)**: Can the player immediately locate their own castle, enemy egg, and travel direction without reading a wall of text? Record YES/NO and where they hesitated.
- **15–35 s (agency)**: Can they move, understand one action, and see a meaningful obstacle/opportunity? Log the first confusion, stuck geometry, or off-screen buttons.
- **35–60 s (interaction)**: Does a distinctive combat/creature/world action actually affect an egg approach, escape, interception or defense? A decorative model alone is not gameplay. Record the concrete action.
- **60–90 s (payoff)**: Does carrying/stealing/defending an egg deliver understandable audiovisual feedback, score state and a reason to keep playing? If not reached in 90 s, record NOT_REACHED; don't fake the event.
- **after match**: Can both sides understand result and replay without technical help? Optional, record player desire to rematch (YES/NO/UNKNOWN).

## Hard technical gates: a fail blocks FUN acceptance even if visuals score highly
A. Studio actual **2 clients** join opposite teams; both move, use HUD, handle egg pickup/carrier/drop/deposit and see consistent shared score; no duplicate rewards or phantom carry.
B. Server-owned win/loss, timeout and replay after death, disconnect/rejoin are coherent. No client-supplied XP/score/HP/egg possession accepted; exploit/duplicate requests do not award twice. Record logs, not assumed PASS.
C. Both castles and intended shortcut/escape routes are physically traversable; no entry/exit ramp lips/hidden collision that traps a child. `#248` ground docks are untested optional alternate build, not automatically in B42.
D. **Android actual device** HUD readable/tappable with thumb reach, camera, performance acceptable; actual capture if possible.
E. No crashes, severe confusion, money prompt, third-party IP, unsafe public publishing or hidden dependencies. All features can be played for free.

## Subjective scorecard (OWNER only; 0–5 each, scores not filled in by authors)
- clarity_first15: objective and team legibility
- action_first35: responsiveness + concrete choice
- distinctive_play_60: actual funny/exciting battle or terrain interaction
- egg_payoff_90: feedback and visible stakes
- fairness_readability: counterplay / no unfair spawn trap
- rematch_desire: human willingness to play again

Acceptance **proposal**, not evidence: compare B42 and A40 on all six; require every hard gate verified PASS, actual human FUN 4/5 or better overall, player wants to rematch, and #250 Product DRI selection followed by #220 independent source integration. If evidence is absent, `WAITING_OWNER_STUDIO`; if hard gate fails, `REVISE`. Keep scores separate from #220 official 100-point S1 number.

## Decision tree: what happens next
- B42 wins: #219/#250 select exact *behavioral diff* for official review; #220 may inspect, not automatically adopt; any A40 visual/AI enhancement is separate optional minimal diff only with source authority and rollback review.
- A40 wins: produce a feature-level delta list and minimal technical/UX adoption request to #220; never replace the entire B42 Game/Remote wholesale.
- Both unfun: product case `REVISE`, choose ONE proven player-visible slice (egg interception, strong enemy feedback or readable objective); fix source in its own exclusive branch, test again.
- Runtime failures: prioritize reproducible defect, source SHA, Play Output, time, reproduction steps and severity over more cosmetics.
- Once #220 issues `INTEGRATOR_ACK` and official RC SHA, record only the *actual* adoption. A private trial selection, offline test, Place generation, model count or Github commit is not official integration.

## Recording obligations / ownership
`adoption_id=P0D-FUN-H1-001`; `PRODUCT_DRI=#219`; `PRODUCT_SELECTION=#250`; `SOLE_RC_WRITER=#220`; `NEXT_REAL_STUDIO_OWNER=OWNER`.
Store candidate source SHA, local Place SHA256, session time, participant count, device, yes/no outcome per first90 prompt, hard-gate results, subjective scores, screenshot/log link, next patch owner, rollback. Mark all unknown outcomes `NOT_TESTED`.
No permission for main write, RC write, merge, Roblox publish, live payment, purchases, PC Codex automation or modifications to other five scheduled tasks. GitHub comments do not launch PC work.
