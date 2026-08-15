# items.py
import random
import pygame
from config import draw_text, TEXT_FONT

# 8 Componenti Base di TFT
COMPONENTS = {
    "bf_sword": {
        "name": "B.F. Sword",
        "short": "Spada",
        "tag": "BF",
        "color": (230, 180, 50),
        "desc": "+15 Attacco Fisico",
        "bonus": {"attack": 15}
    },
    "recurve_bow": {
        "name": "Recurve Bow",
        "short": "Arco",
        "tag": "BOW",
        "color": (240, 210, 70),
        "desc": "+20% Velocità Attacco",
        "bonus": {"attack_speed": 0.20}
    },
    "rod": {
        "name": "Needlessly Large Rod",
        "short": "Bacchetta",
        "tag": "ROD",
        "color": (190, 80, 245),
        "desc": "+25% Potere Abilità",
        "bonus": {"spell_power": 0.25}
    },
    "tear": {
        "name": "Tear of the Goddess",
        "short": "Lacrima",
        "tag": "TEAR",
        "color": (60, 160, 245),
        "desc": "+20 Mana Iniziale",
        "bonus": {"mana_start": 20}
    },
    "vest": {
        "name": "Chain Vest",
        "short": "Corazza",
        "tag": "ARM",
        "color": (220, 130, 60),
        "desc": "+25 Armatura",
        "bonus": {"defense": 25}
    },
    "cloak": {
        "name": "Negatron Cloak",
        "short": "Cappa",
        "tag": "MR",
        "color": (60, 220, 180),
        "desc": "+25 Resistenza Magica",
        "bonus": {"magic_resist": 25}
    },
    "belt": {
        "name": "Giant's Belt",
        "short": "Cintura",
        "tag": "HP",
        "color": (230, 60, 80),
        "desc": "+200 HP Massimi",
        "bonus": {"hp": 200}
    },
    "gloves": {
        "name": "Sparring Gloves",
        "short": "Guanti",
        "tag": "CRIT",
        "color": (210, 200, 90),
        "desc": "+15% Probabilità Critico",
        "bonus": {"crit": 0.15}
    }
}

