#!/usr/bin/env python3
"""Generate a deterministic, portable project handoff; run from any GitHub CI checkout."""
import json
import hashlib
import subprocess
from pathlib import Path
from verify_status import status_ok

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"status"
OUT.mkdir(exist_ok=True)

def read_json(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def main():
    if git("rev-parse","--is-shallow-repository") == "true":
        raise SystemExit("FAIL: shallow Git history cannot identify the source revision; fetch full history first")
    state=read_json("PROJECT_STATE.json")
    chars=read_json("config/characters.json")["characters"]
    policy=read_json("config/quality_policy.json")
    repo=state["github"]["repository"]
    if not status_ok(state["autonomous_coding"],repo):
        raise SystemExit("FAIL: autonomous-agent status is inconsistent")
    if state["release_decision"] != "HOLD_ENGINE_UNVERIFIED" or not policy["never_auto_publish"]:
        raise SystemExit("FAIL: release guard has been changed; owner approval needed")
    sources=sorted((ROOT/"src").glob("*.lua"))+sorted((ROOT/"src").glob("*.luau"))
    files=len(sources)
    lines=sum(len(p.read_text(encoding="utf-8").splitlines()) for p in sources)
    size=sum(p.stat().st_size for p in sources)
    # Ignore state-snapshot-only commits, to prevent an endless generated-file commit loop.
    code_sha=git("log","-1","--format=%H","--","src","tests","tools","docs","config","PROJECT_STATE.json","AGENTS.md",".github","history")
    baseline=read_json("history/C00001_bootstrap.json")["pve_source"]
    delta={"files":files-baseline["files"],"lines":lines-baseline["lines"],"bytes":size-baseline["bytes"]}
    verified=state.get("verification",{})
    character_summary=[{"name":u["name_ja"],"id":u["id"],"role":u["role"],"shape":u["shape"],"status":u["status"]} for u in chars]
    record={
      "schema":2,"canonical_repo":repo,"source_revision":code_sha,
      "source_metrics":{"files":files,"lines":lines,"bytes":size},
      "delta_from_initial_baseline":delta,"characters":character_summary,
      "game":state["game"],"autonomous_coding":state["autonomous_coding"],
      "verification":verified,"release_decision":state["release_decision"],
      "next":state["next"],
      "resume_checkpoint":state.get("resume_checkpoint",{}),
      "review_queue":state.get("review_queue",[]),
      "cloud_game_repair":state.get("cloud_game_repair",{}),
      "pending_approvals":state.get("pending_approvals",{}),
      "execution_coordination":state.get("execution_coordination",{}),
      "system_review":state.get("system_review",{}),
      "approval_authority":state.get("approval_authority",{}),
      "independent_integration":state.get("independent_integration",{}),
      "important":"Actions / Roblox Studio evidence must be checked independently. A generated status page is not proof of runtime health."
    }
    (OUT/"LATEST_STATE.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    fields=[
      "# TOY WARS FACTORY — 新チャット用・継続引き継ぎ",
      "",
      "このファイルはGitHubの最新設計・実装状態から自動再生成する。過去チャットの添付や要約よりGitHubを優先。",
      "",
      "## 現在地",
      "- GitHub: https://github.com/"+repo,
      "- 基準ソースコミット: "+code_sha,
      "- ゲーム公開可否: "+state["release_decision"],
      "- 既存GitHub AIワークフロー: "+state["autonomous_coding"]["status"],
      "- ChatGPT定期ゲーム修正: "+state.get("cloud_game_repair",{}).get("status","NOT_CONFIGURED"),
      "- PvE: "+state["game"]["pve"],
      "- PvP: "+state["game"]["pvp"],
      "- 協力: "+state["game"]["coop"],
      "",
      "## サイズゲート（初回基準との差分）",
      "- ソース: "+str(files)+" ファイル / "+str(lines)+" 行 / "+str(size)+" bytes",
      "- 基準差分: files "+str(delta["files"])+", lines "+str(delta["lines"])+", bytes "+str(delta["bytes"]),
      "- サイズ増加は品質の証明ではない。合理的削減は問題ない。機能・テストの欠損は別途監査。",
      "",
      "## キャラクター（見た目の実機検査ではない）",
    ]
    for u in character_summary:
        fields.append("- "+u["name"]+": "+u["role"]+" / "+u["shape"]+" / "+u["status"])
    fields+=["","## 品質の実測範囲",
      "- Studio: "+verified.get("roblox_studio","UNKNOWN"),
      "- マルチクライアント: "+verified.get("two_client_multiplayer","UNKNOWN"),
      "- スマホ表示: "+verified.get("mobile_visual","UNKNOWN"),
      "- 記録済GitHub QA: "+verified.get("github_actions","UNKNOWN")+"（最新Actionsを別途確認すること）",
      "",
      "## 次の開発優先事項"]
    fields+=["- "+x for x in state.get("next",[])]
    authority=state.get("approval_authority",{})
    if authority.get("decision_owner")=="ASSISTANT":
        fields+=["", "## 委譲された承認判断",
          "- 通常のゲーム/体制開発・main統合は助手が判断する。所有者への承認返信は不要。",
          "- 作者と別タスクの審査役が現在headのCIと実差分を確認し、1件ずつ統合してmainを検査する。",
          "- 完成ロードマップと日次の実測/最新WEB一次資料から次を選ぶ。客観的な品質条件・費用上限は免除しない。"]
    approvals=state.get("pending_approvals",{})
    if approvals.get("items"):
        delegated=approvals.get("decision_owner")=="ASSISTANT"
        fields+=["", "## 現在の自動審査・統合待ち（観測時点）" if delegated else "## 現在の取り込み承認待ち（観測時点）",
          "最新一覧: https://github.com/"+repo+"/blob/twf-repair-coordinator/status/PENDING_APPROVALS.md",
          "", "| PR | 内容 | 現在headのCI |", "| --- | --- | --- |"]
        for item in approvals["items"]:
            summary=item["summary"].replace("|","／").replace("\n"," ")
            fields.append(f"| [#{item['number']}]({item['url']}) | {summary} / {item['kind']} | [合格]({item['ci_url']}) |")
        fields+=["", "独立審査役が処理する。所有者への承認返信は不要。" if delegated else "承認する場合の返信: "+approvals["approval_text"],
          "対象headのmain取り込みのみ。公開・課金・外部モデルは含まない。現在GitHubでhead/CIを再確認する。", ""]
    coordination=state.get("execution_coordination",{})
    if coordination:
        fields+=["", "## 手動goと自動実行の競合防止",
          "- 手動goは既存ゲームタスクへ統一。実行中は追加起動せず確認へ合流する。",
          "- 共通ロック: twf-repair-coordinator / ops/REPAIR_COORDINATOR.json。expected_sha・force=false・epochを必須にする。",
          "- ゲーム修正・日次体制改善・独立審査・手動統合が同じロックを使う。docs/REPAIR_COORDINATION.mdを読む。"]
    system_review=state.get("system_review",{})
    if system_review:
        fields+=["", "## 体制とゲームの日次改善",
          "- タスク: "+system_review.get("task_id","UNKNOWN")+" / 毎朝（Asia/Tokyo）",
          "- 実測の欠陥と最新WEB一次資料から、体制の最小修正・回帰検査・draft PR、ゲームの根拠付き実験候補を進める。",
          "- 現在の方式を最適と固定せず、前後の結果と未解決点を記録する。docs/SYSTEM_REVIEW.mdを読む。"]
    checkpoint=state.get("resume_checkpoint",{})
    if checkpoint:
        fields+=["","## 最新の再開地点（観測時点の記録）",
          "- 記録: "+checkpoint["id"]+" / "+checkpoint["observed_on"],
          "- 照合したmain: "+checkpoint["observed_main_revision"],
          "- 証拠: "+checkpoint["evidence_record"]]
        fields+=["- 完了: "+item for item in checkpoint.get("completed",[])]
        auth=checkpoint.get("authorization",{})
        fields+=["- 新規推論承認: "+str(auth.get("new_inference_authorized",False)),
          "- 定期AI承認: "+str(auth.get("recurring_ai_authorized",False)),
          "- 自動マージ承認: "+str(auth.get("automatic_merge_authorized",False)),
          "- Roblox公開承認: "+str(auth.get("roblox_publish_authorized",False)),
          "- 再実行の前提: "+auth.get("prerequisite","UNKNOWN"),
          "- 再開する作業: "+checkpoint["next_action"]]
        fields+=["- 未確認・制限: "+item for item in checkpoint.get("limitations",[])]
    queue=state.get("review_queue",[])
    if queue:
        fields+=["","## 未マージの提案（現在のPR状態はGitHubで再確認）"]
        for item in queue:
            fields.append("- PR #"+str(item["number"])+": "+item["status"]+" / "+
              item["origin"]+" / "+item["purpose"]+" / "+item["url"])
            if item.get("qa_url"):
                fields.append("  - QA: "+item["qa_scope"]+" "+item["qa_url"])
        fields.append("- mainの実装と未マージPRの提案を合算しない。Geminiの成果と別の修正を区別する。")
    fields+=["","## 新しいチャットでAIが必ず行う引き継ぎ手順",
      "1. まずGitHubの現在main HEAD、AGENTS.md、PROJECT_STATE.json、config/quality_policy.json、最新PR/CIを読む。mainがコード・方針の正本。",
      "読取り専用の別経路: 成功したmainのhandoff-sync GitHub Actions runの toy-wars-handoff 成果物を同じrunから取得できる場合、ZIPの2つのstatusデータと任意のSHA256 manifestを検証。schema=2、canonical_repo、HOLD_ENGINE_UNVERIFIED、source_revisionとmain compareでstatus/以外の差が無いことまで確認。失敗・期限切れ・不明はUNTRUSTED_STALE。実GitHub書込みトークンは不要。",
      "2. 補助的なtwf-handoff-snapshots/status/CHAT_HANDOFF.mdとstatus/LATEST_STATE.jsonを同一不変commitから取得。schema=2・canonical_repo・HOLD_ENGINE_UNVERIFIED・source_revisionを検証し、GitHub compareでsource_revision以降のmain変更がstatus/のみと証明できない場合UNTRUSTED_STALEとして棄却。512コミット超過時はtwf-handoff-snapshots-g0002等の連続した世代を列挙し、全世代の2ファイル100644/512直列履歴と後続rootのprior-snapshot-tip旧tip連鎖を照合し、最新世代の単一不変SHAを使う。検査不能ならUNTRUSTED_STALE。ブランチ不在ならmainのstatusは古い参考値、現在のmain/PR/CIを直接確認。",
      "3. 正本はGitHub。毎回コード変更と品質証拠、サイズ差分、キャラクター監査、再発防止を積み上げる。",
      "4. 無人AIコード生成・Studio試験・面白さの実測を根拠なしに合格扱いしない。",
      "5. プレイヤー向け公開・課金・権限拡張・品質基準緩和にはユーザー承認が必要。",
      "",
      "## ユーザー操作",
      "同じChatGPTプロジェクトの新しいチャットで『TOY WARS再開』と送れば、AIはGitHubへアクセスして続きから着手する。",
      "ただし別チャットへの無条件の自動コンテキスト注入はプラットフォーム上保証されない。",
      "無人作業はGitHub側の認証済みエージェント・ワークフローが実際に稼働してから可能。",
      ""]
    (OUT/"CHAT_HANDOFF.md").write_text("\n".join(fields),encoding="utf-8")
    print("HANDOFF_OK source="+code_sha+" files="+str(files)+" lines="+str(lines)+" bytes="+str(size)+" agent="+state["autonomous_coding"]["status"])

if __name__=="__main__": main()
