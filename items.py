# items.py
import random
import math
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
        "color": (245, 165, 85),
        "desc": "+15 AD/AP, +15% Vampirismo",
        "bonus": {"attack": 15, "spell_power": 0.15, "omnivamp": 0.15}
    },
    ("vest", "vest"): {
        "name": "Bramble Vest",
        "tag": "BV",
        "color": (185, 145, 95),
        "desc": "+55 Corazza, blocca colpi critici",
        "bonus": {"defense": 55}
    },
    ("vest", "cloak"): {
        "name": "Gargoyle Stoneplate",
        "tag": "GSP",
        "color": (185, 185, 125),
        "desc": "+30 Corazza, +30 RM, bonus resistenze",
        "bonus": {"defense": 30, "magic_resist": 30}
    },
    ("vest", "belt"): {
        "name": "Sunfire Cape",
        "tag": "SFC",
        "color": (245, 105, 45),
        "desc": "+25 Corazza, +200 HP, bruciatura AoE",
        "bonus": {"defense": 25, "hp": 200}
    },
    ("vest", "gloves"): {
        "name": "Steadfast Heart",
        "tag": "SH",
        "color": (145, 165, 185),
        "desc": "+25 Corazza, +20% Crit, riduce danni",
        "bonus": {"defense": 25, "crit": 0.20}
    },
    ("cloak", "cloak"): {
        "name": "Dragon's Claw",
        "tag": "DC",
        "color": (65, 205, 185),
        "desc": "+60 RM, rigenera salute ogni 2s",
        "bonus": {"magic_resist": 60}
    },
    ("cloak", "belt"): {
        "name": "Evenshroud",
        "tag": "ES",
        "color": (105, 185, 145),
        "desc": "+25 RM, +200 HP, indebolisce nemici",
        "bonus": {"magic_resist": 25, "hp": 200}
    },
    ("cloak", "gloves"): {
        "name": "Quicksilver",
        "tag": "QSS",
        "color": (145, 205, 245),
        "desc": "+25 RM, +20% Crit, immunità al controllo",
        "bonus": {"magic_resist": 25, "crit": 0.20}
    },
    ("belt", "belt"): {
        "name": "Warmog's Armor",
        "tag": "WM",
        "color": (65, 205, 85),
        "desc": "+600 HP Massimi",
        "bonus": {"hp": 600}
    },
    ("belt", "gloves"): {
        "name": "Guardbreaker",
        "tag": "GBR",
        "color": (205, 125, 145),
        "desc": "+200 HP, +20% Crit, rompe scudi nemici",
        "bonus": {"hp": 200, "crit": 0.20}
    },
    ("gloves", "gloves"): {
        "name": "Thief's Gloves",
        "tag": "TG",
        "color": (225, 65, 125),
        "desc": "+30% Crit, equipaggia 2 oggetti random ogni round",
        "bonus": {"crit": 0.30}
    }
}

# Costruiamo il dizionario bidirezionale per la ricerca ricette
_CANONICAL_RECIPES = {}
for (c1, c2), data in RECIPES.items():
    key = tuple(sorted([c1, c2]))
    _CANONICAL_RECIPES[key] = data

def get_random_component_key():
    """Ritorna la chiave di un componente casuale tra gli 8 disponibili"""
    return random.choice(list(COMPONENTS.keys()))

def normalize_component_key(name_or_key):
    """Converte un nome esteso o chiave di componente nella chiave canonica"""
    if name_or_key in COMPONENTS:
        return name_or_key
    for k, v in COMPONENTS.items():
        if v["name"].lower() == name_or_key.lower() or v.get("short", "").lower() == name_or_key.lower():
            return k
    return None

