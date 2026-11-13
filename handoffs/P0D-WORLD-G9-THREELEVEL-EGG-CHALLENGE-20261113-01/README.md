# G9 private three-level egg tag chase
A **real source-coded** standalone Roblox Studio two-player 3D heist prototype, not the TRAP RAIDERS H1 game.

Same original G8 PORT→SEA→SKY 5 free server-controlled portals (exact unmodified source), plus:
- SEA red/blue eggs at x±22,z168; home score pads x±22,z136, 1 egg each
- First two joins alternate RED/BLUE automatically, no purchase/roles
- E/tap opposite-color egg to steal; E/tap own-color score to score only if own egg home, first to 3 wins with 6-second automatic rematch
- E/tap the egg-carrier's head/body when close to rescue stolen own egg, no violence
- Egg carrying visible overhead, expires after 45s; death/disconnect resets
- SKY lookout gives all players public level-only direction for 7s; 10s global cooldown
- All important authorizations are server-side with avatar health, actual squared-distance and pure authoritative state; no RemoteEvent, DataStore, MarketplaceService, currency or paid actions
- Explicit RunService:IsStudio gate on both server scripts. SOURCE compiler and pure Lua state-machine test do not prove Roblox Studio engine or mobile QA.

Studio trial checklist:
1. Open separately, press Play, make Test Server + two clients; wait for private harbor world and red/blue G9 teams.
2. Both travel PORT→SEA using original G8 bubble E/tap portal; SEA red/blue nests visible on opposite sides. RED steals BLUE egg, returns to own RED score pad; verify +1.
3. BLUE steals RED egg simultaneously. RED score must fail until RED rescues its egg by catching BLUE carrier E/tap. Then score succeeds.
4. Use SEA→SKY portal and skyline lookout to see the stolen-egg tier. Both parties may use same route. SKY→SEA and SKY→PORT return.
5. A carrier disconnects/dies, or stalls >45s: its stolen egg resets. Both teams score three, verify 6s next round.
6. Test malicious prompt distant activation in real Studio with test harness only; confirm server rejects. Inspect mobile screen prompt collision, fps and whether game is actually fun to a child. No such physical tests have been completed by assistant.
