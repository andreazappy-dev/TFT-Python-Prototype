# champions.py
import pygame
import random
import os
import math

# --- DEFINIZIONE COLORI (Greyboxing) ---
# Assegniamo un colore unico a ogni campione per distinguerli
CHAMP_COLORS = {
    "Garen": (0, 0, 200),      # Blu (Tank)
    "Vi": (200, 0, 200),       # Viola (Bruiser)
    "Ahri": (255, 105, 180),   # Rosa (Mago)
    "Ezreal": (255, 255, 0),   # Giallo (ADC)
    "Aurelion": (0, 0, 100),   # Blu Notte (Drago)
    "Riven": (200, 100, 100),  # Rosso chiaro (Combattente)
    "Shen": (100, 0, 200)      # Viola scuro (Tank)
}
DEFAULT_COLOR = (128, 128, 128) # Grigio default

TIER_COLORS = {
    1: (150, 150, 150), # Gray
    2: (30, 200, 50),   # Green
    3: (30, 100, 250),  # Blue
    4: (200, 50, 250),  # Purple
    5: (255, 215, 0)    # Gold
}

class Champion:
    """
    Classe che rappresenta un campione con statistiche di base e di combattimento.
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
        self.tier_color = TIER_COLORS.get(cost, (150, 150, 150))
        
        # Statistiche che scalano
        self.base_hp = int(hp)
        self.base_attack = int(attack)
        self.base_defense = int(defense)
        self.crit_chance = float(crit_chance)
        
        # --- Statistiche Auto-Battler ---
        self.mana_max = int(mana_max)
        self.mana_start = int(mana_start)
        self.attack_speed = float(attack_speed) # Attacchi al secondo
        self.attack_range = int(attack_range) # 1 = melee, >1 = ranged
        
        # --- Stato di Combattimento (variabili) ---
        self.hp = self.base_hp
        self.max_hp = self.base_hp
        self.current_mana = self.mana_start
        self.mana_per_hit = 10 # Mana guadagnato per ogni attacco base
        self.spell_power_mult = 1.0 # Modificatore potenza abilità
        
        self.x = 0 # Posizione reale (pixel)
        self.y = 0
        self.target = None # Il nemico che sta bersagliando
        self.attack_timer = 0.0 # Timer per la velocità d'attacco
        self.is_casting = False
        self.move_speed = 100 # Pixel al secondo

        # --- Statistiche di Tracciamento Battaglia (Damage Meter) ---
        self.damage_dealt_physical = 0
        self.damage_dealt_magic = 0
        self.damage_taken = 0
        self.healing_done = 0
        self.kills_count = 0

        # --- Animazioni e Grafica Dinamica ---
        self.facing_right = True # Per il flip orizzontale
        self.anim_state = "IDLE" # "IDLE", "RUNNING", "ATTACKING", "CASTING"
        self.anim_time = random.uniform(0, 3.14) # Ondeggiamento naturale
        self.lunge_offset_x = 0.0
        self.lunge_offset_y = 0.0
        self.lunge_timer = 0.0
        self.hit_flash_timer = 0.0
        self.rotation_angle = 0.0
        self.death_timer = 0.0
        self.death_alpha = 255
        self.is_dead = False
        
        self.damage_popup_texts = [] # Lista di (text, color, pos, timer) per i popup danno
        self.spell_animation_timer = 0 # Timer per le animazioni abilità
        
    @property
    def total_damage_dealt(self):
        return self.damage_dealt_physical + self.damage_dealt_magic
        
    def get_sprite_surface(self, width=80, height=80):
        """Restituisce lo sprite del personaggio a figura intera orientato e con eventuale hit-flash"""
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
        self.hp = max(0, self.hp - dmg)
        self.hit_flash_timer = 0.12 # Lampeggia di bianco all'impatto
        
    def equip_item(self, item_key):
        """
        Equipaggia un oggetto sul campione.
        Se entrambi sono componenti, li combina automaticamente in un oggetto completo.
        Ritorna ('combined'|'equipped'|'full', item_obj)
        """
        from items import get_item_data, combine_components
        new_data = get_item_data(item_key)
        
        # Se è un componente, controlla se c'è già un componente equipaggiato da combinare
        if new_data.get("is_component", False):
            for i, existing in enumerate(self.items):
                ex_data = get_item_data(existing)
                if ex_data.get("is_component", False):
                    # Combina i due componenti
                    comb = combine_components(existing, item_key)
                    if comb:
                        self.items[i] = comb["name"]
                        return "combined", comb
                        
        # Altrimenti aggiungi normalmente se c'è spazio (< 3 oggetti)
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

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

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
            
        # Calcola la direzione
        dir_x = self.target.x - self.x
        dir_y = self.target.y - self.y
        dist = math.sqrt(dir_x**2 + dir_y**2)
        
        if dist == 0: return # Già arrivato
            
        # Normalizza e muovi
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
        dmg = int(raw_dmg * (1.75 if crit else 1.0))
        
        target.take_damage(dmg)
        target.damage_taken += dmg
        self.damage_dealt_magic += dmg
        
        if was_alive and not target.is_alive():
            self.kills_count += 1
            # Titan's Might stack se presente
            if hasattr(self, 'base_attack') and hasattr(self, 'max_hp'):
                self.base_attack += 12
                self.max_hp += 100
                self.hp += 100
            
        # Vampirismo totale sulle spell
        if getattr(self, "lifesteal", 0.0) > 0:
            heal = max(1, int(dmg * self.lifesteal))
            self.hp = min(self.max_hp, self.hp + heal)
            self.healing_done += heal
            
        # Popup danno magico
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
        damage = self.base_attack * (2 if crit else 1) - getattr(target, 'base_defense', 0)
        damage = max(1, int(damage))
        
        target.take_damage(damage)
        target.damage_taken += damage
        self.damage_dealt_physical += damage

        # Aggiungi il popup del danno
        text_color = (255, 0, 0) if crit else (255, 255, 0) # Rosso per crit, Giallo per normale
        target.damage_popup_texts.append({
            "text": str(damage),
            "color": text_color,
            "pos": [target.x, target.y - 40], # Sopra la testa
            "timer": 1.0 # Dura 1 secondo
        })
        
        # Lifesteal / Vampirismo
        if getattr(self, "lifesteal", 0.0) > 0:
            heal_amount = max(1, int(damage * self.lifesteal))
            self.hp = min(self.max_hp, self.hp + heal_amount)
            self.healing_done += heal_amount

        # Guinsoo's Rageblade stacking (+4% Attack Speed per hit)
        if any("Guinsoo" in str(it) for it in getattr(self, "items", [])):
            self.attack_speed = min(3.0, self.attack_speed + 0.04)

        # Guadagna mana
        mana_gain = getattr(self, "mana_per_hit", 10)
        self.current_mana = min(self.mana_max, self.current_mana + mana_gain)
        
        # Riproduci SFX attacco
        try:
            from audio_manager import AudioManager
            sfx = "attack_ranged" if self.attack_range > 100 else "attack_melee"
            AudioManager.get_instance().play_sfx(sfx)
        except Exception:
            pass
            
        print(f"{self.name} attacca {target.name} per {damage} danni. (Mana: {self.current_mana})")
        if was_alive and not target.is_alive():
            self.kills_count += 1
            print(f"💀 {target.name} è stato sconfitto!\n")
            self.target = None # Cerca un nuovo bersaglio

    def cast_spell(self, enemy_team, friendly_team):
        """ Esegue l'abilità speciale! """
        print(f"✨✨✨ {self.name} USA L'ABILITÀ SPECIAL! ✨✨✨")
        self.is_casting = True
        self.spell_animation_timer = 1.0 # L'animazione dura 1 secondo
        
        try:
            from audio_manager import AudioManager
            AudioManager.get_instance().play_sfx("spell_cast")
        except Exception:
            pass
            
        sp_mult = getattr(self, "spell_power_mult", 1.0)
        spell_mult = (1.0 + (self.level - 1) * 0.75) * sp_mult

        if self.name == "Ahri":
            if self.target and self.target.is_alive():
                dmg = int(180 * spell_mult)
                print(f"Ahri lancia Sfera Mistica su {self.target.name} ({dmg} dmg)!")
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Garen":
            dmg = int(120 * spell_mult)
            print(f"Garen usa GIUDIZIO ({dmg} AoE dmg)!")
            for enemy in enemy_team:
                if enemy.is_alive() and self.get_distance(enemy) < 160: 
                    self.deal_magic_damage_to(enemy, dmg)

        elif self.name == "Vi":
            if self.target and self.target.is_alive():
                dmg = int(220 * spell_mult)
                print(f"Vi usa PUGNO AD IMPATTO su {self.target.name} ({dmg} dmg)!")
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Riven":
            dmg = int(160 * spell_mult)
            shield = int(150 * spell_mult)
            self.hp = min(self.max_hp, self.hp + shield)
            self.healing_done += shield
            print(f"Riven usa LAMA DELLO SCUDO! Si protegge ({shield} HP) e sferra {dmg} dmg!")
            if self.target and self.target.is_alive():
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Shen":
            shield = int(250 * spell_mult)
            self.hp = min(self.max_hp, self.hp + shield)
            self.healing_done += shield
            print(f"Shen attiva RIFUGIO SPIRITUALE (+{shield} HP Shield)!")

        elif self.name == "Ezreal":
            if self.target and self.target.is_alive():
                dmg = int(250 * spell_mult)
                print(f"Ezreal spara COLPO MISTICO su {self.target.name} ({dmg} dmg)!")
                self.deal_magic_damage_to(self.target, dmg)

        elif self.name == "Jinx":
            dmg = int(320 * spell_mult)
            print(f"Jinx lancia SUPER MEGA SUPER RAZZO DELLA MORTE ({dmg} AoE dmg)!")
            if self.target and self.target.is_alive():
                self.deal_magic_damage_to(self.target, dmg)
            for enemy in enemy_team:
                if enemy.is_alive() and enemy != self.target and self.get_distance(enemy) < 200:
                    self.deal_magic_damage_to(enemy, int(dmg * 0.5))

        elif self.name == "Aurelion":
            dmg = int(400 * spell_mult)
            print(f"Aurelion Sol scatena TEMPESTA STELLARE COSMICA ({dmg} dmg su TUTTI)!")
            for enemy in enemy_team:
                if enemy.is_alive():
                    self.deal_magic_damage_to(enemy, dmg)

        elif self.name == "Kayle":
            dmg = int(450 * spell_mult)
            heal = int(200 * spell_mult)
            self.hp = min(self.max_hp, self.hp + heal)
            self.healing_done += heal
            print(f"Kayle ASCENDE CON GIUDIZIO DIVINO ({dmg} dmg + {heal} heal)!")
            for enemy in enemy_team:
                if enemy.is_alive() and self.get_distance(enemy) < 250:
                    self.deal_magic_damage_to(enemy, dmg)
        
        # Fine abilità
        self.current_mana = 0
        self.is_casting = False