def get_item_data(item_key):
    """Restituisce il dizionario con nome, stats, colore e tag per qualsiasi oggetto o componente"""
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
    """Applica tutti i bonus statistici cumulativi degli oggetti equipaggiati sul campione."""
    items = getattr(champion, "items", [])
    if not items:
        return

    for item in items:
        if isinstance(item, str):
            item_data = get_item_data(item)
        else:
            item_data = item

        bonus = item_data.get("bonus", {})
        if "hp" in bonus:
            champion.base_hp += bonus["hp"]
            champion.max_hp += bonus["hp"]
            champion.hp += bonus["hp"]
        if "attack" in bonus:
            champion.base_attack += bonus["attack"]
        if "defense" in bonus:
            champion.base_defense += bonus["defense"]
        if "attack_speed" in bonus:
            champion.attack_speed = float(champion.attack_speed * (1.0 + bonus["attack_speed"]))
        if "mana_start" in bonus:
            champion.mana_start = min(champion.mana_max, champion.mana_start + bonus["mana_start"])
            champion.current_mana = champion.mana_start
        if "mana_per_hit" in bonus:
            champion.mana_per_hit = getattr(champion, "mana_per_hit", 10) + bonus["mana_per_hit"]
        if "crit" in bonus:
            champion.crit_chance = min(1.0, champion.crit_chance + bonus["crit"])
        if "spell_power" in bonus:
            champion.spell_power_mult = getattr(champion, "spell_power_mult", 1.0) + bonus["spell_power"]
        if "omnivamp" in bonus or "lifesteal" in bonus:
            vamp = bonus.get("omnivamp", bonus.get("lifesteal", 0.0))
            champion.lifesteal = getattr(champion, "lifesteal", 0.0) + vamp

# Cache per icone grafiche procedurali
_ITEM_ICON_CACHE = {}

