# traits.py
import pygame
from config import draw_text, TEXT_FONT

# Database completo delle Sinergie (Origini & Classi) - TFT Prototype
TRAITS_DATA = {
    # --- ORIGINI ---
    "Demacia": {
        "type": "ORIGIN",
        "breakpoints": [2, 4],
        "color": (230, 200, 80), # Oro Demacia
        "description": "I Demaciani ottengono +25/+50 Difesa e +150/+300 HP."
    },
    "Piltover": {
        "type": "ORIGIN",
        "breakpoints": [2, 4],
        "color": (80, 200, 230), # Blu Hextech
        "description": "I campioni di Piltover ottengono +30%/+65% Vel. Attacco."
    },
    "Ionia": {
        "type": "ORIGIN",
        "breakpoints": [2, 4, 6],
        "color": (230, 100, 160), # Rosa Ionia
        "description": "Gli Ioniani ottengono +35/+70 Mana iniziale e +15%/+30% Critico."
    },
    "Noxus": {
        "type": "ORIGIN",
        "breakpoints": [2, 4],
        "color": (210, 45, 45), # Rosso Sangue Noxus
        "description": "I campioni di Noxus ottengono +150/+350 HP e +15/+35 Attacco."
    },
    "Freljord": {
        "type": "ORIGIN",
        "breakpoints": [2, 4],
        "color": (120, 210, 255), # Azzurro Glaciale
        "description": "La bufera di Freljord riduce l'armatura nemica del 30%/50% e dona +20 Difesa."
    },
    "Shurima": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (245, 185, 40), # Oro Solare Shurima
        "description": "Il Disco Solare rigenera il 6% HP max ogni 3s e +40% Vel. Attacco."
    },
    "Ombre delle Isole": {
        "type": "ORIGIN",
        "breakpoints": [1, 2],
        "color": (40, 220, 170), # Verde Spettrale
        "description": "Genera uno Scudo spettrale di 250/500 HP all'inizio del round."
    },
    "Drago": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (150, 90, 240), # Viola Cosmico
        "description": "I Draghi ottengono +400 HP e +40% Spell Power."
    },
    "Divino": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (255, 230, 120), # Oro Angelico
        "description": "Ottiene +200 HP e +25% Vel. Attacco."
    },
    "Zaun": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (80, 230, 120), # Verde Tossico
        "description": "Ottiene +25% Probabilità di Colpo Critico."
    },

    # --- CLASSI ---
    "Cavaliere": {
        "type": "CLASS",
        "breakpoints": [2, 4],
        "color": (180, 190, 210), # Grigio Acciaio
        "description": "I Cavalieri bloccano 25/55 danni da ogni attacco subito."
    },
    "Picchiatore": {
        "type": "CLASS",
        "breakpoints": [2, 4],
        "color": (220, 120, 50), # Arancio Brawler
        "description": "I Picchiatori ottengono +250/+600 HP massimi."
    },
    "Mago": {
        "type": "CLASS",
        "breakpoints": [2, 4],
        "color": (170, 85, 245), # Viola Arcano
        "description": "I Maghi infliggono il +45%/+90% di Danni Magici con abilità."
    },
    "Cecchino": {
        "type": "CLASS",
        "breakpoints": [2, 4],
        "color": (245, 195, 45), # Giallo Ambra
        "description": "I Cecchini ottengono +25%/+55% Danno d'Attacco."
    },
    "Duellante": {
        "type": "CLASS",
        "breakpoints": [2, 4],
        "color": (240, 140, 60), # Arancio Duellante
        "description": "I Duellanti ottengono +25%/+50% Vel. Attacco base."
    },
    "Assassino": {
        "type": "CLASS",
        "breakpoints": [2, 4],
        "color": (220, 50, 100), # Magenta Letale
        "description": "Gli Assassini ottengono +25%/+50% Critico e +35%/+70% Danno Critico."
    },
    "Guardiano": {
        "type": "CLASS",
        "breakpoints": [2, 4],
        "color": (70, 150, 230), # Blu Zaffiro
        "description": "I Guardiani conferiscono uno Scudo di 250/500 HP a sé e alleati."
    },
    "Ninja": {
        "type": "CLASS",
        "breakpoints": [1],
        "color": (160, 120, 210), # Viola Ombra
        "description": "Il Ninja ottiene +35 Attacco e +35% Spell Power se solitario."
    }
}

