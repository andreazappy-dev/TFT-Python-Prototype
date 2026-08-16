import pygame
import random
from champions import Champion, get_available_champions
from traits import calculate_team_traits, draw_traits_sidebar, TRAITS_DATA
from items import get_item_data, get_item_icon_surface, draw_item_icon
from asset_loader import get_background_image, draw_glass_panel, create_card_image
from augments import draw_hud_augments

# Importo da config.py
from config import (
    draw_text, draw_star, draw_cross,
    TEXT_FONT, BUTTON_FONT, TITLE_FONT, SUBTITLE_FONT, HEADER_FONT, SMALL_FONT, MICRO_FONT,
    BLUE, LIGHT_BLUE, GRAY, GOLD, BLACK, GREEN, WHITE, RED, WIDTH, HEIGHT
)

class ShopManager:
    """
    Gestisce la logica e il rendering dello shop responsive con risoluzione nativa.
    È controllato da game.py
    """
    def __init__(self, game, champions_database):
        self.game = game  # Riferimento alla classe Game principale
        self.shop_size = 5
        self.card_size = (185, 220)
        self.spacing_x = 199
        self.margin_y = 66
        
        self.champions_pool = champions_database
        self.shop_champs = [] # I 5 campioni in vendita
        
        # Riferimenti ai bottoni per i click (calcolati dinamicamente)
        self.buy_xp_button_rect = pygame.Rect(0, 0, 0, 0)
        self.refresh_button_rect = pygame.Rect(0, 0, 0, 0)
        self.confirm_button_rect = pygame.Rect(0, 0, 0, 0)
        self.sell_zone_rect = pygame.Rect(0, 0, 0, 0)
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
        
        # --- Ispettore Campione su Click DX ---
        self.inspected_champion = None
        self.inspector_rect = pygame.Rect(0, 0, 0, 0)
        self.inspector_close_rect = pygame.Rect(0, 0, 0, 0)
        
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
        
        # Recupera tutti gli oggetti equipaggiati sul campione e rimettili nel banco oggetti
        champ_items = getattr(champion, 'items', [])
        for itm in list(champ_items):
            if len(self.game.player_items) < 8:
                self.game.player_items.append(itm)
                print(f"🎒 Oggetto restituito al banco: {itm}")
        champion.items = []
        
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

        if target_list is self.dragged_from_list and target_index == self.dragged_from_index:
            # Stesso identico slot (click singolo o rilascio sullo stesso posto): rimetti il campione al suo posto!
            target_list[target_index] = self.dragged_champ
        else:
            # Slot differente: esegui swap se occupato, altrimenti piazza
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
        """Calcola le 21 celle della scacchiera (7 colonne x 3 righe, formato canonico TFT)"""
        sw = self.game.screen.get_width()
        sh = self.game.screen.get_height()
        rects = []
        cell_w, cell_h = 88, 76
        cols, rows = 7, 3
        x_start = (sw - (cols * cell_w)) // 2
        y_start = int(sh * 0.32)
        
        for r in range(rows):
            for c in range(cols):
                x = x_start + c * cell_w
                y = y_start + r * cell_h
                rects.append(pygame.Rect(x, y, cell_w, cell_h))
        return rects
        
    def get_bench_rects(self):
        sw = self.game.screen.get_width()
        sh = self.game.screen.get_height()
        rects = []
        cell_w, cell_h = 82, 76
        cols = self.game.bench_slots
        x_start = (sw - (cols * cell_w)) // 2
        y = int(sh * 0.61)
        for i in range(cols):
            x = x_start + i * cell_w
            rects.append(pygame.Rect(x, y, cell_w, cell_h))
        return rects

    def get_item_bench_rects(self):
        """Restituisce le coordinate per gli 8 slot del banco oggetti con dimensioni e margini perfetti"""
        sw = self.game.screen.get_width()
        sh = self.game.screen.get_height()
        rects = []
        slot_size = 42
        spacing = 6
        x_start = 25
        y_start = sh - 146
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
        sw = surface.get_width()
        sh = surface.get_height()
        
        # Aggiorna coordinate pulsanti di azione in basso
        btn_y = sh - 62
        self.buy_xp_button_rect = pygame.Rect(sw // 2 - 320, btn_y, 200, 48)
        self.refresh_button_rect = pygame.Rect(sw // 2 - 100, btn_y, 190, 48)
        self.confirm_button_rect = pygame.Rect(sw // 2 + 110, btn_y, 210, 48)
        self.sell_zone_rect = pygame.Rect(sw // 2 - 280, sh - 64, 560, 50)
        
        # --- 1. SFONDO ARENA AI ---
        bg_surf = get_background_image("board_bg", sw, sh)
        surface.blit(bg_surf, (0, 0))
        
        # Overlay scuro per contrasto
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 145))
        surface.blit(overlay, (0, 0))
        
        # --- 2. TOP BAR (STATO GIOCATORE CON PILLOLE CURVE) ---
        top_w = min(1040, sw - 440)
        top_bar_rect = pygame.Rect((sw - top_w) // 2, 12, top_w, 48)
        draw_glass_panel(surface, top_bar_rect, border_radius=24, bg_color=(12, 16, 26, 230), border_color=(190, 160, 65, 180), border_width=1)
        
        # Pillola HP
        hp_rect = pygame.Rect(top_bar_rect.x + 15, 16, 115, 38)
        draw_glass_panel(surface, hp_rect, border_radius=19, bg_color=(25, 55, 35, 230), border_color=(60, 200, 100, 200), border_width=1)
        draw_text(f"HP: {self.game.player_hp}", HEADER_FONT, (120, 255, 160), surface, hp_rect.centerx, hp_rect.centery)
        
        # Pillola Oro
        gold_rect = pygame.Rect(top_bar_rect.x + 140, 16, 120, 38)
        draw_glass_panel(surface, gold_rect, border_radius=19, bg_color=(55, 45, 15, 230), border_color=(255, 215, 60, 220), border_width=1)
        draw_text(f"ORO: {self.game.player_gold}g", HEADER_FONT, GOLD, surface, gold_rect.centerx, gold_rect.centery)
        
        # Pillola Round
        round_rect = pygame.Rect(top_bar_rect.right - 140, 16, 125, 38)
        draw_glass_panel(surface, round_rect, border_radius=19, bg_color=(35, 40, 55, 230), border_color=(140, 160, 200, 200), border_width=1)
        draw_text(f"ROUND: {self.game.round_number}", HEADER_FONT, (220, 235, 255), surface, round_rect.centerx, round_rect.centery)
        
        # Pillola Livello & Barra XP
        lvl_w = max(200, top_bar_rect.width - 440)
        lvl_rect = pygame.Rect(top_bar_rect.x + 270, 16, lvl_w, 38)
        draw_glass_panel(surface, lvl_rect, border_radius=19, bg_color=(20, 35, 55, 230), border_color=(60, 140, 240, 200), border_width=1)
        
        curr_xp = self.game.player_xp
        max_xp = self.game.xp_to_level.get(self.game.player_level, 999)
        draw_text(f"LVL {self.game.player_level}", HEADER_FONT, (140, 210, 255), surface, lvl_rect.x + 45, lvl_rect.centery)
        
        # Barra di avanzamento XP
        bar_x = lvl_rect.x + 95
        bar_y = lvl_rect.centery - 7
        bar_w = lvl_w - 110
        bar_h = 14
        pygame.draw.rect(surface, (15, 20, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=7)
        if max_xp > 0:
            pct = min(1.0, curr_xp / max_xp)
            if pct > 0:
                pygame.draw.rect(surface, (40, 160, 255), (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=7)
        pygame.draw.rect(surface, (100, 180, 255), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=7)
        draw_text(f"{curr_xp}/{max_xp} XP", SMALL_FONT, WHITE, surface, bar_x + bar_w // 2, lvl_rect.centery)

        # --- 3. RACK NEGOZIO (5 CARTE CAMPIONI) ---
        card_w, card_h = 185, 215
        self.card_size = (card_w, card_h)
        self.spacing_x = card_w + 14
        shop_total_w = 5 * self.spacing_x - 14
        rack_start_x = (sw - shop_total_w) // 2
        rack_y = 66
        
        shop_rack_rect = pygame.Rect(rack_start_x - 10, rack_y - 6, shop_total_w + 20, card_h + 12)
        draw_glass_panel(surface, shop_rack_rect, border_radius=18, bg_color=(12, 16, 25, 210), border_color=(70, 85, 110, 140), border_width=1)
        
        self.buy_buttons.clear() 
        for i, champ in enumerate(self.shop_champs):
            x = rack_start_x + i * self.spacing_x
            y = rack_y
            card_rect = pygame.Rect(x, y, *self.card_size)
            
            if champ: 
                # Sfondo Card
                pygame.draw.rect(surface, (18, 22, 32), card_rect, border_radius=12)
                
                # Illustrazione del Campione
                img_h = 110
                card_img = champ.get_card_surface(card_w, img_h)
                surface.blit(card_img, (x, y))
                
                # Bordo Tier
                tier_color = getattr(champ, 'tier_color', WHITE)
                pygame.draw.rect(surface, tier_color, (x, y, card_w, img_h), width=2, border_radius=12)
                
                # Badge Costo
                cost_badge = pygame.Rect(x + card_w - 40, y + 6, 34, 20)
                pygame.draw.rect(surface, (12, 15, 22, 230), cost_badge, border_radius=6)
                pygame.draw.rect(surface, GOLD, cost_badge, width=1, border_radius=6)
                draw_text(f"{champ.cost}g", SMALL_FONT, GOLD, surface, cost_badge.centerx, cost_badge.centery)
                
                # Tratti Campione (ASCII safe con '-')
                traits_str = " - ".join(getattr(champ, "traits", []))
                draw_text(traits_str, SMALL_FONT, (215, 215, 165), surface, x + card_w // 2, y + img_h + 12)
                
                # Nome Campione
                draw_text(champ.name, TEXT_FONT, WHITE, surface, x + card_w // 2, y + img_h + 30)
                
                # Bordo Totale Card
                pygame.draw.rect(surface, tier_color, card_rect, width=1, border_radius=12)
                
                # Bottone Compra
                buy_button = pygame.Rect(x + 10, y + card_h - 38, card_w - 20, 30)
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
                draw_text(f"Compra ({champ.cost}g)", BUTTON_FONT, WHITE if can_buy else (150, 150, 160), surface, buy_button.centerx, buy_button.centery)
            else:
                draw_glass_panel(surface, card_rect, border_radius=12, bg_color=(18, 22, 32, 160), border_color=(40, 48, 60, 140), border_width=1)
                self.buy_buttons.append(pygame.Rect(0,0,0,0)) 

        # --- 4. PANNELLO SINERGIE & AUGMENTS & DAMAGE METER (LATO SINISTRO CON SPAZIATURA EXTRA) ---
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
        
        draw_hud_augments(surface, mouse_pos, player_augments, start_x=20, start_y=14)
        draw_traits_sidebar(surface, active_traits, start_x=20, start_y=54)
        
        # Calcola altezza dinamica delle Sinergie per posizionare il Damage Meter senza alcuna sovrapposizione
        shown_count = min(6, len(active_traits))
        traits_height = (28 + shown_count * 43) if shown_count > 0 else 0
        dm_y = max(370, 54 + traits_height + 22)
        
        # Damage Meter sotto alle Sinergie a sinistra con margine generoso
        if hasattr(self.game, 'damage_meter') and getattr(self.game, 'last_battle_player_team', None):
            self.game.damage_meter.draw(
                surface, mouse_pos, self.game.last_battle_player_team, 
                elapsed_seconds=getattr(self.game, 'last_battle_duration', 5.0), 
                start_x=20, start_y=dm_y
            )
        
        # --- CLASSIFICA LOBBY (LATO DESTRO, ABBASSATA A Y=52 PER LASCIARE SPAZIO IN ALTO) ---
        if hasattr(self.game, 'lobby_manager'):
            self.game.lobby_manager.draw_leaderboard_sidebar(surface, mouse_pos, start_x=sw - 215, start_y=52)

        # --- 5. SCACCHIERA (7x2 CELLE TRASLUCIDE) ---
        active_count = sum(1 for c in self.game.board if c is not None)
        board_rects = self.get_board_rects()
        b_top = board_rects[0].top
        title_tag = pygame.Rect(sw // 2 - 130, b_top - 28, 260, 26)
        draw_glass_panel(surface, title_tag, border_radius=13, bg_color=(15, 20, 30, 220), border_color=(190, 160, 60, 170), border_width=1)
        draw_text(f"Scacchiera ({active_count}/{self.game.player_level})", HEADER_FONT, GOLD, surface, title_tag.centerx, title_tag.centery)
        
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
                shadow_surf = pygame.Surface((56, 16), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (5, 8, 14, 150), (0, 0, 56, 16))
                surface.blit(shadow_surf, (rect.centerx - 28, rect.centery + 12))
                
                sprite = champ.get_sprite_surface(width=72, height=72)
                surface.blit(sprite, (rect.centerx - 36, rect.centery - 36))
                
                stars = getattr(champ, "level", 1)
                if stars >= 2:
                    for s in range(min(stars, 3)):
                        cx = rect.centerx - (stars - 1) * 8 + s * 16
                        cy = rect.top + 8
                        draw_star(surface, cx, cy, radius=5, color=GOLD)
                
                name_color = GOLD if stars > 1 else WHITE
                draw_text(champ.name, TEXT_FONT, (0,0,0), surface, rect.centerx + 1, rect.bottom - 9)
                draw_text(champ.name, TEXT_FONT, name_color, surface, rect.centerx, rect.bottom - 10)
                
                self.draw_champ_items(surface, champ, rect.centerx, rect.centery + 14)

        # --- 6. PANCHINA (9 CELLE) ---
        bench_rects = self.get_bench_rects()
        bench_top = bench_rects[0].top
        bench_tag = pygame.Rect(sw // 2 - 100, bench_top - 28, 200, 26)
        draw_glass_panel(surface, bench_tag, border_radius=13, bg_color=(15, 20, 30, 220), border_color=(190, 160, 60, 170), border_width=1)
        draw_text("Panchina", HEADER_FONT, GOLD, surface, bench_tag.centerx, bench_tag.centery)
        
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
                shadow_surf = pygame.Surface((56, 16), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (5, 8, 14, 150), (0, 0, 56, 16))
                surface.blit(shadow_surf, (rect.centerx - 28, rect.centery + 12))
                
                sprite = champ.get_sprite_surface(width=72, height=72)
                surface.blit(sprite, (rect.centerx - 36, rect.centery - 36))
                
                stars = getattr(champ, "level", 1)
                if stars >= 2:
                    for s in range(min(stars, 3)):
                        cx = rect.centerx - (stars - 1) * 8 + s * 16
                        cy = rect.top + 8
                        draw_star(surface, cx, cy, radius=5, color=GOLD)
                
                name_color = GOLD if stars > 1 else WHITE
                draw_text(champ.name, TEXT_FONT, (0,0,0), surface, rect.centerx + 1, rect.bottom - 9)
                draw_text(champ.name, TEXT_FONT, name_color, surface, rect.centerx, rect.bottom - 10)
                
                self.draw_champ_items(surface, champ, rect.centerx, rect.centery + 14)

        # --- 7. UI BASSA (BOTTONI O CESTINO DI VENDITA DURANTE IL DRAG) ---
        if self.is_dragging and self.dragged_champ:
            level = getattr(self.dragged_champ, 'level', 1)
            cost = getattr(self.dragged_champ, 'cost', 1)
            total_invested = cost * (3 ** (level - 1))
            sell_price = total_invested if level == 1 else max(1, total_invested - 1)
            
            is_sell_hover = self.sell_zone_rect.collidepoint(mouse_pos)
            bg_sell = (130, 25, 35, 245) if is_sell_hover else (70, 20, 28, 230)
            border_sell = (255, 90, 100) if is_sell_hover else (220, 70, 80)
            
            draw_glass_panel(surface, self.sell_zone_rect, border_radius=25, bg_color=bg_sell, border_color=border_sell, border_width=2 if is_sell_hover else 1)
            
            sell_txt = f"[VENDI] RILASCIA QUI PER VENDERE (+{sell_price} ORO)"
            draw_text(sell_txt, BUTTON_FONT, (255, 235, 140) if is_sell_hover else (255, 200, 205), surface, self.sell_zone_rect.centerx, self.sell_zone_rect.centery)
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

        # --- 8. BANCO INVENTARIO OGGETTI (IN BASSO A SINISTRA) ---
        item_box_rect = pygame.Rect(16, sh - 180, 216, 126)
        draw_glass_panel(surface, item_box_rect, border_radius=14, bg_color=(14, 18, 28, 230), border_color=(190, 160, 60, 170), border_width=1)
        draw_text("BANCO OGGETTI", HEADER_FONT, GOLD, surface, item_box_rect.centerx, item_box_rect.top + 16)
        
        item_rects = self.get_item_bench_rects()
        hovered_item_desc = None
        for i, rect in enumerate(item_rects):
            is_slot_hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (20, 26, 38), rect, border_radius=10)
            pygame.draw.rect(surface, (80, 100, 130) if is_slot_hover else (45, 55, 75), rect, width=1, border_radius=10)
            
            if i < len(self.game.player_items):
                item_key = self.game.player_items[i]
                data = get_item_data(item_key)
                draw_item_icon(surface, item_key, rect, is_hover=is_slot_hover)
                if is_slot_hover and not self.is_dragging_item:
                    hovered_item_desc = f"{data.get('name','')}: {data.get('desc','')}"

        if hovered_item_desc:
            tip_surf = TEXT_FONT.render(hovered_item_desc, True, (245, 245, 255))
            tip_box = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] - 32, tip_surf.get_width() + 18, 30)
            pygame.draw.rect(surface, (12, 16, 25, 240), tip_box, border_radius=8)
            pygame.draw.rect(surface, GOLD, tip_box, width=1, border_radius=8)
            surface.blit(tip_surf, (tip_box.x + 9, tip_box.y + 6))

        # --- DRAG & DROP OGGETTI FEEDBACK ---
        if self.is_dragging_item and self.dragged_item_key:
            drag_icon = get_item_icon_surface(self.dragged_item_key, size=48, is_hover=True)
            surface.blit(drag_icon, (mouse_pos[0] - 24, mouse_pos[1] - 24))

        # --- DRAG & DROP CAMPIONI FEEDBACK ---
        if self.is_dragging and self.dragged_champ:
            drag_token = self.dragged_champ.get_token_surface(size=72)
            surface.blit(drag_token, (mouse_pos[0] - 36, mouse_pos[1] - 36))
            tier_color = getattr(self.dragged_champ, 'tier_color', WHITE)
            pygame.draw.circle(surface, tier_color, mouse_pos, 38, width=3)
            pygame.draw.circle(surface, (255, 255, 255), mouse_pos, 40, width=1)

        # --- 9. MODAL ISPETTORE CAMPIONE SU CLICK DX ---
        if self.inspected_champion:
            self.draw_champion_inspector(surface, self.inspected_champion)

    def draw_champion_inspector(self, surface, champ):
        """
        Disegna la Scheda Dettaglio / Ispettore Campione su Click DX (1920x1080).
        Utilizza rendering vettoriale per stelle e croce X senza problemi di font.
        """
        if not champ:
            return

        mouse_pos = pygame.mouse.get_pos()
        sw = surface.get_width()
        sh = surface.get_height()

        # 1. Dark Backdrop Overlay
        backdrop = pygame.Surface((sw, sh), pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, 175))
        surface.blit(backdrop, (0, 0))

        # 2. Main Modal Rect
        modal_w = 640
        modal_h = 760
        modal_x = (sw - modal_w) // 2
        modal_y = (sh - modal_h) // 2
        self.inspector_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        # Glassmorphism Card Background
        tier_col = getattr(champ, 'tier_color', (180, 160, 60))
        draw_glass_panel(surface, self.inspector_rect, border_radius=24, bg_color=(15, 20, 32, 250), border_color=(*tier_col[:3], 230), border_width=2)

        # Pulsante Chiusura con Croce Vettoriale (draw_cross)
        self.inspector_close_rect = pygame.Rect(modal_x + modal_w - 46, modal_y + 16, 32, 32)
        close_hover = self.inspector_close_rect.collidepoint(mouse_pos)
        pygame.draw.circle(surface, (200, 45, 55) if close_hover else (35, 45, 65), self.inspector_close_rect.center, 16)
        pygame.draw.circle(surface, (255, 100, 110) if close_hover else (80, 95, 120), self.inspector_close_rect.center, 16, width=1)
        draw_cross(surface, self.inspector_close_rect.centerx, self.inspector_close_rect.centery, radius=7, color=WHITE, width=2)

        # 3. HEADER & RITRATTO
        portrait_rect = pygame.Rect(modal_x + 28, modal_y + 24, 110, 110)
        draw_glass_panel(surface, portrait_rect, border_radius=16, bg_color=(10, 14, 22, 240), border_color=tier_col, border_width=2)
        
        p_surf = create_card_image(champ.name, width=104, height=104)
        surface.blit(p_surf, (portrait_rect.x + 3, portrait_rect.y + 3))

        # Nome del Campione
        champ_name_x = modal_x + 155
        draw_text(champ.name, SUBTITLE_FONT, WHITE, surface, champ_name_x, modal_y + 30, center=False)

        # Rango Stelle Vettoriali
        stars = getattr(champ, "level", 1)
        draw_text("Rango: ", HEADER_FONT, GOLD, surface, champ_name_x, modal_y + 68, center=False)
        for s in range(min(stars, 3)):
            star_x = champ_name_x + 75 + s * 22
            star_y = modal_y + 78
            draw_star(surface, star_x, star_y, radius=8, color=GOLD)

        # Badge Costo Tier
        cost = getattr(champ, "cost", 1)
        cost_badge = pygame.Rect(champ_name_x + 160, modal_y + 66, 125, 26)
        pygame.draw.rect(surface, (*tier_col[:3], 60), cost_badge, border_radius=13)
        pygame.draw.rect(surface, tier_col, cost_badge, width=1, border_radius=13)
        draw_text(f"TIER {cost} | {cost} ORO", SMALL_FONT, tier_col, surface, cost_badge.centerx, cost_badge.centery)

        # 4. SEZIONE TRATTI & SINERGIE
        traits_y = modal_y + 150
        draw_text("TRATTI & SINERGIE", HEADER_FONT, (240, 205, 70), surface, modal_x + 28, traits_y, center=False)

        curr_ty = traits_y + 28
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
            tbadge_rect = pygame.Rect(modal_x + 28, curr_ty, modal_w - 56, 52)
            draw_glass_panel(surface, tbadge_rect, border_radius=12, bg_color=(20, 26, 40, 230), border_color=tcolor, border_width=1)
            
            # Icona circolare
            pygame.draw.circle(surface, tcolor, (modal_x + 52, curr_ty + 26), 14)
            pygame.draw.circle(surface, (255, 255, 255), (modal_x + 52, curr_ty + 26), 6)
            
            # Titolo Tratto
            ttxt = f"{tname} ({ttype})"
            draw_text(ttxt, HEADER_FONT, tcolor, surface, modal_x + 78, curr_ty + 8, center=False)
            
            # Breakpoints & Descrizione
            bp_str = "/".join(str(b) for b in tdata.get("breakpoints", []))
            desc_txt = f"Soglie ({bp_str}): {tdata.get('description', '')}"
            draw_text(desc_txt[:70], SMALL_FONT, (210, 220, 235), surface, modal_x + 78, curr_ty + 30, center=False)
            
            curr_ty += 60

        # 5. STATISTICHE DI COMBATTIMENTO
        stats_y = curr_ty + 8
        draw_text("STATISTICHE BASE", HEADER_FONT, (240, 205, 70), surface, modal_x + 28, stats_y, center=False)
        
        # Grid box statistiche
        stats_box = pygame.Rect(modal_x + 28, stats_y + 26, modal_w - 56, 120)
        draw_glass_panel(surface, stats_box, border_radius=14, bg_color=(16, 22, 34, 220), border_color=(60, 75, 100), border_width=1)
        
        # 1a colonna
        c1_x = stats_box.x + 18
        draw_text(f"Salute (HP): {champ.hp} / {champ.max_hp}", TEXT_FONT, (120, 255, 160), surface, c1_x, stats_box.y + 12, center=False)
        draw_text(f"Mana: {champ.mana_start} / {champ.mana_max}", TEXT_FONT, (100, 200, 255), surface, c1_x, stats_box.y + 38, center=False)
        draw_text(f"Attacco (AD): {champ.base_attack}", TEXT_FONT, (255, 215, 80), surface, c1_x, stats_box.y + 64, center=False)
        draw_text(f"Difesa (Armor): {getattr(champ, 'base_defense', 0)}", TEXT_FONT, (190, 205, 230), surface, c1_x, stats_box.y + 90, center=False)
        
        # 2a colonna
        c2_x = stats_box.centerx + 10
        draw_text(f"Vel. Attacco: {champ.attack_speed:.2f}/s", TEXT_FONT, (240, 180, 70), surface, c2_x, stats_box.y + 12, center=False)
        range_str = "Mischia (80px)" if champ.attack_range < 100 else ("Cecchino (500px)" if champ.attack_range > 350 else "Distanza (300px)")
        draw_text(f"Raggio: {range_str}", TEXT_FONT, (220, 225, 240), surface, c2_x, stats_box.y + 38, center=False)
        crit_pct = int(champ.crit_chance * 100)
        draw_text(f"Critico: {crit_pct}% ({champ.crit_multiplier:.1f}x)", TEXT_FONT, (255, 120, 140), surface, c2_x, stats_box.y + 64, center=False)
        sp_pct = int(getattr(champ, 'spell_power_mult', 1.0) * 100)
        draw_text(f"Potere Magico (AP): {sp_pct}%", TEXT_FONT, (210, 130, 255), surface, c2_x, stats_box.y + 90, center=False)

        # 6. ABILITÀ SPECIALE
        ability_y = stats_box.bottom + 12
        ab_info = champ.get_ability_info() if hasattr(champ, 'get_ability_info') else {"name": "Abilità", "type": "Speciale", "cost": "100 Mana", "desc": "Mossa speciale"}
        
        ab_box = pygame.Rect(modal_x + 28, ability_y, modal_w - 56, 88)
        draw_glass_panel(surface, ab_box, border_radius=14, bg_color=(22, 28, 44, 230), border_color=(120, 90, 210), border_width=1)
        
        ab_title = f"[SPELL] {ab_info['name']}  ({ab_info.get('type', 'Speciale')})  -  {ab_info.get('cost', '')}"
        draw_text(ab_title, HEADER_FONT, (255, 235, 120), surface, ab_box.x + 14, ab_box.y + 10, center=False)
        
        desc = ab_info.get("desc", "")
        line1 = desc[:72]
        line2 = desc[72:144] if len(desc) > 72 else ""
        draw_text(line1, SMALL_FONT, (215, 225, 240), surface, ab_box.x + 14, ab_box.y + 36, center=False)
        if line2:
            draw_text(line2, SMALL_FONT, (215, 225, 240), surface, ab_box.x + 14, ab_box.y + 56, center=False)

        # 7. OGGETTI EQUIPAGGIATI (0/3)
        item_y = ab_box.bottom + 12
        draw_text("OGGETTI EQUIPAGGIATI (Max 3):", TEXT_FONT, (180, 195, 215), surface, modal_x + 28, item_y + 12, center=False)
        
        champ_items = getattr(champ, "items", [])
        for idx in range(3):
            slot_rect = pygame.Rect(modal_x + 280 + idx * 54, item_y - 2, 44, 44)
            if idx < len(champ_items):
                draw_item_icon(surface, champ_items[idx], slot_rect)
            else:
                draw_glass_panel(surface, slot_rect, border_radius=10, bg_color=(12, 16, 24, 180), border_color=(45, 55, 75), border_width=1)
