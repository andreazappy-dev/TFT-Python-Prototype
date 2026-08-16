# champions.py
import pygame
import random
import os
import math

# --- DEFINIZIONE COLORI BASE (Fallback & Glow) ---
CHAMP_COLORS = {
    "Garen": (50, 110, 220),      # Blu Demacia
    "Darius": (210, 40, 40),      # Rosso Noxus
    "Ashe": (120, 215, 255),      # Azzurro Ghiaccio
    "Vi": (220, 60, 180),         # Rosa Hextech
    "Ahri": (255, 120, 190),      # Rosa Volpe
    "Zed": (160, 40, 70),         # Rosso Ombra
    "Braum": (70, 140, 230),      # Blu Ghiaccio
    "Ezreal": (255, 220, 60),     # Giallo Mistico
    "Jinx": (255, 70, 150),       # Magenta Caotico
    "Riven": (100, 220, 140),     # Verde Runico
    "Katarina": (230, 50, 60),    # Cremisi
    "Yasuo": (100, 180, 255),     # Vento Celeste
    "Shen": (120, 70, 230),       # Viola Ninja
    "Kayle": (255, 230, 100),     # Oro Divino
    "Lux": (255, 245, 130),       # Luce Arcobaleno
    "Sejuani": (80, 180, 240),    # Glaciale Freljord
    "Aurelion": (130, 70, 245),   # Viola Galattico
    "Azir": (245, 195, 45),       # Oro Solare
    "Thresh": (40, 230, 160)      # Verde Spettrale
}
DEFAULT_COLOR = (128, 128, 128)

TIER_COLORS = {
    1: (160, 165, 175), # Tier 1 - Grigio Ferro
    2: (40, 190, 80),   # Tier 2 - Verde Smeraldo
    3: (40, 130, 245),  # Tier 3 - Blu Zaffiro
    4: (195, 60, 240),  # Tier 4 - Viola Epico
    5: (255, 205, 45)   # Tier 5 - Oro Leggendario
}

