# traits.py
import pygame
from config import draw_text, TEXT_FONT

# Database delle Sinergie (Origini & Classi)
TRAITS_DATA = {
    "Demacia": {
        "type": "ORIGIN",
        "breakpoints": [2],
        "color": (230, 200, 80), # Oro Demacia
        "description": "I Demaciani ottengono +20 Armatura."
    },
    "Piltover": {
        "type": "ORIGIN",
        "breakpoints": [2],
        "color": (80, 200, 230), # Blu Hextech
        "description": "I campioni di Piltover ottengono +30% Vel. Attacco."
    },
    "Ionia": {
        "type": "ORIGIN",
        "breakpoints": [2],
        "color": (230, 100, 160), # Rosa Ionia
        "description": "Gli Ioniani iniziano con +35 Mana e +15% Critico."
    },
    "Noxus": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (200, 40, 40), # Rosso Noxus
        "description": "Ottiene +15 Attacco fisico bonus."
    },
    "Zaun": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (80, 230, 120), # Verde Tossico
        "description": "Ottiene +20% Probabilità di Critico."
    },
    "Cosmico": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (120, 80, 230), # Viola Galattico
        "description": "Rigenera +15 Mana extra per ogni attacco."
    },
    "Divino": {
        "type": "ORIGIN",
        "breakpoints": [1],
        "color": (255, 220, 100), # Oro Divino
        "description": "Ottiene +200 HP e +25% Vel. Attacco."
    },
    "Combattente": {
        "type": "CLASS",
        "breakpoints": [2],
        "color": (220, 120, 50), # Arancio
        "description": "I Combattenti ottengono +250 HP massimi."
    },
    "Guardiano": {
        "type": "CLASS",
        "breakpoints": [2],
        "color": (100, 160, 220), # Blu Acciaio
        "description": "I Guardiani ottengono uno Scudo di 200 HP."
    },
    "Mago": {
        "type": "CLASS",
        "breakpoints": [2],
        "color": (160, 80, 240), # Viola Arcano
        "description": "I Maghi infliggono il +50% di Danni Magici."
    },
    "Cecchino": {
        "type": "CLASS",
        "breakpoints": [2],
        "color": (240, 180, 40), # Giallo Oro
        "description": "I Cecchini ottengono +25% Danno d'Attacco."
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
        
        # Trova la soglia più vicina
        req = breakpoints[0]
        for bp in breakpoints:
            if count >= bp:
                req = bp

        is_active = count >= req and count > 0
        
        # Mostra solo tratti con almeno 1 campione o tratto bonus attivo
        if count > 0:
            results.append({
                "name": trait_name,
                "count": count,
                "req": req,
                "active": is_active,
                "data": data
            })

    # Ordina: prima i tratti attivi, poi per conteggio decrescente
    results.sort(key=lambda x: (not x["active"], -x["count"], x["name"]))
    return results

def apply_trait_buffs(team, active_traits_info):
    """
    Applica i modificatori statistici reali alle copie di battaglia del team.
    """
    active_trait_names = {t["name"] for t in active_traits_info if t["active"]}
    
    for champ in team:
        traits = getattr(champ, "traits", [])
        
        # 1. Demacia (2) -> +20 Difesa
        if "Demacia" in traits and "Demacia" in active_trait_names:
            champ.base_defense += 20
            
        # 2. Piltover (2) -> +30% Velocità Attacco
        if "Piltover" in traits and "Piltover" in active_trait_names:
            champ.attack_speed = float(champ.attack_speed * 1.30)
            
        # 3. Ionia (2) -> +35 Starting Mana e +15% Crit
        if "Ionia" in traits and "Ionia" in active_trait_names:
            champ.mana_start = min(champ.mana_max, champ.mana_start + 35)
            champ.current_mana = champ.mana_start
            champ.crit_chance = min(1.0, champ.crit_chance + 0.15)
            
        # 4. Combattente (2) -> +250 HP
        if "Combattente" in traits and "Combattente" in active_trait_names:
            champ.base_hp += 250
            champ.max_hp += 250
            champ.hp += 250
            
        # 5. Guardiano (2) -> +200 Scudo
        if "Guardiano" in traits and "Guardiano" in active_trait_names:
            champ.base_hp += 200
            champ.max_hp += 200
            champ.hp += 200
            
        # 6. Mago (2) -> +50% Spell Power
        if "Mago" in traits and "Mago" in active_trait_names:
            champ.spell_power_mult = 1.5
            
        # 7. Cecchino (2) -> +25% Attacco
        if "Cecchino" in traits and "Cecchino" in active_trait_names:
            champ.base_attack = int(champ.base_attack * 1.25)
            
        # 8. Cosmico (1) -> +15 Mana per hit
        if "Cosmico" in traits and "Cosmico" in active_trait_names:
            champ.mana_per_hit = getattr(champ, "mana_per_hit", 10) + 15
            
        # 9. Divino (1) -> +200 HP e +25% Vel. Attacco
        if "Divino" in traits and "Divino" in active_trait_names:
            champ.base_hp += 200
            champ.max_hp += 200
            champ.hp += 200
            champ.attack_speed = float(champ.attack_speed * 1.25)
            
        # 10. Noxus (1) -> +15 Attacco
        if "Noxus" in traits and "Noxus" in active_trait_names:
            champ.base_attack += 15
            
        # 11. Zaun (1) -> +20% Crit
        if "Zaun" in traits and "Zaun" in active_trait_names:
            champ.crit_chance = min(1.0, champ.crit_chance + 0.20)

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
    
    # Titolo Sinergie Curvo
    header_rect = pygame.Rect(start_x, start_y, panel_w, 26)
    header_surf = pygame.Surface((panel_w, 26), pygame.SRCALPHA)
    pygame.draw.rect(header_surf, (14, 18, 28, 220), (0, 0, panel_w, 26), border_radius=13)
    pygame.draw.rect(header_surf, (200, 170, 75, 180), (0, 0, panel_w, 26), width=1, border_radius=13)
    surface.blit(header_surf, (start_x, start_y))
    draw_text("SINERGIE", title_font, (245, 225, 170), surface, header_rect.centerx, header_rect.centery)

    current_y = start_y + 32
    for item in traits_list:
        t_name = item["name"]
        count = item["count"]
        req = item["req"]
        is_active = item["active"]
        data = item["data"]
        
        rect = pygame.Rect(start_x, current_y, panel_w, badge_h)
        card_surf = pygame.Surface((panel_w, badge_h), pygame.SRCALPHA)
        
        # Sfondo curvo & Bordo
        if is_active:
            bg_col = (20, 32, 50, 235)
            border_col = data["color"]
            border_w = 2
        else:
            bg_col = (14, 18, 26, 185)
            border_col = (50, 60, 75, 160)
            border_w = 1

        pygame.draw.rect(card_surf, bg_col, (0, 0, panel_w, badge_h), border_radius=12)
        if border_w > 0:
            pygame.draw.rect(card_surf, border_col, (0, 0, panel_w, badge_h), width=border_w, border_radius=12)
            
        surface.blit(card_surf, (start_x, current_y))
        
        # Emblema / Badge Conteggio
        count_box = pygame.Rect(start_x + 8, current_y + 8, 34, 28)
        count_bg = data["color"] if is_active else (40, 48, 62)
        pygame.draw.rect(surface, count_bg, count_box, border_radius=8)
        pygame.draw.rect(surface, (0, 0, 0, 150), count_box, width=1, border_radius=8)
        
        count_text = f"{count}/{req}"
        draw_text(count_text, badge_font, (10, 10, 15) if is_active else (210, 215, 225), surface, count_box.centerx, count_box.centery)
        
        # Nome Tratto
        name_color = (255, 255, 255) if is_active else (175, 185, 200)
        draw_text(t_name, badge_font, name_color, surface, start_x + 48, current_y + 13, center=False)
        
        # Stato / Descrizione
        status_text = "ATTIVO" if is_active else "Incompleto"
        status_color = data["color"] if is_active else (110, 120, 135)
        draw_text(status_text, sub_font, status_color, surface, start_x + 48, current_y + 27, center=False)

        current_y += badge_h + spacing

