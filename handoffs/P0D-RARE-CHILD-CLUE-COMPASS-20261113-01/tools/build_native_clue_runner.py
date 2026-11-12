"""Reuses #239's ACTUAL whole-original-server native Luau QA harness.
No game-source logic is copied/reimplemented in Python. New trial's ORIGINAL
server and Clue modules run in the same native interpreter with external Roblox
engine service doubles. Test-only optin overrides a flag in generated QA only.
"""
from pathlib import Path
import argparse,importlib.util
ROOT=Path(__file__).resolve().parents[1]
PARENT_HARNESS=ROOT.parent/"P0D-RARE-BOOK-FULL-SERVER-QA-20261112-01/tools/build_full_server_runner.py"
spec=importlib.util.spec_from_file_location("p0d_original_full_server_source_qa",PARENT_HARNESS)
assert spec and spec.loader
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

TRIAL_SERVER=ROOT/"src/RareDiscoveryCluePreview.server.luau"
CLUE=ROOT/"src/RareCluePolicy.luau"
CLUE_HUD=ROOT/"src/RareClueHUD.luau"
base.FILES.extend([
    ("Clue",CLUE,"return Clue"),
    ("ClueHUD",CLUE_HUD,"return HintHUD"),
])
base.SERVER=TRIAL_SERVER
original_wrap=base.wrap_source
original_build=base.build
active_source_mutation={"kind":None}

def source_wrap(name,body):
    if name=="Clue":
        token="local Book = require(script.Parent.RareDiscoveryBook)"
        if body.count(token)!=1:raise RuntimeError("original Clue requires exact existing Book")
        body=body.replace(token,"local Book = Book",1)
        if active_source_mutation["kind"]=="BAD_WRONG_HUB_CLUE":
            a='Clue.STUDIO_HUB = "テスト: みどりの ひろばで そらをみよう"'
            b='Clue.STUDIO_HUB = "テスト: あかい おしろで まちながら そらをみよう"'
            if body.count(a)!=1:raise ValueError("missing exact original hub cue")
            body=body.replace(a,b,1)
        elif active_source_mutation["kind"]=="BAD_PROMISE_COINS":
            a='Clue.ALL_DONE = "4/4！みつけたね。 べつの みちも あるいてみよう"'
            b='Clue.ALL_DONE = "4/4！みつけたね。 コイン100こを もらえるよ！"'
            if body.count(a)!=1:raise ValueError("missing exact original completion cue")
            body=body.replace(a,b,1)
        elif active_source_mutation["kind"]=="BAD_DAILY_PRESSURE":
            a='Clue.ALL_DONE = "4/4！みつけたね。 べつの みちも あるいてみよう"'
            b='Clue.ALL_DONE = "4/4！まいにち こないと きえちゃうよ！"'
            if body.count(a)!=1:raise ValueError("missing exact original completion cue")
            body=body.replace(a,b,1)
    elif name=="ClueHUD":
        token="local Clue = require(script.Parent.RareCluePolicy)"
        if body.count(token)!=1:raise RuntimeError("original ClueHUD requires exact original Clue")
        body=body.replace(token,"local Clue = Clue",1)
        if active_source_mutation["kind"]=="BAD_HINT_HIDDEN":
            a='hint.Text=guidance.title.."\\n"..guidance.text'
            b='hint.Text="   "'
            if body.count(a)!=1:raise ValueError("missing original actual hint rendering")
            body=body.replace(a,b,1)
        elif active_source_mutation["kind"]=="BAD_CLUE_GUI_TOO_SMALL":
            a='panel.Size=UDim2.fromOffset(222,244)'
            b='panel.Size=UDim2.fromOffset(222,191)'
            if body.count(a)!=1:raise ValueError("missing original actual panel dimension")
            body=body.replace(a,b,1)
        elif active_source_mutation["kind"]=="BAD_DUPLICATE_CLUE_ROW":
            a='if not existing then'
            b='if true then'
            if body.count(a)!=1:raise ValueError("missing original hint idempotent guard")
            body=body.replace(a,b,1)
        elif active_source_mutation["kind"]=="BAD_TEST_MODE_WORLD":
            a='HintHUD.MODE = "TEST_HUB"'
            b='HintHUD.MODE = "WORLD"'
            if body.count(a)!=1:raise ValueError("missing original true test scope")
            body=body.replace(a,b,1)
    return original_wrap(name,body)
