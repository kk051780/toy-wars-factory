# P0D企画室：峡谷＋7職業PvE＋仲間卵リレーの60ソース累積候補（未公開）

**これは本物の正式RC採用ではない。** GitHub Draftのみ。#220唯一RC writerの採用・CAS・公開・課金・PC操作を代行しない。

## 最新の各独立成功ソース
- 正式RC57 = `34d6d384d04ba1d4a394331a3e5c74f798e57a22`, Actions43508562967（本物の正式RC 57/57）
- WCS安全なクリスタル峡谷 = PR#300 `db568966f9ef91159cd2489598e485e066064ec9`, Actions43516046707（隔離58/58）
- 戦士、魔法使い、忍者、罠師、建築士、魔獣使い、ゾンビ使いの**中立PvE技のみ** = PR#297 `98edf843fb8a8f6123c13a67745b216712bfe63d`、Actions43512092000（隔離58/58＋33 native job policy）
- この2件を同じPlaceへ積んだ直接親PR#305 `ee4fc7e7eb043294fefc355b070abeb9e28a3181`、Actions43517208170（隔離59/59＋Rojo一致）
- 仲間卵リレー原作者PR#296 `f1c0866423c2c1d36a5cd8eafe8cee7558b1a1dd`、原規則 `d09a52a3b7ca1fe400e30370606d5751751a6941`。原作者独立58/58、native game handler30/30、policy41/41成功 Actions43513482289。**Classicの1卵のみ**、5卵リレーは未実装。

## この新しい枝が実装すること
`apply_egg_overlay.py` は、先に再現性検査済みの合成59ソースを作ってから、**既存の唯一GameとHUDの2ファイルのみを原作者の15個の固定アンカー差分で追加変更**し、純EggRelayPolicy ModuleScript1本を追加する。最終60ソース。新Game/Remote/Storeは作らない。元58のWCSとSevenJobsRulesをバイト完全保持する。ソースのHash、Game/Remote一意、H2五卵モード除外、得点/H2Score呼出数、役職表示/HUD維持、Rojo manifestをチェックする。

`EGG_RELAY_CLASSIC_V1` は独立ビルドOFFで元の合成59を保全し、起動時にはStudioのみBoolValue `ServerStorage.P0D_RC_ENABLE_EGG_RELAY_CLASSIC` が明示trueの時だけ配線される。候補Rojo projectにはこのBoolValueを明示的にセットするので**仮Studio試遊**で体験可能にする狙い。非Studioは常にOFF。作成済みの実アセットとして運用するが、実機検証や多人数同期は未試験。

## CI条件
- HEADを固定した新規GitHub Actionsが **60/60 native Luau コンパイル＋Rojo SourceExact60** を両方証明しなければ「60完成」と数えない。
- 上記15アンカーのどれかが既存7jobs Game/HUDと競合すれば **source-preflight FAILUREで停止**。旧59の成功を60の成功と誤認しない。もし競合したら、既存Game/Remote/Storeを一意に保つ狭い差分の再設計が必要。
- 人間のStudio 2client、Android、実DataStore保存再入場、OWNER FUNは公開前に一括検証。現在は未試験。
- #220担当が正式RCをRC57→WCS58→7jobs59→relay60へ段階的に積み、**各最新SHAの正式canonical CI合格**で初めて正式採用。各枝のprivate CIは採用ACKではない。
- 現時点の公式企画台帳：RC21 / SOURCE27 / IDEA10、合計58件、RC採用 **36.2%**。別企画としてWCS 059等を新規登録した場合は分母を増やす。卵リレーの既存企画007を二重追加しない。歴史的S1公開評価75/100 FUN_NO_GO据え置き。

main変更、GitHub Draftの無断マージ、Roblox公開・実課金・有料支出、PC/Codex、定期Automations改変は一切しない。
