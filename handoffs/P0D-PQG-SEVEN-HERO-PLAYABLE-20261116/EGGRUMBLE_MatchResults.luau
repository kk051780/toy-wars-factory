--!strict
-- EGGRUMBLE V3: independent post-match personal results, pure scoring + Studio-only presentation.
-- CLAIM: RESULT_SCREEN / SCORE_BALANCE only. No role, combat, castle, neutral AI, item or lobby rule writes.
-- KOs are real Humanoid deaths from SwarmCombat.kills, eggs/castles from the authoritative Rules.events.
-- Scores are deliberately capped PER category to prevent one grind from erasing the egg/castle objectives.
local Results={}

local SCORE={
 KO_CAP=1200, KO_RATE=6,
 EGG_STEAL_CAP=7, EGG_STEAL_RATE=170,
 EGG_DEPOSIT_CAP=8, EGG_DEPOSIT_RATE=120,
 CASTLE_CAP=3, CASTLE_RATE=440,
 SURVIVE=200, WIN=500,
}
Results.SCORE=SCORE

local function integer(value:any):number
 if type(value)~="number" or value~=value or value<0 or value==math.huge then return 0 end
 return math.floor(value)
end

local function points(row:any):number
 -- Losing a castle does not erase earlier player accomplishments.
 return math.min(SCORE.KO_CAP,row.ko*SCORE.KO_RATE)
  +math.min(SCORE.EGG_STEAL_CAP,row.stolen)*SCORE.EGG_STEAL_RATE
  +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE
  +math.min(SCORE.CASTLE_CAP,row.castlesDestroyed)*SCORE.CASTLE_RATE
  +(if row.alive then SCORE.SURVIVE else 0)
  +(if row.won then SCORE.WIN else 0)
end