# Ricette Oggetti Combinati Completi
RECIPES = {
    ("bf_sword", "bf_sword"): {
        "name": "Deathblade",
        "tag": "DB",
        "color": (245, 130, 40),
        "desc": "+40 AD, +15% danni totali",
        "bonus": {"attack": 40, "damage_amp": 0.15}
    },
    ("bf_sword", "recurve_bow"): {
        "name": "Giant Slayer",
        "tag": "GS",
        "color": (245, 190, 60),
        "desc": "+20 AD, +20% AS, colpi potenziati",
        "bonus": {"attack": 20, "attack_speed": 0.20, "giant_slayer": True}
    },
    ("bf_sword", "rod"): {
        "name": "Hextech Gunblade",
        "tag": "GB",
        "color": (190, 100, 230),
        "desc": "+20 AD, +25% AP, 25% cura sui danni",
        "bonus": {"attack": 20, "spell_power": 0.25, "omnivamp": 0.25}
    },
    ("bf_sword", "tear"): {
        "name": "Spear of Shojin",
        "tag": "SHJ",
        "color": (90, 180, 245),
        "desc": "+15 AD, +20 Mana, +10 Mana per colpo",
        "bonus": {"attack": 15, "mana_start": 20, "mana_per_hit": 10}
    },
    ("bf_sword", "vest"): {
        "name": "Edge of Night",
        "tag": "EON",
        "color": (90, 90, 150),
        "desc": "+15 AD, +25 Corazza, scudo salvavita",
        "bonus": {"attack": 15, "defense": 25, "save_shield": True}
    },
    ("bf_sword", "belt"): {
        "name": "Sterak's Gage",
        "tag": "STR",
        "color": (220, 80, 80),
        "desc": "+15 AD, +200 HP, scudo al 50% HP",
        "bonus": {"attack": 15, "hp": 200, "steraks": True}
    },
    ("bf_sword", "cloak"): {
        "name": "Bloodthirster",
        "tag": "BT",
        "color": (210, 30, 40),
        "desc": "+15 AD, +25 RM, 20% Vampirismo",
        "bonus": {"attack": 15, "magic_resist": 25, "lifesteal": 0.20}
    },
    ("bf_sword", "gloves"): {
        "name": "Infinity Edge",
        "tag": "IE",
        "color": (245, 215, 40),
        "desc": "+25 AD, +30% Crit, critici devastanti",
        "bonus": {"attack": 25, "crit": 0.30, "crit_damage": 0.40}
    },
    ("recurve_bow", "recurve_bow"): {
        "name": "Rapid Firecannon",
        "tag": "RFC",
        "color": (255, 225, 50),
        "desc": "+45% Velocità Attacco, +100 Range",
        "bonus": {"attack_speed": 0.45, "range_bonus": 100}
    },
    ("recurve_bow", "rod"): {
        "name": "Guinsoo's Rageblade",
        "tag": "RBG",
        "color": (245, 110, 30),
        "desc": "+15% AS, +20% AP, +5% AS ad ogni attacco",
        "bonus": {"attack_speed": 0.15, "spell_power": 0.20, "guinsoo": True}
    },
    ("recurve_bow", "tear"): {
        "name": "Statikk Shiv",
        "tag": "SS",
        "color": (80, 225, 245),
        "desc": "+20% AS, +20 Mana, scarica elettrica AoE",
        "bonus": {"attack_speed": 0.20, "mana_start": 20, "statikk": True}
    },
    ("recurve_bow", "vest"): {
        "name": "Titan's Resolve",
        "tag": "TR",
        "color": (205, 145, 65),
        "desc": "+20% AS, +25 Corazza, stacka attacco",
        "bonus": {"attack_speed": 0.20, "defense": 25, "titans": True}
    },
    ("recurve_bow", "belt"): {
        "name": "Nashor's Tooth",
        "tag": "NTO",
        "color": (190, 85, 130),
        "desc": "+20% AS, +200 HP, velocità aumentata",
        "bonus": {"attack_speed": 0.20, "hp": 200}
    },
    ("recurve_bow", "cloak"): {
        "name": "Runaan's Hurricane",
        "tag": "RH",
        "color": (125, 205, 225),
        "desc": "+25% AS, +25 RM, dardi secondari",
        "bonus": {"attack_speed": 0.25, "magic_resist": 25}
    },
    ("recurve_bow", "gloves"): {
        "name": "Last Whisper",
        "tag": "LW",
        "color": (225, 205, 85),
        "desc": "+20% AS, +20% Crit, perfora armatura",
        "bonus": {"attack_speed": 0.20, "crit": 0.20}
    },
    ("rod", "rod"): {
        "name": "Rabadon's Deathcap",
        "tag": "DC",
        "color": (185, 45, 245),
        "desc": "+65% Potere Abilità",
        "bonus": {"spell_power": 0.65}
    },
    ("rod", "tear"): {
        "name": "Archangel's Staff",
        "tag": "AAS",
        "color": (125, 185, 255),
        "desc": "+25% AP, +20 Mana, mana extra",
        "bonus": {"spell_power": 0.25, "mana_start": 20}
    },
    ("rod", "vest"): {
        "name": "Crownguard",
        "tag": "CG",
        "color": (225, 185, 65),
        "desc": "+25% AP, +25 Corazza, scudo gigante",
        "bonus": {"spell_power": 0.25, "defense": 25, "hp": 150}
    },
    ("rod", "belt"): {
        "name": "Morellonomicon",
        "tag": "MOR",
        "color": (225, 85, 45),
        "desc": "+25% AP, +200 HP, brucia i nemici",
        "bonus": {"spell_power": 0.25, "hp": 200, "burn": True}
    },
    ("rod", "cloak"): {
        "name": "Ionic Spark",
        "tag": "IS",
        "color": (145, 105, 245),
        "desc": "+25% AP, +25 RM, fulmina i nemici",
        "bonus": {"spell_power": 0.25, "magic_resist": 25}
    },
    ("rod", "gloves"): {
        "name": "Jeweled Gauntlet",
        "tag": "JG",
        "color": (225, 145, 245),
        "desc": "+30% AP, +20% Crit, spell critici",
        "bonus": {"spell_power": 0.30, "crit": 0.20}
    },
    ("tear", "tear"): {
        "name": "Blue Buff",
        "tag": "BB",
        "color": (45, 165, 255),
        "desc": "+40 Starting Mana, cast frequenti",
        "bonus": {"mana_start": 40}
    },
    ("tear", "vest"): {
        "name": "Protector's Vow",
        "tag": "PV",
        "color": (105, 165, 225),
        "desc": "+20 Mana, +25 Corazza, scudo",
        "bonus": {"mana_start": 20, "defense": 25, "hp": 100}
    },
    ("tear", "belt"): {
        "name": "Redemption",
        "tag": "RED",
        "color": (125, 225, 185),
        "desc": "+20 Mana, +200 HP, aura curativa",
        "bonus": {"mana_start": 20, "hp": 200}
    },
    ("tear", "cloak"): {
        "name": "Adaptive Helm",
        "tag": "ADH",
        "color": (125, 145, 225),
        "desc": "+20 Mana, +25 RM, +15 Corazza",
        "bonus": {"mana_start": 20, "magic_resist": 25, "defense": 15}
    },
    ("tear", "gloves"): {
        "name": "Hand of Justice",
        "tag": "HOJ",
        "color": (245, 185, 85),
        "desc": "+20 Mana, +15% Crit, +15% Danno & Cura",
        "bonus": {"mana_start": 20, "crit": 0.15, "omnivamp": 0.15}
    },
    ("vest", "vest"): {
        "name": "Bramble Vest",
        "tag": "BV",
        "color": (185, 105, 45),
        "desc": "+55 Corazza, riduce danni subiti",
        "bonus": {"defense": 55}
    },
    ("vest", "belt"): {
        "name": "Sunfire Cape",
        "tag": "SFC",
        "color": (245, 105, 25),
        "desc": "+25 Corazza, +200 HP, brucia nemici",
        "bonus": {"defense": 25, "hp": 200}
    },
    ("vest", "cloak"): {
        "name": "Gargoyle Stoneplate",
        "tag": "GSP",
        "color": (165, 165, 185),
        "desc": "+30 Corazza, +30 Resistenza Magica",
        "bonus": {"defense": 30, "magic_resist": 30}
    },
    ("vest", "gloves"): {
        "name": "Steadfast Heart",
        "tag": "SH",
        "color": (185, 145, 205),
        "desc": "+25 Corazza, +15% Crit, -15% danni subiti",
        "bonus": {"defense": 25, "crit": 0.15}
    },
    ("belt", "belt"): {
        "name": "Warmog's Armor",
        "tag": "WAR",
        "color": (45, 225, 105),
        "desc": "+650 HP Massimi",
        "bonus": {"hp": 650}
    },
    ("belt", "cloak"): {
        "name": "Evenshroud",
        "tag": "EVS",
        "color": (145, 85, 165),
        "desc": "+200 HP, +25 RM",
        "bonus": {"hp": 200, "magic_resist": 25}
    },
    ("belt", "gloves"): {
        "name": "Guardbreaker",
        "tag": "GBK",
        "color": (225, 125, 105),
        "desc": "+200 HP, +20% Crit, +20% Danni",
        "bonus": {"hp": 200, "crit": 0.20}
    },
    ("cloak", "cloak"): {
        "name": "Dragon's Claw",
        "tag": "DCW",
        "color": (85, 205, 225),
        "desc": "+60 Resistenza Magica, rigenerazione",
        "bonus": {"magic_resist": 60}
    },
    ("cloak", "gloves"): {
        "name": "Quicksilver",
        "tag": "QSS",
        "color": (185, 225, 245),
        "desc": "+25 RM, +20% Crit, +30% Vel. Attacco",
        "bonus": {"magic_resist": 25, "crit": 0.20, "attack_speed": 0.30}
    },
    ("gloves", "gloves"): {
        "name": "Thief's Gloves",
        "tag": "TG",
        "color": (225, 185, 65),
        "desc": "+30% Critico, +150 HP, +15 AD",
        "bonus": {"crit": 0.30, "hp": 150, "attack": 15}
    }
}

