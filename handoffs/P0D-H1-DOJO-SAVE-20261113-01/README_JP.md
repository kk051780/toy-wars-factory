# P0D H1 修行の「再ログイン保存」— 既存プロフィール同居の非公開開発候補

2026-11-13 JST。前作 B42（卵1/5）＋FIRST90（目標ナビ）＋無双V7（雑魚8体+精鋭・実ダメージ数値/撃破演出）＋物理天空城＋Studio1人練習＋自動BEAST/WEAPON道場の、**固定44スクリプト** を元にする。

## 本版で実際に組み込んだもの

- 魔獣・武器の「乗るだけで自動修行」およびフレンドXP1.5倍は保持、上限各Lv5、PvEのみダメージ強化最大+20%、PvP攻撃/HP/速さの追加強化なし。
- 既存の **PersistentHatchStore (original schema=1)** に任意の `dojo` フィールドを追加。旧ユーザー（dojoフィールドなし）は正規として読み込み、Lv1から始める。**新たなDataStoreを作らない**。既存の所持品・XP・進化と同じレコード／同じ一つの更新権限。
- 保存は元のPrivate Studio用 `EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1` 名前空間だけで、Roblox Studio実行＋実際のUserId>0＋ロード成功の時に有効。Studio APIサービス不可や負のテストユーザーIDなら自動的にLOCAL_ONLY。公開サーバー動作には保存更新が入らない。
- Dojoは元Gameの0.5secサーバーtickで自動修行を算定し、約20秒間隔、退室またはBindToClose時に同期でなく **元のUpdateAsyncを利用した非同期保存**を依頼する。内部の継続書込個数も元Gameと共通。新規RemoteEvent/第2Game/第2Storeを作らない。
- 保存用トークンはサーバー生成＋書込番号。UpdateAsyncが途中で結果不明になった際は同一トークン再試行。dojo専用の独立revisionで競合を判定し、古いレベル・修行秒数への巻戻しを拒否。STORE内部は `normalized` 処理に `dojo` を正しく引き継ぐので、既存の自由孵化/装備/マッチXP/進化更新でも道場の記録が欠落しない。サーバーが認めたbounded snapshotだけ保存。
- HUDは魔獣・武器レベルと「保存済」「保存待ち」「保存失敗」「読込中」「このプレイのみ」をサーバー値に従い表示する。**書込成功が未確認の時に「保存済」と誤表記しない**。
- 前回44本のうち41本は完全バイト同一。Game.server、HUD.client、PersistentHatchStoreのみ変更。Rojoで一体型Private .rbxlxを生成。

## 再ログイン試遊条件と注意

1. Studioの作業中ファイルをバックアップ、CI artifactの「DOJO_DURABLE_DEV_PRIVATE」 .rbxlx を別タブで開く。本番Publishは禁止。
2. 公開済みではない**専用DEVデータ名前空間**なので、実データを保存したい場合は、適切なテスト環境で Studio API サービス許可および正のUserIdを使っていることを確認。通常のStudio1クライアントの負の仮UserIdは「このプレイのみ」と表示され、永続保存の実証には使えない。実ユーザーの保存済みプロフィールに混ぜない。
3. まず修行台に乗る→約20秒後「保存済」表示→ゲーム終了→再入室して修行Lv/熟練度が保持されるか→敵NPCのダメージ上昇と対人戦不変を確認。
4. 次に魔獣の孵化・進化・1/5卵得点後のXP保存を試し、前後でDojoデータが消えないこと、万一書込が失敗した時はHUDが保存失敗/LOCAL_ONLYであることを確認。
5. 2クライアント赤青対戦、フレンドXPボーナス、天空城の物理連結、Android画面/FPSと子供視点の楽しさは独立試遊要件。

### 未証明の制限（絶対に過大評価しない）
- Github CIのnative Luau FakeStoreは本物のRoblox DataStore/ネットワークではない。実Studio 1client/2client、実API保存、再ログイン復帰、実フレンド認識、Androidや本人FUNはすべて **NOT_TESTED**。
- 退室・シャットダウン直前でまだ前回の書込が進行中など、未確認の最後数秒を失う可能性は残る。HUDの成否表示と、実Studioでの長短時間・同時入退出試験が必要。
- この版は**技術的な保存試験候補**で、課金・時間短縮・PvP優位・全6道場・offline catch-upはまだ実装しない。正式プロダクト選定/RC採用は #250/#220、OWNER実機FUNを通過した後。
- 元の公開/main/公式S1 RC/他feature branchは書き換えていない。正式S1完成度は最後の公式値75/100、FUN_NO_GOから変更しない。
