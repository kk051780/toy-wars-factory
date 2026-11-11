# TRAP RAIDERS S1 — 試合結果の日本語表示（任意採用候補）
game_id=TRAP_RAIDERS; work_id=p0d-siege-v19
packet_id=P0D-S1-RESULT-LOCALIZATION-20261112-01
source_parent=b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc
original_HUD_sha256=50d9d9a6fc56ee796bc7999ce030c9cfc5d5af697591760c9e444eaefeb5de07
patched_HUD_sha256=b2c17440a486cb94d3c033c065ad26e9f991b88411d7fba340e9ce204583cb3d
owner_lane=CHAT-S1-RESULT-COPY-ONLY-20261112-01

## 実装
現行30-file実ゲーム候補の **HUD.client.luau 全文** を、RESULTS分岐に限って可逆変更。
- 勝利・敗北・引き分け・結果未確定を区別し、未確定値から勝敗を推定しない。
- EGG_CAPTURE / CASTLE_DESTROYED / OPPONENT_LEFT / TEAM_EMPTY / TIME_LIMIT を日本語のプレイヤー向け理由へ変換し、未知の内部コードを画面表示しない。
- 次の準備までの秒数を 0〜3600 の数値に限定し不正/無限大/NaNは0へフォールバック。
- 「再戦確定」ではなく次のロビー準備と明示（相手の入室は保証されない）。
- ゲーム権限/HP/イベント抽選/報酬/ネットワーク/ルールには変更なし。既存HUDを別HUDで重複起動しない。

## 採用方法（#220唯一のCHAT-INTEGRATORのみ）
1. RC側 HUD が **元のGit SHA256 50d9d9a6fc56ee796bc7999ce030c9cfc5d5af697591760c9e444eaefeb5de07** と一致する時だけ、`src/client/HUD.client.luau` を既存HUDと置換する。差分がある場合は勝手に上書きせず手動3-way検証する。
2. `python -m unittest discover -s tests -p "test_result_copy.py" -v` をこのpacket rootで実施。
3. このpacketはRojo全体プロジェクトではない。既存30-file候補や#220 RCに新しいStarterPlayerScriptを増やさない。
4. 再戦/スマホ表示/未知reasonの正常動作は最終PC Studio全体QAに含める。Studio NOT_TESTED。旧HUDを戻せば無効化できる。

## 検証の境界
Pythonテストは source-pin/可逆変換/構造とPython参照オラクルであり、LuauインタプリタやRoblox Studioでの動作そのものは証明しない。
PUBLIC_SOURCE_V1: このゲームの公開許可済みオリジナルソースのみ。秘密情報/第三者アセットなし。main/RC/既存機能branch変更、merge、publish、課金、支出なし。
