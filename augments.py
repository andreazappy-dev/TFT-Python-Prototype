# augments.py
import random
import pygame
from config import (
    draw_text, WIDTH, HEIGHT, GOLD, WHITE, BLACK, RED, GREEN, 
    TEXT_FONT, SMALL_FONT, MICRO_FONT, HEADER_FONT, TITLE_FONT, BUTTON_FONT
)
from asset_loader import draw_glass_panel, get_background_image

# Tier Colors
TIER_SILVER = (195, 205, 215)
TIER_GOLD = (235, 190, 50)
TIER_PRISMATIC = (80, 225, 255)

AUGMENTS_DATABASE = {
    # --- SILVER AUGMENTS ---
    "cybernetic_implants": {
        "id": "cybernetic_implants",
        "name": "Impianti Cibernetici",
        "tier": "Silver",
        "tag": "CYBER",
        "color": TIER_SILVER,
        "desc": "I campioni con almeno 1 oggetto ottengono +250 HP e +20 Attacco.",
        "effect": {"cyber_hp": 250, "cyber_ad": 20}
    },
    "living_armor": {
        "id": "living_armor",
        "name": "Armatura Vivente",
        "tier": "Silver",
        "tag": "ARMOR",
        "color": TIER_SILVER,
        "desc": "Tutta la tua squadra ottiene +30 Armatura e +30 Resistenza Magica.",
        "effect": {"team_armor": 30, "team_mr": 30}
    },
    "hextech_accelerator": {
        "id": "hextech_accelerator",
        "name": "Acceleratore Hextech",
        "tier": "Silver",
        "tag": "ACCEL",
        "color": TIER_SILVER,
        "desc": "Tutti i tuoi campioni iniziano la battaglia con +35 Mana.",
        "effect": {"team_start_mana": 35}
    },
    "hyper_growth": {
        "id": "hyper_growth",
        "name": "Iper-Crescita",
        "tier": "Silver",
        "tag": "GROW",
        "color": TIER_SILVER,
        "desc": "Guadagni permanentemente +2 XP gratuiti alla fine di ogni round.",
        "effect": {"extra_xp_per_round": 2}
    },
    "aegis_light": {
        "id": "aegis_light",
        "name": "Scudo della Luce",
        "tier": "Silver",
        "tag": "AEGIS",
        "color": TIER_SILVER,
        "desc": "All'inizio dello scontro, tutti gli alleati ottengono uno Scudo di 180 HP.",
        "effect": {"team_start_shield": 180}
    },
    "long_shot": {
        "id": "long_shot",
        "name": "Tiro da Cecchino",
        "tier": "Silver",
        "tag": "SNIPER",
        "color": TIER_SILVER,
        "desc": "I campioni a distanza ottengono +100 Gittata e +15% Danno.",
        "effect": {"ranged_range": 100, "ranged_damage": 0.15}
    },

    # --- GOLD AUGMENTS ---
    "jeweled_lotus": {
        "id": "jeweled_lotus",
        "name": "Loto Gioiellato",
        "tier": "Gold",
        "tag": "LOTUS",
        "color": TIER_GOLD,
        "desc": "Le abilità magiche possono infliggere Colpi Critici (+25% Crit Damage).",
        "effect": {"spell_crit": True, "crit_damage": 0.25}
    },
    "rich_get_richer": {
        "id": "rich_get_richer",
        "name": "I Ricchi si Arricchiscono",
        "tier": "Gold",
        "tag": "RICH",
        "color": TIER_GOLD,
        "desc": "Ottieni subito +10 Oro. Il limite massimo interessi sale a 70g (+7g a round).",
        "effect": {"instant_gold": 10, "max_interest_cap": 70}
    },
    "celestial_vampirism": {
        "id": "celestial_vampirism",
        "name": "Vampirismo Cosmico",
        "tier": "Gold",
        "tag": "VAMP",
        "color": TIER_GOLD,
        "desc": "Tutta la squadra si cura del 20% di tutti i danni inflitti (Vampirismo Totale).",
        "effect": {"team_omnivamp": 0.20}
    },
    "berserkers_rage": {
        "id": "berserkers_rage",
        "name": "Furia Berserker",
        "tier": "Gold",
        "tag": "RAGE",
        "color": TIER_GOLD,
        "desc": "I campioni ottengono +6% Velocità d'Attacco per ogni 10% di HP mancanti.",
        "effect": {"berserker_as": True}
    },
    "demacia_crown": {
        "id": "demacia_crown",
        "name": "Corona Demaciana",
        "tier": "Gold",
        "tag": "DEMAC",
        "color": TIER_GOLD,
        "desc": "Conta come +1 Demacia permanente sulla scacchiera e dona +120 HP ai Demaciani.",
        "effect": {"bonus_trait": "Demacia", "demacia_hp": 120}
    },
    "piltover_heart": {
        "id": "piltover_heart",
        "name": "Cuore di Piltover",
        "tier": "Gold",
        "tag": "PILT",
        "color": TIER_GOLD,
        "desc": "Conta come +1 Piltover permanente e dona +15% Vel. Attacco alla squadra.",
        "effect": {"bonus_trait": "Piltover", "team_as": 0.15}
    },
    "ionia_soul": {
        "id": "ionia_soul",
        "name": "Anima di Ionia",
        "tier": "Gold",
        "tag": "IONIA",
        "color": TIER_GOLD,
        "desc": "Conta come +1 Ionia permanente e +20 Mana iniziale a tutti gli Ioniani.",
        "effect": {"bonus_trait": "Ionia", "ionia_mana": 20}
    },

    # --- PRISMATIC AUGMENTS ---
    "golden_ticket": {
        "id": "golden_ticket",
        "name": "Biglietto Dorato",
        "tier": "Prismatic",
        "tag": "TICKET",
        "color": TIER_PRISMATIC,
        "desc": "Ogni volta che fai un Reroll, hai il 45% di probabilità di ottenerne uno Gratuito.",
        "effect": {"free_reroll_chance": 0.45}
    },
    "item_buffet": {
        "id": "item_buffet",
        "name": "Banchetto degli Oggetti",
        "tier": "Prismatic",
        "tag": "BUFFET",
        "color": TIER_PRISMATIC,
        "desc": "Ricevi istantaneamente 2 componenti casuali e 1 oggetto combinato completo!",
        "effect": {"instant_components": 2, "instant_completed_item": 1}
    },
    "titans_might": {
        "id": "titans_might",
        "name": "Forza Primordiale",
        "tier": "Prismatic",
        "tag": "TITAN",
        "color": TIER_PRISMATIC,
        "desc": "Quando un campione sconfigge un nemico, guadagna permanentemente +12 AD e +100 HP.",
        "effect": {"on_kill_stack_ad": 12, "on_kill_stack_hp": 100}
    }
}

