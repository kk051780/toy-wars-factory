# P0D 7職業PvE V1：正式RC57成功版への追加58（2026-11-14 JST）

## 対象となる正本

- 最後に確実にSUCCESSの正式RC57：SHA 34d6d384d04ba1d4a394331a3e5c74f798e57a22、GitHub Actions 43508562967、正式Rojo Place SHA256 15521b7dadbd96c0ef1ed12367b5fcf2f3738c4428ebf2fb8c43532b39b8b1a8。スカウト3種、保存武器/魔獣強化、六技能DEV保存、Realm Hunt、卵1/5、天空、Musouを含む。
- 今回の独立58ソース試遊候補：P0D_RICH58_SEVEN_JOBS_SCOUT_SPECIES_PRIVATE.rbxlx、SHA256 533f37efae0eb131d5eb427a42141c7858f71005cc9d7ee6a60adc5712edbc9b、522586バイト。実物Roblox XML内にソース58本。新Rojoや本物のStudioエンジン実行PASSは未確認。
- 旧57ソースの55はバイト一致。唯一GameとHUDだけ変更、元作者GitBlob a7253d36cb67df47d4ba65d35af212ed1eb7b5b2 の純SevenJobsRules ModuleScriptを1本追加。Store、H2五卵計算、ScoutSpeciesPolicy、SavedBeastEvolutionPolicy、SavedPveMasteryPolicy、RealmHunt二本、既存六技能関連は変更なし。Game/Remote/Store追加なし。

## 実際の職業技

戦士：正面重撃、魔法使い：前方3方向攻撃、忍者：前後斬り、罠師：4方向衝撃、建築士：無衝突・無レイキャスト仮設砲台、魔獣使い：突進＋追撃、ゾンビ使い：3段攻撃。LobbyでJ/画面選択（同チーム同職1人）、ACTIVE中Q/画面で発動。元唯一Gameがserver team、alive、卵非携帯、拘束、CD、replay seqを検証し、追加ダメージは元のMusouHorde中立敵のみ。新job固有PvP HP/足速/永続召喚/本物の罠拘束は未実装。

## 今回の重要な修正

旧作者patchのHUDのjobTitle.Textにダブルクォート途中の生改行が入っていた。これはLuau文字列の構文エラーとなりうるので、バックスラッシュ+nの2文字へ置換した。GitHub tools/apply_seven_jobs.pyには生改行が元の場所に厳密に1回ある時だけ置換するfail-closedガードと、修正後HUD SHA256 6d510976b25789a99686fc58ed6ae4c85dbd2b04f9080e2d4e88e09057506f30 を登録。Builder仮設砲台CanQuery=falseも維持。

GitHub builderが期待する真正公式RC57 Game SHA256 aaa03616ee4aadee32bfeb90a0016ca036919a52a2725e908a0c360adf087739、生成後 Game SHA256 6308e02c0d6930af2ec4ba0f86bf280be435ca8b7c46f1c8c8ee81b4164269eb。元のpatch --fuzz=0でGame全8ハンク、HUD適用成功。元57が違う場合STOP。

## 検査証拠

ローカル独立Python source/unittest 38/38 PASS。公式ZIP SHA256 552c506ef2812b220285f716562edfb17cdb285fc985b4cacec82996c88ecbdf および実物Place SHAを照合し、57→58、旧55完全同一、唯一Game/Remote、保存済BEAST/WEAPON、スカウト3種ルール、HUD構文を検査。改変負例も拒否。

所有者向け自己完結ファイル P0D_RC58_SEVEN_JOBS_SCOUT_SAFE_HANDOFF.zip SHA256 76e8b13f2985cf3b7a1ad8c365fed0bc90e4a81c00fbb9a73487a02dc56c7ec0。9ファイル、正式57 ZIP、独立58 Place、Python再生成コード、38件テスト、元Game/HUD patch、Luau源、receipt、日本語README。

専用 .github/workflows/p0d-sevenjobs-private55-native-20261114.yml は歴史的名称ながらSOURCE内容は正式57固定→ScoutSpecies builder→sevenjobs追加→native Luau58 + pure33ケース→Rojo57?ではなく**58 source exact**を要求。CIはソース登録済みだが成功run IDはNOT_VERIFIED。元公式RC57のSUCCESSを今回新58のnative PASSと誤認禁止。Roblox Studio1/2、Android、保存再入場、OWNER FUNもNOT_TESTED。正式RCへの採用NO、出版NO、課金NO。

## #220唯一RC担当の次の作業

現在の正式RCブランチを再読。先行したGame変更があれば狭い再ベースを選び、古い元Placeの丸ごと上書きを拒否。新規1 ModuleScript / Game/HUD diffを現行唯一RCのapply_scout_species.py後に追加し、SEVEN_JOBS_PVE_V1の独立OFFスイッチを付け、一本の正式RC Actionsでネイティブ58/58、Rojo58埋込みソース完全一致、唯一Game/Remote/Store、既存SCOUT/BEAST/WEAPONの欠損なし、OFF rollbackを証明後にのみ採用記録。人間Studio/Android/FUNはOWNER方針で公開前ゲートのまま。旧S1公開品質75/100 FUN_NO_GOを勝手に上げない。

本feature branchはmain、正式RC、Roblox公開、課金、PC/Codex、Automationsを変更していない。