# Dizionario ricette con chiavi ordinate canoniche per sicurezza
_CANONICAL_RECIPES = {
    tuple(sorted(k)): v for k, v in RECIPES.items()
}

def normalize_component_key(comp):
    """Normalizza una chiave o nome componente alla sua chiave canonica"""
    if comp in COMPONENTS:
        return comp
    for k, v in COMPONENTS.items():
        if v["name"] == comp or v.get("short") == comp:
            return k
    return None

def get_random_component_key():
    """Restituisce la chiave di un componente casuale"""
    return random.choice(list(COMPONENTS.keys()))

def get_item_data(item_key):
    """Restituisce le info di un componente o oggetto combinato"""
    # 1. Controllo per chiave componente
    if item_key in COMPONENTS:
        data = dict(COMPONENTS[item_key])
        data["is_component"] = True
        data["key"] = item_key
        return data
    
    # 2. Controllo per nome componente
    for k, v in COMPONENTS.items():
        if v["name"] == item_key or v.get("short") == item_key:
            data = dict(v)
            data["is_component"] = True
            data["key"] = k
            return data
    
    # 3. Cerca tra gli oggetti combinati completi
    for recipe in _CANONICAL_RECIPES.values():
        if recipe["name"] == item_key:
            data = dict(recipe)
            data["is_component"] = False
            data["key"] = recipe["name"]
            return data
            
    # Oggetto generico
    return {
        "name": item_key,
        "tag": "OBJ",
        "color": (150, 150, 150),
        "desc": "Oggetto",
        "bonus": {},
        "is_component": False,
        "key": item_key
    }

