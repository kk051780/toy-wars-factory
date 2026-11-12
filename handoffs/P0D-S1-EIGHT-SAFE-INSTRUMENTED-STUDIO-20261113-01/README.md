# P0D S1 8点版｜Studio実機検証用・観測器組込の別Place

- 追跡 [Issue #245](https://github.com/kk051780/toy-wars-factory/issues/245)
- game_id: `TRAP_RAIDERS`
- work_id: `p0d-siege-v19`
- release_id: `P0D-S1-KIDS-RC01`
- 観測対象の8点フルゲーム固定ソース: `3120b9d3c0a5ec58c9f2613c5d186f3493b54f83`
- 元の本物の未公開Place: `TRAP_RAIDERS_S1_EIGHT_SAFE_HUD_REVIEW.rbxlx`、159,080バイト、SHA256 `b27f401cd6aed7242665098a4cf323184fe13f2ef964b59a3c97b82daf998d04`

## 前回のPCキットとの差

これは**単に別の受渡しZIPを作る作業ではない**。前回の完全8点ゲームをそのまま残し、別の独立した未公開Studio実機QA用Placeに**既に審査済みの読み取り専用観測器2本**を自動で埋め込み、Output記録を検収用の証拠サマリーへ変換する。

観測器は他チャットが先に制作・検証した正本 `e2662b540f2312c95af67a1761ea05842482919d` を**一文字も変更せず再利用**する。

- `StudioPassiveClientProbe.client.luau` 元Git blob `c0fb0a8ff39ba02277bd4484604b80f3207d7756`
- `StudioPassiveServerProbe.server.luau` 元Git blob `6272cbd587c714046685aba82be775c6dad21057`

ゲーム本体の21本は**元のGit Blobと完全一致のまま**。増えるのは、`ServerScriptService`直下の `P0D_QA_ONLY_ReadOnlyServerObserver` と、`StarterPlayerScripts` 直下の `P0D_QA_ONLY_ReadOnlyClientObserver` だけ。検査用コピーのLocalScriptは `RunService:IsStudio()` 以外では起動せず、イベント・UI・城・スコア・攻撃・罠・Player・Remoteを変更しない。新Remoteや課金処理は一切作らない。元ゲームを上書きしたり公開したりしてはいけない。

## 自動で行うこと／行わないこと

**GitHub Actionsが実際に行う処理:** 固定版Rojo 7.7.1で元の8点ゲームの本物の未公開 `.rbxlx` を再生成してSHA256照合、元21 Luaの完全一致を再検査し、固定済み2観測器を新規XML Itemとして追加。計23 Lua（Server Script2、Local Script4、Module Script17）の全原文・配置・原Git blobを再検査し、さらに実Luauコンパイラですべての構文を解析する。改ざん／欠落／二重スクリプト／古い元ゲームの差替／出力上書きが拒否されることも実行検査。生成した `P0D_S1_EIGHT_SAFE_STUDIO_QA_ONLY_DO_NOT_PUBLISH.rbxlx`、受領書、ログ変換プログラム、34項目の未実施検収表をGitHub Actionsの**非公開本番ではないレビュー成果物**として保存。

**行っていないこと:** Roblox Studio上での実際の起動、二人のログイン操作、卵の実ゲームプレイ、スマホのタッチやFPS、子どもの試遊、OWNER公開承認。CI内の元Luaコンパイルや試験用XMLは本物のStudioプレイ証拠ではない。

## OWNERのWindows Studio実機実行

1. 成果物をダウンロードし、**既存の公式/作業中Placeとは別のフォルダへ展開**する。元の8点Placeも必ず保存。QA用ファイル名には `QA_ONLY_DO_NOT_PUBLISH` を入れてある。
2. QA専用 `.rbxlx` をRoblox Studioで**ローカルファイルとして開く**。Publish / Save to Roblox / 既存PlaceIDへの上書きは絶対に実行しない。
3. Studio `Server & Clients` で2クライアント起動。**Server Output、RED client Output、BLUE client Outputを別々のUTF-8テキストファイル**に保存する。Sourceと別に画面のスクリーンショット、GUIと卵・得点・結果、実施操作を残す。
4. QA中、Outputに `P0D_STUDIO_PROBE_V1` が出ることを確認する。観測器の結果は `OBSERVED` や `UI_WARNING` を示すだけで、正式な合格にはならない。特にStudio Touch Emulatorは物理スマホではない。
5. 作業終了後、Studioの **End Session** で2クライアントとサーバーをすべて閉じ、Studio自体も正常終了する。
6. WindowsのPython 3で以下を実行。結果JSONは **OBSERVED_ONLY_NOT_STUDIO_PASS** であり、34件の手動QA項目をPASSに書き換えない。3ログを揃えない／REDとBLUE逆転／ログ混在・同一ならエラー。
```powershell
py review_studio_probe_logs.py --server-log SERVER.txt --red-client-log RED.txt --blue-client-log BLUE.txt --output STUDIO_OBSERVATIONS_ONLY.json
```
7. 実際の画面録画／スクリーンショット／時刻付き操作・実行端末とこの観測サマリーを唯一の統合担当 [#220](https://github.com/kk051780/toy-wars-factory/issues/220) に渡す。手動PASS・FAIL・BLOCKED・NOT_TESTEDの確定とS1の公開判断は統合担当とOWNERだけが行う。

別途、本番から隔離した元の8点版そのものも最終確認する。観測用スクリプトを含むQAコピーを公開用に転用しない。

**絶対に禁止**：main／公式 `rc/p0d-s1-kids-rc01`／他チャットのブランチへの書込、merge、Roblox公開、追加料金、OWNERのWindows Codexの無許可起動、P0A/B/C/CAS/既存5自動化の変更。

全体進捗は統合担当直近の公式75%で据え置く。QA組込パック自身の完成率とリリース可能性を混同しない。
