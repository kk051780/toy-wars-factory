#!/usr/bin/env python3
"""Build single Command Bar installer directly from audited source files."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
src=root/'src'; dest=root/'studio/TOY_WARS_v1_2_ONE_CLICK_INSTALLER.lua'
def embed(text):
    bracket='='
    while f']{bracket}]' in text or f'[{bracket}[' in text: bracket+='='
    return f'[{bracket}[\n{text}\n]{bracket}]'
modules={
    'balance': (src/'ToyWarsBalance.lua').read_text(encoding='utf-8'),
    'server': (src/'ToyWarsServer.server.lua').read_text(encoding='utf-8'),
    'hud': (src/'ToyWarsHUD.client.lua').read_text(encoding='utf-8'),
    'smoke': (src/'ToyWarsSmokeTest.server.lua').read_text(encoding='utf-8'),
}
installer='''-- TOY WARS FACTORY v1.2 / INSTALLER FOR ROBLOX STUDIO EDIT-MODE COMMAND BAR
-- Execute ONCE in EDIT MODE. Installer is repeatable and removes older prototypes.
-- Uses only built-in Roblox instances, no external assets/network/API keys.
-- NOTE: this package is Studio-UNVERIFIED.
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")
local StarterGui = game:GetService("StarterGui")
local function drop(parent, name)
    local old=parent:FindFirstChild(name)
    if old then old:Destroy() end
end
drop(ServerScriptService,"ToyWorksServer")
drop(ServerScriptService,"ToyWarsServer")
drop(ServerScriptService,"ToyWarsSmokeTest")
drop(StarterGui,"ToyWorksHUD")
drop(StarterPlayer.StarterPlayerScripts,"ToyWarsHUD")
drop(ReplicatedStorage,"ToyWarsBalance")
drop(ReplicatedStorage,"ToyWarsSelectUnit")
local oldWorld=workspace:FindFirstChild("ToyWorksWorld")
if oldWorld then oldWorld:Destroy() end
local world=workspace:FindFirstChild("ToyWarsWorld")
if world then world:Destroy() end

local balance=Instance.new("ModuleScript")
balance.Name="ToyWarsBalance"
balance.Source=@@balance@@
balance.Parent=ReplicatedStorage

local event=Instance.new("RemoteEvent")
event.Name="ToyWarsSelectUnit"
event.Parent=ReplicatedStorage

local server=Instance.new("Script")
server.Name="ToyWarsServer"
server.Enabled=false
server.Source=@@server@@
server.Parent=ServerScriptService

local hud=Instance.new("LocalScript")
hud.Name="ToyWarsHUD"
hud.Enabled=false
hud.Source=@@hud@@
hud.Parent=StarterPlayer.StarterPlayerScripts

local smoke=Instance.new("Script")
smoke.Name="ToyWarsSmokeTest"
smoke.Enabled=false
smoke.Source=@@smoke@@
smoke.Parent=ServerScriptService

server.Enabled=true
hud.Enabled=true
smoke.Enabled=true
print("TWF_INSTALL_OK v1.2 - press Play in Studio and inspect Output for TWF_QA_SUMMARY")
'''
for key,value in modules.items(): installer=installer.replace('@@'+key+'@@',embed(value))
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_bytes(installer.encode('utf-8'))
manifest={key:hashlib.sha256(value.encode()).hexdigest() for key,value in modules.items()}
manifest['installer_sha256']=hashlib.sha256(installer.encode()).hexdigest()
(root/'evidence').mkdir(parents=True,exist_ok=True)
(root/'evidence/SOURCE_MANIFEST.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print('built',dest,'bytes',len(installer))