def get_random_augments(count=3, exclude_ids=None):
    """Estrae casualmente 'count' Augments non ancora posseduti dal giocatore"""
    exclude_ids = exclude_ids or []
    available = [aug for k, aug in AUGMENTS_DATABASE.items() if k not in exclude_ids]
    if len(available) < count:
        return available
    return random.sample(available, count)

def draw_augment_selection_screen(surface, mouse_pos, offered_augments, can_reroll=True):
    """
    Disegna la spettacolare schermata di selezione a 3 carte con effetto Glassmorphism,
    badge di rarità, descrizioni chiare e pulsante di Reroll.
    Restituisce: (selected_augment_index_or_None, clicked_reroll_bool, list_of_card_rects, reroll_rect)
    """
    # 1. Sfondo oscurato con bagliore
    bg_surf = get_background_image("board_bg", WIDTH, HEIGHT)
    surface.blit(bg_surf, (0, 0))
    
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 14, 24, 210))
    surface.blit(overlay, (0, 0))
    
    # 2. Header Schermata
    header_rect = pygame.Rect(WIDTH // 2 - 370, 35, 740, 58)
    draw_glass_panel(surface, header_rect, border_radius=29, bg_color=(14, 18, 30, 235), border_color=(235, 190, 60, 220), border_width=2)
    draw_text("SCEGLI UN AUGMENT HEXTECH", pygame.font.SysFont("Arial", 38, bold=True), GOLD, surface, header_rect.centerx, header_rect.centery)
    
    sub_font = pygame.font.SysFont("Arial", 13, bold=True)
    draw_text("POTENZIAMENTO PERMANENTE PER LA TUA SQUADRA", sub_font, (190, 210, 240), surface, WIDTH // 2, 110)
    
    # 3. Le 3 Carte degli Augments
    card_w = 270
    card_h = 360
    spacing = 40
    start_x = WIDTH // 2 - (3 * card_w + 2 * spacing) // 2
    card_y = 150
    
    card_rects = []
    button_rects = []
    
    for i, aug in enumerate(offered_augments):
        cx = start_x + i * (card_w + spacing)
        rect = pygame.Rect(cx, card_y, card_w, card_h)
        card_rects.append(rect)
        
        is_hover = rect.collidepoint(mouse_pos)
        tier_color = aug["color"]
        
        # Sfondo card glassmorphic
        bg_col = (20, 26, 42, 245) if is_hover else (14, 18, 30, 230)
        border_w = 3 if is_hover else 2
        draw_glass_panel(surface, rect, border_radius=22, bg_color=bg_col, border_color=tier_color, border_width=border_w)
        
        # Badge Tier in alto al centro
        tier_badge = pygame.Rect(cx + card_w // 2 - 55, card_y + 16, 110, 26)
        pygame.draw.rect(surface, (12, 16, 24), tier_badge, border_radius=13)
        pygame.draw.rect(surface, tier_color, tier_badge, width=1, border_radius=13)
        draw_text(f"{aug['tier'].upper()}", pygame.font.SysFont("Arial", 12, bold=True), tier_color, surface, tier_badge.centerx, tier_badge.centery)
        
        # Stemma Centrale con Tag
        emblem_rect = pygame.Rect(cx + card_w // 2 - 42, card_y + 56, 84, 84)
        pygame.draw.rect(surface, (18, 24, 38), emblem_rect, border_radius=18)
        pygame.draw.rect(surface, tier_color, emblem_rect, width=2, border_radius=18)
        draw_text(aug["tag"], pygame.font.SysFont("Arial", 18, bold=True), tier_color, surface, emblem_rect.centerx, emblem_rect.centery)
        
        # Nome Augment
        name_font = pygame.font.SysFont("Arial", 17, bold=True)
        draw_text(aug["name"], name_font, WHITE, surface, cx + card_w // 2, card_y + 160)
        
        # Descrizione dettagliata (Multi-line)
        desc_font = pygame.font.SysFont("Arial", 13, bold=True)
        words = aug["desc"].split(" ")
        lines = []
        curr_line = []
        for word in words:
            curr_line.append(word)
            if len(" ".join(curr_line)) > 26:
                lines.append(" ".join(curr_line[:-1]))
                curr_line = [word]
        if curr_line:
            lines.append(" ".join(curr_line))
            
        for l_idx, line in enumerate(lines):
            draw_text(line, desc_font, (215, 225, 245), surface, cx + card_w // 2, card_y + 200 + l_idx * 20)
            
        # Pulsante SCEGLI in basso
        btn_rect = pygame.Rect(cx + 25, card_y + card_h - 58, card_w - 50, 42)
        button_rects.append(btn_rect)
        btn_hover = btn_rect.collidepoint(mouse_pos)
        
        btn_col = (35, 175, 75) if btn_hover else (25, 130, 55)
        pygame.draw.rect(surface, btn_col, btn_rect, border_radius=21)
        pygame.draw.rect(surface, (100, 240, 130) if btn_hover else (50, 180, 80), btn_rect, width=2, border_radius=21)
        draw_text("SCEGLI", HEADER_FONT, WHITE, surface, btn_rect.centerx, btn_rect.centery)

    # 4. Pulsante Reroll Augment in fondo
    reroll_rect = pygame.Rect(WIDTH // 2 - 140, card_y + card_h + 30, 280, 46)
    r_hover = reroll_rect.collidepoint(mouse_pos) and can_reroll
    r_col = (195, 130, 25) if r_hover else ((150, 95, 20) if can_reroll else (45, 48, 56))
    
    pygame.draw.rect(surface, r_col, reroll_rect, border_radius=23)
    pygame.draw.rect(surface, (255, 210, 80) if can_reroll else (70, 75, 85), reroll_rect, width=2, border_radius=23)
    
    reroll_text = "REROLL AUGMENT (1 Rimasto)" if can_reroll else "REROLL ESAURITO"
    draw_text(reroll_text, BUTTON_FONT, WHITE if can_reroll else (140, 140, 140), surface, reroll_rect.centerx, reroll_rect.centery)
    
    return card_rects, button_rects, reroll_rect

def draw_hud_augments(surface, mouse_pos, player_augments, start_x=12, start_y=38):
    """
    Disegna fino a 3 stemmi esagonali/arrotondati degli Augments posseduti dal giocatore,
    con tooltip all'hover.
    """
    if not player_augments:
        return
        
    badge_w = 48
    badge_h = 32
    spacing = 8
    
    hovered_aug = None
    for i, aug_id in enumerate(player_augments[:3]):
        aug = AUGMENTS_DATABASE.get(aug_id)
        if not aug:
            continue
            
        bx = start_x + i * (badge_w + spacing)
        by = start_y
        rect = pygame.Rect(bx, by, badge_w, badge_h)
        
        is_hover = rect.collidepoint(mouse_pos)
        if is_hover:
            hovered_aug = aug
            
        tier_col = aug.get("color", TIER_SILVER)
        pygame.draw.rect(surface, (14, 18, 28, 230), rect, border_radius=8)
        pygame.draw.rect(surface, tier_col, rect, width=2 if is_hover else 1, border_radius=8)
        
        draw_text(aug["tag"][:4], MICRO_FONT, tier_col, surface, rect.centerx, rect.centery)
        
    # Tooltip all'hover
    if hovered_aug:
        tip_w = 230
        tip_h = 100
        tip_x = min(WIDTH - tip_w - 10, max(10, mouse_pos[0] + 15))
        tip_y = min(HEIGHT - tip_h - 10, max(10, mouse_pos[1] + 15))
        
        tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
        draw_glass_panel(surface, tip_rect, border_radius=12, bg_color=(12, 16, 26, 245), border_color=hovered_aug["color"], border_width=2)
        
        draw_text(hovered_aug["name"], pygame.font.SysFont("Arial", 13, bold=True), hovered_aug["color"], surface, tip_x + 12, tip_y + 14, center=False)
        draw_text(f"Tier: {hovered_aug['tier']}", MICRO_FONT, (180, 190, 210), surface, tip_x + 12, tip_y + 32, center=False)
        
        # Descrizione in 2 righe
        words = hovered_aug["desc"].split(" ")
        lines = []
        curr = []
        for w in words:
            curr.append(w)
            if len(" ".join(curr)) > 28:
                lines.append(" ".join(curr[:-1]))
                curr = [w]
        if curr:
            lines.append(" ".join(curr))
            
        for l_idx, line in enumerate(lines[:3]):
            draw_text(line, MICRO_FONT, WHITE, surface, tip_x + 12, tip_y + 52 + l_idx * 14, center=False)
