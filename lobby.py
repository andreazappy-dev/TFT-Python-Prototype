# lobby.py
import random
import pygame
from config import draw_text, WIDTH, HEIGHT, GOLD, WHITE, BLACK, RED, GREEN, TEXT_FONT, SMALL_FONT, MICRO_FONT, HEADER_FONT
from traits import calculate_team_traits
from items import get_random_component_key
from asset_loader import draw_glass_panel

BOT_NAMES_DATA = [
    {
        "name": "PenguMaster", 
        "theme": "Demacia/Cavaliere", 
        "color": (230, 200, 80),
        "target_traits": ["Demacia", "Cavaliere"],
        "carries": ["Lux", "Kayle", "Garen"],
        "tanks": ["Garen", "Sejuani", "Braum"]
    },
    {
        "name": "HextechKing", 
        "theme": "Piltover/Zaun", 
        "color": (80, 200, 230),
        "target_traits": ["Piltover", "Picchiatore", "Cecchino"],
        "carries": ["Jinx", "Ezreal", "Ashe"],
        "tanks": ["Vi", "Braum"]
    },
    {
        "name": "ChonccLover", 
        "theme": "Ionia/Mago", 
        "color": (230, 100, 160),
        "target_traits": ["Ionia", "Assassino", "Mago"],
        "carries": ["Ahri", "Yasuo", "Zed"],
        "tanks": ["Shen", "Yasuo"]
    },
    {
        "name": "DariusMain", 
        "theme": "Noxus/Cavaliere", 
        "color": (220, 50, 50),
        "target_traits": ["Noxus", "Cavaliere", "Assassino"],
        "carries": ["Darius", "Katarina"],
        "tanks": ["Darius", "Garen", "Braum"]
    },
    {
        "name": "CosmicVoyager", 
        "theme": "Drago/Divino/Mago", 
        "color": (140, 90, 240),
        "target_traits": ["Drago", "Divino", "Mago"],
        "carries": ["Aurelion", "Kayle", "Azir"],
        "tanks": ["Shen", "Garen"]
    },
    {
        "name": "SniperQueen", 
        "theme": "Freljord/Cecchino", 
        "color": (240, 180, 40),
        "target_traits": ["Freljord", "Cecchino", "Guardiano"],
        "carries": ["Ashe", "Ezreal"],
        "tanks": ["Braum", "Sejuani"]
    },
    {
        "name": "ShadowIsles", 
        "theme": "Ombre/Guardiano", 
        "color": (60, 220, 130),
        "target_traits": ["Ombre delle Isole", "Guardiano", "Mago"],
        "carries": ["Thresh", "Lux"],
        "tanks": ["Thresh", "Shen", "Braum"]
    },
]

