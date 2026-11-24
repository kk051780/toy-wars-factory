-- Keep existing neutral spawn choices reproducible without altering source.
math.randomseed(618)
-- Extra Roblox API fixtures for observing the existing BEAST loop. MoveTo
-- records the real command; it does not simulate Humanoid physics/navigation.
local third=Instance.new('Player');third.Name='CurseTeammate';third.UserId=44;third.Parent=Players
local thirdGui=Instance.new('PlayerGui');thirdGui.Parent=third
local thirdBag=Instance.new('Backpack');thirdBag.Parent=third
local thirdCharacter=Instance.new('Model');thirdCharacter.Name='CurseTeammateAvatar';thirdCharacter.Parent=workspace
local thirdHumanoid=Instance.new('Humanoid');thirdHumanoid.Parent=thirdCharacter
local thirdRoot=Instance.new('Part');thirdRoot.Name='HumanoidRootPart';thirdRoot.Parent=thirdCharacter
thirdCharacter.PrimaryPart=thirdRoot;third.Character=thirdCharacter
table.insert(currentPlayers,third)
local fourth=Instance.new('Player');fourth.Name='CurseOpponent';fourth.UserId=45;fourth.Parent=Players
local fourthGui=Instance.new('PlayerGui');fourthGui.Parent=fourth
local fourthBag=Instance.new('Backpack');fourthBag.Parent=fourth
local fourthCharacter=Instance.new('Model');fourthCharacter.Name='CurseOpponentAvatar';fourthCharacter.Parent=workspace
local fourthHumanoid=Instance.new('Humanoid');fourthHumanoid.Parent=fourthCharacter
local fourthRoot=Instance.new('Part');fourthRoot.Name='HumanoidRootPart';fourthRoot.Parent=fourthCharacter
fourthCharacter.PrimaryPart=fourthRoot;fourth.Character=fourthCharacter
table.insert(currentPlayers,fourth)
local beastMoves={}
function methods:MoveTo(at)
 if self.Parent and self.Parent:GetAttribute('EGGRUMBLE_BeastCompanion')==true then
  table.insert(beastMoves,{humanoid=self,at=now,target=at,line=debug.info(2,'l')})
 end
end
