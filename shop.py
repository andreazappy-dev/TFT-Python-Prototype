import pygame
import random
from champions import Champion, get_available_champions
from traits import calculate_team_traits, draw_traits_sidebar, TRAITS_DATA
from items import get_item_data, get_item_icon_surface, draw_item_icon
from asset_loader import get_background_image, draw_glass_panel, create_card_image
from augments import draw_hud_augments

# Importo da config.py
from config import (
    draw_text, TEXT_FONT, BUTTON_FONT, TITLE_FONT, 
    BLUE, LIGHT_BLUE, GRAY, GOLD, BLACK, GREEN, WHITE, RED, WIDTH, HEIGHT
)

class ShopManager:
    """
    Gestisce la logica e il rendering dello shop.
    È controllato da game.py
    """
    def __init__(self, game, champions_database):
        self.game = game  # Riferimento alla classe Game principale
        self.shop_size = 5
        self.card_size = (165, 205)
        self.spacing_x = 205
        self.margin_y = 86
        
        self.champions_pool = champions_database
        self.shop_champs = [] # I 5 campioni in vendita
        
        # Riferimenti ai bottoni per i click
        screen_width = self.game.screen.get_width()
        screen_height = self.game.screen.get_height()
        self.buy_xp_button_rect = pygame.Rect(screen_width//2 - 350, screen_height - 68, 210, 48)
        self.refresh_button_rect = pygame.Rect(screen_width//2 - 120, screen_height - 68, 180, 48)
        self.confirm_button_rect = pygame.Rect(screen_width//2 + 80, screen_height - 68, 220, 48)
        
        # Area Cestino di Vendita Dinamica (stile TFT durante il drag)
        self.sell_zone_rect = pygame.Rect(screen_width//2 - 240, screen_height - 68, 480, 48)
        
        self.buy_buttons = []

        # --- Aggiunte per Drag & Drop ---
        self.is_dragging = False
        self.dragged_champ = None
        self.dragged_from_list = None # 'board' o 'bench'
        self.dragged_from_index = -1
        
        # --- Drag & Drop Oggetti ---
        self.is_dragging_item = False
        self.dragged_item_idx = -1
        self.dragged_item_key = None
        
        # --- Ispettore Campione su Click ---
        self.inspected_champion = None
        self.inspector_rect = pygame.Rect(0, 0, 540, 660)
        self.inspector_close_rect = pygame.Rect(0, 0, 36, 36)
        
        self.scroll_y = 0

        self.roll_shop(is_free=True)

    def reset(self):
        self.roll_shop(is_free=True)

    def roll_shop(self, is_free=False):
        player_augments = getattr(self.game, 'player_augments', [])
        is_golden_ticket_free = False
        
        if not is_free:
            if "golden_ticket" in player_augments and random.random() < 0.45:
                is_golden_ticket_free = True
                print("🎟️ BIGLIETTO DORATO! Questo Reroll è Gratuito!")
                if hasattr(self.game, 'audio'):
                    self.game.audio.play_sfx("coin_buy")
            elif self.game.player_gold >= 2:
                self.game.player_gold -= 2
            else:
                print("Oro non sufficiente per il Reroll!")
                return
                
        # Tabella probabilità: {livello: [C1, C2, C3, C4, C5]}
        shop_odds = {
            1: [1.00, 0.00, 0.00, 0.00, 0.00],
            2: [1.00, 0.00, 0.00, 0.00, 0.00],
            3: [0.75, 0.25, 0.00, 0.00, 0.00],
            4: [0.55, 0.30, 0.15, 0.00, 0.00],
            5: [0.45, 0.33, 0.20, 0.02, 0.00],
            6: [0.30, 0.40, 0.25, 0.05, 0.00],
            7: [0.19, 0.30, 0.35, 0.15, 0.01],
            8: [0.18, 0.25, 0.32, 0.22, 0.03],
            9: [0.10, 0.20, 0.25, 0.35, 0.10],
        }
        
        level = min(9, max(1, self.game.player_level))
        odds = shop_odds[level]
        
        self.shop_champs = []
        for _ in range(self.shop_size):
            r = random.random()
            cumulative = 0
            target_cost = 1
            for cost, prob in enumerate(odds, start=1):
                cumulative += prob
                if r <= cumulative:
                    target_cost = cost
                    break
            
            pool = [c for c in self.champions_pool if c.cost == target_cost]
            if not pool: 
                pool = self.champions_pool 
            self.shop_champs.append(random.choice(pool))
            
        if not is_free and hasattr(self.game, 'audio'):
            self.game.audio.play_sfx("reroll")
        print("Shop ricaricato.")

    # --- Acquisto Campione ---
    def buy_champion(self, champ_to_buy, shop_slot_index):
        # Cerca il primo slot libero nella panchina
        free_slot = -1
        for i in range(self.game.bench_slots):
            if self.game.bench[i] is None:
                free_slot = i
                break
                
        if free_slot == -1:
            print("Panchina piena!")
            return 

        cost = self.shop_champs[shop_slot_index].cost
        if self.game.player_gold >= cost:
            self.game.player_gold -= cost
            
            bought_champ = self.shop_champs[shop_slot_index]
            self.shop_champs[shop_slot_index] = None # Slot vuoto
            
            # Aggiungi il campione alla panchina
            self.game.bench[free_slot] = bought_champ
            if hasattr(self.game, 'audio'):
                self.game.audio.play_sfx("coin_buy")
            print(f"Comprato: {bought_champ.name} per {cost}g. Aggiunto alla panchina nello slot {free_slot}.")
            
            # Controlla i merge dopo ogni acquisto
            self.merge_champions(bought_champ)
        else:
            print("Oro non sufficiente!")

    # --- Controllo Merge ---
    def merge_champions(self, champ_just_added):
        if not champ_just_added:
            return False

        name_to_check = champ_just_added.name
        level_to_check = getattr(champ_just_added, 'level', 1)
        if level_to_check >= 3:
            return False # Già a 3 stelle
        
        # 1. Trova tutte le copie (in entrambe le liste) e i loro indici
        board_copies = [(i, c, 'board') for i, c in enumerate(self.game.board) if c and c.name == name_to_check and getattr(c, 'level', 1) == level_to_check]
        bench_copies = [(i, c, 'bench') for i, c in enumerate(self.game.bench) if c and c.name == name_to_check and getattr(c, 'level', 1) == level_to_check]
        
        all_copies = board_copies + bench_copies
        
        if len(all_copies) < 3:
            return False # Non c'è un merge

        print(f"🌟 MERGE DI {name_to_check} Lvl {level_to_check} -> Lvl {level_to_check + 1}!")
        copies_to_merge = all_copies[:3]
        base_champ = copies_to_merge[0][1]
        
        # Raccogli tutti gli oggetti e identifica se c'era una copia sulla scacchiera
        collected_items = []
        preferred_board_slot = None
        
        for idx, c, location in copies_to_merge:
            c_items = list(getattr(c, 'items', []))
            collected_items.extend(c_items)
            if location == 'board' and preferred_board_slot is None:
                preferred_board_slot = idx
                
        # 2. Rimuovi le 3 copie da board o bench
        for idx, c, location in copies_to_merge:
            if location == 'board' and self.game.board[idx] == c:
                self.game.board[idx] = None
            elif location == 'bench' and self.game.bench[idx] == c:
                self.game.bench[idx] = None
            
        # 3. Crea il campione potenziato
        new_level = level_to_check + 1
        multiplier = 1.8 if new_level == 2 else 3.2 
        
        upgraded = Champion(
            base_champ.name, 
            int(base_champ.base_hp * multiplier), 
            int(base_champ.base_attack * multiplier), 
            int(getattr(base_champ, 'base_defense', 0) * multiplier),
            getattr(base_champ, 'crit_chance', 0.1),
            getattr(base_champ, 'mana_max', 100),
            getattr(base_champ, 'mana_start', 0),
            getattr(base_champ, 'attack_speed', 0.7),
            getattr(base_champ, 'attack_range', 1),
            cost=getattr(base_champ, 'cost', 1),
            traits=getattr(base_champ, 'traits', [])
        )
        upgraded.level = new_level
        upgraded.max_hp = upgraded.base_hp
        upgraded.hp = upgraded.max_hp
        
        # 4. Trasferisci, combina ed equipaggia tutti gli oggetti raccolti
        excess_items = []
        for item in collected_items:
            res, obj = upgraded.equip_item(item)
            if res == 'full':
                excess_items.append(item)
                
        # Restituisci gli oggetti in eccesso al banco oggetti del giocatore
        for excess in excess_items:
            if len(self.game.player_items) < 8:
                self.game.player_items.append(excess)
                print(f"Restituito oggetto in eccesso al banco: {excess}")
        
        # 5. Posizionamento: se una copia era sulla board, mantienilo sulla board
        placed = False
        if preferred_board_slot is not None and self.game.board[preferred_board_slot] is None:
            self.game.board[preferred_board_slot] = upgraded
            placed = True
            print(f"Schierato {upgraded.name} Lvl {upgraded.level} direttamente sulla scacchiera nello slot {preferred_board_slot}.")
        else:
            # Cerca posto in panchina
            for i in range(self.game.bench_slots):
                if self.game.bench[i] is None:
                    self.game.bench[i] = upgraded
                    placed = True
                    print(f"Messo {upgraded.name} Lvl {upgraded.level} in panchina nello slot {i}.")
                    break
                    
        # Se panchina piena e c'era posto in board
        if not placed:
            for i in range(self.game.board_slots):
                if self.game.board[i] is None:
                    self.game.board[i] = upgraded
                    placed = True
                    break

        if hasattr(self.game, 'audio'):
            self.game.audio.play_sfx("merge_star")
            
        # Controlla ricorsivamente se ora si può fare un 3 stelle!
        self.merge_champions(upgraded)
        return True

    def handle_event(self, event):
        mouse_pos = getattr(event, 'pos', pygame.mouse.get_pos())
        
        # 1. Chiusura Ispettore (se aperto)
        if self.inspected_champion:
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_SPACE]:
                self.inspected_champion = None
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Se clicca sulla "✕" o fuori dal modal, chiudi l'ispettore
                if self.inspector_close_rect.collidepoint(mouse_pos) or not self.inspector_rect.collidepoint(mouse_pos):
                    self.inspected_champion = None
                    return
                # Clic all'interno dell'ispettore -> assorbi l'evento
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if not self.inspector_rect.collidepoint(mouse_pos):
                    self.inspected_champion = None

        if hasattr(self.game, 'damage_meter') and self.game.damage_meter.handle_event(event):
            return
            
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 30
            self.scroll_y = max(-350, min(0, self.scroll_y)) 
            return 
        
        # --- RILASCIO OGGETTI SUI CAMPIONI (MOUSEBUTTONUP) ---
        if self.is_dragging_item and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_item = False
            board_rects = self.get_board_rects()
            bench_rects = self.get_bench_rects()
            
            target_champ = None
            for i, rect in enumerate(board_rects):
                if rect.collidepoint(mouse_pos) and self.game.board[i]:
                    target_champ = self.game.board[i]
                    break
            if not target_champ:
                for i, rect in enumerate(bench_rects):
                    if rect.collidepoint(mouse_pos) and self.game.bench[i]:
                        target_champ = self.game.bench[i]
                        break
                        
            if target_champ:
                status, res = target_champ.equip_item(self.dragged_item_key)
                if status in ["combined", "equipped"]:
                    if self.dragged_item_idx < len(self.game.player_items):
                        self.game.player_items.pop(self.dragged_item_idx)
                    if status == "combined":
                        if hasattr(self.game, 'audio'): self.game.audio.play_sfx("merge_star")
                        print(f"✨ FUSIONE OGGETTO! Creato: {res['name']} per {target_champ.name}!")
                    else:
                        if hasattr(self.game, 'audio'): self.game.audio.play_sfx("drop_token")
                        print(f"Equipaggiato {res['name']} su {target_champ.name}.")
                else:
                    print("Campione già pieno (max 3 oggetti)!")
            self.dragged_item_key = None
            return

        # --- RILASCIO CAMPIONI DRAGGATI (MOUSEBUTTONUP) ---
        if self.is_dragging and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # 1. RILASCIO SUL CESTINO DI VENDITA
            if self.sell_zone_rect.collidepoint(mouse_pos):
                self.sell_champion(self.dragged_champ)
                self.is_dragging = False
                self.dragged_champ = None
                self.dragged_from_list = None
                self.dragged_from_index = -1
                return

            board_rects = self.get_board_rects()
            bench_rects = self.get_bench_rects()
            
            # 2. Rilascio su BOARD
            for i, rect in enumerate(board_rects):
                if rect.collidepoint(mouse_pos):
                    # Controllo limite di campioni attivi
                    active_count = sum(1 for c in self.game.board if c is not None)
                    if self.dragged_from_list == self.game.bench and active_count >= self.game.player_level and self.game.board[i] is None:
                        print("Livello insufficiente per aggiungere un altro campione!")
                        self.return_dragged_champ()
                        return
                    
                    self.place_champ_in_list(self.game.board, i)
                    return
            
            # 3. Rilascio su BENCH
            for i, rect in enumerate(bench_rects):
                if rect.collidepoint(mouse_pos):
                    self.place_champ_in_list(self.game.bench, i)
                    return

            # 4. Fallback sicuro: se mollato nel vuoto, torna SEMPRE al suo posto originale!
            self.return_dragged_champ()
            return

        # --- GESTIONE CLICK DEL MOUSE ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            # === TASTO DESTRO (BUTTON 3): SOLO ED ESCLUSIVAMENTE ISPEZIONE SCHEDA ===
            if event.button == 3:
                # Ispezione carte nello Shop
                for i, champ in enumerate(self.shop_champs):
                    if champ:
                        x = 215 + i * self.spacing_x
                        y = self.margin_y + self.scroll_y
                        card_rect = pygame.Rect(x, y, *self.card_size)
                        if card_rect.collidepoint(mouse_pos):
                            self.inspected_champion = champ
                            return

                # Ispezione campioni su Board o Bench
                board_rects = self.get_board_rects()
                bench_rects = self.get_bench_rects()
                for i, rect in enumerate(board_rects):
                    if rect.collidepoint(mouse_pos) and self.game.board[i]:
                        self.inspected_champion = self.game.board[i]
                        return 
                for i, rect in enumerate(bench_rects):
                    if rect.collidepoint(mouse_pos) and self.game.bench[i]:
                        self.inspected_champion = self.game.bench[i]
                        return 
                return 

            # === TASTO SINISTRO (BUTTON 1): ACQUISTO, PULSANTI E SPOSTAMENTO (DRAG) ===
            if event.button == 1:
                # Bottoni UI
                if self.refresh_button_rect.collidepoint(mouse_pos):
                    self.roll_shop()
                    return
                if self.buy_xp_button_rect.collidepoint(mouse_pos):
                    self.game.buy_xp()
                    return
                if self.confirm_button_rect.collidepoint(mouse_pos) and any(c is not None for c in self.game.board):
                    self.game.start_battle()
                    return
                    
                # Click sulle Card dello Shop (Acquisto)
                for i, rect in enumerate(self.buy_buttons):
                    if rect.collidepoint(mouse_pos):
                        if self.shop_champs[i]:
                            self.buy_champion(self.shop_champs[i], i)
                        return
                
                # Inizia DRAG OGGETTI
                item_rects = self.get_item_bench_rects()
                for i, rect in enumerate(item_rects):
                    if rect.collidepoint(mouse_pos) and i < len(self.game.player_items):
                        self.is_dragging_item = True
                        self.dragged_item_idx = i
                        self.dragged_item_key = self.game.player_items[i]
                        return

                # Inizia DRAG CAMPIONI (NESSUNA APERTURA ISPETTORE SU CLICK SINISTRO)
                board_rects = self.get_board_rects()
                bench_rects = self.get_bench_rects()
                
                for i, rect in enumerate(board_rects):
                    if rect.collidepoint(mouse_pos) and self.game.board[i]:
                        self.start_dragging(self.game.board, i)
                        return
                for i, rect in enumerate(bench_rects):
                    if rect.collidepoint(mouse_pos) and self.game.bench[i]:
                        self.start_dragging(self.game.bench, i)
                        return
    
    def sell_champion(self, champion):
        if not champion:
            return
        level = getattr(champion, 'level', 1)
        cost = getattr(champion, 'cost', 1)
        
        total_invested = cost * (3 ** (level - 1))
        sell_price = total_invested if level == 1 else max(1, total_invested - 1)
        
        self.game.player_gold += sell_price
        if hasattr(self.game, 'audio'):
            self.game.audio.play_sfx("sell")
        print(f"💰 VENDUTO {champion.name} (★{level}) per +{sell_price} Oro!")

    def start_dragging(self, from_list, index):
        if self.is_dragging or from_list[index] is None:
            return 
        
        self.dragged_champ = from_list[index]
        from_list[index] = None 
        self.dragged_from_list = from_list 
        self.dragged_from_index = index 
        self.is_dragging = True

    def place_champ_in_list(self, target_list, target_index):
        if not self.dragged_champ or self.dragged_from_list is None:
            self.is_dragging = False
            self.dragged_champ = None
            return

        # Se lo slot è occupato, esegui lo scambio
        champ_in_slot = target_list[target_index]
        target_list[target_index] = self.dragged_champ
        self.dragged_from_list[self.dragged_from_index] = champ_in_slot
            
        self.is_dragging = False
        self.dragged_champ = None
        self.dragged_from_list = None
        self.dragged_from_index = -1
        if hasattr(self.game, 'audio'):
            self.game.audio.play_sfx("drop_token")

    def return_dragged_champ(self):
        if self.dragged_champ and self.dragged_from_list is not None and self.dragged_from_index >= 0:
            self.dragged_from_list[self.dragged_from_index] = self.dragged_champ
        self.is_dragging = False
        self.dragged_champ = None
        self.dragged_from_list = None
        self.dragged_from_index = -1

    def get_board_rects(self):
        rects = []
        cell_w, cell_h = 100, 100
        cols, rows = 7, 2
        x_start = (self.game.screen.get_width() - (cols * cell_w)) // 2
        y_start = self.game.screen.get_height() - 400 + self.scroll_y
        
        for r in range(rows):
            for c in range(cols):
                x = x_start + c * cell_w
                y = y_start + r * cell_h
                rects.append(pygame.Rect(x, y, cell_w, cell_h))
        return rects
        
    def get_bench_rects(self):
        rects = []
        cell_w, cell_h = 100, 100
        x_start = (self.game.screen.get_width() - (self.game.bench_slots * cell_w)) // 2
        y = self.game.screen.get_height() - 150 + self.scroll_y
        for i in range(self.game.bench_slots):
            x = x_start + i * cell_w
            rects.append(pygame.Rect(x, y, cell_w, cell_h))
        return rects

    def get_item_bench_rects(self):
        rects = []
        slot_size = 44
        spacing = 6
        x_start = 20
        y_start = self.game.screen.get_height() - 105 + self.scroll_y
        for i in range(8):
            col = i % 4
            row = i // 4
            x = x_start + col * (slot_size + spacing)
            y = y_start + row * (slot_size + spacing)
            rects.append(pygame.Rect(x, y, slot_size, slot_size))
        return rects

    def draw_champ_items(self, surface, champ, cx, cy):
        items = getattr(champ, "items", [])
        if not items:
            return
        for idx, item in enumerate(items[:3]):
            ix = cx - 20 + idx * 20
            iy = cy + 18
            ibox = pygame.Rect(ix - 9, iy - 9, 18, 18)
            draw_item_icon(surface, item, ibox)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        
        # --- 1. SFONDO ARENA AI ---
        bg_surf = get_background_image("board_bg", surface.get_width(), surface.get_height())
        surface.blit(bg_surf, (0, 0))
        
        # Overlay scuro per contrasto
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 145))
        surface.blit(overlay, (0, 0))
        
        # --- 2. TOP BAR (STATO GIOCATORE CON PILLOLE CURVE) ---
        top_bar_rect = pygame.Rect(surface.get_width() // 2 - 490, 12, 980, 50)
        draw_glass_panel(surface, top_bar_rect, border_radius=25, bg_color=(12, 16, 26, 220), border_color=(190, 160, 65, 170), border_width=1)
        
        stat_font = pygame.font.SysFont("Arial", 14, bold=True)
        small_font = pygame.font.SysFont("Arial", 11, bold=True)
        
        # Pillola HP
        hp_rect = pygame.Rect(top_bar_rect.x + 18, 19, 115, 36)
        draw_glass_panel(surface, hp_rect, border_radius=18, bg_color=(25, 55, 35, 230), border_color=(60, 200, 100, 200), border_width=1)
        draw_text(f"HP: {self.game.player_hp}", stat_font, (120, 255, 160), surface, hp_rect.centerx, hp_rect.centery)
        
        # Pillola Oro
        gold_rect = pygame.Rect(top_bar_rect.x + 148, 19, 120, 36)
        draw_glass_panel(surface, gold_rect, border_radius=18, bg_color=(55, 45, 15, 230), border_color=(255, 215, 60, 220), border_width=1)
        draw_text(f"ORO: {self.game.player_gold}g", stat_font, GOLD, surface, gold_rect.centerx, gold_rect.centery)
        
        # Pillola Round
        round_rect = pygame.Rect(top_bar_rect.right - 145, 19, 125, 36)
        draw_glass_panel(surface, round_rect, border_radius=18, bg_color=(35, 40, 55, 230), border_color=(140, 160, 200, 200), border_width=1)
        draw_text(f"ROUND: {self.game.round_number}", stat_font, (220, 235, 255), surface, round_rect.centerx, round_rect.centery)
        
        # Pillola Livello & Barra XP
        lvl_rect = pygame.Rect(top_bar_rect.x + 282, 19, 390, 36)
        draw_glass_panel(surface, lvl_rect, border_radius=18, bg_color=(20, 35, 55, 230), border_color=(60, 140, 240, 200), border_width=1)
        
        curr_xp = self.game.player_xp
        max_xp = self.game.xp_to_level.get(self.game.player_level, 999)
        draw_text(f"LVL {self.game.player_level}", stat_font, (140, 210, 255), surface, lvl_rect.x + 48, lvl_rect.centery)
        
        # Barra di avanzamento XP
        bar_x = lvl_rect.x + 105
        bar_y = lvl_rect.centery - 7
        bar_w = 200
        bar_h = 14
        pygame.draw.rect(surface, (15, 20, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=7)
        if max_xp > 0:
            pct = min(1.0, curr_xp / max_xp)
            if pct > 0:
                pygame.draw.rect(surface, (40, 160, 255), (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=7)
        pygame.draw.rect(surface, (100, 180, 255), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=7)
        draw_text(f"{curr_xp}/{max_xp} XP", small_font, WHITE, surface, bar_x + bar_w // 2, lvl_rect.centery)

        # --- 3. RACK NEGOZIO (CARTE CAMPIONI CURVE SENZA SOVRAPPOSIZIONI) ---
        shop_rack_rect = pygame.Rect(200, self.margin_y + self.scroll_y - 8, 1040, self.card_size[1] + 16)
        draw_glass_panel(surface, shop_rack_rect, border_radius=20, bg_color=(12, 16, 25, 210), border_color=(70, 85, 110, 140), border_width=1)
        
        self.buy_buttons.clear() 
        for i, champ in enumerate(self.shop_champs):
            x = 215 + i * self.spacing_x
            y = self.margin_y + self.scroll_y
            card_rect = pygame.Rect(x, y, *self.card_size)
            
            if champ: 
                # 1. Sfondo Card Completa
                pygame.draw.rect(surface, (18, 22, 32), card_rect, border_radius=14)
                
                # 2. Illustrazione del Campione (Sezione superiore)
                img_h = 108
                card_img = champ.get_card_surface(self.card_size[0], img_h)
                surface.blit(card_img, (x, y))
                
                # Bordo Tier Curvo sulla porzione immagine
                tier_color = getattr(champ, 'tier_color', WHITE)
                pygame.draw.rect(surface, tier_color, (x, y, self.card_size[0], img_h), width=2, border_radius=14)
                
                # 3. Badge Costo Curvo in alto a destra
                cost_badge = pygame.Rect(x + self.card_size[0] - 38, y + 6, 32, 20)
                pygame.draw.rect(surface, (12, 15, 22, 230), cost_badge, border_radius=6)
                pygame.draw.rect(surface, GOLD, cost_badge, width=1, border_radius=6)
                draw_text(f"{champ.cost}g", pygame.font.SysFont("Arial", 12, bold=True), GOLD, surface, cost_badge.centerx, cost_badge.centery)
                
                # 4. Tratti Campione (Spazio dedicato sotto l'immagine)
                traits_str = " • ".join(getattr(champ, "traits", []))
                trait_font = pygame.font.SysFont("Arial", 11, bold=True)
                draw_text(traits_str, trait_font, (215, 215, 165), surface, x + self.card_size[0]//2, y + img_h + 12)
                
                # 5. Nome Campione
                name_font = pygame.font.SysFont("Arial", 14, bold=True)
                draw_text(champ.name, name_font, WHITE, surface, x + self.card_size[0]//2, y + img_h + 30)
                
                # 6. Bordo Totale Card
                pygame.draw.rect(surface, tier_color, card_rect, width=1, border_radius=14)
                
                # 7. Bottone Compra Integrato sul fondo della card
                buy_button = pygame.Rect(x + 10, y + self.card_size[1] - 38, self.card_size[0] - 20, 30)
                self.buy_buttons.append(buy_button) 
                
                can_buy = self.game.player_gold >= champ.cost and any(s is None for s in self.game.bench)
                btn_is_hover = buy_button.collidepoint(mouse_pos)
                
                if can_buy:
                    btn_color = (35, 175, 75) if btn_is_hover else (25, 130, 55)
                    border_btn = (100, 240, 130) if btn_is_hover else (50, 180, 80)
                else:
                    btn_color = (45, 48, 58)
                    border_btn = (70, 75, 88)
                    
                pygame.draw.rect(surface, btn_color, buy_button, border_radius=15)
                pygame.draw.rect(surface, border_btn, buy_button, width=1, border_radius=15)
                draw_text(f"Compra ({champ.cost}g)", pygame.font.SysFont("Arial", 13, bold=True), WHITE if can_buy else (150, 150, 160), surface, buy_button.centerx, buy_button.centery)
            else:
                # Slot Shop Vuoto
                draw_glass_panel(surface, card_rect, border_radius=14, bg_color=(18, 22, 32, 160), border_color=(40, 48, 60, 140), border_width=1)
                self.buy_buttons.append(pygame.Rect(0,0,0,0)) 

        # --- 4. PANNELLO SINERGIE LATERALE A SINISTRA & CLASSIFICA A DESTRA & AUGMENTS ---
        bonus_traits = []
        player_augments = getattr(self.game, 'player_augments', [])
        if "demacia_crown" in player_augments:
            bonus_traits.append("Demacia")
        if "piltover_heart" in player_augments:
            bonus_traits.append("Piltover")
        if "ionia_soul" in player_augments:
            bonus_traits.append("Ionia")
            
        active_board_champs = [c for c in self.game.board if c is not None]
        active_traits = calculate_team_traits(active_board_champs, bonus_traits=bonus_traits)
        
        draw_hud_augments(surface, mouse_pos, player_augments, start_x=12, start_y=30 + self.scroll_y)
        draw_traits_sidebar(surface, active_traits, start_x=12, start_y=75 + self.scroll_y)
        
        # --- DAMAGE METER (POST-BATTAGLIA) ---
        if hasattr(self.game, 'damage_meter') and getattr(self.game, 'last_battle_player_team', None):
            meter_y = max(390, 75 + len(active_traits) * 44 + 36) + self.scroll_y
            self.game.damage_meter.draw(
                surface, mouse_pos, self.game.last_battle_player_team, 
                elapsed_seconds=getattr(self.game, 'last_battle_duration', 5.0), 
                start_x=12, start_y=meter_y
            )
        
        if hasattr(self.game, 'lobby_manager'):
            self.game.lobby_manager.draw_leaderboard_sidebar(surface, mouse_pos, start_x=1230, start_y=75 + self.scroll_y)

        # --- 5. SCACCHIERA (CELLE CURVE TRASLUCIDE) ---
        active_count = sum(1 for c in self.game.board if c is not None)
        title_tag = pygame.Rect(surface.get_width() // 2 - 120, HEIGHT - 425 + self.scroll_y - 12, 240, 26)
        draw_glass_panel(surface, title_tag, border_radius=13, bg_color=(15, 20, 30, 210), border_color=(190, 160, 60, 160), border_width=1)
        draw_text(f"Scacchiera ({active_count}/{self.game.player_level})", stat_font, GOLD, surface, title_tag.centerx, title_tag.centery)
        
        board_rects = self.get_board_rects() 
        for i in range(self.game.board_slots):
            rect = board_rects[i]
            is_hover_slot = rect.collidepoint(mouse_pos)
            
            slot_bg = (28, 38, 52, 220) if is_hover_slot else (18, 24, 35, 180)
            slot_border = (80, 180, 240, 200) if is_hover_slot else (45, 55, 75, 140)
            
            cell_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(cell_surf, slot_bg, (0, 0, rect.width, rect.height), border_radius=12)
            pygame.draw.rect(cell_surf, slot_border, (0, 0, rect.width, rect.height), width=1, border_radius=12)
            surface.blit(cell_surf, (rect.x, rect.y))
            
            champ = self.game.board[i]
            if champ:
                # Ombra al suolo
                shadow_surf = pygame.Surface((56, 16), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (5, 8, 14, 150), (0, 0, 56, 16))
                surface.blit(shadow_surf, (rect.centerx - 28, rect.centery + 12))
                
                # Sprite Personaggio 2D
                sprite = champ.get_sprite_surface(width=72, height=72)
                surface.blit(sprite, (rect.centerx - 36, rect.centery - 38))
                
                stars = getattr(champ, "level", 1)
                if stars >= 2:
                    for s in range(min(stars, 3)):
                        cx = rect.centerx - (stars - 1) * 7 + s * 14
                        cy = rect.top + 8
                        pygame.draw.circle(surface, GOLD, (cx, cy), 4)
                        pygame.draw.circle(surface, (0, 0, 0), (cx, cy), 4, width=1)
                
                name_color = GOLD if stars > 1 else WHITE
                draw_text(champ.name, TEXT_FONT, (0,0,0), surface, rect.centerx + 1, rect.bottom - 9)
                draw_text(champ.name, TEXT_FONT, name_color, surface, rect.centerx, rect.bottom - 10)
                
                self.draw_champ_items(surface, champ, rect.centerx, rect.centery + 14)

        # --- 6. PANCHINA (CELLE CURVE) ---
        bench_tag = pygame.Rect(surface.get_width() // 2 - 75, HEIGHT - 180 + self.scroll_y - 12, 150, 26)
        draw_glass_panel(surface, bench_tag, border_radius=13, bg_color=(15, 20, 30, 210), border_color=(190, 160, 60, 160), border_width=1)
        draw_text("Panchina", stat_font, GOLD, surface, bench_tag.centerx, bench_tag.centery)
        
        bench_rects = self.get_bench_rects()
        for i in range(self.game.bench_slots):
            rect = bench_rects[i]
            is_hover_slot = rect.collidepoint(mouse_pos)
            
            slot_bg = (28, 38, 52, 220) if is_hover_slot else (18, 24, 35, 180)
            slot_border = (80, 180, 240, 200) if is_hover_slot else (45, 55, 75, 140)
            
            cell_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(cell_surf, slot_bg, (0, 0, rect.width, rect.height), border_radius=12)
            pygame.draw.rect(cell_surf, slot_border, (0, 0, rect.width, rect.height), width=1, border_radius=12)
            surface.blit(cell_surf, (rect.x, rect.y))
            
            champ = self.game.bench[i]
            if champ:
                # Ombra al suolo
                shadow_surf = pygame.Surface((56, 16), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (5, 8, 14, 150), (0, 0, 56, 16))
                surface.blit(shadow_surf, (rect.centerx - 28, rect.centery + 12))
                
                # Sprite Personaggio 2D
                sprite = champ.get_sprite_surface(width=72, height=72)
                surface.blit(sprite, (rect.centerx - 36, rect.centery - 38))
                
                stars = getattr(champ, "level", 1)
                if stars >= 2:
                    for s in range(min(stars, 3)):
                        cx = rect.centerx - (stars - 1) * 7 + s * 14
                        cy = rect.top + 8
                        pygame.draw.circle(surface, GOLD, (cx, cy), 4)
                        pygame.draw.circle(surface, (0, 0, 0), (cx, cy), 4, width=1)
                
                name_color = GOLD if stars > 1 else WHITE
                draw_text(champ.name, TEXT_FONT, (0,0,0), surface, rect.centerx + 1, rect.bottom - 9)
                draw_text(champ.name, TEXT_FONT, name_color, surface, rect.centerx, rect.bottom - 10)
                
                self.draw_champ_items(surface, champ, rect.centerx, rect.centery + 14)

        # --- 7. UI BASSA (BOTTONI O CESTINO DI VENDITA DURANTE IL DRAG) ---
        if self.is_dragging and self.dragged_champ:
            # Mostra Cestino di Vendita Dinamico stile TFT
            level = getattr(self.dragged_champ, 'level', 1)
            cost = getattr(self.dragged_champ, 'cost', 1)
            total_invested = cost * (3 ** (level - 1))
            sell_price = total_invested if level == 1 else max(1, total_invested - 1)
            
            is_sell_hover = self.sell_zone_rect.collidepoint(mouse_pos)
            bg_sell = (120, 25, 35, 240) if is_sell_hover else (60, 18, 25, 230)
            border_sell = (255, 90, 100) if is_sell_hover else (220, 70, 80)
            
            draw_glass_panel(surface, self.sell_zone_rect, border_radius=24, bg_color=bg_sell, border_color=border_sell, border_width=2 if is_sell_hover else 1)
            
            sell_font = pygame.font.SysFont("Arial", 16, bold=True)
            sell_txt = f"🗑️ RILASCIA QUI PER VENDERE (+{sell_price} ORO)"
            draw_text(sell_txt, sell_font, (255, 235, 140) if is_sell_hover else (255, 200, 205), surface, self.sell_zone_rect.centerx, self.sell_zone_rect.centery)
        else:
            # Bottone Compra XP
            can_xp = self.game.player_gold >= 4 and self.game.player_level < 9
            xp_hover = self.buy_xp_button_rect.collidepoint(mouse_pos)
            x_color = (35, 140, 240) if xp_hover and can_xp else ((25, 105, 195) if can_xp else (50, 52, 60))
            pygame.draw.rect(surface, x_color, self.buy_xp_button_rect, border_radius=24)
            pygame.draw.rect(surface, (100, 200, 255) if can_xp else (70, 75, 85), self.buy_xp_button_rect, width=2, border_radius=24)
            draw_text("COMPRA XP (4g)", BUTTON_FONT, WHITE if can_xp else (150, 150, 150), surface, self.buy_xp_button_rect.centerx, self.buy_xp_button_rect.centery)

            # Bottone Reroll
            reroll_hover = self.refresh_button_rect.collidepoint(mouse_pos)
            can_reroll = self.game.player_gold >= 2
            r_color = (210, 140, 20) if reroll_hover and can_reroll else ((170, 110, 15) if can_reroll else (50, 52, 60))
            pygame.draw.rect(surface, r_color, self.refresh_button_rect, border_radius=24)
            pygame.draw.rect(surface, (255, 210, 80) if can_reroll else (70, 75, 85), self.refresh_button_rect, width=2, border_radius=24)
            draw_text("REROLL (2g)", BUTTON_FONT, WHITE if can_reroll else (150, 150, 150), surface, self.refresh_button_rect.centerx, self.refresh_button_rect.centery)

            # Bottone Inizia Battaglia
            can_confirm = active_count > 0 
            btn_hover = self.confirm_button_rect.collidepoint(mouse_pos)
            c_color = (35, 185, 85) if btn_hover and can_confirm else ((25, 145, 65) if can_confirm else (50, 52, 60))
            pygame.draw.rect(surface, c_color, self.confirm_button_rect, border_radius=24)
            pygame.draw.rect(surface, (120, 255, 160) if can_confirm else (70, 75, 85), self.confirm_button_rect, width=2, border_radius=24)
            draw_text("COMBATTI", BUTTON_FONT, WHITE if can_confirm else (150, 150, 150), surface, self.confirm_button_rect.centerx, self.confirm_button_rect.centery)

        # --- 8. BANCO INVENTARIO OGGETTI (CURVO GLASSMORPHISM) ---
        item_box_rect = pygame.Rect(12, HEIGHT - 118 + self.scroll_y, 200, 100)
        draw_glass_panel(surface, item_box_rect, border_radius=16, bg_color=(14, 18, 28, 220), border_color=(190, 160, 60, 160), border_width=1)
        
        item_title_font = pygame.font.SysFont("Arial", 11, bold=True)
        draw_text("BANCO OGGETTI", item_title_font, GOLD, surface, item_box_rect.centerx, item_box_rect.top + 12)
        
        item_rects = self.get_item_bench_rects()
        
        hovered_item_desc = None
        for i, rect in enumerate(item_rects):
            is_slot_hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (20, 26, 38), rect, border_radius=8)
            pygame.draw.rect(surface, (80, 100, 130) if is_slot_hover else (45, 55, 75), rect, width=1, border_radius=8)
            
            if i < len(self.game.player_items):
                item_key = self.game.player_items[i]
                data = get_item_data(item_key)
                
                # Disegna icona grafica reale
                draw_item_icon(surface, item_key, rect, is_hover=is_slot_hover)
                
                if is_slot_hover and not self.is_dragging_item:
                    hovered_item_desc = f"{data.get('name','')}: {data.get('desc','')}"

        if hovered_item_desc:
            tip_font = pygame.font.SysFont("Arial", 13, bold=True)
            tip_surf = tip_font.render(hovered_item_desc, True, (245, 245, 255))
            tip_box = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] - 30, tip_surf.get_width() + 16, 26)
            pygame.draw.rect(surface, (12, 16, 25, 235), tip_box, border_radius=8)
            pygame.draw.rect(surface, GOLD, tip_box, width=1, border_radius=8)
            surface.blit(tip_surf, (tip_box.x + 8, tip_box.y + 6))

        # --- DRAG & DROP OGGETTI FEEDBACK (ICONA GRAFICA) ---
        if self.is_dragging_item and self.dragged_item_key:
            drag_icon = get_item_icon_surface(self.dragged_item_key, size=44, is_hover=True)
            surface.blit(drag_icon, (mouse_pos[0] - 22, mouse_pos[1] - 22))

        # --- DRAG & DROP CAMPIONI FEEDBACK ---
        if self.is_dragging and self.dragged_champ:
            drag_token = self.dragged_champ.get_token_surface(size=64)
            surface.blit(drag_token, (mouse_pos[0] - 32, mouse_pos[1] - 32))
            tier_color = getattr(self.dragged_champ, 'tier_color', WHITE)
            pygame.draw.circle(surface, tier_color, mouse_pos, 34, width=3)
            pygame.draw.circle(surface, (255, 255, 255), mouse_pos, 36, width=1)

        # --- 9. MODAL ISPETTORE CAMPIONE SU CLICK ---
        if self.inspected_champion:
            self.draw_champion_inspector(surface, self.inspected_champion)

    def draw_champion_inspector(self, surface, champ):
        """
        Disegna la Scheda Dettaglio / Ispettore Campione su Click (Glassmorphism TFT).
        Mostra: Portrait grande, Tier/Costo, Stelle, Tratti/Sinergie con spiegazione estesa,
        statistiche di combattimento complete, abilità speciale e oggetti.
        """
        if not champ:
            return

        mouse_pos = pygame.mouse.get_pos()
        sw = surface.get_width()
        sh = surface.get_height()

        # 1. Dark Backdrop Overlay
        backdrop = pygame.Surface((sw, sh), pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, 165))
        surface.blit(backdrop, (0, 0))

        # 2. Main Modal Rect
        modal_w = 540
        modal_h = 660
        modal_x = (sw - modal_w) // 2
        modal_y = (sh - modal_h) // 2
        self.inspector_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        # Glassmorphism Card Background
        tier_col = getattr(champ, 'tier_color', (180, 160, 60))
        draw_glass_panel(surface, self.inspector_rect, border_radius=22, bg_color=(15, 20, 32, 250), border_color=(*tier_col[:3], 220), border_width=2)

        # Pulsante Chiusura "✕"
        self.inspector_close_rect = pygame.Rect(modal_x + modal_w - 44, modal_y + 16, 30, 30)
        close_hover = self.inspector_close_rect.collidepoint(mouse_pos)
        pygame.draw.circle(surface, (200, 45, 55) if close_hover else (35, 45, 65), self.inspector_close_rect.center, 15)
        pygame.draw.circle(surface, (255, 100, 110) if close_hover else (80, 95, 120), self.inspector_close_rect.center, 15, width=1)
        close_font = pygame.font.SysFont("Arial", 16, bold=True)
        draw_text("✕", close_font, (255, 255, 255), surface, self.inspector_close_rect.centerx, self.inspector_close_rect.centery)

        # Fonts
        title_font = pygame.font.SysFont("Arial", 24, bold=True)
        h2_font = pygame.font.SysFont("Arial", 14, bold=True)
        body_font = pygame.font.SysFont("Arial", 12, bold=False)
        sub_font = pygame.font.SysFont("Arial", 11, bold=True)

        # 3. HEADER & RITRATTO
        portrait_rect = pygame.Rect(modal_x + 24, modal_y + 24, 96, 96)
        draw_glass_panel(surface, portrait_rect, border_radius=14, bg_color=(10, 14, 22, 240), border_color=tier_col, border_width=2)
        
        p_surf = create_card_image(champ.name, width=90, height=90)
        surface.blit(p_surf, (portrait_rect.x + 3, portrait_rect.y + 3))

        # Nome del Campione
        champ_name_x = modal_x + 135
        draw_text(champ.name, title_font, (255, 255, 255), surface, champ_name_x + 10, modal_y + 36)

        # Stelle ★
        stars = getattr(champ, "level", 1)
        star_str = "★" * stars
        draw_text(f"Rango: {star_str}", h2_font, GOLD, surface, champ_name_x + 40, modal_y + 64)

        # Badge Costo Tier
        cost = getattr(champ, "cost", 1)
        cost_badge = pygame.Rect(champ_name_x + 130, modal_y + 54, 110, 22)
        pygame.draw.rect(surface, (*tier_col[:3], 60), cost_badge, border_radius=11)
        pygame.draw.rect(surface, tier_col, cost_badge, width=1, border_radius=11)
        draw_text(f"TIER {cost} • {cost} ORO", sub_font, tier_col, surface, cost_badge.centerx, cost_badge.centery)

        # 4. SEZIONE TRATTI & SINERGIE (CON DESCRIZIONI COMPLETE)
        traits_y = modal_y + 135
        draw_text("TRATTI & SINERGIE", h2_font, (240, 205, 70), surface, modal_x + 85, traits_y)

        curr_ty = traits_y + 16
        for tname in getattr(champ, "traits", []):
            tdata = TRAITS_DATA.get(tname, {
                "color": (160, 160, 160),
                "type": "ORIGIN",
                "breakpoints": [2],
                "description": "Sinergia di combattimento."
            })
            tcolor = tdata["color"]
            ttype = tdata.get("type", "ORIGIN")
            
            # Badge Tratto
            tbadge_rect = pygame.Rect(modal_x + 24, curr_ty, modal_w - 48, 48)
            draw_glass_panel(surface, tbadge_rect, border_radius=10, bg_color=(20, 26, 40, 230), border_color=tcolor, border_width=1)
            
            # Icona circolare
            pygame.draw.circle(surface, tcolor, (modal_x + 44, curr_ty + 24), 12)
            pygame.draw.circle(surface, (255, 255, 255), (modal_x + 44, curr_ty + 24), 5)
            
            # Titolo Tratto + Tipo
            ttxt = f"{tname} ({ttype})"
            name_surf = h2_font.render(ttxt, True, tcolor)
            surface.blit(name_surf, (modal_x + 65, curr_ty + 5))
            
            # Breakpoints & Descrizione
            bp_str = "/".join(str(b) for b in tdata.get("breakpoints", []))
            desc_txt = f"Soglie ({bp_str}): {tdata.get('description', '')}"
            desc_surf = sub_font.render(desc_txt[:62], True, (210, 220, 235))
            surface.blit(desc_surf, (modal_x + 65, curr_ty + 26))
            
            curr_ty += 54

        # 5. STATISTICHE DI COMBATTIMENTO
        stats_y = curr_ty + 10
        draw_text("STATISTICHE BASE", h2_font, (240, 205, 70), surface, modal_x + 85, stats_y)
        
        # Grid box statistiche
        stats_box = pygame.Rect(modal_x + 24, stats_y + 16, modal_w - 48, 110)
        draw_glass_panel(surface, stats_box, border_radius=12, bg_color=(16, 22, 34, 220), border_color=(60, 75, 100), border_width=1)
        
        # 1a colonna
        c1_x = stats_box.x + 14
        draw_text(f"Salute (HP): {champ.hp} / {champ.max_hp}", sub_font, (120, 255, 160), surface, c1_x + 60, stats_box.y + 18)
        draw_text(f"Mana: {champ.mana_start} / {champ.mana_max}", sub_font, (100, 200, 255), surface, c1_x + 48, stats_box.y + 42)
        draw_text(f"Attacco (AD): {champ.base_attack}", sub_font, (255, 215, 80), surface, c1_x + 55, stats_box.y + 66)
        draw_text(f"Difesa (Armor): {getattr(champ, 'base_defense', 0)}", sub_font, (190, 205, 230), surface, c1_x + 58, stats_box.y + 90)
        
        # 2a colonna
        c2_x = stats_box.centerx + 14
        draw_text(f"Vel. Attacco: {champ.attack_speed:.2f}/s", sub_font, (240, 180, 70), surface, c2_x + 55, stats_box.y + 18)
        range_str = "Mischia (80px)" if champ.attack_range < 100 else ("Cecchino (500px)" if champ.attack_range > 350 else "Distanza (300px)")
        draw_text(f"Raggio: {range_str}", sub_font, (220, 225, 240), surface, c2_x + 65, stats_box.y + 42)
        crit_pct = int(champ.crit_chance * 100)
        draw_text(f"Critico: {crit_pct}% ({champ.crit_multiplier:.1f}x)", sub_font, (255, 120, 140), surface, c2_x + 58, stats_box.y + 66)
        sp_pct = int(getattr(champ, 'spell_power_mult', 1.0) * 100)
        draw_text(f"Potere Magico (AP): {sp_pct}%", sub_font, (210, 130, 255), surface, c2_x + 68, stats_box.y + 90)

        # 6. ABILITÀ SPECIALE
        ability_y = stats_box.bottom + 12
        ab_info = champ.get_ability_info() if hasattr(champ, 'get_ability_info') else {"name": "Abilità", "type": "Speciale", "cost": "100 Mana", "desc": "Mossa speciale"}
        
        ab_box = pygame.Rect(modal_x + 24, ability_y, modal_w - 48, 80)
        draw_glass_panel(surface, ab_box, border_radius=12, bg_color=(22, 28, 44, 230), border_color=(120, 90, 210), border_width=1)
        
        ab_title = f"✨ {ab_info['name']}  ({ab_info.get('type', 'Speciale')})  -  {ab_info.get('cost', '')}"
        ab_surf = h2_font.render(ab_title, True, (255, 235, 120))
        surface.blit(ab_surf, (ab_box.x + 12, ab_box.y + 8))
        
        desc = ab_info.get("desc", "")
        line1 = desc[:66]
        line2 = desc[66:132] if len(desc) > 66 else ""
        surface.blit(body_font.render(line1, True, (215, 225, 240)), (ab_box.x + 12, ab_box.y + 32))
        if line2:
            surface.blit(body_font.render(line2, True, (215, 225, 240)), (ab_box.x + 12, ab_box.y + 50))

        # 7. OGGETTI EQUIPAGGIATI (0/3)
        item_y = ab_box.bottom + 10
        draw_text("OGGETTI EQUIPAGGIATI (Max 3):", sub_font, (180, 195, 215), surface, modal_x + 115, item_y + 12)
        
        champ_items = getattr(champ, "items", [])
        for idx in range(3):
            slot_rect = pygame.Rect(modal_x + 240 + idx * 48, item_y - 2, 38, 38)
            if idx < len(champ_items):
                draw_item_icon(surface, champ_items[idx], slot_rect)
            else:
                draw_glass_panel(surface, slot_rect, border_radius=8, bg_color=(12, 16, 24, 180), border_color=(45, 55, 75), border_width=1)
                draw_text("•", sub_font, (80, 90, 110), surface, slot_rect.centerx, slot_rect.centery)