SPRITE_SIZE = (70, 70)
SPELL_EFFECT_SIZE = (50, 50)

def get_available_champions():
    """
    Restituisce una lista di campioni disponibili con TUTTE le stats.
    Range: 1 = Melee (50px), 3 = Ranged (300px), 5 = Long Ranged (500px)
    """
    # base_path = os.path.join("images")

    # Range in pixel reali
    R_MELEE = 80 
    R_RANGED = 300
    R_SNIPER = 500

    return [
        # Costo 1
        Champion("Garen", 650, 50, defense=10, crit_chance=0.1, 
                 mana_max=100, mana_start=0, attack_speed=0.6, attack_range=R_MELEE, cost=1,
                 traits=["Demacia", "Guardiano"]),
        Champion("Vi", 600, 60, defense=8, crit_chance=0.1, 
                 mana_max=80, mana_start=0, attack_speed=0.7, attack_range=R_MELEE, cost=1,
                 traits=["Piltover", "Combattente"]),
                 
        # Costo 2
        Champion("Ahri", 500, 40, defense=5, crit_chance=0.2, 
                 mana_max=70, mana_start=10, attack_speed=0.75, attack_range=R_RANGED, cost=2,
                 traits=["Ionia", "Mago"]),
        Champion("Riven", 550, 55, defense=8, crit_chance=0.15, 
                 mana_max=100, mana_start=0, attack_speed=0.7, attack_range=R_MELEE, cost=2,
                 traits=["Noxus", "Combattente"]),
                 
        # Costo 3
        Champion("Shen", 700, 45, defense=12, crit_chance=0.1, 
                 mana_max=100, mana_start=50, attack_speed=0.65, attack_range=R_MELEE, cost=3,
                 traits=["Ionia", "Guardiano"]),
        Champion("Ezreal", 500, 45, defense=4, crit_chance=0.25, 
                 mana_max=60, mana_start=0, attack_speed=0.8, attack_range=R_SNIPER, cost=3,
                 traits=["Piltover", "Cecchino"]),

        # Costo 4
        Champion("Aurelion", 700, 60, defense=5, crit_chance=0.2, 
                 mana_max=120, mana_start=40, attack_speed=0.65, attack_range=R_RANGED, cost=4,
                 traits=["Cosmico", "Mago"]),
        Champion("Jinx", 550, 70, defense=5, crit_chance=0.3, 
                 mana_max=80, mana_start=0, attack_speed=0.9, attack_range=R_SNIPER, cost=4,
                 traits=["Zaun", "Cecchino"]),

        # Costo 5
        Champion("Kayle", 800, 90, defense=10, crit_chance=0.3, 
                 mana_max=150, mana_start=50, attack_speed=1.0, attack_range=R_SNIPER, cost=5,
                 traits=["Demacia", "Divino"]),
    ]