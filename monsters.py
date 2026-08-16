# monsters.py
import random
import math
import pygame
from config import draw_text, WIDTH, HEIGHT, GOLD, WHITE, BLACK, RED, GREEN, BLUE, TEXT_FONT, SMALL_FONT, MICRO_FONT, HEADER_FONT
from champions import Champion
from items import get_random_component_key, get_item_data

class Monster(Champion):
    """
    Rappresenta un Mostro o Boss neutrale per i round PvE di Mini TFT.
    Compatibile al 100% con la logica di combattimento di BattleManager.
    """
    def __init__(self, name, hp, attack, defense=20, attack_speed=0.85, attack_range=1, crit_chance=0.15, mana_max=100, mana_start=0, monster_type="minion", traits=None):
        super().__init__(
            name=name,
            hp=hp,
            attack=attack,
            defense=defense,
            crit_chance=crit_chance,
            mana_max=mana_max,
            mana_start=mana_start,
            attack_speed=attack_speed,
            attack_range=attack_range,
            cost=0,
            traits=traits or ["Mostro"]
        )
        self.monster_type = monster_type # "minion_melee", "minion_caster", "krug_big", "krug_small", "wolf_alpha", "wolf", "dragon"
        self.is_monster = True
        self.max_hp = hp
        self.hp = hp
        self.tier_color = (255, 100, 100) if monster_type == "dragon" else ((160, 120, 240) if "krug" in monster_type or "wolf" in monster_type else (130, 140, 160))

    def copy(self):
        """Crea una copia esatta del mostro per la battaglia"""
        new_m = Monster(
            name=self.name,
            hp=self.base_hp,
            attack=self.base_attack,
            defense=self.base_defense,
            attack_speed=self.attack_speed,
            attack_range=self.attack_range,
            crit_chance=self.crit_chance,
            mana_max=self.mana_max,
            mana_start=self.mana_start,
            monster_type=self.monster_type,
            traits=list(self.traits)
        )
        new_m.level = self.level
        new_m.hp = self.hp
        new_m.max_hp = self.max_hp
        new_m.board_index = getattr(self, 'board_index', 0)
        return new_m

    def get_token_surface(self, size=44):
        """Genera un token grafico personalizzato per il mostro con dettagli e colori a tema."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        r = size // 2 - 2
        
        # Sfondi colorati per archetipo
        if self.monster_type == "dragon":
            base_col = (180, 30, 20)
            glow_col = (255, 120, 30)
            tag = "DRG"
        elif "krug" in self.monster_type:
            base_col = (90, 80, 70)
            glow_col = (180, 160, 120)
            tag = "KRG"
        elif "wolf" in self.monster_type:
            base_col = (40, 50, 80)
            glow_col = (80, 140, 220)
            tag = "WLF"
        elif "caster" in self.monster_type:
            base_col = (50, 30, 90)
            glow_col = (160, 90, 240)
            tag = "MAG"
        else:
            base_col = (60, 70, 80)
            glow_col = (120, 140, 160)
            tag = "MIN"

        # Corpo token circolare
        pygame.draw.circle(surf, base_col, (center, center), r)
        pygame.draw.circle(surf, glow_col, (center, center), r, width=2)
        
        # Dettaglio interno distintivo
        if self.monster_type == "dragon":
            # Corna/Occhi infuocati
            pygame.draw.circle(surf, (255, 220, 50), (center - 4, center - 2), 2)
            pygame.draw.circle(surf, (255, 220, 50), (center + 4, center - 2), 2)
            pygame.draw.polygon(surf, (255, 60, 30), [(center, center - 7), (center - 4, center + 4), (center + 4, center + 4)])
        else:
            # Tag identificativo
            font = pygame.font.SysFont(["Helvetica Neue", "Arial", "sans-serif"], max(8, size // 4), bold=True)
            draw_text(tag, font, WHITE, surf, center, center)

        return surf

    def use_ability(self, target, all_enemies, battle_manager):
        """Abilità speciale dei mostri / boss"""
        if self.monster_type == "dragon":
            # Boss Drago: Soffio Infernale AOE a tutti i campioni del giocatore
            print("🔥 DRAGO ANTICO: Soffio Infernale AOE!")
            if hasattr(battle_manager, 'shockwaves'):
                from battle_animations import ShockwaveVFX, Particle
                battle_manager.shockwaves.append(ShockwaveVFX(self.x, self.y, max_radius=180, color=(255, 100, 20), duration=0.6))
                for _ in range(35):
                    ang = random.uniform(0, math.pi * 2)
                    spd = random.uniform(80, 240)
                    battle_manager.particles.append(Particle(self.x, self.y, math.cos(ang)*spd, math.sin(ang)*spd, (255, random.randint(120, 220), 30), lifetime=0.7, size=4))
            
            # Applica danno ad area a tutti i campioni del giocatore
            for enemy in all_enemies:
                if enemy.is_alive():
                    enemy.take_damage(240, is_crit=False, damage_type="magic")
                    if hasattr(battle_manager, 'custom_vfx'):
                        battle_manager.custom_vfx.append({
                            "type": "burn",
                            "x": enemy.x, "y": enemy.y,
                            "timer": 1.2
                        })
            return 240
        else:
            # Colpo pesante potenziato per Krug / Lupi / Minion
            dmg = int(self.base_attack * 1.8)
            if target and target.is_alive():
                target.take_damage(dmg, is_crit=True, damage_type="physical")
            return dmg


class LootOrb:
    """
    Rappresenta una Sfera di Bottino tridimensionale fluttuante (Grigia, Blu, Oro).
    Rilascia Oro, Componenti Oggetto o Campioni Rari all'apertura.
    """
    def __init__(self, x, y, tier="grey", rewards=None):
        self.x = float(x)
        self.y = float(y)
        self.base_y = float(y)
        self.tier = tier # "grey", "blue", "gold"
        self.rewards = rewards or {"gold": 2, "item": None, "champion": None}
        self.is_opened = False
        self.time_alive = 0.0
        self.scale = 0.1 # Effetto pop-in
        self.radius = 18
        self.particles = []
        
        # Palette colori per tier
        if self.tier == "gold":
            self.color = (255, 215, 0)
            self.glow_color = (255, 240, 120)
            self.inner_color = (255, 165, 0)
        elif self.tier == "blue":
            self.color = (40, 160, 255)
            self.glow_color = (130, 210, 255)
            self.inner_color = (20, 90, 210)
        else: # grey
            self.color = (180, 190, 205)
            self.glow_color = (230, 235, 245)
            self.inner_color = (120, 130, 145)

    def update(self, dt):
        """Aggiorna l'animazione di galleggiamento e particelle della sfera"""
        self.time_alive += dt
        if self.scale < 1.0:
            self.scale = min(1.0, self.scale + dt * 4.0)
            
        # Fluttuazione sinusoidale dolce
        self.y = self.base_y + math.sin(self.time_alive * 4.0) * 5.0

    def draw(self, surface):
        """Disegna la sfera di bottino luminosa con bagliore e riflesso speculare"""
        if self.is_opened or self.scale <= 0:
            return

        cur_r = max(2, int(self.radius * self.scale))
        glow_r = int(cur_r * 1.5)
        
        # 1. Bagliore etereo trasparente
        glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pulse = 0.85 + 0.15 * math.sin(self.time_alive * 6.0)
        glow_alpha = int(90 * pulse)
        pygame.draw.circle(glow_surf, (*self.glow_color[:3], glow_alpha), (glow_r + 2, glow_r + 2), glow_r)
        surface.blit(glow_surf, (int(self.x - glow_r - 2), int(self.y - glow_r - 2)))
        
        # 2. Corpo Sfera sferica con sfumatura radiale
        pygame.draw.circle(surface, self.inner_color, (int(self.x), int(self.y)), cur_r)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), cur_r - 2)
        
        # 3. Riflesso speculare bianco in alto a sinistra
        spec_x = int(self.x - cur_r * 0.35)
        spec_y = int(self.y - cur_r * 0.35)
        spec_r = max(1, int(cur_r * 0.3))
        pygame.draw.circle(surface, (255, 255, 255, 220), (spec_x, spec_y), spec_r)
        
        # 4. Anello dorato per sfere Gold
        if self.tier == "gold":
            pygame.draw.circle(surface, (255, 245, 180), (int(self.x), int(self.y)), cur_r + 2, width=1)

    def open_orb(self, game):
        """Apre la sfera e rilascia le ricompense nel gioco"""
        if self.is_opened:
            return None
        self.is_opened = True
        
        gold_gain = self.rewards.get("gold", 0)
        item_gain = self.rewards.get("item", None)
        champ_gain = self.rewards.get("champion", None)
        
        msg_parts = []
        if gold_gain > 0:
            game.player_gold += gold_gain
            msg_parts.append(f"+{gold_gain} Oro")
            
        if item_gain:
            if len(game.player_items) < 8:
                game.player_items.append(item_gain)
                item_d = get_item_data(item_gain)
                msg_parts.append(f"{item_d.get('name', item_gain)}")
                
        if champ_gain:
            # Trova slot libero in panchina
            for i, slot in enumerate(game.bench):
                if slot is None:
                    db_champs = getattr(game, 'champions_database', [])
                    template = next((c for c in db_champs if c.name == champ_gain), None)
                    if template:
                        game.bench[i] = template.copy()
                        msg_parts.append(f"Campione: {template.name}")
                    break
                    
        if hasattr(game, 'audio'):
            game.audio.play_sfx("coin_buy")
            
        summary = " & ".join(msg_parts) if msg_parts else "Bottino Raccolto!"
        print(f"🎁 SFERA APERTA ({self.tier.upper()}): {summary}")
        return summary


