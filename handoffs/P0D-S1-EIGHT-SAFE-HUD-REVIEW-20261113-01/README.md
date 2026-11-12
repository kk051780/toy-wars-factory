# TRAP RAIDERS S1｜8点改善を取り込んだ完全Rojoレビューゲーム

- game_id: `TRAP_RAIDERS`
- work_id: `p0d-siege-v19`
- release_id: `P0D-S1-KIDS-RC01`
- 追跡: https://github.com/kk051780/toy-wars-factory/issues/241
- 公式RCの唯一の統合担当: #220

## 概要

7点統合済みの**フル37ファイル**のレビュー候補 `6cc131d3de06fe8799d00f475fc446a526e4b2c4` に、前回完了したHUDの通信巻き戻り防止 `82847cb97d06394f8fba5ec5c88e644dce0a336b` を取り込んだ**8点版の独立・未公開レビュー候補**。

変更した実ゲームファイルは正確に次の二つのみ。

- `releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau`：元の7点版HUDのGit blob `b3d3996c40c690e19007a36a847d5b10fc6a1522` を、独立した実Luau QA合格済みのHUD `50823390853989ccdda78e28c16ea4757bbe0715` にバイト単位で置換。
- `releases/P0D_S1_KIDS_RC01/BUILD_MANIFEST.json`：37ファイル台帳の中でHUDの `sha256` とバイト長だけ変更。**他36件は完全一致**。

最新Game.serverには既にサーバーの `updateId` 通知、FirstMinuteModelには `lastUpdateId` がある。今回のHUD修正がそこに接続されることで、通常HUDのスコア・勝敗・役職ボタンと、初回ガイドの両方を同一プロトコルで扱う。モバイルの罠ボタン、既存ボス警告表示、サーバーの卵/HP/勝敗/罠ロジック、退場処理、場外復帰は全く変更しない。D07/D08の未承認ボスはOFFのまま。

## 独立QA

- `verify_eight_review.py`：Gitの固定7点原本と固定#240 HUD候補のSHAを直接読み、37件の全ファイルを照合。他36ファイルが旧7点とバイト完全一致、実スクリプトが21本で唯一のサーバーゲーム権限かを検査。
- `verify_eight_real_rojo.py`：固定SHA256の実Rojo 7.7.1が生成する **本物の未公開 `.rbxlx`** の内部21本すべてを全文バイト照合。さらに重複ゲーム・卵回収消失・誤ったGUI座標・通信順序ガード削除など12種類の危険なXML改変を拒否。
- `verify_eight_hud_native.py`：実際のこの8点版に配置されたHUDを、固定版の本物のnative Luauで実行。前回の元HUD QA43項目と意図的に壊した6種類の変異を再検査。
- 本物のLuauコンパイラで21本すべての構文検査と不正文法の拒否。元のS1テストを実行。
- GitHub Actions成功時、レビュー用PlaceとJSON受領書を14日間のActions成果物として保存。**これはRoblox公開やStudio実機成功ではない。**

## 引き渡し

正式な統合担当 #220 が現行の実RC、別チャットの統合候補、追加の独立QAを照合したうえで採用するか決定する。採用前にはWindows/Roblox Studio実機2クライアント・スマホ・実際のUI配置と動作の検収が必要。実測のない「Studio PASS」「販売開始」といった表現は禁止。

**禁止:** mainと公式 `rc/p0d-s1-kids-rc01` の直接変更、他チャットのreviewブランチ変更、無許可merge、Roblox本番公開、課金・支出、OWNERのWindows Codex起動、P0-A/B/C/CASや5件の自動化の設定変更。

全体進捗率は公式統合担当#220の直近値75%を据え置き、パックの完成率とは区別する。
