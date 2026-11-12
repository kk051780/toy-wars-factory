# TRAP RAIDERS S1｜通常HUDにも通信の巻き戻り防止を追加する独立候補

game_id=TRAP_RAIDERS / work_id=p0d-siege-v19 / release_id=P0D-S1-KIDS-RC01
担当 Issue [#240](https://github.com/kk051780/toy-wars-factory/issues/240)

## 実際に確認したソース欠落

7点改善済みフルゲームの独立レビュー `6cc131d3de06fe8799d00f475fc446a526e4b2c4` には、サーバーの `SNAPSHOT.updateId` とFirstMinuteModelの `lastUpdateId` が実装され、ガイドは古い通信の巻き戻りを防止できる。しかし実際の `HUD.client.luau`（元のGit blob `b3d3996c40c690e19007a36a847d5b10fc6a1522`）は**試合番号serialだけ**を検査する。同じserialの古い通知が遅延すると、スコア・勝敗・タイマー・Guardian罠ボタンの状態を古い値に戻すおそれがある。これはソースで確かめたリスクであり、実機不具合の再現ではない。

## 修正内容（3箇所の限定差分）

`candidate/src/client/HUD.client.luau` のフルLuauソースを、既存のHUD原本から**3個の正確な差分だけ**で生成。1) `lastUpdateId=-1` の記憶、2) SNAPSHOTを表示する前に `updateId` の整数範囲と単調増加を検査、3) 受け入れた通知でだけ最後のIDを保存。新形式を一度受け取ったらID無し旧形式が遅れてきても破棄する。初めて受け取る旧形式通知は互換のため表示でき、その後新形式へ移行できる。

Guardians罠ボタンの右側配置、タッチ操作、F/Tキー、攻撃・役職RemoteEventの送信内容、ボス警告イベントの独立した `seq` 保護、Map・HP・勝敗は変更しない。元の7点版のゲームソース・統合担当の公式RC・他チャットのreviewブランチは触らない。

## 本物のHUDソースを動かす検証

`tools/check_hud_native.py` はGitHubの固定コミットから実際のHUD原本Git blobを取り出し、新候補が原本の3つの文字列置換と**バイト単位で完全一致**することを確認。さらに、同じ7点版の本物のサーバーGameに `snapshotUpdateId` が存在することも固定SHAで検査する。

その後、**元のフルHUDのLuauコードをそのまま真正native Luauで実行**し、外部RobloxのInstance/GUIイベント/Remoteは最低限の試験用ダブルで代替。Lobby→Guardian ACTIVE→遅延した同試合の古いLobby、RESULTS→遅延ACTIVE、勝利2点の維持、同一ID・不正小数/文字列/負数/未採番・次ラウンドの古いIDを拒否、初回の旧式→新式移行、既存ボスの通知、攻撃/罠のintent-only Remoteを確認。壊れた元HUD変異6種類も、どの検査で検出されたか証明する。

これは**ソース品質の検証**であり、実際のRoblox Studioクライアントの描画・ネットワーク遅延・スマホタップ感度・子どもの操作性やFPSの実測ではない。正式な採用・S1全体の進捗加点は統合担当 #220 の専権。後段でWindows実機2client・スマホ・OWNER判断が必要。

テストコマンド：
```bash
python3 handoffs/P0D-S1-HUD-SNAPSHOT-ORDER-20261112-09/tools/check_hud_native.py --selftest
python3 -m unittest discover -s handoffs/P0D-S1-HUD-SNAPSHOT-ORDER-20261112-09/tests -v
python3 handoffs/P0D-S1-HUD-SNAPSHOT-ORDER-20261112-09/tools/check_hud_native.py --repo . --luau /path/to/native/luau
```

禁止：main・公式RC・他reviewブランチ書込み、merge、ゲーム公開・支出、Codexの無断起動、P0ABC/CAS/5自動化の変更。
