#!/usr/bin/env python3
"""Generate a deterministic, portable project handoff; run from any GitHub CI checkout."""
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from verify_status import status_ok

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"status"
OUT.mkdir(exist_ok=True)

def read_json(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def main():
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
      "schema":1,"canonical_repo":repo,"source_revision":code_sha,
      "source_metrics":{"files":files,"lines":lines,"bytes":size},
      "delta_from_initial_baseline":delta,"characters":character_summary,
      "game":state["game"],"autonomous_coding":state["autonomous_coding"],
      "verification":verified,"release_decision":state["release_decision"],
      "next":state["next"],
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
      "- 自律AI開発: "+state["autonomous_coding"]["status"],
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
    fields+=["","## 新しいチャットでAIが必ず行う引き継ぎ手順",
      "1. GitHubコネクタでこのファイルと status/LATEST_STATE.json、PROJECT_STATE.json、AGENTS.md、config/quality_policy.json を読み込む。",
      "2. 最新 main、Actions実行結果、PR、Issuesを直接確認し、生成ファイルのsource_revisionと整合させる。",
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