def calculate_team_traits(champions_list, bonus_traits=None):
    """
    Calcola le sinergie attive basandosi sui campioni UNICI presenti sulla scacchiera.
    Include anche eventuali tratti bonus conferiti dagli Augments (es. Corona Demaciana).
    """
    unique_champs = {}
    for c in champions_list:
        if c is not None and c.name not in unique_champs:
            unique_champs[c.name] = c

    trait_counts = {}
    for champ in unique_champs.values():
        traits = getattr(champ, "traits", [])
        for t in traits:
            trait_counts[t] = trait_counts.get(t, 0) + 1

    # Aggiungi tratti bonus da Augments
    if bonus_traits:
        for bt in bonus_traits:
            trait_counts[bt] = trait_counts.get(bt, 0) + 1

    results = []
    for trait_name, data in TRAITS_DATA.items():
        count = trait_counts.get(trait_name, 0)
        breakpoints = data["breakpoints"]
        
        # Trova la soglia raggiunta più alta
        active_tier = 0
        active_req = 0
        for bp in breakpoints:
            if count >= bp:
                active_tier += 1
                active_req = bp

        is_active = count >= breakpoints[0] and count > 0
        
        # Mostra tratti presenti
        if count > 0:
            results.append({
                "name": trait_name,
                "count": count,
                "req": active_req if is_active else breakpoints[0],
                "tier": active_tier,
                "active": is_active,
                "data": data
            })

    # Ordina: prima i tratti attivi (tier più alto), poi per conteggio decrescente
    results.sort(key=lambda x: (not x["active"], -x["tier"], -x["count"], x["name"]))
    return results