function Results.build(state:any,kills:any):any
 assert(type(state)=="table" and type(state.castles)=="table" and type(state.events)=="table","invalid match")
 local rows={};local byId={}
 -- Fixed roster order gives deterministic tie breaks across servers and native tests.
 for _,id in ipairs(state.ids or {}) do
  local c=state.castles[id]
  if c then
   local row={id=tostring(id),team=c.team,alive=c.alive==true,
    isAI=c.isAI==true,ko=integer(kills and kills[id]),
    stolen=0,deposited=0,castlesDestroyed=0,won=false,score=0}
   rows[#rows+1]=row;byId[tostring(id)]=row
  end
 end
 for _,event in ipairs(state.events) do
  local kind=event.type
  if kind=="EGG_TAKEN" then
   local row=byId[tostring(event.thief)]
   if row then row.stolen+=integer(event.quantity) end
  elseif kind=="EGG_DEPOSIT" then
   local row=byId[tostring(event.owner)]
   if row then row.deposited+=integer(event.quantity) end
  elseif kind=="CASTLE_FALL" then
   local row=byId[tostring(event.attacker)]
   if row then row.castlesDestroyed+=1 end
  end
 end
 for _,row in ipairs(rows) do
  row.won=state.phase=="FINISHED" and state.winner~=nil and
   (if state.mode=="TEAM" then row.team==state.winner else row.id==tostring(state.winner))
  row.score=points(row)
 end
 table.sort(rows,function(a,b)
  if a.score~=b.score then return a.score>b.score end
  if a.ko~=b.ko then return a.ko>b.ko end
  return a.id<b.id
 end)
 return {mode=state.mode,phase=state.phase,winner=state.winner,rows=rows}
end

-- Called ONCE when a match ends, never as a screen-occupying in-game tutorial.
function Results.show(state:any,kills:any,players:{Player})
 if state.phase~="FINISHED" then return end
 local snapshot=Results.build(state,kills)
 local Players=game:GetService("Players")
 local palette={
  background=Color3.fromRGB(19,25,39),surface=Color3.fromRGB(31,41,62),
  ink=Color3.fromRGB(239,241,245),gold=Color3.fromRGB(255,217,122),
  muted=Color3.fromRGB(168,183,203),
 }
 local function text(parent:Instance,name:string,position:UDim2,size:UDim2,value:string,color:Color3,bold:boolean):TextLabel
  local label=Instance.new("TextLabel")
  label.Name=name;label.BackgroundTransparency=1;label.Position=position;label.Size=size
  label.Text=value;label.TextColor3=color;label.TextScaled=true;label.TextWrapped=false
  label.TextXAlignment=Enum.TextXAlignment.Left
  label.Font=if bold then Enum.Font.GothamBold else Enum.Font.Gotham
  label.Parent=parent
  return label
 end
 for _,player in ipairs(players) do
  if player.Parent and state.castles[tostring(player.UserId)] then
   local pg=player:FindFirstChildOfClass("PlayerGui")
   if pg then
    local previous=pg:FindFirstChild("EGGRUMBLE_MatchResults")
    if previous then previous:Destroy() end
    local gui=Instance.new("ScreenGui")
    gui.Name="EGGRUMBLE_MatchResults";gui.ResetOnSpawn=false
    gui.DisplayOrder=60;gui.IgnoreGuiInset=false;gui.Parent=pg
    local panel=Instance.new("Frame")
    panel.Name="PostMatchOnly";panel.AnchorPoint=Vector2.new(.5,.5)
    panel.Position=UDim2.fromScale(.5,.47);panel.Size=UDim2.fromScale(.90,.73)
    panel.BackgroundColor3=palette.background;panel.BorderSizePixel=0;panel.Parent=gui
    local size=Instance.new("UISizeConstraint");size.MaxSize=Vector2.new(650,570);size.MinSize=Vector2.new(250,235);size.Parent=panel
    local corner=Instance.new("UICorner");corner.CornerRadius=UDim.new(0,13);corner.Parent=panel
    local stroke=Instance.new("UIStroke");stroke.Color=palette.gold;stroke.Transparency=.35;stroke.Thickness=2;stroke.Parent=panel
    local teamLabel=if state.mode=="TEAM" then (tostring(state.winner).." の勝利") else "最後の城が勝利"
    text(panel,"Title",UDim2.fromScale(.05,.035),UDim2.fromScale(.9,.085),
     "EGGRUMBLE  試合結果",palette.gold,true)
    text(panel,"Winner",UDim2.fromScale(.05,.135),UDim2.fromScale(.9,.063),
     teamLabel,palette.ink,true)
    local ownId=tostring(player.UserId)
    local own=nil
    for _,row in ipairs(snapshot.rows) do if row.id==ownId then own=row;break end end
    if own then
     text(panel,"Personal",UDim2.fromScale(.05,.22),UDim2.fromScale(.9,.073),
      string.format("あなた: %d点  |  KO %d  卵奪取 %d  納入 %d  城撃破 %d",
       own.score,own.ko,own.stolen,own.deposited,own.castlesDestroyed),palette.gold,true)
    end
    text(panel,"RankCaption",UDim2.fromScale(.05,.32),UDim2.fromScale(.9,.053),
     "順位  |  個人得点  |  中立KO  |  卵奪取 / 納入  |  城",palette.muted,false)
    for i=1,math.min(6,#snapshot.rows) do
     local row=snapshot.rows[i]
     local who=if row.id==ownId then "自分" else
      (if row.isAI then "AI "..row.id else
       (Players:GetPlayerByUserId(tonumber(row.id) or -1) and
        Players:GetPlayerByUserId(tonumber(row.id) or -1).DisplayName or "プレイヤー"))
     local label=string.format("%d位  %s  | %d点  | KO%d  | 卵%d/%d  | 城%d",
      i,who,row.score,row.ko,row.stolen,row.deposited,row.castlesDestroyed)
     local at=.385+(i-1)*.082
     local plate=Instance.new("Frame")
     plate.Name="Rank_"..i;plate.Size=UDim2.fromScale(.9,.073)
     plate.Position=UDim2.fromScale(.05,at)
     plate.BackgroundColor3=palette.surface
     plate.BackgroundTransparency=if row.id==ownId then .02 else .20
     plate.BorderSizePixel=0;plate.Parent=panel
     text(plate,"Details",UDim2.fromScale(.018,.06),UDim2.fromScale(.96,.88),
      label,if row.id==ownId then palette.gold else palette.ink,row.id==ownId)
    end
    text(panel,"Footer",UDim2.fromScale(.05,.89),UDim2.fromScale(.9,.068),
     "中立KO・卵・城を公平評価  |  20秒後に自動で閉じます",palette.muted,false)
    task.delay(20,function() if gui.Parent then gui:Destroy() end end)
   end
  end
 end
end

return Results
