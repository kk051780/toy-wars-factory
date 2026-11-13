# EGG RAID RUMBLE｜中立無双 × 本物の稼いだ強さ H1

**非公開Studio比較用。公開版ではない。2026-11-13 JST。** 既存のオリジナル #288 38 Luau単一Gameに、原作者#285の純サーバー成長パワールール（GitBlob `86e79877cf0e58603a4de67db29155bf98cc511d`）を**バイト同一で1本だけ**追加。既存元ソース36/38本不変、変更したのは独立コピーの `Game.server.luau` と `HUD.client.luau` のみ。計39 Luauを同じRojo private Placeで組み立てる。

## 実装したゲーム上の変化
- 認定済みの卵Pickup/Deposit/DEFEND等だけが覚醒ゲージを満たす。モブ撃破・攻撃・放置・購入でゲージは増えない。正規XPと**同じ**サーバー発行イベントID、回数制限を使用。
- Lv1では元と同じ攻撃力。Lv50/熟練10で中立雑魚への実ダメージ最大3.3倍、Lv10以上がゲージ80以上を蓄えて覚醒に成功した場合は**2秒の実3D予兆、8秒だけ最大3.8倍**。対人は通常最大1.25倍、覚醒中は最大1.4倍。元の `horde:hit(...)` と `Humanoid:TakeDamage(...)` に倍率を接続してあり、説明だけの倍率ではない。
- 1試合の覚醒は1回だけ。卵所持・拘束中は新規覚醒不可。サーバーがRemoteのシーケンス・役割・Phase・生存・ゲージ・レベルを検査。攻撃/覚醒のイベントは既存唯一のGameと既存唯一のRemote内。
- 既存の5卵得点/従来卵争奪、雑魚8体/精鋭1体、拘束/救出、魔獣スカウト、孵化、経験値保存は元#288同様に保持。卵得点・城HPダメージ・課金・データ保存スキーマは強化しない。
- Client HUDはサーバーのLv/charge/timerを**読むだけ**。新しい⚡覚醒ボタン／Vキー、サーバー生成のHighlightで予兆と覚醒中を表示する。位置が他ボタンと被らないかは物理Androidで未検証。

## 実装時刻の重要対策
#285元ルールの時刻検査は整数0..1,000,000,000。Robloxの `workspace:GetServerTimeNow()` は実世界Unix秒（2026年はこれを超える）。Game側で**match.startedAtを引いたサーバー認定の試合経過整数秒**を渡すことで、Lv50でも無効な状態にならないようにした。元の#285 policy sourceは1バイトも改変しない。

## セーフティ・未実装
- 今回のパワーと覚醒は **RunService:IsStudio()でのみ**有効。本番への漏れを防止。
- HP倍率+20%は今回まだ実ゲームに接続していない（対人威力のみ）。永久進化と段階形態の実ゲーム接続も未実施。開幕課金なし。
- #220正式RC・main・他チャット元ブランチの変更は**ゼロ**。他者の39本実装をRCにそのまま上書きしない。
- Native Luau、Rojoで合格してもStudio2client/Android/FUNは合格していない。OWNER試遊の評価が必要。公式進捗は最後75/100、FUN_NO_GO。

## 再構築（Git checkoutでソースと環境がある場合）
`python -B handoffs/P0D-MUSOU-EARNED-POWER-H1-20261113-01/tests/test_power_bridge.py`

`python -B handoffs/P0D-MUSOU-EARNED-POWER-H1-20261113-01/tools/assemble.py --assemble`

既存の元#288 assemble 38本を作り、同じProjectではなく自分専用の `dist/EGG_RAID_RUMBLE_MUSOU_EARNED_POWER_H1_PRIVATE_STUDIO_ONLY` にのみ出力。既存distがあると上書きを拒否。

独立Actionsで本物のLuau39本コンパイル/純粋ルール native runtime検査/Rojo非公開rbxlxの39/39厳密照合を要求。**Actions実行結果とRunner logを確認するまでは、CI PASSと主張しない。**

次は #250採用判断 → #220差分パッチのみ → 独立QA/OWNER実機2client/Android/初見60秒の面白さ採点。
