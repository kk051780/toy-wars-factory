#!/usr/bin/env python3
"""Extract the exact selected 41-script Realm weather helper for real native VM."""
from __future__ import annotations

import argparse
from pathlib import Path

from patch_weather41 import (
    REALM,RENDER,REALM_HELPER,REALM_NEW,STAGE_INSERT,flatten,
)

HARNESS = r'''
local WEATHER_PHASE_SECONDS=35
__REAL_AUTHOR_HELPER__
local world={}
local stage={Parent=world,attrs={
 GQ802_WeatherPolicy="DW_STAGE_V1",
 GQ802_WeatherStart=1000,
 GQ802_WeatherPhase2="STORM",
 GQ802_WeatherPhase3="METEOR"
}}
function world:FindFirstChild(name)
 assert(name=="GQ802_VISUAL_TILE_STAGE_V1")
 return self.stage
end
function stage:GetAttribute(key) return self.attrs[key] end
world.stage=stage
local function check(t,expectedWeather,expectedTheme)
 local weather,theme=weatherFromVerifiedStage(t,1000,world)
 assert(weather==expectedWeather,
  "RED_STORM_THEME_ALIASES "..tostring(t).." got "..tostring(weather).." expected "..expectedWeather)
 assert(theme==expectedTheme,"RED_WEATHER_THEME_RECEIPT "..tostring(theme))
end
check(1000,"CLEAR","CLEAR")
check(1119,"CLEAR","CLEAR")
check(1120,"THUNDER","STORM")
check(1239,"THUNDER","STORM")
check(1240,"THUNDER","METEOR")
stage.attrs.GQ802_WeatherPhase2="SNOW"
stage.attrs.GQ802_WeatherPhase3="AURORA"
check(1120,"WIND","SNOW")
check(1240,"CLEAR","AURORA")
stage.attrs.GQ802_WeatherPhase2="RAIN"
stage.attrs.GQ802_WeatherPhase3="STORM"
check(1120,"RAIN","RAIN")
check(1240,"THUNDER","STORM")
stage.attrs.GQ802_WeatherPolicy="UNTRUSTED"
check(1071,"RAIN","LEGACY")
stage.attrs.GQ802_WeatherPolicy="DW_STAGE_V1"
stage.attrs.GQ802_WeatherStart=math.huge
check(1036,"WIND","LEGACY")
stage.attrs.GQ802_WeatherStart=1000
stage.attrs.GQ802_WeatherPhase2="UNKNOWN"
check(1106,"THUNDER","LEGACY")
stage.attrs.GQ802_WeatherPhase2="RAIN"
stage.Parent=nil
check(1000,"CLEAR","LEGACY")
stage.Parent=world
world.stage=nil
check(1071,"RAIN","LEGACY")
world.stage=stage
stage.attrs.GQ802_WeatherStart=-9999
check(1200,"WIND","LEGACY")
print("GQ8_STAGE_WEATHER_REAL41_REAL_HELPER_16_CASES_PASS")
'''


def extract(project:Path)->str:
    _,files=flatten(project)
    if len(files) not in (41,42) or REALM not in files or RENDER not in files:
        raise ValueError("RED_NOT_SELECTED_REAL41")
    realm=files[REALM].read_text(encoding="utf8")
    render=files[RENDER].read_text(encoding="utf8")
    begin="-- GQ8_SEEDED_WEATHER_REALM_BRIDGE_BEGIN"
    end="-- GQ8_SEEDED_WEATHER_REALM_BRIDGE_END"
    if realm.count(begin)!=1 or realm.count(end)!=1:
        raise ValueError("RED_SELECTED_REALM_BRIDGE_ABSENT")
    section=realm.split(begin,1)[1].split(end,1)[0]
    if "local function weatherFromVerifiedStage(" not in section or REALM_NEW not in realm:
        raise ValueError("RED_REALM_WEATHER_DECISION_UNWIRED")
    if render.count(STAGE_INSERT)!=1 or render.count('root:SetAttribute("SourceSeed",manifest.seed)')!=1:
        raise ValueError("RED_STAGE_WEATHER_PUBLISHER_UNWIRED")
    if "weather==\"THUNDER\" and state.pendingLightning and now>=state.pendingLightning" not in realm:
        raise ValueError("RED_PREEXISTING_THUNDER_FENCE_DELETED")
    return "local function weatherFromVerifiedStage("+section.split("local function weatherFromVerifiedStage(",1)[1]


def generate(project:Path,good:Path,mutant:Path):
    body=extract(project)
    good.write_text(HARNESS.replace("__REAL_AUTHOR_HELPER__",body),encoding="utf8")
    evil=body.replace('theme=="STORM" or theme=="METEOR"','theme=="STORM" and theme=="METEOR"',1)
    if evil==body:raise ValueError("RED_MUTANT_NOT_CREATED")
    mutant.write_text(HARNESS.replace("__REAL_AUTHOR_HELPER__",evil),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    a=p.parse_args()
    generate(a.project,a.out,a.mutant)