def get_item_icon_surface(item_key, size=36, is_hover=False):
    """
    Restituisce una Surface Pygame con l'icona grafica dettagliata ad alta definizione dell'oggetto.
    Disegna simboli stilizzati (Spade, Archi, Bacchette, Lacrime, Armature, ecc.).
    """
    cache_key = (str(item_key), size, is_hover)
    if cache_key in _ITEM_ICON_CACHE:
        return _ITEM_ICON_CACHE[cache_key]

    data = get_item_data(item_key)
    name = data.get("name", str(item_key)).lower()
    is_comp = data.get("is_component", False)
    theme_col = data.get("color", (180, 160, 60))

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # 1. Bordo e Sfondo con Glassmorphism metallico
    bg_col = (20, 24, 36, 240)
    border_col = (255, 215, 80) if not is_comp else (theme_col if is_hover else (140, 150, 175))
    border_w = 2 if (not is_comp or is_hover) else 1

    pygame.draw.rect(surf, bg_col, (0, 0, size, size), border_radius=7)
    
    # Gradiente interno
    inner_rect = pygame.Rect(2, 2, size - 4, size - 4)
    tint_surf = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
    tint_surf.fill((*theme_col[:3], 45))
    surf.blit(tint_surf, (2, 2))

    cx = size // 2
    cy = size // 2
    
    # 2. VETTORIALE STILIZZATO PER OGNI OGGETTO
    if "sword" in name or "spada" in name or "blade" in name or "slayer" in name:
        # Spada metallica
        blade_col = (235, 240, 255) if is_comp else (255, 215, 70)
        pygame.draw.line(surf, blade_col, (cx - 7, cy + 7), (cx + 7, cy - 7), 3) # Lama
        pygame.draw.line(surf, (190, 160, 50), (cx - 3, cy + 1), (cx - 1, cy + 5), 2) # Guardia
        pygame.draw.circle(surf, (220, 40, 40), (cx - 7, cy + 7), 2) # Pomolo
        
    elif "bow" in name or "arco" in name or "whisper" in name or "hurricane" in name:
        # Arco d'oro ricurvo con corda
        pygame.draw.arc(surf, (245, 215, 60), (cx - 9, cy - 9, 18, 18), -0.7, 2.4, width=2)
        pygame.draw.line(surf, (140, 230, 255), (cx - 7, cy - 7), (cx + 7, cy + 7), 1)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 2)
        
    elif "rod" in name or "bacchetta" in name or "deathcap" in name or "archangel" in name or "morello" in name or "spark" in name:
        # Scettro / Gemma magica pulsante
        pygame.draw.line(surf, (160, 130, 80), (cx - 6, cy + 6), (cx + 3, cy - 3), 2)
        pygame.draw.circle(surf, (200, 80, 255), (cx + 5, cy - 5), 5)
        pygame.draw.circle(surf, (255, 255, 255), (cx + 5, cy - 5), 2)
        
    elif "tear" in name or "lacrima" in name or "blue buff" in name or "redemption" in name or "vow" in name:
        # Goccia di Zaffiro brillante
        pygame.draw.circle(surf, (60, 160, 255), (cx, cy + 2), 6)
        pygame.draw.polygon(surf, (60, 160, 255), [(cx - 5, cy + 2), (cx + 5, cy + 2), (cx, cy - 7)])
        pygame.draw.circle(surf, (255, 255, 255), (cx - 1, cy + 1), 2)
        
    elif "vest" in name or "corazza" in name or "bramble" in name or "stoneplate" in name or "sunfire" in name or "gargoyle" in name:
        # Corazza a piastre
        pygame.draw.polygon(surf, (190, 200, 215), [(cx - 7, cy - 6), (cx + 7, cy - 6), (cx + 5, cy + 7), (cx - 5, cy + 7)])
        pygame.draw.line(surf, (245, 190, 50), (cx, cy - 5), (cx, cy + 6), 2)
        
    elif "cloak" in name or "cappa" in name or "dragon" in name or "quicksilver" in name or "evenshroud" in name:
        # Cappa / Mantello mistico
        pygame.draw.polygon(surf, (60, 220, 180), [(cx - 7, cy - 6), (cx + 7, cy - 6), (cx + 8, cy + 7), (cx - 8, cy + 7)])
        pygame.draw.circle(surf, (255, 240, 120), (cx, cy - 4), 2)
        
    elif "belt" in name or "cintura" in name or "warmog" in name or "sterak" in name or "nashor" in name:
        # Cintura massiccia con fibbia
        pygame.draw.rect(surf, (180, 50, 60), (cx - 8, cy - 4, 16, 8), border_radius=2)
        pygame.draw.rect(surf, (255, 215, 60), (cx - 4, cy - 5, 8, 10), width=2, border_radius=2)
        
    elif "glove" in name or "guanti" in name or "thief" in name or "guardbreaker" in name or "justice" in name:
        # Guanto da combattimento
        pygame.draw.rect(surf, (220, 70, 90), (cx - 6, cy - 5, 12, 11), border_radius=3)
        pygame.draw.circle(surf, (245, 215, 50), (cx - 3, cy - 2), 2)
        pygame.draw.circle(surf, (245, 215, 50), (cx + 3, cy - 2), 2)
        
    else:
        # Icona generica emblema / cristallo
        pygame.draw.circle(surf, theme_col, (cx, cy), 6)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 3)

    # 3. Disegna bordo
    pygame.draw.rect(surf, border_col, (0, 0, size, size), width=border_w, border_radius=7)
    
    # 4. Indicatore Oggetto Completo (Angolo d'Oro)
    if not is_comp:
        pygame.draw.circle(surf, (255, 215, 60), (size - 4, 4), 2)

    _ITEM_ICON_CACHE[cache_key] = surf
    return surf

def draw_item_icon(surface, item_key, rect, is_hover=False):
    """Disegna direttamente l'icona grafica nel rettangolo specificato"""
    icon_surf = get_item_icon_surface(item_key, size=min(rect.width, rect.height), is_hover=is_hover)
    surface.blit(icon_surf, (rect.x, rect.y))
