# P0D 7職業 PvE V1：公式RC56 → 独立RC57 検収（2026-11-14 JST）

## 実物ベース

正式な直近成功ビルド: RC commit 947cddb5351ba95b9b27597b9ec1828a8297cd66、Actions43504336646、実物ZIP SHA256 de43ff8676691c1faab498a09f27c64311a5522d7919919834956c26277d26c4、Place SHA256 3b8df96e32433a645a957604e7f50062a9ffd2e34831d8e6ba21f7ab2bfabc5c。実物の56ソースを直接パースした。

生成した独立57スクリプト Place SHA256 9d2b124e1f7499c701d2ea50254e62a7bc1cefa3e4d87df85ee2da47aec6bfce（518326 bytes）。旧56個のうち54個はソース1バイトも変更していない。変更は元GameとHUDのみ、追加は純 SevenJobsRules ModuleScript のみ（元作者GitBlob a7253d36cb67df47d4ba65d35af212ed1eb7b5b2）。Store、SAVED_PVE_MASTERY、SAVED_BEAST_EVOLUTION、六技能保存、Musou、Realm Hunt、天空、卵の既存コードは保持。唯一のGameとRemoteを維持。これは実物のRoblox XMLであり、新規RojoビルドやStudioエンジン動作の成功は未主張。

## 今回修正した具体的バグ

元のHUD差分の jobTitle.Text ではダブルクォート文字列の内側に改行LFが直接入っていた。Luauで不正な文字列になり得るため、改行をバックスラッシュ+nの2文字に変換した。再生成builderは元の壊れた文字列を1回だけ検出して修正し、期待SHAと一致しなければSTOPする。建築士砲台は CanCollide=false、CanTouch=false、CanQuery=false にしてレイキャストとプレイヤーの経路を阻害しない。

## 職業の操作

戦士:正面重撃、魔法使い:3方向魔法、忍者:前後連撃、罠師:4方向衝撃、建築士:非衝突仮設砲台、魔獣使い:魔獣突進、ゾンビ使い:3段亡者攻撃。Jキー/画面ボタンからLobby内の同team同職重複なし選択、Q/画面からACTIVE時技。原Gameが生存、team、卵非運搬、非拘束、seq、CDをサーバー検証し、追加攻撃は元の中立Hordeのみ。7職業の固有PvP HP/速度、罠拘束、実際の召喚部隊・スキル育成連動は未実装。

## 検査・真実

このチャットの自己完結 ZIP: P0D_RC57_SEVEN_JOBS_BEAST_SAFE_HANDOFF.zip SHA256 64f428b742c5e66c942666acc988a6c98d8b643c53eaf718adfc03a770fc4a6d。元のGitHub ZIP、独立57 .rbxlx、再生成Python、diff、35件Pythonテストとレシートを含む。実際のPython unittest **35/35 PASS**。Native Luau57および新しいRojo57のCIはワークフローの実行結果未確認。Studio1/2、Android、保存再入場、OWNER FUNはNOT_TESTED。

GitHub tools/apply_seven_jobs.py は旧公式Game SHA 2aa21aa8508f234e178b4cd67b233fbc942b05c989a68e339d86ca7d344168af と元HUD SHA 3f2654199c2531bea34371a4ea33beecf65d1e306ecd91e86f5164ab3ddca06d を入力固定。新Game efd1b43350b3102bb493e118cff87ffdb3d57984a41b9831c37144250414c77d、新HUD 6d510976b25789a99686fc58ed6ae4c85dbd2b04f9080e2d4e88e09057506f30、合計57 sourceで照合。元原作者7jobs pureモジュール変更なし。別のRC変更があるとSTOPする。

## #220唯一の正式RC統合担当へ

現行の公式RC branch HEADを再確認し、ゲーム/GameのSHAが元公式56から進んだ場合はGameだけ狭く再ベースすること。旧Place丸ごとで公式を上書きしない。元のrc_fastlane apply_saved_beast.pyのあとに今回builderを実行し、7職業のみ独立OFFできるフラグを追加。正本同一CIでNative57、純policy33ケース、Rojo SourceExact57、唯一Game/Store/Remote、OFF rollbackの確認後にのみSEVEN_JOBS_PVE_V1をRC採用記録する。

公開・課金・mainマージ・追加支出はOWNER別承認。公開品質の過去評価75/100 FUN_NO_GOは変えない。