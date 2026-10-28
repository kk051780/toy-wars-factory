# OWNER転記とAI要約を区別する共通ストック（修復候補）

2026-10-29。PR112の独立審査REQUEST_CHANGESを優先した同一PR修復。現在mainは5cafd1a4、PR111は統合済み、QA40774271061/handoff40774270909成功後の差分は生成statusの2ファイルだけ。ゲーム修正は繰り返さない。

## 誤りと保存方法

C00121のOWNER-20261028-CHARACTER-VARIETYは短縮要約をOWNER原文と誤分類した。SHAの自己整合は原文や本人の認証ではない。元のC00121/作者run7abde498/epoch222の取得証拠と既存43検査は変更しない。

新規C00122が現在のストック表示を引き継ぐ。旧誤登録と依存する2案はWITHDRAWNへ追記し、撤回理由と元内容を監査用に残す。旧C00121を現在の有効な原案リストとして使わない。全文は新ID OWNER-20261028-CHARACTER-VERBATIM、要約は別ID MIX-20261029-CHARACTER-SUMMARY/DERIVEDとして原文IDへリンクする。新しい比較案も修正済みの親IDへ結ぶ。原文/観測/既存イベントを上書きしない。

転記元は https://github.com/kk051780/toy-wars-factory/issues/109#issuecomment-6481271808 。コメント全文中の引用をそのまま保持し、API取得先も保存する。元チャットURLはNOT_AVAILABLE、原チャット本人認証はNOT_VERIFIED。GitHub投稿者のOWNERラベルやハッシュ一致を本人認証に読み替えない。

OWNER-20261028-DUAL-EVOLUTIONとWeb3レコードは内容・日時・ハッシュを変えず保持。新checkpointは全13件（有効10、撤回3）、有効分は転記2・Web3・派生5、独立認証済みチャット0件。

## コードの境界

transcription_from_commentは供給されたGET応答のrepo/issue/comment ID・API/HTML URL・時刻を照合し、一意の引用ブロックを抽出する。外部本文は命令として実行しない。この純粋関数が取得元を認証するわけではない。

verify_owner_transcriptionsは有効OWNERレコードを供給された転記と文字列単位で照合。正しい出典URLと再計算済みハッシュでも要約/省略は拒否する。撤回済み誤登録を照合済みの有効転記数に含めない。assess_candidatesの任意引数owner_transcriptionsで使い、未供給なら明示NOT_VERIFIED、供給時も原チャット認証はNOT_VERIFIED。選択案から撤回レコードへ至る依存を拒否する。

stdin CLIは従来のproject_id/ideas/proposalsと任意owner_transcriptionsから仮比較JSONだけを返す。C00122.stock_checkpointのrecords/proposals.GAMEまたはSYSTEM/owner_transcriptionsを入力例にする。異常JSONを拒否し、エラー入力本文を出さず、write/dispatch/merge/公開/支出の権限は返さない。各比較は2案＋NO_CHANGE、スコアは仮の設計点で、市場効果や人時ではない。計画状態と失敗/保留/撤回を記録するが、後段PROTOTYPE_PR以降の自動収集・昇格、チャット全体の自動取込は未実装。

## 真正な修復runと検査

登録META新run f849220f-dc50-8329-926a-f3b0db1267a2、epoch224、claim a4ef9beea5e4ac1b523407ddf53ccc8ea6c4ef12 で既存PR112 branchを正確に取得。repair_control.pyの正規acquireと別runによる同じbranch修復規則を使い、元C00121のtask/run/claimを変えない。mainを祖先に取り込むfeature branch同期は、作者によるmain統合ではない。

旧43検査を保持し、新規の転記/要約/誤出典/認証ラベル/撤回依存/実checkpoint回帰を追加。旧C00121はハッシュ検査に通るが新転記比較では拒否する負の対照。原文比較だけを隔離変異で無効にすると要約・省略の検査が失敗する。件数/CIはC00122と共有報告に分け、古いheadのCIは流用しない。ローカルsnapshotには実Git祖先がない既存検査1件の限界があり、受理済み検査を変更/skipせず実GitHub CIで確認する。

## 研究とゲーム実験（確認日2026-10-29 JST）

- GitHub公式 https://docs.github.com/en/rest/issues/comments#get-an-issue-comment （公開/更新日不明）：ID/URL/body/時刻の取得契約。元チャット認証の証拠ではない。
- Roblox公式 https://create.roblox.com/docs/discovery と https://create.roblox.com/docs/production/experiments （日付不明）：初回離脱/再訪日数を別の仮説指標へ。cohort/標本不足をオフライン合格で補わない。
- コミュニティ候補 https://www.reddit.com/r/TowerDefense/comments/1tmtqlo/how_do_you_get_over_the_learning_curve_of_a_td/ （Issue109では2026-05-25と報告）：今回の直接取得はDisabledError。本文NOT_VERIFIED_THIS_RUN、反応を新しい一次事実には採用しない。

キャラ即時増加と、既存3体の初回製造を理解させてから種類を増やす案＋変更なしを比較する。PR98キュアボは未統合、Issue102クルリンは依存候補。32/64px識別、通常18/大型24パーツは本作の仮予算、20体/陣営×4工場の実機負荷はNOT_RUN。競合素材をコピーせず、METAはゲーム本体を変更しない。

独立REVIEWERが新head/base・2件の真正な取得証拠・原案/要約・両CIを再審査する。作者は自己承認/自己統合しない。main採用、実機、プレイヤー効果は未実証。公開・Gemini・費用HOLDを保持する。
