--!strict
-- A separate native Luau regression. Existing PR #487 owner may load it
-- after scoped authorization using local Results.lua (ScoreBalance module).
-- Runner example: assert(require('./EGGRUMBLE_RelayScoreRegression.spec')(require('./Results')))
return function(Results:any):boolean
 local assertions=0
 local function eq(actual:any,want:any,case:string)
  assertions+=1
  assert(actual==want,case..' expected '..tostring(want)..' got '..tostring(actual))
 end
 local function scenario(events:{any}):any
  local state={mode='TEAM',phase='ACTIVE',winner=nil,ids={'a','b','enemy'},
   castles={a={alive=true,team='RED'},b={alive=true,team='RED'},enemy={alive=true,team='BLUE'}},
   events=events}
  local result=Results.build(state,{})
  local resultById={}
  for _,row in ipairs(result.rows) do resultById[row.id]=row end
  return resultById
 end
 local relay={type='EGG_RELAY',from='a',to='b',quantity=1,seq=1}
 local after=scenario({
  {type='EGG_TAKEN',thief='a',source='enemy',quantity=1},relay,
  {type='EGG_TAKEN',thief='a',source='FIELD',quantity=1},
  {type='EGG_DEPOSIT',owner='a',quantity=1}})
 eq(after.a.stolen,1,'raw raid history kept after teammate relay')
 eq(after.a.securedSteals,0,'donor later field deposit cannot claim old raid')
 eq(after.a.score,320,'donor receives only survival 200 + deposit 120')
 eq(after.b.pendingField,1,'recipient relay provenance conservative')
 local receiver=scenario({
  {type='EGG_TAKEN',thief='a',source='enemy',quantity=1},relay,
  {type='EGG_DEPOSIT',owner='b',quantity=1}})
 eq(receiver.b.securedSteals,0,'receiver never earns donor self-steal credit')
 eq(receiver.b.deposited,1,'relay recipient still gets genuine delivery')
 eq(receiver.b.score,320,'receiver gets only survival + genuine delivery')
 local oneLeft=scenario({
  {type='EGG_TAKEN',thief='a',source='enemy',quantity=2},relay,
  {type='EGG_DEPOSIT',owner='a',quantity=1}})
 eq(oneLeft.a.pendingSteals,0,'remaining stolen egg consumed on deposit')
 eq(oneLeft.a.securedSteals,1,'one retained egg legitimately returned')
 eq(oneLeft.a.score,490,'survival + real raid + real deposit')
 local incomingBeforeOwnRaid=scenario({
  {type='FIELD_EGG_TAKEN',owner='a',eggId='FIELD_RELAY_1'},relay,{type='EGG_TAKEN',thief='b',source='enemy',quantity=1},
  {type='EGG_DEPOSIT',owner='b',quantity=1}})
 eq(incomingBeforeOwnRaid.b.securedSteals,0,'unknown incoming egg conservatively spent first')
 eq(incomingBeforeOwnRaid.b.pendingSteals,1,'own later raid awaits real deposit')
 local bothReturned=scenario({
  {type='FIELD_EGG_TAKEN',owner='a',eggId='FIELD_RELAY_2'},relay,{type='EGG_TAKEN',thief='b',source='enemy',quantity=1},
  {type='EGG_DEPOSIT',owner='b',quantity=2}})
 eq(bothReturned.b.securedSteals,1,'both deposits prove one own raid')
 local malformed=scenario({
  {type='EGG_TAKEN',thief='a',source='enemy',quantity=1},
  {type='EGG_RELAY',from='a',to='unknown',quantity=1},
  {type='EGG_DEPOSIT',owner='a',quantity=1}})
 eq(malformed.a.securedSteals,0,'malformed receipt fails closed')
 local drop=scenario({{type='FIELD_EGG_TAKEN',owner='a',eggId='FIELD_RELAY_3'},relay,{type='EGG_DROP',owner='b',quantity=1}})
 eq(drop.b.pendingField,0,'recipient drop clears unknown egg accounting')
 local noRelay=scenario({
  {type='EGG_TAKEN',thief='a',source='enemy',quantity=1},
  {type='EGG_DEPOSIT',owner='a',quantity=1}})
 eq(noRelay.a.securedSteals,1,'existing direct theft deposit preserved')
 print('EGGRUMBLE_RELAY_SCORE_NATIVE_REGRESSION_PASS assertions='..assertions)
 return true
end