def apply_trait_buffs(team, active_traits_info):
    """
    Applica i modificatori statistici reali alle copie di battaglia del team.
    """
    active_traits_map = {t["name"]: t for t in active_traits_info if t["active"]}
    
    for champ in team:
        traits = getattr(champ, "traits", [])
        
        # 1. Demacia (2/4) -> Difesa e HP
        if "Demacia" in traits and "Demacia" in active_traits_map:
            tier = active_traits_map["Demacia"]["tier"]
            def_bonus = 25 if tier == 1 else 50
            hp_bonus = 150 if tier == 1 else 300
            champ.base_defense += def_bonus
            champ.base_hp += hp_bonus
            champ.max_hp += hp_bonus
            champ.hp += hp_bonus
            
        # 2. Piltover (2/4) -> Velocità Attacco
        if "Piltover" in traits and "Piltover" in active_traits_map:
            tier = active_traits_map["Piltover"]["tier"]
            mult = 1.30 if tier == 1 else 1.65
            champ.attack_speed = float(champ.attack_speed * mult)
            
        # 3. Ionia (2/4/6) -> Mana Iniziale e Critico
        if "Ionia" in traits and "Ionia" in active_traits_map:
            tier = active_traits_map["Ionia"]["tier"]
            mana_b = 35 if tier == 1 else (70 if tier == 2 else 100)
            crit_b = 0.15 if tier == 1 else (0.30 if tier == 2 else 0.45)
            champ.mana_start = min(champ.mana_max, champ.mana_start + mana_b)
            champ.current_mana = champ.mana_start
            champ.crit_chance = min(1.0, champ.crit_chance + crit_b)
            
        # 4. Noxus (2/4) -> HP e Attacco
        if "Noxus" in traits and "Noxus" in active_traits_map:
            tier = active_traits_map["Noxus"]["tier"]
            hp_b = 150 if tier == 1 else 350
            atk_b = 15 if tier == 1 else 35
            champ.base_hp += hp_b
            champ.max_hp += hp_b
            champ.hp += hp_b
            champ.base_attack += atk_b
            
        # 5. Freljord (2/4) -> Difesa alleata
        if "Freljord" in traits and "Freljord" in active_traits_map:
            champ.base_defense += 20
            
        # 6. Shurima (1) -> Rigenerazione HP e Vel. Attacco
        if "Shurima" in traits and "Shurima" in active_traits_map:
            champ.attack_speed = float(champ.attack_speed * 1.40)
            champ.shurima_regen = True
            
        # 7. Ombre delle Isole (1/2) -> Scudo Iniziale
        if "Ombre delle Isole" in traits and "Ombre delle Isole" in active_traits_map:
            tier = active_traits_map["Ombre delle Isole"]["tier"]
            shield_val = 250 if tier == 1 else 500
            champ.shield = getattr(champ, "shield", 0) + shield_val
            champ.base_hp += shield_val
            champ.max_hp += shield_val
            champ.hp += shield_val
            
        # 8. Drago (1) -> HP e Spell Power
        if "Drago" in traits and "Drago" in active_traits_map:
            champ.base_hp += 400
            champ.max_hp += 400
            champ.hp += 400
            champ.spell_power_mult = getattr(champ, "spell_power_mult", 1.0) * 1.40
            
        # 9. Divino (1) -> HP e Vel. Attacco
        if "Divino" in traits and "Divino" in active_traits_map:
            champ.base_hp += 200
            champ.max_hp += 200
            champ.hp += 200
            champ.attack_speed = float(champ.attack_speed * 1.25)
            
        # 10. Zaun (1) -> Crit Chance
        if "Zaun" in traits and "Zaun" in active_traits_map:
            champ.crit_chance = min(1.0, champ.crit_chance + 0.25)

        # 11. Cavaliere (2/4) -> Riduzione danno fisso
        if "Cavaliere" in traits and "Cavaliere" in active_traits_map:
            tier = active_traits_map["Cavaliere"]["tier"]
            champ.knight_damage_block = 25 if tier == 1 else 55
            champ.base_defense += 15

        # 12. Picchiatore (2/4) -> HP Massimi
        if "Picchiatore" in traits and "Picchiatore" in active_traits_map:
            tier = active_traits_map["Picchiatore"]["tier"]
            hp_add = 250 if tier == 1 else 600
            champ.base_hp += hp_add
            champ.max_hp += hp_add
            champ.hp += hp_add

        # 13. Mago (2/4) -> Spell Power
        if "Mago" in traits and "Mago" in active_traits_map:
            tier = active_traits_map["Mago"]["tier"]
            mult = 1.45 if tier == 1 else 1.90
            champ.spell_power_mult = getattr(champ, "spell_power_mult", 1.0) * mult

        # 14. Cecchino (2/4) -> Attacco
        if "Cecchino" in traits and "Cecchino" in active_traits_map:
            tier = active_traits_map["Cecchino"]["tier"]
            mult = 1.25 if tier == 1 else 1.55
            champ.base_attack = int(champ.base_attack * mult)

        # 15. Duellante (2/4) -> Vel. Attacco
        if "Duellante" in traits and "Duellante" in active_traits_map:
            tier = active_traits_map["Duellante"]["tier"]
            mult = 1.25 if tier == 1 else 1.50
            champ.attack_speed = float(champ.attack_speed * mult)

        # 16. Assassino (2/4) -> Crit Chance e Danno Critico
        if "Assassino" in traits and "Assassino" in active_traits_map:
            tier = active_traits_map["Assassino"]["tier"]
            crit_chance_add = 0.25 if tier == 1 else 0.50
            crit_dmg_add = 0.35 if tier == 1 else 0.70
            champ.crit_chance = min(1.0, champ.crit_chance + crit_chance_add)
            champ.crit_multiplier = getattr(champ, "crit_multiplier", 1.5) + crit_dmg_add
            champ.is_assassin = True # Salta alle spalle

        # 17. Guardiano (2/4) -> Scudo
        if "Guardiano" in traits and "Guardiano" in active_traits_map:
            tier = active_traits_map["Guardiano"]["tier"]
            shield_val = 250 if tier == 1 else 500
            champ.base_hp += shield_val
            champ.max_hp += shield_val
            champ.hp += shield_val

        # 18. Ninja (1) -> Attacco e Spell Power
        if "Ninja" in traits and "Ninja" in active_traits_map:
            champ.base_attack += 35
            champ.spell_power_mult = getattr(champ, "spell_power_mult", 1.0) * 1.35