# --- GENERATORE DI ENCOUNTER PVE ---

def is_pve_round(round_number):
    """Ritorna True se il round specificato è un combattimento contro mostri neutrali PvE"""
    return round_number in [2, 6, 9, 12]

def get_pve_encounter(round_number):
    """
    Restituisce i mostri e le sfere di bottino pianificate per il round PvE.
    """
    if round_number == 2:
        # Ondata Minion (2 Mischia in Frontline, 1 Caster in Midline)
        m1 = Monster("Minion Mischia", hp=360, attack=28, defense=15, attack_range=1, monster_type="minion_melee")
        m2 = Monster("Minion Caster", hp=280, attack=35, defense=10, attack_range=3, monster_type="minion_caster")
        m3 = Monster("Minion Mischia", hp=360, attack=28, defense=15, attack_range=1, monster_type="minion_melee")
        m1.board_index = 16 # Row 2 (Frontline)
        m2.board_index = 10 # Row 1 (Midline)
        m3.board_index = 18 # Row 2 (Frontline)
        monsters = [m1, m2, m3]
        orbs = [
            LootOrb(0, 0, tier="grey", rewards={"gold": 3, "item": None}),
            LootOrb(0, 0, tier="blue", rewards={"gold": 1, "item": get_random_component_key()})
        ]
        return {
            "name": "Ondata Minion",
            "theme": "Minion della Landa",
            "monsters": monsters,
            "orbs": orbs
        }
        
    elif round_number == 6:
        # Golem di Pietra (Krugs in Frontline)
        k1 = Monster("Krug Antico", hp=1100, attack=68, defense=35, attack_range=1, monster_type="krug_big")
        k2 = Monster("Krug Minore", hp=750, attack=50, defense=25, attack_range=1, monster_type="krug_small")
        k1.board_index = 16 # Row 2
        k2.board_index = 18 # Row 2
        monsters = [k1, k2]
        orbs = [
            LootOrb(0, 0, tier="blue", rewards={"gold": 2, "item": get_random_component_key()}),
            LootOrb(0, 0, tier="blue", rewards={"gold": 2, "item": get_random_component_key()})
        ]
        return {
            "name": "Golem di Pietra (Krugs)",
            "theme": "Rocce Antiche",
            "monsters": monsters,
            "orbs": orbs
        }
        
    elif round_number == 9:
        # Lupi delle Tenebre (Murkwolves in Frontline & Fianchi)
        w1 = Monster("Lupo Alpha", hp=950, attack=75, defense=25, crit_chance=0.40, attack_speed=1.15, monster_type="wolf_alpha")
        w2 = Monster("Lupo Silvano", hp=680, attack=58, defense=20, crit_chance=0.30, attack_speed=1.10, monster_type="wolf")
        w3 = Monster("Lupo Silvano", hp=680, attack=58, defense=20, crit_chance=0.30, attack_speed=1.10, monster_type="wolf")
        w1.board_index = 17 # Row 2 Centro
        w2.board_index = 15 # Row 2 Fianco
        w3.board_index = 19 # Row 2 Fianco
        monsters = [w1, w2, w3]
        orbs = [
            LootOrb(0, 0, tier="blue", rewards={"gold": 3, "item": get_random_component_key()}),
            LootOrb(0, 0, tier="gold", rewards={"gold": 5, "item": get_random_component_key(), "champion": random.choice(["Lux", "Yasuo", "Darius"])})
        ]
        return {
            "name": "Lupi delle Tenebre (Murkwolves)",
            "theme": "Predatori Notturni",
            "monsters": monsters,
            "orbs": orbs
        }
        
    elif round_number >= 12:
        # Boss Drago Antico (Centro Frontline)
        d = Monster("Drago Antico", hp=3500, attack=130, defense=55, attack_range=2, mana_max=100, mana_start=40, monster_type="dragon")
        d.board_index = 17 # Row 2 Centro
        monsters = [d]
        completed_pool = ["Giant Slayer", "Infinity Edge", "Warmog's Armor", "Rabadon's Deathcap", "Bloodthirster"]
        orbs = [
            LootOrb(0, 0, tier="gold", rewards={"gold": 10, "item": random.choice(completed_pool), "champion": random.choice(["Azir", "Thresh", "Aurelion"])})
        ]
        return {
            "name": "Drago Antico (Boss)",
            "theme": "Signore del Fuoco",
            "monsters": monsters,
            "orbs": orbs
        }
        
    return None
