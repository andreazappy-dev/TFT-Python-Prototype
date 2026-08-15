# lobby.py
import random
import pygame
from config import draw_text, WIDTH, HEIGHT, GOLD, WHITE, BLACK, RED, GREEN, TEXT_FONT, SMALL_FONT, MICRO_FONT, HEADER_FONT
from traits import calculate_team_traits
from items import get_random_component_key
from asset_loader import draw_glass_panel

BOT_NAMES_DATA = [
    {"name": "PenguMaster", "theme": "Demacia/Guardiano", "color": (230, 200, 80)},
    {"name": "HextechKing", "theme": "Piltover/Zaun", "color": (80, 200, 230)},
    {"name": "ChonccLover", "theme": "Ionia/Mago", "color": (230, 100, 160)},
    {"name": "DariusMain", "theme": "Noxus/Combattente", "color": (220, 50, 50)},
    {"name": "CosmicVoyager", "theme": "Cosmico/Divino", "color": (140, 90, 240)},
    {"name": "SniperQueen", "theme": "Piltover/Cecchino", "color": (240, 180, 40)},
    {"name": "ShadowIsles", "theme": "Zaun/Mago", "color": (60, 220, 130)},
]

class BotPlayer:
    """
    Rappresenta un giocatore avversario controllato dall'AI nella Lobby a 8 Giocatori.
    """
    def __init__(self, name, theme, color):
        self.name = name
        self.theme = theme
        self.color = color
        self.hp = 100
        self.max_hp = 100
        self.gold = 20
        self.level = 1
        self.xp = 0
        self.is_alive = True
        self.placement = None
        self.win_streak = 0
        self.loss_streak = 0
        self.board = [] # Lista di istanze Champion
        self.items_bank = []
        
    def get_team_power(self):
        """Calcola un punteggio di forza dell'armata per le simulazioni bot vs bot"""
        power = self.level * 15
        for c in self.board:
            stars = getattr(c, 'level', 1)
            cost = getattr(c, 'cost', 1)
            power += (cost * 12) * (stars ** 1.6)
            power += len(getattr(c, 'items', [])) * 14
        return power

    def update_progression(self, round_number, champions_db):
        """
        Simula l'economia, i livelli, gli acquisti di campioni, upgrade a 2/3 stelle ed equipaggiamento oggetti.
        """
        if not self.is_alive:
            return

        # 1. Guadagno Oro ed XP
        self.gold += 5 + min(5, self.gold // 10)
        self.xp += 2
        
        # Livellamento del bot in base al round
        target_level = min(9, max(1, 1 + round_number // 2))
        while self.level < target_level and self.gold >= 4:
            self.gold -= 4
            self.level += 1

        # 2. Generazione Componenti Oggetto periodici
        if round_number in [1, 2, 3] or round_number % 3 == 0:
            self.items_bank.append(get_random_component_key())

        # 3. Composizione Squadra coerente con il livello
        desired_slots = min(self.level, 7)
        available_champs = [c for c in champions_db if c.cost <= min(5, 1 + self.level // 2)]
        
        # Seleziona campioni tematici
        if not self.board or len(self.board) < desired_slots:
            while len(self.board) < desired_slots and available_champs:
                chosen = random.choice(available_champs).copy()
                # Probabilità stella 2 in base al round
                if round_number >= 3 and random.random() < 0.45:
                    chosen.level = 2
                    chosen.hp = int(chosen.hp * 1.8)
                    chosen.max_hp = chosen.hp
                    chosen.base_attack = int(chosen.base_attack * 1.8)
                if round_number >= 7 and random.random() < 0.20:
                    chosen.level = 3
                    chosen.hp = int(chosen.hp * 3.2)
                    chosen.max_hp = chosen.hp
                    chosen.base_attack = int(chosen.base_attack * 3.2)
                self.board.append(chosen)

        # 4. Equipaggia oggetti sui campioni del bot
        while self.items_bank and self.board:
            item = self.items_bank.pop(0)
            target_champ = random.choice(self.board)
            if len(getattr(target_champ, 'items', [])) < 3:
                target_champ.equip_item(item)

    def take_damage(self, dmg):
        """Applica danno alla vita del bot e verifica eventuale eliminazione"""
        self.hp = max(0, self.hp - dmg)
        if self.hp == 0:
            self.is_alive = False
        return not self.is_alive


class LobbyManager:
    """
    Gestisce la Lobby di 8 Giocatori (1 Umano + 7 Bot), il matchmaking di ogni round,
    le simulazioni bot-vs-bot in background e il rendering della Classifica Live.
    """
    def __init__(self, game):
        self.game = game
        self.bots = [BotPlayer(b["name"], b["theme"], b["color"]) for b in BOT_NAMES_DATA]
        self.current_opponent = None
        self.eliminated_count = 0
        
    def get_alive_bots(self):
        return [b for b in self.bots if b.is_alive]
        
    def start_round(self, round_number):
        """
        Prepara il matchmaking del round, fa progredire tutti i bot e seleziona l'avversario del giocatore.
        """
        # 1. Fai progredire i bot
        for bot in self.bots:
            bot.update_progression(round_number, self.game.champions_database)
            
        alive_bots = self.get_alive_bots()
        if not alive_bots:
            self.current_opponent = None
            return None
            
        # 2. Scegli un avversario vivo per il giocatore
        self.current_opponent = random.choice(alive_bots)
        
        # 3. Simula le battaglie bot vs bot per i bot rimanenti
        other_alive = [b for b in alive_bots if b != self.current_opponent]
        random.shuffle(other_alive)
        
        for i in range(0, len(other_alive), 2):
            if i + 1 < len(other_alive):
                b1 = other_alive[i]
                b2 = other_alive[i+1]
                self._simulate_bot_match(b1, b2, round_number)
            elif len(other_alive) % 2 != 0:
                # Bot dispari combatte contro un ghost / clone
                b_solo = other_alive[i]
                if random.random() < 0.5:
                    b_solo.win_streak += 1
                    b_solo.loss_streak = 0
                else:
                    dmg = 4 + round_number
                    if b_solo.take_damage(dmg):
                        self._assign_elimination_placement(b_solo)

        return self.current_opponent

    def _simulate_bot_match(self, b1, b2, round_number):
        """Simula una rapida battaglia tra due bot basandosi sul loro team power"""
        p1 = b1.get_team_power() + random.randint(-15, 15)
        p2 = b2.get_team_power() + random.randint(-15, 15)
        base_dmg = 3 + round_number * 2
        
        if p1 >= p2:
            winner, loser = b1, b2
        else:
            winner, loser = b2, b1
            
        winner.win_streak += 1
        winner.loss_streak = 0
        loser.loss_streak += 1
        loser.win_streak = 0
        
        surviving = max(1, random.randint(1, max(1, winner.level // 2)))
        dmg = base_dmg + surviving * 2
        
        if loser.take_damage(dmg):
            self._assign_elimination_placement(loser)

    def _assign_elimination_placement(self, player_obj):
        """Assegna il piazzamento (8°, 7°, ecc.) a chi viene eliminato"""
        self.eliminated_count += 1
        player_obj.placement = 8 - (self.eliminated_count - 1)
        print(f"💀 {player_obj.name} è stato eliminato! ({player_obj.placement}° Posto)")

    def resolve_player_match(self, winner, player_surviving, enemy_surviving, round_number):
        """
        Applica il risultato del combattimento tra il giocatore umano e l'avversario bot.
        """
        if not self.current_opponent:
            return

        base_dmg = 2 + round_number
        if winner == "player":
            dmg = base_dmg + player_surviving * 2
            print(f"Hai sconfitto {self.current_opponent.name}! Gli infliggi {dmg} danni.")
            self.current_opponent.loss_streak += 1
            self.current_opponent.win_streak = 0
            if self.current_opponent.take_damage(dmg):
                self._assign_elimination_placement(self.current_opponent)
        else:
            dmg = base_dmg + enemy_surviving * 2
            print(f"Sei stato sconfitto da {self.current_opponent.name}! Subisci {dmg} danni.")
            self.current_opponent.win_streak += 1
            self.current_opponent.loss_streak = 0
            # Il danno al giocatore viene applicato in game.py

    def get_leaderboard(self):
        """
        Restituisce la lista di tutti gli 8 giocatori ordinata per:
        1. In vita prima di eliminati
        2. HP decrescente
        3. Streak decrescente
        """
        human_entry = {
            "is_human": True,
            "name": "Tu (Giocatore)",
            "hp": self.game.player_hp,
            "level": self.game.player_level,
            "is_alive": self.game.player_hp > 0,
            "placement": getattr(self.game, 'player_placement', None),
            "streak": self.game.win_streak if self.game.win_streak > 0 else -self.game.loss_streak,
            "board": [c for c in self.game.board if c is not None],
            "color": (40, 220, 255)
        }
        
        all_players = [human_entry]
        for b in self.bots:
            all_players.append({
                "is_human": False,
                "bot_ref": b,
                "name": b.name,
                "hp": b.hp,
                "level": b.level,
                "is_alive": b.is_alive,
                "placement": b.placement,
                "streak": b.win_streak if b.win_streak > 0 else -b.loss_streak,
                "board": b.board,
                "color": b.color
            })
            
        all_players.sort(key=lambda p: (
            1 if p["is_alive"] else 0,
            p["hp"],
            p["streak"]
        ), reverse=True)
        
        return all_players

    def draw_leaderboard_sidebar(self, surface, mouse_pos, start_x=1230, start_y=75):
        """
        Disegna la colonna della classifica a destra con barre HP dinamiche, nomi, streak e tooltip all'hover.
        """
        players = self.get_leaderboard()
        
        card_w = 156
        card_h = 42
        spacing = 5
        
        # Header Classifica
        head_rect = pygame.Rect(start_x, start_y, card_w, 24)
        head_surf = pygame.Surface((card_w, 24), pygame.SRCALPHA)
        pygame.draw.rect(head_surf, (14, 18, 28, 220), (0, 0, card_w, 24), border_radius=12)
        pygame.draw.rect(head_surf, (200, 170, 75, 180), (0, 0, card_w, 24), width=1, border_radius=12)
        surface.blit(head_surf, (start_x, start_y))
        draw_text("CLASSIFICA LOBBY", pygame.font.SysFont("Arial", 11, bold=True), (245, 225, 170), surface, head_rect.centerx, head_rect.centery)

        hovered_player = None
        current_y = start_y + 28

        for rank, p in enumerate(players, start=1):
            rect = pygame.Rect(start_x, current_y, card_w, card_h)
            is_hover = rect.collidepoint(mouse_pos)
            if is_hover and not p["is_human"] and p["is_alive"]:
                hovered_player = p
                
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            
            # Sfondo card
            if p["is_human"]:\
                bg_col = (18, 38, 55, 240) if is_hover else (12, 28, 42, 220)
                border_col = (60, 200, 255, 220)
                border_w = 2
            elif p["is_alive"]:
                bg_col = (25, 30, 42, 220) if is_hover else (15, 18, 26, 190)
                border_col = (60, 75, 95, 150)
                border_w = 1
            else:
                # Eliminato
                bg_col = (15, 15, 20, 160)
                border_col = (45, 45, 55, 100)
                border_w = 1

            pygame.draw.rect(card_surf, bg_col, (0, 0, card_w, card_h), border_radius=10)
            pygame.draw.rect(card_surf, border_col, (0, 0, card_w, card_h), width=border_w, border_radius=10)
            surface.blit(card_surf, (start_x, current_y))
            
            # 1. Badge Posizione (#1 - #8)
            rank_col = GOLD if rank == 1 else ((215, 225, 235) if rank == 2 else ((205, 140, 80) if rank == 3 else (140, 150, 165)))
            draw_text(f"#{rank}", pygame.font.SysFont("Arial", 12, bold=True), rank_col, surface, start_x + 14, current_y + 13)
            
            # 2. Nome Giocatore / Bot
            name_col = (80, 220, 255) if p["is_human"] else (WHITE if p["is_alive"] else (110, 115, 125))
            draw_text(p["name"][:13], pygame.font.SysFont("Arial", 11, bold=True), name_col, surface, start_x + 32, current_y + 6, center=False)
            
            if p["is_alive"]:
                # 3. Barra Vita Mini
                hp_pct = max(0.0, min(1.0, p["hp"] / 100.0))
                bar_x = start_x + 32
                bar_y = current_y + 22
                bar_w = 80
                bar_h = 8
                
                # Colore barra HP
                if hp_pct > 0.5:
                    hp_col = (50, 210, 90)
                elif hp_pct > 0.25:
                    hp_col = (235, 185, 40)
                else:
                    hp_col = (235, 60, 60)
                    
                pygame.draw.rect(surface, (20, 24, 32), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                if hp_pct > 0:
                    pygame.draw.rect(surface, hp_col, (bar_x, bar_y, int(bar_w * hp_pct), bar_h), border_radius=4)
                pygame.draw.rect(surface, (0, 0, 0, 140), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)
                
                # Testo HP
                draw_text(f"{p['hp']}", pygame.font.SysFont("Arial", 10, bold=True), WHITE, surface, start_x + card_w - 20, current_y + 26)
                
                # Streak indicator
                streak_val = p["streak"]
                if streak_val >= 2:
                    draw_text(f"+{streak_val}", pygame.font.SysFont("Arial", 9, bold=True), (255, 160, 50), surface, start_x + card_w - 18, current_y + 11)
                elif streak_val <= -2:
                    draw_text(f"{streak_val}", pygame.font.SysFont("Arial", 9, bold=True), (140, 160, 220), surface, start_x + card_w - 18, current_y + 11)
            else:
                # Testo eliminato
                draw_text(f"ELIMINATO", pygame.font.SysFont("Arial", 10, bold=True), (180, 70, 70), surface, start_x + 32, current_y + 22, center=False)

            current_y += card_h + spacing

        # Tooltip Scouting Bot al passaggio del mouse
        if hovered_player and not hovered_player["is_human"]:
            self._draw_bot_scouting_tooltip(surface, hovered_player, mouse_pos)

    def _draw_bot_scouting_tooltip(self, surface, bot_data, mouse_pos):
        """Disegna un popup informativo con composizione e sinergie del bot"""
        tip_w = 210
        tip_h = 160
        tip_x = max(10, mouse_pos[0] - tip_w - 15)
        tip_y = min(HEIGHT - tip_h - 10, max(10, mouse_pos[1] - 40))
        
        tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
        draw_glass_panel(surface, tip_rect, border_radius=14, bg_color=(12, 16, 26, 240), border_color=bot_data["color"], border_width=2)
        
        # Nome e Livello
        draw_text(bot_data["name"], HEADER_FONT, bot_data["color"], surface, tip_x + 12, tip_y + 14, center=False)
        draw_text(f"Livello {bot_data['level']} • {bot_data['hp']} HP", SMALL_FONT, (190, 200, 220), surface, tip_x + 12, tip_y + 34, center=False)
        
        # Sinergie del bot
        traits = calculate_team_traits(bot_data["board"])
        traits_str = ", ".join([f"{t['name']} ({t['count']}/{t['req']})" for t in traits if t['active']])
        if not traits_str:
            traits_str = "Nessuna attiva"
            
        draw_text("Sinergie:", SMALL_FONT, GOLD, surface, tip_x + 12, tip_y + 56, center=False)
        draw_text(traits_str[:28], MICRO_FONT, WHITE, surface, tip_x + 12, tip_y + 72, center=False)
        
        # Campioni schierati
        draw_text("Composizione:", SMALL_FONT, GOLD, surface, tip_x + 12, tip_y + 92, center=False)
        roster_names = [f"{c.name} ({getattr(c, 'level', 1)}★)" for c in bot_data["board"]]
        for idx, r_name in enumerate(roster_names[:3]):
            draw_text(r_name, MICRO_FONT, (220, 230, 245), surface, tip_x + 12, tip_y + 110 + idx * 14, center=False)
        if len(roster_names) > 3:
            draw_text(f"+ altri {len(roster_names) - 3} campioni", MICRO_FONT, (140, 160, 180), surface, tip_x + 12, tip_y + 110 + 3 * 14, center=False)
