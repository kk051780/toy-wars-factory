# Six 48px silhouette review targets (original V7 signatures)

| Original ID | Near outline must show | Far 48px must retain | Not gameplay |
|---|---|---|---|
| TRCA-BE-027 | Wide turtle + a HUGE upright incomplete gear-shell + asymmetric boot and monocle | Massive gear arch, tiny right boot, monocle dot | No siege/collision/damage |
| TRCA-SP-036 | Three uneven hexagonal crystal frames, broken top edge, small open door under one frame | Hex frame + crack + escape doorway | No shield/bubble authority |
| TRCA-VE-045 | Triangular suspended platform, one-sided large feather vane, telescope looking DOWN | Unequal feather + downward scope + triangular hull | No flight/physics |
| TRCA-WE-054 | Y-tube, two different clam-shell scrolls, one small pearl | Two conch coils + pearl + crack indicator | No weapon/hit/sound |
| TRCA-ZO-009 | Squarish guide with reverse arrow hat, UNEVEN boots, chest bell | Reverse arrow and bell and asymmetric boots | No NPC pathfinding/AI |
| TRCA-TR-018 | Two protecting bud leaves, one broken tip, central wood button, visible twig spring | Two leaves, bent tip, button | No trigger/jump/knockback |

Static offline source tests assert required tagged parts survive far-Lod; these alone do **not** demonstrate readability at 48px or that children like the result. Use actual phone capture/human QA before release and record the original versus new silhouette comparison.