class Champion:
    """
    Classe che rappresenta un campione con statistiche di base, abilità speciali e animazioni.
    """
    def __init__(self, name, hp, attack,
                 defense=0, crit_chance=0.1, 
                 mana_max=100, mana_start=0, attack_speed=0.7, attack_range=1, cost=1, traits=None, items=None):
        
        # --- Statistiche Base ---
        self.name = name
        self.level = 1
        self.cost = cost
        self.traits = list(traits) if traits else []
        self.items = list(items) if items else []
        self.lifesteal = 0.0
        self.color = CHAMP_COLORS.get(name, DEFAULT_COLOR)
        self.tier_color = TIER_COLORS.get(cost, (160, 165, 175))
        
        # Statistiche che scalano
        self.base_hp = int(hp)
        self.base_attack = int(attack)
        self.base_defense = int(defense)
        self.crit_chance = float(crit_chance)
        self.crit_multiplier = 1.5
        
        # --- Statistiche Auto-Battler ---
        self.mana_max = int(mana_max)
        self.mana_start = int(mana_start)
        self.attack_speed = float(attack_speed) # Attacchi al secondo
        self.attack_range = int(attack_range) # Distanza d'attacco in pixel
        
        # --- Stato di Combattimento ---
        self.hp = self.base_hp
        self.max_hp = self.base_hp
        self.current_mana = self.mana_start
        self.mana_per_hit = 10
        self.spell_power_mult = 1.0
        self.shield = 0
        self.is_assassin = False
        
        self.x = 0.0
        self.y = 0.0
        self.target = None
        self.attack_timer = 0.0
        self.is_casting = False
        self.move_speed = 110 # Pixel al secondo

        # --- Statistiche Damage Meter ---
        self.damage_dealt_physical = 0
        self.damage_dealt_magic = 0
        self.damage_taken = 0
        self.healing_done = 0
        self.kills_count = 0

        # --- Animazioni e Visuals ---
        self.facing_right = True
        self.anim_state = "IDLE"
        self.anim_time = random.uniform(0, 3.14)
        self.lunge_offset_x = 0.0
        self.lunge_offset_y = 0.0
        self.lunge_timer = 0.0
        self.hit_flash_timer = 0.0
        self.rotation_angle = 0.0
        self.death_timer = 0.0
        self.death_alpha = 255
        self.is_dead = False
        
        self.damage_popup_texts = []
        self.spell_animation_timer = 0.0

    @property
    def total_damage_dealt(self):
        return self.damage_dealt_physical + self.damage_dealt_magic
        
    def get_sprite_surface(self, width=80, height=80):
        """Restituisce lo sprite del personaggio a figura intera orientato con eventuale hit-flash"""
        from asset_loader import get_champion_sprite
        flip = not self.facing_right
        flash = self.hit_flash_timer > 0
        return get_champion_sprite(self.name, width=width, height=height, flip_x=flip, white_flash=flash)

    def copy(self):
        """Crea una copia indipendente del campione preservando statistiche e oggetti"""
        c = Champion(
            self.name,
            self.base_hp,
            self.base_attack,
            getattr(self, 'base_defense', 0),
            getattr(self, 'crit_chance', 0.1),
            getattr(self, 'mana_max', 100),
            getattr(self, 'mana_start', 0),
            getattr(self, 'attack_speed', 0.7),
            getattr(self, 'attack_range', 1),
            cost=getattr(self, 'cost', 1),
            traits=list(getattr(self, 'traits', []))
        )
        c.level = getattr(self, 'level', 1)
        c.items = list(getattr(self, 'items', []))
        c.hp = self.hp
        c.max_hp = self.max_hp
        c.damage_dealt_physical = self.damage_dealt_physical
        c.damage_dealt_magic = self.damage_dealt_magic
        c.damage_taken = self.damage_taken
        c.healing_done = self.healing_done
        c.kills_count = self.kills_count
        return c
        
    def take_damage(self, dmg):
        """Subisce danno gestendo scudi protettivi, block e hit-flash"""
        actual_dmg = dmg
        
        # Scudi protettivi
        if hasattr(self, 'shield') and self.shield > 0:
            if self.shield >= actual_dmg:
                self.shield -= actual_dmg
                actual_dmg = 0
            else:
                actual_dmg -= self.shield
                self.shield = 0
                
        # Cavaliere block
        if hasattr(self, 'knight_damage_block') and self.knight_damage_block > 0:
            actual_dmg = max(1, actual_dmg - self.knight_damage_block)
            
        self.hp = max(0, self.hp - actual_dmg)
        self.hit_flash_timer = 0.12 # Lampeggia di bianco all'impatto
        
    def equip_item(self, item_key):
        """
        Equipaggia un oggetto sul campione.
        Se entrambi sono componenti, li combina automaticamente in un oggetto completo.
        """
        from items import get_item_data, combine_components
        new_data = get_item_data(item_key)
        
        if new_data.get("is_component", False):
            for i, existing in enumerate(self.items):
                ex_data = get_item_data(existing)
                if ex_data.get("is_component", False):
                    comb = combine_components(existing, item_key)
                    if comb:
                        self.items[i] = comb["name"]
                        return "combined", comb
                        
        if len(self.items) < 3:
            self.items.append(new_data["name"])
            return "equipped", new_data
            
        return "full", None
        
    def get_token_surface(self, size=50, flip_x=False):
        """Ottiene il token circolare con ritratto del campione"""
        from asset_loader import create_circular_token
        return create_circular_token(self.name, size=size, flip_x=flip_x)

    def get_card_surface(self, width=150, height=130):
        """Ottiene l'illustrazione della carta per lo shop"""
        from asset_loader import create_card_image
        return create_card_image(self.name, width=width, height=height)
        
    def is_alive(self):
        return self.hp > 0

    def get_distance(self, other_champ):
        """ Calcola la distanza (euclidea) da un altro campione """
        return math.sqrt((self.x - other_champ.x)**2 + (self.y - other_champ.y)**2)

    def find_closest_target(self, enemy_team):
        """ Trova il nemico vivo più vicino """
        closest_dist = float('inf')
        closest_enemy = None
        
        for enemy in enemy_team:
            if enemy.is_alive():
                dist = self.get_distance(enemy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = enemy
        self.target = closest_enemy

    def move_towards_target(self, delta_time):
        """ Fa un passo verso il bersaglio """
        if not self.target:
            return
            
        dir_x = self.target.x - self.x
        dir_y = self.target.y - self.y
        dist = math.sqrt(dir_x**2 + dir_y**2)
        
        if dist == 0: 
            return
            
        dir_x /= dist
        dir_y /= dist
        
        self.x += dir_x * self.move_speed * delta_time
        self.y += dir_y * self.move_speed * delta_time

    def deal_magic_damage_to(self, target, raw_dmg):
        """Applica danno magico da abilità tracciando metrica, critici e vampirismo"""
        if not target or not target.is_alive():
            return
            
        was_alive = target.is_alive()
        crit = getattr(self, "spell_crit", False) and (random.random() < self.crit_chance)
        dmg = int(raw_dmg * (self.crit_multiplier if crit else 1.0))
        
        target.take_damage(dmg)
        target.damage_taken += dmg
        self.damage_dealt_magic += dmg
        
        if was_alive and not target.is_alive():
            self.kills_count += 1
            
        if getattr(self, "lifesteal", 0.0) > 0:
            heal = max(1, int(dmg * self.lifesteal))
            self.hp = min(self.max_hp, self.hp + heal)
            self.healing_done += heal
            
        color = (255, 120, 255) if crit else (140, 210, 255)
        target.damage_popup_texts.append({
            "text": str(dmg),
            "color": color,
            "pos": [target.x, target.y - 40],
            "timer": 1.0
        })

    def basic_attack(self, target):
        """ Esegue un attacco base """
        if not target or not target.is_alive():
            return
            
        was_alive = target.is_alive()
        crit = random.random() < self.crit_chance
        mult = self.crit_multiplier if crit else 1.0
        damage = int(self.base_attack * mult) - getattr(target, 'base_defense', 0)
        damage = max(1, int(damage))
        
        target.take_damage(damage)
        target.damage_taken += damage
        self.damage_dealt_physical += damage

        text_color = (255, 60, 60) if crit else (255, 235, 80)
        target.damage_popup_texts.append({
            "text": str(damage),
            "color": text_color,
            "pos": [target.x, target.y - 40],
            "timer": 1.0
        })
        
        if getattr(self, "lifesteal", 0.0) > 0:
            heal_amount = max(1, int(damage * self.lifesteal))
            self.hp = min(self.max_hp, self.hp + heal_amount)
            self.healing_done += heal_amount

        if any("Guinsoo" in str(it) for it in getattr(self, "items", [])):
            self.attack_speed = min(3.2, self.attack_speed + 0.05)

        mana_gain = getattr(self, "mana_per_hit", 10)
        self.current_mana = min(self.mana_max, self.current_mana + mana_gain)
        
        try:
            from audio_manager import AudioManager
            sfx = "attack_ranged" if self.attack_range > 100 else "attack_melee"
            AudioManager.get_instance().play_sfx(sfx)
        except Exception:
            pass
            
        if was_alive and not target.is_alive():
            self.kills_count += 1
            self.target = None

    def cast_spell(self, enemy_team, friendly_team):
        """ Esegue l'abilità speciale iconica con calcolo danni e status! """
        print(f"✨✨✨ {self.name} USA L'ABILITÀ SPECIALE! ✨✨✨")
        self.is_casting = True
        self.spell_animation_timer = 1.0
        
        try:
            from audio_manager import AudioManager
            AudioManager.get_instance().play_sfx("spell_cast")
        except Exception:
            pass
            
        sp_mult = getattr(self, "spell_power_mult", 1.0)
        spell_mult = (1.0 + (self.level - 1) * 0.80) * sp_mult

        # --- 1-COST CHAMPIONS ---
        if self.name == "Garen":
            dmg = int(140 * spell_mult)
            for enemy in enemy_team:
                if enemy.is_alive() and self.get_distance(enemy) < 170: 
                    self.deal_magic_damage_to(enemy, dmg)

        elif self.name == "Darius":
            if self.target and self.target.is_alive():
                dmg = int(280 * spell_mult)
                self.deal_magic_damage_to(self.target, dmg)
                if not self.target.is_alive():
                    # Reset se killa!
                    self.current_mana = self.mana_max
                    print("🪓 GHIGLIOTTINA NOXIANA: Reset del Mana!")

        elif self.name == "Ashe":
            if self.target and self.target.is_alive():
                dmg = int(200 * spell_mult)
                self.deal_magic_damage_to(self.target, dmg)
                self.target.attack_speed = max(0.3, self.target.attack_speed * 0.5) # Rallenta attacco

        # --- 2-COST CHAMPIONS ---
        elif self.name == "Ahri":
            if self.target and self.target.is_alive():
                dmg = int(190 * spell_mult)
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Vi":
            if self.target and self.target.is_alive():
                dmg = int(240 * spell_mult)
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Zed":
            # Teletrasporto alle spalle del target
            if self.target and self.target.is_alive():
                self.x = self.target.x + 30
                self.y = self.target.y
                dmg = int(290 * spell_mult)
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Braum":
            shield = int(450 * spell_mult)
            self.shield += shield
            self.healing_done += shield
            self.base_defense += 30

        # --- 3-COST CHAMPIONS ---
        elif self.name == "Ezreal":
            if self.target and self.target.is_alive():
                dmg = int(270 * spell_mult)
                self.deal_magic_damage_to(self.target, dmg)
                self.attack_speed = min(2.5, self.attack_speed * 1.35)

        elif self.name == "Jinx":
            dmg = int(340 * spell_mult)
            if self.target and self.target.is_alive():
                self.deal_magic_damage_to(self.target, dmg)
            for enemy in enemy_team:
                if enemy.is_alive() and enemy != self.target and self.get_distance(enemy) < 220:
                    self.deal_magic_damage_to(enemy, int(dmg * 0.55))

        elif self.name == "Riven":
            dmg = int(180 * spell_mult)
            shield = int(220 * spell_mult)
            self.shield += shield
            self.healing_done += shield
            if self.target and self.target.is_alive():
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Katarina":
            # Salta nel mezzo dei nemici e lancia pugnali
            enemies_in_range = [e for e in enemy_team if e.is_alive()]
            for e in enemies_in_range[:3]:
                dmg = int(240 * spell_mult)
                self.deal_magic_damage_to(e, dmg)

        elif self.name == "Yasuo":
            # Tornado a cono
            dmg = int(260 * spell_mult)
            for enemy in enemy_team:
                if enemy.is_alive() and self.get_distance(enemy) < 220:
                    self.deal_magic_damage_to(enemy, dmg)

        # --- 4-COST CHAMPIONS ---
        elif self.name == "Shen":
            shield = int(320 * spell_mult)
            self.shield += shield
            self.healing_done += shield
            for ally in friendly_team:
                if ally.is_alive() and self.get_distance(ally) < 180:
                    ally.shield = getattr(ally, 'shield', 0) + int(shield * 0.6)

        elif self.name == "Kayle":
            dmg = int(460 * spell_mult)
            heal = int(250 * spell_mult)
            self.hp = min(self.max_hp, self.hp + heal)
            self.healing_done += heal
            for enemy in enemy_team:
                if enemy.is_alive() and self.get_distance(enemy) < 260:
                    self.deal_magic_damage_to(enemy, dmg)

        elif self.name == "Lux":
            dmg = int(500 * spell_mult)
            # Raggio laser che colpisce il target e tutti i nemici allineati
            for enemy in enemy_team:
                if enemy.is_alive():
                    self.deal_magic_damage_to(enemy, dmg)

        elif self.name == "Sejuani":
            dmg = int(320 * spell_mult)
            for enemy in enemy_team:
                if enemy.is_alive() and self.get_distance(enemy) < 260:
                    self.deal_magic_damage_to(enemy, dmg)
                    enemy.attack_speed = max(0.3, enemy.attack_speed * 0.4)

        # --- 5-COST LEGENDARIES ---
        elif self.name == "Aurelion":
            dmg = int(420 * spell_mult)
            for enemy in enemy_team:
                if enemy.is_alive():
                    self.deal_magic_damage_to(enemy, dmg)

        elif self.name == "Azir":
            dmg = int(460 * spell_mult)
            for enemy in enemy_team:
                if enemy.is_alive():
                    self.deal_magic_damage_to(enemy, dmg)

        elif self.name == "Thresh":
            # Trascina il nemico più lontano
            furthest_enemy = max((e for e in enemy_team if e.is_alive()), key=lambda e: self.get_distance(e), default=None)
            if furthest_enemy:
                dmg = int(440 * spell_mult)
                self.deal_magic_damage_to(furthest_enemy, dmg)
                furthest_enemy.x = self.x + 50
                furthest_enemy.y = self.y
                # Scudo agli alleati
                for ally in friendly_team:
                    if ally.is_alive():
                        ally.shield = getattr(ally, 'shield', 0) + 300
        
        # Fine abilità
        self.current_mana = 0
        self.is_casting = False


def get_available_champions():
    """
    Restituisce l'intero database di 19 Campioni bilanciati per costo, statistiche, raggio e tratti.
    """
    R_MELEE = 80 
    R_RANGED = 300
    R_SNIPER = 500

    return [
        # --- COSTO 1 (TIER 1) ---
        Champion("Garen", 650, 52, defense=15, crit_chance=0.1, 
                 mana_max=100, mana_start=0, attack_speed=0.60, attack_range=R_MELEE, cost=1,
                 traits=["Demacia", "Cavaliere"]),
        Champion("Darius", 640, 58, defense=12, crit_chance=0.15, 
                 mana_max=70, mana_start=0, attack_speed=0.65, attack_range=R_MELEE, cost=1,
                 traits=["Noxus", "Cavaliere"]),
        Champion("Ashe", 500, 48, defense=6, crit_chance=0.2, 
                 mana_max=60, mana_start=0, attack_speed=0.75, attack_range=R_SNIPER, cost=1,
                 traits=["Freljord", "Cecchino"]),

        # --- COSTO 2 (TIER 2) ---
        Champion("Ahri", 520, 42, defense=6, crit_chance=0.2, 
                 mana_max=70, mana_start=15, attack_speed=0.75, attack_range=R_RANGED, cost=2,
                 traits=["Ionia", "Mago"]),
        Champion("Vi", 620, 62, defense=10, crit_chance=0.1, 
                 mana_max=80, mana_start=0, attack_speed=0.70, attack_range=R_MELEE, cost=2,
                 traits=["Piltover", "Picchiatore"]),
        Champion("Zed", 550, 68, defense=8, crit_chance=0.25, 
                 mana_max=60, mana_start=10, attack_speed=0.80, attack_range=R_MELEE, cost=2,
                 traits=["Ionia", "Assassino"]),
        Champion("Braum", 750, 40, defense=25, crit_chance=0.05, 
                 mana_max=90, mana_start=30, attack_speed=0.55, attack_range=R_MELEE, cost=2,
                 traits=["Freljord", "Guardiano"]),

        # --- COSTO 3 (TIER 3) ---
        Champion("Ezreal", 520, 48, defense=5, crit_chance=0.25, 
                 mana_max=60, mana_start=0, attack_speed=0.80, attack_range=R_SNIPER, cost=3,
                 traits=["Piltover", "Cecchino"]),
        Champion("Jinx", 560, 72, defense=6, crit_chance=0.3, 
                 mana_max=80, mana_start=0, attack_speed=0.85, attack_range=R_SNIPER, cost=3,
                 traits=["Zaun", "Cecchino"]),
        Champion("Riven", 600, 58, defense=10, crit_chance=0.15, 
                 mana_max=90, mana_start=0, attack_speed=0.75, attack_range=R_MELEE, cost=3,
                 traits=["Noxus", "Duellante"]),
        Champion("Katarina", 580, 65, defense=8, crit_chance=0.25, 
                 mana_max=75, mana_start=15, attack_speed=0.80, attack_range=R_MELEE, cost=3,
                 traits=["Noxus", "Assassino"]),
        Champion("Yasuo", 620, 64, defense=10, crit_chance=0.25, 
                 mana_max=80, mana_start=20, attack_speed=0.85, attack_range=R_MELEE, cost=3,
                 traits=["Ionia", "Duellante"]),

        # --- COSTO 4 (TIER 4) ---
        Champion("Shen", 780, 50, defense=16, crit_chance=0.1, 
                 mana_max=100, mana_start=50, attack_speed=0.65, attack_range=R_MELEE, cost=4,
                 traits=["Ionia", "Ninja"]),
        Champion("Kayle", 820, 95, defense=12, crit_chance=0.3, 
                 mana_max=140, mana_start=40, attack_speed=1.00, attack_range=R_SNIPER, cost=4,
                 traits=["Demacia", "Divino"]),
        Champion("Lux", 600, 65, defense=6, crit_chance=0.25, 
                 mana_max=100, mana_start=20, attack_speed=0.75, attack_range=R_SNIPER, cost=4,
                 traits=["Demacia", "Mago"]),
        Champion("Sejuani", 850, 55, defense=20, crit_chance=0.1, 
                 mana_max=120, mana_start=40, attack_speed=0.60, attack_range=R_MELEE, cost=4,
                 traits=["Freljord", "Cavaliere"]),

        # --- COSTO 5 (TIER 5 LEGENDARIES) ---
        Champion("Aurelion", 750, 65, defense=8, crit_chance=0.2, 
                 mana_max=120, mana_start=40, attack_speed=0.65, attack_range=R_RANGED, cost=5,
                 traits=["Drago", "Mago"]),
        Champion("Azir", 720, 70, defense=8, crit_chance=0.25, 
                 mana_max=110, mana_start=30, attack_speed=0.80, attack_range=R_RANGED, cost=5,
                 traits=["Shurima", "Mago"]),
        Champion("Thresh", 880, 60, defense=22, crit_chance=0.1, 
                 mana_max=130, mana_start=50, attack_speed=0.60, attack_range=R_MELEE, cost=5,
                 traits=["Ombre delle Isole", "Guardiano"]),
    ]

SPRITE_SIZE = (70, 70)
SPELL_EFFECT_SIZE = (50, 50)