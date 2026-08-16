# game.py
import pygame
import sys
import random

# Importa le classi manager
from champions import get_available_champions, Champion
from shop import ShopManager
from battle import BattleManager
from carousel import CarouselManager

# Importa TUTTE le costanti e le utility da config.py
from config import (
    WIDTH, HEIGHT, WHITE, BLUE, LIGHT_BLUE, 
    GREEN, RED, GOLD, TITLE_FONT, BUTTON_FONT, HEADER_FONT, TEXT_FONT, SMALL_FONT, MICRO_FONT, draw_text
)
from audio_manager import AudioManager
from items import get_random_component_key
from asset_loader import get_background_image, draw_glass_panel
from lobby import LobbyManager
from damage_meter import DamageMeter

# --- Inizializzazione Audio ---
audio_manager = AudioManager.get_instance()

# --- Inizializzazione Pygame ---
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini TFT - 8-Player Lobby Battle Royale")


# --- CLASSE PRINCIPALE DEL GIOCO ---

class Game:
    """
    Classe principale che gestisce il ciclo di gioco, gli stati,
    l'economia e orchestra Shop, Battaglia e Lobby 8 Giocatori.
    """
    def __init__(self):
        self.screen = SCREEN
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "MAIN_MENU" # "MAIN_MENU", "SHOP", "BATTLE", "RESULT"
        
        # Inizializza il database dei campioni
        self.champions_database = get_available_champions()
        
        # --- Dati del Giocatore ---
        self.player_hp = 100
        self.player_gold = 20
        self.player_level = 1
        self.player_xp = 0
        self.xp_to_level = {1:2, 2:2, 3:6, 4:10, 5:20, 6:36, 7:56, 8:80, 9:999}
        self.win_streak = 0
        self.loss_streak = 0
        self.winstreak = 0
        self.losestreak = 0
        self.player_placement = None
        self.is_game_finished = False
        
        # --- Sistema Augments Hextech ---
        self.player_augments = []
        self.offered_augments = []
        self.can_reroll_augments = True
        self.augment_rounds = [2, 5, 8]
        self.augment_selection_triggered_rounds = set()
        self.augment_card_rects = []
        self.augment_btn_rects = []
        self.augment_reroll_rect = None
        
        # --- Sistema Carosello Condiviso (Shared Draft) ---
        self.carousel_manager = None
        self.carousel_rounds = [1, 4, 7]
        self.carousel_selection_triggered_rounds = set()
        
        self.board_slots = 14 # 7 colonne x 2 righe
        self.bench_slots = 9 
        self.board = [None] * self.board_slots 
        self.bench = [None] * self.bench_slots
        self.player_items = []
        self.round_number = 1
        
        # Manager di gioco
        self.audio = audio_manager
        self.lobby_manager = LobbyManager(self)
        self.shop_manager = ShopManager(self, self.champions_database)
        self.battle_manager = None
        self.damage_meter = DamageMeter()
        self.last_battle_player_team = []
        self.last_battle_duration = 5.0
        
        # Variabile per tenere traccia del vincitore dell'ultima battaglia
        self.last_battle_winner = None
        self.last_round_stats = {}
        self.play_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 10, 240, 64)
        self.continue_button_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 135, 280, 52)
        self.audio.play_music("shop_theme")

    def run(self):
        """ Il loop di gioco principale, non bloccante. """
        
        # if not pygame.mixer.music.get_busy():
        #     try:
        #         pygame.mixer.music.play(-1)
        #     except Exception as e:
        #         print(f"Errore play musica: {e}")
            
        while self.running:
            # 1. Gestisci Eventi
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.audio.toggle_mute()
                    
                if self.game_state == "MAIN_MENU":
                    self.handle_menu_events(event)
                elif self.game_state == "CAROUSEL" and self.carousel_manager:
                    self.carousel_manager.handle_event(event)
                elif self.game_state == "AUGMENT_SELECTION":
                    self.handle_augment_events(event)
                elif self.game_state == "SHOP":
                    self.shop_manager.handle_event(event)
                elif self.game_state == "BATTLE" and self.battle_manager:
                    self.battle_manager.handle_event(event)
                elif self.game_state == "RESULT":
                    self.handle_result_events(event)

            # 2. Aggiorna Logica
            if self.game_state == "CAROUSEL" and self.carousel_manager:
                self.carousel_manager.update()
            elif self.game_state == "BATTLE" and self.battle_manager:
                self.battle_manager.update()
                if self.battle_manager.is_over:
                    self.end_battle(self.battle_manager.winner)

            # 3. Disegna (Render)
            self.screen.fill((20, 20, 20))
            
            if self.game_state == "MAIN_MENU":
                self.audio.play_music("shop_theme")
                self.draw_main_menu()
            elif self.game_state == "CAROUSEL" and self.carousel_manager:
                self.audio.play_music("shop_theme")
                self.carousel_manager.draw(self.screen)
            elif self.game_state == "AUGMENT_SELECTION":
                self.audio.play_music("shop_theme")
                self.draw_augment_selection()
            elif self.game_state == "SHOP":
                self.audio.play_music("shop_theme")
                self.shop_manager.draw(self.screen)
            elif self.game_state == "BATTLE" and self.battle_manager:
                self.audio.play_music("battle_theme")
                self.battle_manager.draw(self.screen)
            elif self.game_state == "RESULT":
                self.draw_result_screen()
                
            # Indicatore Audio in alto
            audio_status = "MUTATO (M)" if self.audio.is_muted else "ATTIVO (M)"
            audio_color = (255, 100, 100) if self.audio.is_muted else (120, 220, 120)
            draw_text(f"AUDIO: {audio_status}", SMALL_FONT, audio_color, self.screen, WIDTH - 100, 18)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    # --- Gestione Stato: MAIN_MENU ---
    def draw_main_menu(self):
        # 1. Background Cinematico AI
        bg_surf = get_background_image("menu_bg", WIDTH, HEIGHT)
        self.screen.blit(bg_surf, (0, 0))
        
        # Vignette scura per contrasto
        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        vignette.fill((10, 12, 20, 130))
        self.screen.blit(vignette, (0, 0))
        
        # 2. Pannello Centrale Glassmorphism
        center_panel = pygame.Rect(WIDTH // 2 - 260, HEIGHT // 2 - 200, 520, 390)
        draw_glass_panel(self.screen, center_panel, border_radius=24, bg_color=(12, 16, 26, 215), border_color=(210, 175, 75, 200), border_width=2)
        
        # 3. Titolo con Bagliore Aureo
        draw_text("MINI TFT", TITLE_FONT, (0, 0, 0), self.screen, WIDTH // 2 + 3, HEIGHT // 2 - 130 + 3)
        draw_text("MINI TFT", TITLE_FONT, (255, 200, 40), self.screen, WIDTH // 2 + 1, HEIGHT // 2 - 130 + 1)
        draw_text("MINI TFT", TITLE_FONT, (255, 240, 180), self.screen, WIDTH // 2, HEIGHT // 2 - 130)
        
        sub_font = pygame.font.SysFont("Arial", 16, bold=True)
        draw_text("TACTICAL AUTO-BATTLER - PROTOTYPE", sub_font, (170, 200, 240), self.screen, WIDTH // 2, HEIGHT // 2 - 65)
        draw_text("by andreazappy-dev", TEXT_FONT, (140, 150, 170), self.screen, WIDTH // 2, HEIGHT // 2 - 35)

        # 4. Bottone GIOCA Curvo & Luminoso
        self.play_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 10, 240, 64)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.play_button_rect.collidepoint(mouse_pos)
        
        btn_color = (45, 150, 255) if is_hover else (30, 110, 210)
        border_glow = (255, 230, 100) if is_hover else (120, 190, 255)
        
        # Glow all'hover
        if is_hover:
            glow_rect = self.play_button_rect.inflate(8, 8)
            pygame.draw.rect(self.screen, (60, 160, 255, 100), glow_rect, border_radius=34)
            
        pygame.draw.rect(self.screen, btn_color, self.play_button_rect, border_radius=32)
        pygame.draw.rect(self.screen, border_glow, self.play_button_rect, width=2, border_radius=32)
        draw_text("GIOCA", HEADER_FONT, WHITE, self.screen, WIDTH // 2, HEIGHT // 2 + 42)
        
        # 5. Pillola Comandi Rapidi in basso
        tip_rect = pygame.Rect(WIDTH // 2 - 350, HEIGHT - 65, 700, 36)
        draw_glass_panel(self.screen, tip_rect, border_radius=18, bg_color=(15, 18, 25, 200), border_color=(80, 100, 130, 150), border_width=1)
        tip_font = pygame.font.SysFont("Arial", 12, bold=True)
        draw_text("[M] Muto Audio   |   [Click SX] Schiera / Compra   |   [Click DX] Scheda Info", tip_font, (210, 220, 240), self.screen, WIDTH // 2, HEIGHT - 47)

    def handle_menu_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Assicurati che play_button_rect esista
            if hasattr(self, 'play_button_rect') and self.play_button_rect.collidepoint(event.pos):
                # Resettiamo i dati del giocatore per una nuova partita
                self.player_gold = 20
                self.player_hp = 100
                self.player_level = 1
                self.player_xp = 0
                self.winstreak = 0
                self.losestreak = 0
                self.board = [None] * self.board_slots
                self.bench = [None] * self.bench_slots
                self.player_items = []
                self.player_augments = []
                self.can_reroll_augments = True
                self.augment_selection_triggered_rounds = set()
                self.carousel_selection_triggered_rounds = set()
                self.last_battle_player_team = []
                self.shop_manager.reset() # Ricarica lo shop
                self.round_number = 1   
                self.trigger_carousel()

    def buy_xp(self):
        if self.player_gold >= 4 and self.player_level < 9:
            self.player_gold -= 4
            self.player_xp += 4
            self.audio.play_sfx("xp_buy")
            self.check_level_up()
            print(f"XP comprata! Livello: {self.player_level} ({self.player_xp}/{self.xp_to_level[self.player_level]})")
            
    def check_level_up(self):
        leveled = False
        while self.player_level < 9 and self.player_xp >= self.xp_to_level[self.player_level]:
            self.player_xp -= self.xp_to_level[self.player_level]
            self.player_level += 1
            leveled = True
            print(f"Level UP! Ora sei livello {self.player_level}!")
        if leveled:
            self.audio.play_sfx("level_up")

    # --- Gestione Stato: BATTLE ---
    def start_battle(self):
        print(f"--- INIZIO ROUND {self.round_number} ---")
        
        active_champs = []
        for i, c in enumerate(self.board):
            if c is not None:
                c.board_index = i
                active_champs.append(c)
                
        print("Avvio battaglia con:", [c.name for c in active_champs])
        
        # Matchmaking e progressione con Lobby 8 Giocatori
        opponent_bot = self.lobby_manager.start_round(self.round_number)
        
        if not opponent_bot:
            # Tutti i bot sono stati eliminati: Vittoria Assoluta!
            self.is_game_finished = True
            self.player_placement = 1
            self.last_battle_winner = "player"
            self.game_state = "RESULT"
            return
            
        print(f"Matchmaking: Affronti {opponent_bot.name} ({opponent_bot.hp} HP)!")
        enemy_team_to_battle = [c.copy() for c in opponent_bot.board]
        
        # Passa il riferimento a game, database e nome avversario al BattleManager
        self.battle_manager = BattleManager(self, active_champs, enemy_team_to_battle, self.champions_database, opponent_name=opponent_bot.name) 
        self.game_state = "BATTLE"

    def end_battle(self, winner):
        self.last_battle_winner = winner
        self.game_state = "RESULT"
        
        # Salva report per Damage Meter
        if self.battle_manager:
            self.last_battle_player_team = [c.copy() for c in getattr(self.battle_manager, 'player_team', [])]
            self.last_battle_duration = max(1.0, (pygame.time.get_ticks() - getattr(self.battle_manager, 'battle_start_ticks', pygame.time.get_ticks())) / 1000.0)
            
        # Calcolo unità sopravvissute
        surviving_player = sum(1 for c in getattr(self.battle_manager, 'player_team', []) if c.is_alive()) if self.battle_manager else 1
        surviving_enemy = sum(1 for c in getattr(self.battle_manager, 'enemy_team', []) if c.is_alive()) if self.battle_manager else 0
        
        # Risolvi la partita nella Lobby 8 Giocatori
        self.lobby_manager.resolve_player_match(winner, surviving_player, surviving_enemy, self.round_number)
        
        base_income = 5
        max_interest_cap = 7 if "rich_get_richer" in self.player_augments else 5
        interest = min(max_interest_cap, self.player_gold // 10)
        
        streak_gold = 0
        if self.win_streak >= 2 or self.loss_streak >= 2:
            streak_gold = 1
        if self.win_streak >= 4 or self.loss_streak >= 4:
            streak_gold = 2
        if self.win_streak >= 5 or self.loss_streak >= 5:
            streak_gold = 3
        
        round_gold = base_income + interest + streak_gold
        damage_taken = 0
        
        if winner == "player":
            self.win_streak += 1
            self.loss_streak = 0
            self.winstreak = self.win_streak
            self.losestreak = 0
            self.player_gold += round_gold + 1 # +1 vittoria immediata
            self.audio.play_sfx("victory")
            print(f"Vittoria! Oro: {self.player_gold} (+{round_gold + 1}) [Int:{interest}, Str:{streak_gold}]")
        else:
            self.loss_streak += 1
            self.win_streak = 0
            self.losestreak = self.loss_streak
            self.winstreak = 0
            self.player_gold += round_gold
            damage_taken = 2 + self.round_number + surviving_enemy * 2
            self.player_hp = max(0, self.player_hp - damage_taken)
            self.audio.play_sfx("defeat")
            print(f"Sconfitta! Oro: {self.player_gold} (+{round_gold}), HP: {self.player_hp} (-{damage_taken})")
            
        opp_name = self.lobby_manager.current_opponent.name if self.lobby_manager.current_opponent else "Bot"
        
        # Controllo condizioni di fine partita (Game Over o Vittoria 1° Posto)
        if self.player_hp <= 0:
            self.is_game_finished = True
            self.player_placement = 8 - self.lobby_manager.eliminated_count
            print(f"💀 Sei stato eliminato! Ti sei piazzato al {self.player_placement}° Posto.")
        elif len(self.lobby_manager.get_alive_bots()) == 0:
            self.is_game_finished = True
            self.player_placement = 1
            print(f"🏆 VITTORIA ASSOLUTA! Ti sei piazzato al 1° Posto su 8 Giocatori!")
            
        self.last_round_stats = {
            "winner": winner,
            "gold": round_gold + (1 if winner == "player" else 0),
            "interest": interest,
            "streak": streak_gold,
            "damage": damage_taken,
            "round": self.round_number,
            "opponent": opp_name,
            "is_game_finished": self.is_game_finished,
            "placement": self.player_placement
        }
            
        extra_xp = 2 if "hyper_growth" in self.player_augments else 0
        if extra_xp > 0:
            print("🌱 IPER-CRESCITA: +2 XP gratuiti extra!")
        self.player_xp += 2 + extra_xp
        self.check_level_up()
        
        # Drop Oggetti: nei round 1, 2, 3 e poi ogni 3 round
        if self.round_number <= 3 or self.round_number % 3 == 0:
            if len(self.player_items) < 8:
                dropped = get_random_component_key()
                self.player_items.append(dropped)
                print(f"🎁 DROP OGGETTO! Hai ottenuto: {dropped}")
        
        # Incrementa il round
        self.round_number += 1
        
        # Ricarica gratuita dello shop per il prossimo round
        self.shop_manager.roll_shop(is_free=True)

    # --- Gestione Stato: RESULT ---
    def draw_result_screen(self):
        is_win = self.last_battle_winner == "player"
        bg_name = "victory_bg" if (is_win or (self.is_game_finished and self.player_placement == 1)) else "defeat_bg"
        bg_surf = get_background_image(bg_name, WIDTH, HEIGHT)
        self.screen.blit(bg_surf, (0, 0))
        
        # Vignette scura
        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        vignette.fill((10, 12, 18, 140))
        self.screen.blit(vignette, (0, 0))
        
        # Card Risultati Centrale
        card_rect = pygame.Rect(WIDTH // 2 - 260, HEIGHT // 2 - 230, 520, 460)
        border_col = (230, 190, 70, 220) if is_win else (210, 60, 60, 220)
        draw_glass_panel(self.screen, card_rect, border_radius=24, bg_color=(14, 18, 28, 230), border_color=border_col, border_width=2)
        
        # Titolo Trionfo / Sconfitta / Fine Partita
        if self.is_game_finished:
            if self.player_placement == 1:
                title_text = "1° POSTO - VITTORIA!"
                title_col = (255, 220, 60)
            else:
                title_text = f"{self.player_placement}° POSTO - ELIMINATO"
                title_col = (240, 80, 80)
        else:
            title_text = "VITTORIA!" if is_win else "SCONFITTA..."
            title_col = (255, 220, 60) if is_win else (240, 80, 80)
            
        draw_text(title_text, TITLE_FONT, (0,0,0), self.screen, WIDTH // 2 + 2, HEIGHT // 2 - 165 + 2)
        draw_text(title_text, TITLE_FONT, title_col, self.screen, WIDTH // 2, HEIGHT // 2 - 165)
        
        round_idx = self.last_round_stats.get("round", self.round_number - 1)
        opp_name = self.last_round_stats.get("opponent", "Avversario")
        sub_font = pygame.font.SysFont("Arial", 14, bold=True)
        draw_text(f"ROUND {round_idx} - VS {opp_name.upper()}", sub_font, (180, 200, 230), self.screen, WIDTH // 2, HEIGHT // 2 - 110)
        
        # Statistiche Round
        stats_y = HEIGHT // 2 - 75
        gold_earned = self.last_round_stats.get("gold", 5)
        int_earned = self.last_round_stats.get("interest", 0)
        strk_earned = self.last_round_stats.get("streak", 0)
        
        # Box statistiche interno
        stat_box = pygame.Rect(WIDTH // 2 - 220, stats_y, 440, 180)
        draw_glass_panel(self.screen, stat_box, border_radius=14, bg_color=(20, 26, 40, 180), border_color=(60, 75, 100, 150), border_width=1)
        
        row_font = pygame.font.SysFont("Arial", 14, bold=True)
        draw_text("Oro Guadagnato:", row_font, (220, 220, 230), self.screen, WIDTH // 2 - 95, stats_y + 28)
        draw_text(f"+{gold_earned}g  (Int: +{int_earned}g, Serie: +{strk_earned}g)", row_font, GOLD, self.screen, WIDTH // 2 + 95, stats_y + 28)
        
        hp_lost = self.last_round_stats.get("damage", 0)
        hp_text = f"{self.player_hp} HP  (-{hp_lost})" if hp_lost > 0 else f"{self.player_hp} HP (Nessun Danno)"
        draw_text("Vita Giocatore:", row_font, (220, 220, 230), self.screen, WIDTH // 2 - 95, stats_y + 68)
        draw_text(hp_text, row_font, (80, 220, 120) if hp_lost == 0 else (240, 90, 90), self.screen, WIDTH // 2 + 95, stats_y + 68)
        
        draw_text("Livello Giocatore:", row_font, (220, 220, 230), self.screen, WIDTH // 2 - 95, stats_y + 108)
        draw_text(f"Lvl {self.player_level} ({self.player_xp}/{self.xp_to_level.get(self.player_level, 999)} XP)", row_font, (90, 180, 255), self.screen, WIDTH // 2 + 95, stats_y + 108)
        
        draw_text("Oro in Banca:", row_font, (220, 220, 230), self.screen, WIDTH // 2 - 95, stats_y + 148)
        draw_text(f"{self.player_gold}g", row_font, GOLD, self.screen, WIDTH // 2 + 95, stats_y + 148)

        # Bottone Continua / Torna al Menu
        self.continue_button_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 135, 280, 52)
        mouse_pos = pygame.mouse.get_pos()
        btn_hover = self.continue_button_rect.collidepoint(mouse_pos)
        
        btn_text = "MENU PRINCIPALE" if self.is_game_finished else "CONTINUA AL NEGOZIO"
        btn_col = (45, 160, 255) if btn_hover else (30, 120, 210)
        pygame.draw.rect(self.screen, btn_col, self.continue_button_rect, border_radius=26)
        pygame.draw.rect(self.screen, (150, 220, 255) if btn_hover else (80, 160, 230), self.continue_button_rect, width=2, border_radius=26)
        draw_text(btn_text, BUTTON_FONT, WHITE, self.screen, WIDTH // 2, HEIGHT // 2 + 161)

    def handle_result_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_game_finished:
                # Resetta la partita e torna al menu
                self.__init__()
                self.game_state = "MAIN_MENU"
            else:
                # 1. Controlla se il nuovo round richiede la selezione di un Carosello (es. Round 4, 7)
                if self.round_number in self.carousel_rounds and self.round_number not in self.carousel_selection_triggered_rounds:
                    self.trigger_carousel()
                # 2. Controlla se il nuovo round richiede la selezione di un Augment (es. Round 2, 5, 8)
                elif self.round_number in self.augment_rounds and self.round_number not in self.augment_selection_triggered_rounds:
                    self.trigger_augment_selection()
                else:
                    self.game_state = "SHOP"

    # --- Gestione Stato: CAROUSEL ---
    def trigger_carousel(self):
        from carousel import CarouselManager
        self.carousel_selection_triggered_rounds.add(self.round_number)
        self.carousel_manager = CarouselManager(self, round_number=self.round_number)
        self.game_state = "CAROUSEL"
        print(f"🎠 FASE CAROSELLO CONDIVISO ROUND {self.round_number}: Seleziona il tuo campione!")

    # --- Gestione Stato: AUGMENT_SELECTION ---
    def trigger_augment_selection(self):
        from augments import get_random_augments
        self.offered_augments = get_random_augments(3, exclude_ids=self.player_augments)
        self.augment_selection_triggered_rounds.add(self.round_number)
        self.game_state = "AUGMENT_SELECTION"
        print(f"🔮 FASE AUGMENT ROUND {self.round_number}: Seleziona un potenziamento!")

    def draw_augment_selection(self):
        from augments import draw_augment_selection_screen
        mouse_pos = pygame.mouse.get_pos()
        card_rects, btn_rects, reroll_rect = draw_augment_selection_screen(
            self.screen, mouse_pos, self.offered_augments, self.can_reroll_augments
        )
        self.augment_card_rects = card_rects
        self.augment_btn_rects = btn_rects
        self.augment_reroll_rect = reroll_rect

    def handle_augment_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # 1. Clic su una delle 3 carte / pulsanti SCEGLI
            for i, btn_rect in enumerate(self.augment_btn_rects):
                card_hit = i < len(self.augment_card_rects) and self.augment_card_rects[i].collidepoint(mouse_pos)
                btn_hit = btn_rect.collidepoint(mouse_pos)
                if card_hit or btn_hit:
                    chosen_aug = self.offered_augments[i]
                    self.select_augment(chosen_aug["id"])
                    return
                    
            # 2. Clic su REROLL AUGMENT
            if self.augment_reroll_rect and self.augment_reroll_rect.collidepoint(mouse_pos) and self.can_reroll_augments:
                from augments import get_random_augments
                self.can_reroll_augments = False
                current_ids = [a["id"] for a in self.offered_augments] + self.player_augments
                self.offered_augments = get_random_augments(3, exclude_ids=current_ids)
                if hasattr(self, 'audio'):
                    self.audio.play_sfx("coin_buy")
                print("🎲 Reroll Augment effettuato con successo!")

    def select_augment(self, augment_id):
        from augments import AUGMENTS_DATABASE
        self.player_augments.append(augment_id)
        aug_data = AUGMENTS_DATABASE.get(augment_id, {})
        aug_name = aug_data.get("name", augment_id)
        print(f"⚡ AUGMENT SELEZIONATO: {aug_name} ({aug_data.get('tier', 'Silver')})")
        
        # Effetti immediati
        if augment_id == "rich_get_richer":
            self.player_gold += 10
            print("💰 I Ricchi si Arricchiscono: Ricevuti +10 Oro immediati!")
        elif augment_id == "item_buffet":
            from items import get_random_component_key
            if len(self.player_items) < 8:
                self.player_items.append(get_random_component_key())
            if len(self.player_items) < 8:
                self.player_items.append(get_random_component_key())
            if len(self.player_items) < 8:
                completed_pool = ["Giant Slayer", "Deathblade", "Infinity Edge", "Warmog's Armor", "Bloodthirster", "Rabadon's Deathcap"]
                self.player_items.append(random.choice(completed_pool))
            print("🎁 Banchetto degli Oggetti: Ricevuti componenti e oggetto combinato!")
            
        if hasattr(self, 'audio'):
            self.audio.play_sfx("level_up")
            
        self.game_state = "SHOP"


#--- AVVIO DEL GIOCO ---
if __name__ == "__main__":
    game = Game()
    game.run()