def draw_traits_sidebar(surface, traits_list, start_x=15, start_y=130):
    """
    Disegna il pannello HUD laterale a sinistra con tutti i tratti attivi e il loro progresso (Stile Moderno TFT).
    """
    if not traits_list:
        return

    # Header del pannello
    title_font = pygame.font.SysFont("Arial", 14, bold=True)
    badge_font = pygame.font.SysFont("Arial", 13, bold=True)
    sub_font = pygame.font.SysFont("Arial", 11, bold=True)

    panel_w = 180
    badge_h = 44
    spacing = 7
    
    # Contenitore vetrato del pannello intero
    total_h = min(280, 24 + len(traits_list[:6]) * (badge_h + spacing))
    panel_rect = pygame.Rect(start_x - 5, start_y - 28, panel_w + 10, total_h)
    
    panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (15, 20, 32, 220), (0, 0, panel_rect.width, panel_rect.height), border_radius=12)
    pygame.draw.rect(panel_surf, (180, 160, 60, 180), (0, 0, panel_rect.width, panel_rect.height), width=1, border_radius=12)
    surface.blit(panel_surf, (panel_rect.x, panel_rect.y))

    # Titolo
    draw_text("SINERGIE ATTIVE", title_font, (240, 200, 60), surface, panel_rect.centerx, start_y - 14)

    curr_y = start_y + 2
    for t in traits_list[:6]: # Mostra fino alle prime 6 sinergie
        name = t["name"]
        count = t["count"]
        req = t["req"]
        is_active = t["active"]
        data = t["data"]
        trait_color = data["color"]
        
        box_rect = pygame.Rect(start_x, curr_y, panel_w, badge_h)
        
        # Colore sfondo card
        if is_active:
            bg_color = (25, 35, 55, 235)
            border_color = trait_color
            border_w = 2
        else:
            bg_color = (18, 22, 30, 180)
            border_color = (60, 70, 85, 150)
            border_w = 1

        card_surf = pygame.Surface((panel_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, bg_color, (0, 0, panel_w, badge_h), border_radius=8)
        pygame.draw.rect(card_surf, border_color, (0, 0, panel_w, badge_h), width=border_w, border_radius=8)
        surface.blit(card_surf, (start_x, curr_y))

        # Icona esagonale / Cerchio per il conteggio
        icon_cx = start_x + 22
        icon_cy = curr_y + badge_h // 2
        icon_col = trait_color if is_active else (80, 90, 110)
        
        pygame.draw.circle(surface, (10, 14, 20), (icon_cx, icon_cy), 15)
        pygame.draw.circle(surface, icon_col, (icon_cx, icon_cy), 15, width=2)
        draw_text(f"{count}", badge_font, (255, 255, 255) if is_active else (150, 160, 175), surface, icon_cx, icon_cy)

        # Nome del tratto
        name_color = (255, 255, 255) if is_active else (150, 160, 175)
        name_surf = badge_font.render(name, True, name_color)
        surface.blit(name_surf, (start_x + 44, curr_y + 6))

        # Barra / Soglia progresso
        breakpoints_str = " / ".join(str(bp) for bp in data["breakpoints"])
        status_text = f"({breakpoints_str})"
        status_color = trait_color if is_active else (110, 125, 145)
        draw_text(status_text, sub_font, status_color, surface, start_x + 44 + name_surf.get_width() // 2 + 10, curr_y + 26)

        curr_y += badge_h + spacing