def combine_components(comp1_key, comp2_key):
    """Combina due componenti e ritorna il dizionario dell'oggetto combinato"""
    k1 = normalize_component_key(comp1_key)
    k2 = normalize_component_key(comp2_key)
    if not k1 or not k2:
        return None
    key = tuple(sorted([k1, k2]))
    if key in _CANONICAL_RECIPES:
        data = dict(_CANONICAL_RECIPES[key])
        data["is_component"] = False
        data["key"] = data["name"]
        return data
    return None

def apply_item_stats(champion):
    """
    Applica tutti i bonus statistici cumulativi degli oggetti equipaggiati sul campione.
    """
    items = getattr(champion, "items", [])
    if not items:
        return

    for item in items:
        if isinstance(item, str):
            item_data = get_item_data(item)
        else:
            item_data = item

        bonus = item_data.get("bonus", {})
        
        # HP
        if "hp" in bonus:
            champion.base_hp += bonus["hp"]
            champion.max_hp += bonus["hp"]
            champion.hp += bonus["hp"]
            
        # Attack Damage
        if "attack" in bonus:
            champion.base_attack += bonus["attack"]
            
        # Defense (Armor)
        if "defense" in bonus:
            champion.base_defense += bonus["defense"]
            
        # Attack Speed
        if "attack_speed" in bonus:
            champion.attack_speed = float(champion.attack_speed * (1.0 + bonus["attack_speed"]))
            
        # Starting Mana
        if "mana_start" in bonus:
            champion.mana_start = min(champion.mana_max, champion.mana_start + bonus["mana_start"])
            champion.current_mana = champion.mana_start
            
        # Mana per hit
        if "mana_per_hit" in bonus:
            champion.mana_per_hit = getattr(champion, "mana_per_hit", 10) + bonus["mana_per_hit"]
            
        # Crit Chance
        if "crit" in bonus:
            champion.crit_chance = min(1.0, champion.crit_chance + bonus["crit"])
            
        # Spell Power
        if "spell_power" in bonus:
            champion.spell_power_mult = getattr(champion, "spell_power_mult", 1.0) + bonus["spell_power"]
            
        # Omnivamp / Lifesteal
        if "omnivamp" in bonus or "lifesteal" in bonus:
            vamp = bonus.get("omnivamp", bonus.get("lifesteal", 0.0))
            champion.lifesteal = getattr(champion, "lifesteal", 0.0) + vamp
