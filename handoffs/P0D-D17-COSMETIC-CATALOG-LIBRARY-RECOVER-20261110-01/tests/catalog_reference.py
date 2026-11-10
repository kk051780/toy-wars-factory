"""D17 deterministic Python oracle for the isolated Luau *reference* module.
No purchase logic, analytics, persistence, or client-defined entitlements.
"""
from dataclasses import dataclass
import re
from typing import Callable

ITEMS = {
    'banner_starter': ('BANNER','STARTER',0),
    'egg_glow_amber': ('EGG_GLOW','ENTITLEMENT',4),
    'lobby_plinth_jade': ('LOBBY_PLINTH','ENTITLEMENT',0),
    'victory_petals': ('VICTORY_FX','PREVIEW_ONLY',12),
    'dragon_wave_emote': ('EMOTE','PREVIEW_ONLY',0),
}
SLOTS = {'BANNER','EGG_GLOW','LOBBY_PLINTH','VICTORY_FX','EMOTE'}
MAX_SESSION_PLAYERS = 256


def valid_player(key):
    if type(key) is int:
        return 0 < key < 10**16
    if type(key) is str:
        return 0 < len(key) <= 64 and re.fullmatch(r'[A-Za-z0-9_-]+',key) is not None
    return False

@dataclass
class Catalog:
    active: Callable
    owns: Callable
    def __post_init__(self):
        self.selected = {}
    def is_active(self,player):
        if not valid_player(player): return False
        try: return self.active(player) is True
        except Exception: return False
    def is_owned(self,player,item):
        if item not in ITEMS or ITEMS[item][1]=='PREVIEW_ONLY': return False
        if ITEMS[item][1]=='STARTER': return True
        try: return self.owns(player,item) is True
        except Exception: return False
    def view_item(self,player,item):
        slot,gate,particles=ITEMS[item]
        return {'itemId':item,'slot':slot,'gate':gate,'owned':self.is_owned(player,item),
                'previewable':True,'maxParticles':particles,'noCombatStats':True,
                'purchaseEnabled':False,'saved':False}
    def list(self,player):
        if not self.is_active(player): return None,'NOT_ACTIVE'
        return [self.view_item(player,item) for item in ITEMS],'OK'
    def preview(self,player,item):
        if not self.is_active(player): return None,'NOT_ACTIVE'
        if type(item) is not str or len(item)>64 or item not in ITEMS:return None,'INVALID_ITEM'
        return self.view_item(player,item),'OK'
    def equip(self,player,item):
        if not self.is_active(player): return False,'NOT_ACTIVE'
        if type(item) is not str or len(item)>64 or item not in ITEMS:return False,'INVALID_ITEM'
        if not self.is_owned(player,item):return False,'NOT_OWNED'
        if player not in self.selected:
            if len(self.selected)>=MAX_SESSION_PLAYERS:return False,'SESSION_CAPACITY'
            self.selected[player]={}
        slot=ITEMS[item][0]
        if self.selected[player].get(slot)==item:return True,'ALREADY_EQUIPPED'
        self.selected[player][slot]=item
        return True,'EQUIPPED'
    def unequip(self,player,slot):
        if not self.is_active(player):return False,'NOT_ACTIVE'
        if type(slot) is not str or slot not in SLOTS:return False,'INVALID_SLOT'
        if slot not in self.selected.get(player,{}):return True,'ALREADY_EMPTY'
        del self.selected[player][slot]
        if not self.selected[player]:del self.selected[player]
        return True,'UNEQUIPPED'
    def equipped(self,player):
        if not self.is_active(player):return None,'NOT_ACTIVE'
        return {slot:self.view_item(player,item) for slot,item in self.selected.get(player,{}).items()
                if slot in SLOTS and item in ITEMS and ITEMS[item][0]==slot and self.is_owned(player,item)},'OK'
    def player_left(self,player):self.selected.pop(player,None)
    def reset_session(self):self.selected={}
