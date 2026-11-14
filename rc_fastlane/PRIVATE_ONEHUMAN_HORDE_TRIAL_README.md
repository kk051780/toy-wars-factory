# #444 Private one-human neutral-Horde trial — source only

The current formal RC81 source already contains OWNER-private gated original Horde
reset/hit/tick. However the unchanged StudioSolo.canStart refuses an actual
private nonStudio server with only 1 human even when the human presses READY,
so the 9-monster engine path cannot reach ACTIVE for a solo owner phone test.

This A-PREP stage edits **only** original single server/Game.server.luau,
leaving all other 80 sources, including original StudioSoloPreviewRules,
MusouHorde, HUD, Game HP/Remote/Store/egg/round serial, source-exact.
It plugs the **same already adopted server-side PrivateServerId plus
Workspace owner bool P0D_PRIVATE_LIVE_HORDE_NINE** into 2 canStart calls,
one isSoloRound latch and one emptyWinner. No other gameplay authority.
Only a nonStudio private server with owner explicit opt-in gets a one-human
practice round, and only after clicking the existing voluntary READY button
and the normal 7-second countdown. Public still requires 2 humans on both
teams. Studio solo is exactly unchanged. SoloTeamBots remain studio-only
(no bot-based fake PvP); original 9 neutral enemies become the practice
opponents, and no winner/egg-capture claim is made for single-player practice.

The special mode is NOT automatically enabled by this branch, and the
private Workspace attribute must be set server-side by an OWNER-authorized
procedure before the round. Revoking the attribute removes permission to
start or continue solo. This is NOT a public game release feature.

Native case source tests use the real authored Game READY roster and real
StudioSolo Module to cover studio/public/private/owner READY, spectator,
two humans, team balance, opt-out and revoke; runtime Roblox not tested.
No real 9 mobs evidence, verified HP damage, PC/Android low-end 15 min or
children FUN / 32 screenshots exists; owner accepted false. LIVE_HORDE,
LIVE_ART, ART, MOBILE, FUN are all NO_GO. Only B #220 may adopt after
independent critical review and nonforce CAS + official same-HEAD evidence.
No main, normal merge, Roblox Publish, paid feature or Windows operation.