class BotPlayer:
    """
    Rappresenta un giocatore avversario controllato dall'AI nella Lobby a 8 Giocatori.
    Implementa AI Tattica TFT:
    - Composizioni e sinergie mirate
    - Fusione ed equipaggiamento strategico degli oggetti
    - Posizionamento su griglia intelligente (Frontline Tank / Backline Carry / Ali Assassini)
    """
    def __init__(self, name, theme, color, target_traits=None, carries=None, tanks=None):
        self.name = name
        self.theme = theme
        self.color = color
        self.target_traits = target_traits or ["Cavaliere", "Mago"]
        self.preferred_carries = carries or ["Lux", "Ashe", "Darius"]
        self.preferred_tanks = tanks or ["Braum", "Garen", "Shen"]
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
        self.items_bank = [] # Componenti grezzi
        
    def get_team_power(self):
        """Calcola un punteggio di forza dell'armata per le simulazioni bot vs bot"""
        power = self.level * 18
        for c in self.board:
            stars = getattr(c, 'level', 1)
            cost = getattr(c, 'cost', 1)
            power += (cost * 14) * (stars ** 1.7)
            power += len(getattr(c, 'items', [])) * 18
        return power

    def update_progression(self, round_number, champions_db):
        """
        Simula l'economia, i livelli, la selezione sinergica dei campioni, 
        upgrade a 2/3 stelle, fusione intelligente degli oggetti e posizionamento tattico.
        """
        if not self.is_alive:
            return

        from items import combine_components

        # 1. Guadagno Oro ed Economia Intelligente
        interest = min(5, self.gold // 10)
        self.gold += 5 + interest
        self.xp += 2
        
        # Curva di Livellamento Realistica TFT
        # Round 1-3: Lvl 2-3 | Round 4-5: Lvl 4-5 | Round 6-7: Lvl 6 | Round 8-10: Lvl 7 | Round 11+: Lvl 8-9
        target_level = min(9, max(1, 1 + (round_number + 1) // 2))
        while self.level < target_level and self.gold >= 4:
            self.gold -= 4
            self.level += 1

        # 2. Generazione Componenti Oggetto periodici
        if round_number in [1, 2, 3] or round_number % 3 == 0:
            self.items_bank.append(get_random_component_key())

        # 3. Costruzione Squadra Sinergica basata sull'archetipo
        desired_slots = min(self.level, 7)
        
        # Filtra i campioni adatti alla composizione del bot
        thematic_pool = []
        for c in champions_db:
            if c.cost <= min(5, 1 + self.level // 2):
                matches_trait = any(t in self.target_traits for t in getattr(c, 'traits', []))
                is_fav = c.name in self.preferred_carries or c.name in self.preferred_tanks
                if matches_trait or is_fav:
                    thematic_pool.append(c)
                    
        if not thematic_pool:
            thematic_pool = [c for c in champions_db if c.cost <= min(5, 1 + self.level // 2)]

        # Ricarica/aggiorna la board del bot
        current_names = [c.name for c in self.board]
        while len(self.board) < desired_slots and thematic_pool:
            chosen_template = random.choice(thematic_pool)
            chosen = chosen_template.copy()
            
            # Probabilità di upgrade stella basata sul round
            star_roll = random.random()
            if round_number >= 3 and star_roll < 0.50:
                chosen.level = 2
                chosen.hp = int(chosen.hp * 1.8)
                chosen.max_hp = chosen.hp
                chosen.base_attack = int(chosen.base_attack * 1.8)
            if round_number >= 7 and star_roll < 0.22:
                chosen.level = 3
                chosen.hp = int(chosen.hp * 3.2)
                chosen.max_hp = chosen.hp
                chosen.base_attack = int(chosen.base_attack * 3.2)
                
            self.board.append(chosen)

        # 4. Fusione ed Equipaggiamento Intelligente degli Oggetti
        while len(self.items_bank) >= 2:
            c1 = self.items_bank.pop(0)
            c2 = self.items_bank.pop(0)
            completed_res = combine_components(c1, c2)
            
            if completed_res:
                item_name = completed_res["name"]
                bonus = completed_res.get("bonus", {})
                
                # Sceglie il miglior portatore in base alle statistiche dell'oggetto
                is_tank_item = "defense" in bonus or "hp" in bonus or "magic_resist" in bonus
                is_magic_item = "spell_power" in bonus or "mana_start" in bonus
                
                target_champ = None
                if is_tank_item:
                    # Cerca prima tra i Tank
                    tank_candidates = [c for c in self.board if c.name in self.preferred_tanks and len(getattr(c, 'items', [])) < 3]
                    if tank_candidates:
                        target_champ = tank_candidates[0]
                elif is_magic_item:
                    # Cerca prima tra i Carry Maghi
                    mage_candidates = [c for c in self.board if ("Mago" in getattr(c, 'traits', []) or c.name in self.preferred_carries) and len(getattr(c, 'items', [])) < 3]
                    if mage_candidates:
                        target_champ = mage_candidates[0]
                else:
                    # Oggetto AD / Attack Speed: assegna al carry fisico
                    ad_candidates = [c for c in self.board if c.name in self.preferred_carries and len(getattr(c, 'items', [])) < 3]
                    if ad_candidates:
                        target_champ = ad_candidates[0]
                        
                # Fallback se non trova il candidato ideale
                if not target_champ:
                    available = [c for c in self.board if len(getattr(c, 'items', [])) < 3]
                    if available:
                        target_champ = random.choice(available)
                        
                if target_champ:
                    target_champ.equip_item(item_name)
            else:
                # Se non combinabili, rimetti in banca
                self.items_bank.append(c1)

        # 5. Posizionamento Tattico su Griglia Hex (Frontline / Backline / Flank)
        self.assign_tactical_positions()

    def assign_tactical_positions(self):
        """
        Assegna le posizioni dei campioni sulla griglia nemica 7x2:
        - Row 1 (Indici 7..13 - Prima Linea): Tank, Cavalieri, Guardiani, Picchiatori
        - Row 0 (Indici 0..6 - Retroguardia): Cecchini, Maghi, Carry fragili
        - Ali/Fianchi (0, 6, 7, 13): Assassini
        """
        frontline_slots = [10, 9, 11, 8, 12, 7, 13] # Centro prima linea preferito
        backline_slots = [3, 2, 4, 1, 5, 0, 6]     # Centro/angoli retroguardia
        flank_slots = [0, 6, 7, 13]
        
        used_slots = set()
        
        for champ in self.board:
            traits = getattr(champ, 'traits', [])
            name = champ.name
            
            is_tank = any(t in ["Cavaliere", "Guardiano", "Picchiatore"] for t in traits) or name in self.preferred_tanks
            is_assassin = "Assassino" in traits or name in ["Zed", "Katarina"]
            is_ranged = champ.attack_range > 1 or any(t in ["Cecchino", "Mago"] for t in traits)
            
            assigned_slot = None
            if is_assassin:
                for slot in flank_slots:
                    if slot not in used_slots:
                        assigned_slot = slot
                        break
            elif is_tank:
                for slot in frontline_slots:
                    if slot not in used_slots:
                        assigned_slot = slot
                        break
            elif is_ranged:
                for slot in backline_slots:
                    if slot not in used_slots:
                        assigned_slot = slot
                        break
                        
            # Fallback se gli slot ideali sono pieni
            if assigned_slot is None:
                for slot in range(14):
                    if slot not in used_slots:
                        assigned_slot = slot
                        break
                        
            if assigned_slot is not None:
                used_slots.add(assigned_slot)
                champ.board_index = assigned_slot

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
        self.bots = [
            BotPlayer(
                name=b["name"], 
                theme=b["theme"], 
                color=b["color"],
                target_traits=b.get("target_traits"),
                carries=b.get("carries"),
                tanks=b.get("tanks")
            ) for b in BOT_NAMES_DATA
        ]
        self.current_opponent = None
        self.eliminated_count = 0
        
    def get_alive_bots(self):
        return [b for b in self.bots if b.is_alive]
        
    def start_pve_round(self, round_number):
        """Prepara e fa progredire tutti i bot durante i round PvE neutrali"""
        for bot in self.bots:
            bot.update_progression(round_number, self.game.champions_database)
        self.current_opponent = None

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

    def draw_leaderboard_sidebar(self, surface, mouse_pos, start_x=None, start_y=52):
        """
        Disegna la colonna della classifica a destra con barre HP dinamiche, nomi, streak e tooltip all'hover.
        Posizionata a start_y=52 per lasciare spazio all'indicatore di stato in alto a destra.
        """
        players = self.get_leaderboard()
        
        card_w = 195
        card_h = 34
        spacing = 4
        px = start_x if start_x is not None else (surface.get_width() - card_w - 20)
        
        # Header Classifica
        head_rect = pygame.Rect(px, start_y, card_w, 24)
        head_surf = pygame.Surface((card_w, 24), pygame.SRCALPHA)
        pygame.draw.rect(head_surf, (14, 18, 28, 230), (0, 0, card_w, 24), border_radius=12)
        pygame.draw.rect(head_surf, (200, 170, 75, 180), (0, 0, card_w, 24), width=1, border_radius=12)
        surface.blit(head_surf, (px, start_y))
        head_font = pygame.font.SysFont(["Helvetica Neue", "Arial", "sans-serif"], 11, bold=True)
        draw_text("CLASSIFICA LOBBY", head_font, (245, 225, 170), surface, head_rect.centerx, head_rect.centery)

        hovered_player = None
        current_y = start_y + 28
        row_font = pygame.font.SysFont(["Helvetica Neue", "Arial", "sans-serif"], 10, bold=True)

        for rank, p in enumerate(players, start=1):
            rect = pygame.Rect(px, current_y, card_w, card_h)
            is_hover = rect.collidepoint(mouse_pos)
            if is_hover and not p["is_human"] and p["is_alive"]:
                hovered_player = p
                
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            
            # Sfondo card
            if p["is_human"]:
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

            pygame.draw.rect(card_surf, bg_col, (0, 0, card_w, card_h), border_radius=8)
            pygame.draw.rect(card_surf, border_col, (0, 0, card_w, card_h), width=border_w, border_radius=8)
            surface.blit(card_surf, (px, current_y))
            
            # 1. Badge Posizione (#1 - #8)
            rank_col = GOLD if rank == 1 else ((215, 225, 235) if rank == 2 else ((205, 140, 80) if rank == 3 else (140, 150, 165)))
            draw_text(f"#{rank}", row_font, rank_col, surface, px + 12, current_y + card_h // 2)
            
            # 2. Nome Giocatore / Bot
            name_col = (80, 220, 255) if p["is_human"] else (WHITE if p["is_alive"] else (110, 115, 125))
            draw_text(p["name"][:11], row_font, name_col, surface, px + 26, current_y + 4, center=False)
            
            if p["is_alive"]:
                # 3. Barra Vita Mini
                hp_pct = max(0.0, min(1.0, p["hp"] / 100.0))
                bar_x = px + 26
                bar_y = current_y + 19
                bar_w = 110
                bar_h = 7
                
                # Colore barra HP
                if hp_pct > 0.5:
                    hp_col = (50, 210, 90)
                elif hp_pct > 0.25:
                    hp_col = (235, 185, 40)
                else:
                    hp_col = (235, 60, 60)
                    
                pygame.draw.rect(surface, (20, 24, 32), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
                if hp_pct > 0:
                    pygame.draw.rect(surface, hp_col, (bar_x, bar_y, int(bar_w * hp_pct), bar_h), border_radius=3)
                pygame.draw.rect(surface, (0, 0, 0, 140), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=3)
                
                # Testo HP
                draw_text(f"{p['hp']}", row_font, WHITE, surface, px + card_w - 20, current_y + 22)
                
                # Streak indicator
                streak = p["streak"]
                if streak >= 2:
                    draw_text(f"+{streak}", row_font, (100, 230, 255), surface, px + card_w - 20, current_y + 8)
                elif streak <= -2:
                    draw_text(f"{streak}", row_font, (220, 150, 60), surface, px + card_w - 20, current_y + 8)
            else:
                draw_text("ELIMINATO", row_font, (120, 120, 130), surface, px + 80, current_y + card_h // 2)

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
        draw_text(f"Livello {bot_data['level']} - {bot_data['hp']} HP", SMALL_FONT, (190, 200, 220), surface, tip_x + 12, tip_y + 34, center=False)
        
        # Sinergie del bot
        traits = calculate_team_traits(bot_data["board"])
        traits_str = ", ".join([f"{t['name']} ({t['count']}/{t['req']})" for t in traits if t['active']])
        if not traits_str:
            traits_str = "Nessuna attiva"
            
        draw_text("Sinergie:", SMALL_FONT, GOLD, surface, tip_x + 12, tip_y + 56, center=False)
        draw_text(traits_str[:28], MICRO_FONT, WHITE, surface, tip_x + 12, tip_y + 72, center=False)
        
        # Campioni schierati
        draw_text("Composizione:", SMALL_FONT, GOLD, surface, tip_x + 12, tip_y + 92, center=False)
        roster_names = [f"{c.name} (Lvl {getattr(c, 'level', 1)})" for c in bot_data["board"]]
        for idx, r_name in enumerate(roster_names[:3]):
            draw_text(r_name, MICRO_FONT, (220, 230, 245), surface, tip_x + 12, tip_y + 110 + idx * 14, center=False)
        if len(roster_names) > 3:
            draw_text(f"+ altri {len(roster_names) - 3} campioni", MICRO_FONT, (140, 160, 180), surface, tip_x + 12, tip_y + 110 + 3 * 14, center=False)