base.wrap_source=source_wrap

def real_clue_server_builder(trial):
    tokens=[
      'local Clue=require(script.Parent.RareCluePolicy)',
      'local ClueHUD=require(script.Parent.RareClueHUD)',
    ]
    for token in tokens:
        if trial.count(token)!=1:raise ValueError("original standalone clue server lost module require: "+token)
        name="ClueHUD" if "ClueHUD" in token else "Clue"
        trial=trial.replace(token,"local "+name+"="+name,1)
    return original_build(trial)
base.build=real_clue_server_builder

ADDITIONAL_TESTS=r'''
local good,why=Clue.validate()
ok(good,"true original Clue source safe "..tostring(why))
ok(ClueHUD.MODE=="TEST_HUB","owner-only QA really tells children the hub location")
ok(Clue.STUDIO_HUB=="テスト: みどりの ひろばで そらをみよう",
    "don't misdirect players to an inaccessible castle in the QA bench")
ok(Clue.ALL_DONE=="4/4！みつけたね。 べつの みちも あるいてみよう",
    "no fake payout, FOMO or timed collectible pressure after completing the book")
local blank=Book.fresh()
local first=Clue.next(blank,"TEST_HUB")
ok(first.kind=="HINT" and first.id=="SPACE" and first.scope=="TEST_HUB",
   "fresh user gets correct world candidate in honest QA mode")
local worldFirst=Clue.next(blank,"WORLD")
ok(worldFirst.id=="SPACE" and
   string.find(worldFirst.text,"ほしの おしろ",1,true)~=nil,
   "future original realm clue uses a REAL world landmark without exact coordinates")
ok(Clue.next(blank,"INVALID").kind=="INVALID","invalid hint contexts fail closed")
local seen=blank
for i,id in ipairs(Book.ORDER) do
    local nextHint=Clue.next(seen,"WORLD")
    ok(nextHint.kind=="HINT" and nextHint.id==id,
       "original source-only hint selects first not-yet-found among four realms")
    local newBook,status=Book.accept(seen,id,i)
    ok(status=="NEW","real original Book accepts next distinct candidate")
    seen=newBook
end
local completed=Clue.next(seen,"TEST_HUB")
ok(completed.kind=="DONE" and completed.id==nil and completed.text==Clue.ALL_DONE,
   "completed users get only a gentle replay suggestion, not a reset or rewards")
ok(seen.count==4,"hint logic didn't mutate the original immutable Book")
local function panelFor(player)
    local playerGui=player:FindFirstChildOfClass("PlayerGui")
    local gui=playerGui and playerGui:FindFirstChild("RareDiscoverySessionBook")
    return gui and gui:FindFirstChild("NotebookPanel")
end
local panelA=panelFor(userA)
local panelB=panelFor(userB)
local panelNew=panelFor(newlyJoined)
ok(panelA and panelB and panelNew,"three independently mounted honest source hint GUIs")
local hintA=panelA:FindFirstChild("NextGentleClue")
local hintB=panelB:FindFirstChild("NextGentleClue")
local hintNew=panelNew:FindFirstChild("NextGentleClue")
ok(hintA and hintB and hintNew,"each user gets one original hint label")
ok(panelA.Size.X==222 and panelA.Size.Y==244,
   "one additional hint row is physically laid out under the four original rows")
ok(panelB.Size.X==222 and panelB.Size.Y==244,
   "second user also gets same sized readable frame")
ok(hintA.TextWrapped==true and hintB.TextWrapped==true,
   "long Japanese child text wraps instead of clipping into buttons")
ok(string.find(hintA.Text,Clue.ALL_DONE,1,true)~=nil,
   "player A after four discoveries sees truthful completed source hint")
ok(string.find(hintB.Text,Clue.ALL_DONE,1,true)~=nil,
   "independent second Player after four discoveries sees own completed hint")
ok(string.find(hintNew.Text,"みどりの ひろば",1,true)~=nil,
   "brand-new Player at 0/4 gets truthful central QA world clue")
ok(string.find(hintNew.Text,"コイン",1,true)==nil and
   string.find(hintB.Text,"コイン",1,true)==nil,
   "no invented rare rewards/coins shown in any source child hint")
ok(string.find(hintB.Text,"まいにち",1,true)==nil,
   "no guilt/shame/FOMO daily-streak compulsion")
local beforeCount=0
for _,part in ipairs(panelB:GetChildren()) do
    if part.Name=="NextGentleClue" then beforeCount+=1 end
end
ok(beforeCount==1,"initial source hint UI uses exactly one child row")
ok(ClueHUD.mount(userB,seen)==true and ClueHUD.mount(userB,seen)==true,
   "repeated GUI mount attempts are safe even after avatar/session events")
local afterCount=0
for _,part in ipairs(panelB:GetChildren()) do
    if part.Name=="NextGentleClue" then afterCount+=1 end
end
ok(afterCount==1,"repeated source UI montage doesn't stack hint panels")
originalPrint("P0D_RARE_CHILD_CLUE_FULL_NATIVE_PASS assertions="..tostring(assertCount)..
    " original_game_server=true simulated_players=2 hints_without_rewards=true")
'''
# Reuse all 85 original real game-server integration asserts and add the
# original CluePolicy + ClueHUD assertions on the same server test cases.
base.TESTS=base.TESTS+"\n"+ADDITIONAL_TESTS

