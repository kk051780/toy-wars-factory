# P0D S1 V6｜退出イベントの順序に依存しない勝敗判定の実装候補

game_id=TRAP_RAIDERS / work_id=p0d-siege-v19 / release_id=P0D-S1-KIDS-RC01
packet_id=P0D-S1-V6-PLAYERREMOVING-ORDER-20261112-01
報告 https://github.com/kk051780/toy-wars-factory/issues/234

## 根拠

公式ゲームのPlayerRemoving処理は `teamCount(side) <= 1` に依存する。もし `Players:GetPlayers()` がこの時点で退出者を**含む**なら、2人チームは2なので試合を続ける。一方、イベント配信と一覧更新の順序が逆で**既に含まない**なら、残った味方が1人いても人数=1と見なされ試合を途中終了する可能性がある。

このテストは両順序をネイティブLuauの外部Robloxサービス・ダブルで意図的に再現する。**実際のRoblox本番で順序逆転を観測したという主張ではない。**

## 修正候補

公式固定RC `1263a03701211a652b99b91d2339575dc8104eff` の `Game.server.luau` 元Git Blob `7c5229f600f17537bc1bbbb0b96b6a2435875374` に対して、**退出者本人を除外して残りの同陣営プレイヤーを数えるブロックのみ**変更する。

```luau
local teammates = 0
for _, other in ipairs(Players:GetPlayers()) do
    if other ~= player and getTeamName(other) == side then
        teammates += 1
    end
end
if teammates == 0 then
    stopRound(Rules.opponent(side), "OPPONENT_LEFT")
end
```

通信権限、勝敗得点、卵、タイマー、ロビー再配分、クライアント入力、レアワールド、ボスOFF状態は変更しない。

## 実証

元のV6実6ソース（Game/実MapBuilder/S1Rules/LobbyTeamRecovery/Config/S1TrapRules）を固定Git blobで取得し、既に合格したV6・4人参加/退出ラウンドQA `664284d6ec29741060bead3bd0df66e9ea6b1e76` の**原本バイト**を読み出して追加する。

1. **元Game：** 人数一覧からRED二人目が先に削除された状態で `PlayerRemoving` を発火させ、残るREDがいるにもかかわらず結果表示になる問題を再現し、狙いの検査点で失敗したことを要求。
2. **修正Game：** 退出前・退出後の両方の順序で、2対2→仲間1人残存のときはACTIVE、最後の1人が退出したらRESULTS、卵回収・第三ラウンド・通信リプレイ拒否を含む元QAも合格させる。
3. **不正なGame4変異：** 一人残存時も負け、退出者本人も数える、相手チームを数える、最後の1人退出でも終了しない、を各々専用検査で拒否。

GitHub Actionsは本当のnative Luau `f46d879e28302a430029304f7f6a162aed66f103` を固定してビルド、原本＋候補の完全差分・全ファイルSHA256・Python回帰検査・ネイティブLuauまで検査する。

公式RCを改変したわけではない。唯一のS1統合担当 #220 が採用/差戻しを決める。**Roblox Studio実機／2クライアント／スマホ／実際の退出タイミング／公開は未検証**。プレビューテストはその代用ではない。

保護: main、唯一の公式RC、merge、Roblox live公開、課金/支出、OWNERのWindows Codex起動、P0A/B/C/CAS、既存5自動化への変更をしない。
