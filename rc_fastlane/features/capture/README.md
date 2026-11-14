# P0D-018 罠師の敵拘束・味方救出 / Private67 source verified

**正式RCは未変更**。現公式RC66の固定HEAD: `43543378f976374e2cac2d68b3136ac355d3191b`。
独立PR #358の private67 は既存のただ1つの `Game.server.luau` に実際に接続済みで、新しい純粋 `CapturePolicy.luau` 1本のみ追加。既存Clientの `JOB_SKILL` が発火源で、新しいRemote・第二Game・独自スケジューラなし。

罠師のスキルで敵を最大4秒拘束。味方が7スタッド以内の3Dプロンプト「救出」を触れば解除。18秒CD/各チーム1件制限。旧GUARDIAN網は残し、移動/ジャンプ復旧は元Gameの `slowed/restoreSlow/tickTraps` に集約。死亡、退室、再出現、ラウンド終了、フラグOFFへの後始末を含む。Studioのみ、`ServerStorage.P0D_CAPTURE_PVP_V1=true` が必要。

## 証拠
- 実Native Luau policy **18/18 PASS**（SHA固定の作者Luauから構築）。
- 元のRC66からprivate67への隔離統合：Game1本変更、pure ModuleScript1本追加、他65本同一。
- 同HEAD [Actions #43553287101](https://github.com/kk051780/toy-wars-factory/actions/runs/43553287101) SUCCESS：元66とOFF完全一致、67 Luau compile、実Rojo/Place埋込ソース全67完全一致。
- PRIVATE67 Place **611340 B** SHA256 `2885d6777227bded11d468d8a668d14681400c5fa113d3a2a872a8eb6179a63f`、PRIVATE ZIP **174962 B**。GitHub Actions別成果物（公式RC容量ではない）。
- 静的独立QAもPASS。実Studio 1/2client、Android、OWNER FUN **NOT_TESTED**。実機動作をPASSと宣言しない。

## Bへの受入
このブランチはあくまで作者ソースで、公式CIは別にRC66をビルドし、private67は隔離出力。**PRを丸ごとfast-forwardしても公式RC67にはならない。** B #220は最新公式HEAD再検査→本作者の `apply_capture.py` ソースを固定→正式workflowで67生成→同HEAD CI/台帳/容量/ACKを実施して初めて正式採用とする。Sourcery P0/P1未解決があればHOLD。最新RC基準、完了前の二重計上は禁止。

元Game/Store/Remote、`main`、公開、課金、Windows操作は行わない。