def build_case(name,body,mutation=None):
    active_source_mutation["kind"]=mutation
    generated=base.build(body)
    active_source_mutation["kind"]=None
    return generated

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    a=p.parse_args()
    output=Path(a.output)
    output.mkdir(parents=True,exist_ok=True)
    source=TRIAL_SERVER.read_text(encoding="utf-8")
    if not source.startswith("--!strict\n"):raise ValueError("original candidate must remain strict")
    server_mutations={
        "positive":(source,None),
        "BAD_SERVER_HINT_WRONG_PLAYER":(
            source.replace("ClueHUD.update(player,nextBook)",
                 "ClueHUD.update(Players:GetPlayers()[1],nextBook)",1),None),
        "BAD_SERVER_HINT_SHOWS_EMPTY_BOOK":(
            source.replace("ClueHUD.update(player,nextBook)",
                 "ClueHUD.update(player,Book.fresh())",1),None),
    }
    if len({s for s,_ in server_mutations.values()})!=len(server_mutations):
        raise ValueError("original server mutants did not change")
    for key,(candidate,mutation) in server_mutations.items():
        f=output/(key+".luau")
        f.write_text(build_case(key,candidate,mutation),encoding="utf-8")
        print("P0D_CLUE_ORIGINAL_SERVER_CASE",key)
    for key in (
       "BAD_WRONG_HUB_CLUE","BAD_PROMISE_COINS","BAD_DAILY_PRESSURE",
       "BAD_HINT_HIDDEN","BAD_CLUE_GUI_TOO_SMALL","BAD_DUPLICATE_CLUE_ROW",
       "BAD_TEST_MODE_WORLD",
    ):
        f=output/(key+".luau")
        f.write_text(build_case(key,source,key),encoding="utf-8")
        print("P0D_CLUE_ORIGINAL_MODULE_MUTANT",key)
    if len(list(output.glob("*.luau")))!=10:
        raise AssertionError("all 1 positive +9 corrupted real source cases required")
if __name__=="__main__":
    main()
