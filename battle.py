# battle.py
import pygame
import random
import copy
import math

# Importiamo da config.py
from config import draw_text, TEXT_FONT, GREEN, RED, BLUE, BLACK, WHITE, GOLD

# Importiamo la classe Champion aggiornata
from champions import Champion, SPRITE_SIZE
from traits import calculate_team_traits, apply_trait_buffs, draw_traits_sidebar
from items import apply_item_stats, get_item_data, draw_item_icon, get_item_icon_surface
from asset_loader import get_background_image, draw_glass_panel, get_champion_sprite
from augments import draw_hud_augments
from damage_meter import DamageMeter
from battle_animations import (
    Particle, Projectile, SlashVFX, ShockwaveVFX, 
    LaserBeamVFX, SandSoldiersVFX, HookChainVFX
)

class BattleManager:
    """
    Gestisce la logica e il rendering della battaglia IN TEMPO REALE
    con sprite 2D animati, particelle, proiettili e VFX abilità.
    """
    def __init__(self, game, player_team_base, enemy_team_base, champions_database, opponent_name="Nemico"):
        self.game = game
        self.opponent_name = opponent_name
        self.champions_database = champions_database
        self.damage_meter = getattr(self.game, 'damage_meter', DamageMeter())
        self.battle_start_ticks = pygame.time.get_ticks()
        
        # Effetti Visivi e Animazioni
        self.particles = []
        self.projectiles = []
        self.slash_effects = []
        self.shockwaves = []
        self.custom_vfx = []
        self.screen_shake_timer = 0.0
        self.screen_shake_intensity = 0
        
        # --- Copia i Campioni ---
        self.player_team = self.create_battle_copies(player_team_base)
        self.enemy_team = self.create_battle_copies(enemy_team_base)
        
        # --- Raccogli Tratti Bonus da Augments ---
        bonus_traits = []
        player_augments = getattr(self.game, 'player_augments', [])
        if "demacia_crown" in player_augments:
            bonus_traits.append("Demacia")
        if "piltover_heart" in player_augments:
            bonus_traits.append("Piltover")
        if "ionia_soul" in player_augments:
            bonus_traits.append("Ionia")
        
        # --- Applica Sinergie (Buff Reali) ---
        self.player_traits = calculate_team_traits(self.player_team, bonus_traits=bonus_traits)
        apply_trait_buffs(self.player_team, self.player_traits)
        
        self.enemy_traits = calculate_team_traits(self.enemy_team)
        apply_trait_buffs(self.enemy_team, self.enemy_traits)
        
        # --- Applica Buff Augments ---
        self.apply_augment_buffs()
        
        self.all_champs = self.player_team + self.enemy_team

        # --- Posiziona i Campioni ---
        self.setup_board_positions()
        
        self.is_over = False
        self.winner = None
        self.clock = pygame.time.Clock()
        self.inspected_champion = None

    def apply_augment_buffs(self):
        augments = getattr(self.game, 'player_augments', [])
        if not augments:
            return
            
        for champ in self.player_team:
            if "cybernetic_implants" in augments and getattr(champ, 'items', []):
                champ.base_hp += 250
                champ.max_hp += 250
                champ.hp += 250
                champ.base_attack += 20
                
            if "living_armor" in augments:
                champ.base_defense = getattr(champ, 'base_defense', 0) + 30
                
            if "hextech_accelerator" in augments:
                champ.mana_start = min(champ.mana_max, champ.mana_start + 35)
                champ.current_mana = champ.mana_start
                
            if "aegis_light" in augments:
                champ.max_hp += 180
                champ.hp += 180
                
            if "long_shot" in augments and champ.attack_range > 1:
                champ.attack_range += 100
                champ.base_attack = int(champ.base_attack * 1.15)
                
            if "jeweled_lotus" in augments:
                champ.spell_crit = True
                champ.crit_chance = min(1.0, champ.crit_chance + 0.15)
                
            if "celestial_vampirism" in augments:
                champ.lifesteal = getattr(champ, 'lifesteal', 0.0) + 0.20
                
            if "demacia_crown" in augments and "Demacia" in getattr(champ, 'traits', []):
                champ.base_hp += 120
                champ.max_hp += 120
                champ.hp += 120
                
            if "piltover_heart" in augments:
                champ.attack_speed = float(champ.attack_speed * 1.15)
                
            if "ionia_soul" in augments and "Ionia" in getattr(champ, 'traits', []):
                champ.mana_start = min(champ.mana_max, champ.mana_start + 20)
                champ.current_mana = champ.mana_start

    # In battle.py, sostituisci l'intero metodo create_battle_copies (inizia circa alla riga 30)

    def create_battle_copies(self, base_team):
        """ 
        Crea copie da battaglia dei campioni.
        Questa funzione ORA FORZA i dati corretti presi dal database.
        """
        battle_team = []
        for c in base_team:
            
            # --- IL MARTELLO ---
            # Non ci fidiamo del campione 'c'. Cerchiamo il campione "vero"
            # nel nostro database per recuperare i dati che potrebbero mancare.
            
            # 1. Trova il "template" corretto dal database
            template = None
            for db_champ in self.champions_database:
                if db_champ.name == c.name:
                    template = db_champ
                    break
            
            if not template:
                print(f"!!! ERRORE GRAVE: Impossibile trovare {c.name} nel database !!!")
                continue # Salta questo campione

            # 2. Creiamo una NUOVA istanza Champion usando i dati del template
            #    e sovrascrivendo con i dati di 'c' (come HP, Livello)
            
            battle_copy = Champion(
                c.name,
                getattr(c, 'base_hp', template.base_hp), 
                getattr(c, 'base_attack', template.base_attack),
                getattr(c, 'base_defense', template.base_defense),
                template.crit_chance,
                template.mana_max,
                template.mana_start,
                template.attack_speed,
                template.attack_range,
                cost=getattr(c, 'cost', template.cost),
                traits=getattr(c, 'traits', template.traits),
                items=getattr(c, 'items', [])
            )

            # 3. Applica i modificatori di livello (se 'c' era Lvl 2+)
            battle_copy.level = getattr(c, 'level', 1)
            if battle_copy.level > 1:
                multiplier = 1.6 if battle_copy.level == 2 else 2.5
                battle_copy.base_hp = int(battle_copy.base_hp * multiplier)
                battle_copy.base_attack = int(battle_copy.base_attack * multiplier)
            
            # 4. Applica Statistiche Oggetti
            apply_item_stats(battle_copy)
            
            # 5. Finalizza le statistiche di battaglia
            battle_copy.max_hp = getattr(c, 'max_hp', battle_copy.base_hp) # Usa gli HP max se potenziati
            battle_copy.hp = battle_copy.max_hp # Full vita
            battle_copy.current_mana = battle_copy.mana_start
            battle_copy.board_index = getattr(c, 'board_index', 0)
            
            battle_team.append(battle_copy)
        return battle_team

    def setup_board_positions(self):
        """ Assegna le posizioni X, Y iniziali ai campioni su una griglia 7x4 """
        cell_w, cell_h = 100, 100
        offset_x, offset_y = 350, 250 # Centro dello schermo 1400x900
        
        for champ in self.player_team:
            idx = getattr(champ, 'board_index', 0)
            row = 2 + (idx // 7)
            col = idx % 7
            champ.x = offset_x + col * cell_w + cell_w // 2
            champ.y = offset_y + row * cell_h + cell_h // 2
                
        # Nemici random nelle prime due righe
        if self.enemy_team:
            enemy_slots = random.sample(range(14), min(14, len(self.enemy_team)))
            for i, champ in enumerate(self.enemy_team):
                idx = enemy_slots[i]
                row = idx // 7
                col = idx % 7
                champ.x = offset_x + col * cell_w + cell_w // 2
                champ.y = offset_y + row * cell_h + cell_h // 2

    def handle_event(self, event):
        self.damage_meter.handle_event(event)

    def update(self):
        """ Loop di update della battaglia, chiamato 60 volte al secondo """
        if self.is_over:
            return
            
        delta_time = self.clock.tick(60) / 1000.0
        if delta_time > 0.1: delta_time = 0.1

        # --- 1. AGGIORNAMENTO PARTICELLE, PROIETTILI E VFX ---
        for p in list(self.particles):
            p.update(delta_time)
            if p.life <= 0:
                self.particles.remove(p)

        for proj in list(self.projectiles):
            proj.update(delta_time, self.particles)
            if not proj.is_alive:
                self.projectiles.remove(proj)

        for slash in list(self.slash_effects):
            slash.update(delta_time)
            if not slash.is_alive:
                self.slash_effects.remove(slash)

        for wave in list(self.shockwaves):
            wave.update(delta_time)
            if not wave.is_alive:
                self.shockwaves.remove(wave)

        # --- 2. CICLO LOGICA CAMPIONI ---
        for champ in self.all_champs:
            # Recupero lunge offset
            if champ.lunge_timer > 0:
                champ.lunge_timer -= delta_time
                champ.lunge_offset_x *= 0.82
                champ.lunge_offset_y *= 0.82
            else:
                champ.lunge_offset_x = 0
                champ.lunge_offset_y = 0

            # Hit flash timer
            if champ.hit_flash_timer > 0:
                champ.hit_flash_timer -= delta_time

            # Gestione morte / dissolvenza
            if not champ.is_alive():
                if not champ.is_dead:
                    champ.is_dead = True
                    # Particelle sconfitta
                    for _ in range(12):
                        self.particles.append(Particle(champ.x, champ.y, random.uniform(-40, 40), random.uniform(-60, 10), (220, 200, 120), radius=random.randint(2, 5), max_life=0.6))
                if champ.death_alpha > 0:
                    champ.death_alpha = max(0, champ.death_alpha - int(450 * delta_time))
                    if random.random() < 0.25:
                        self.particles.append(Particle(champ.x + random.uniform(-15, 15), champ.y + random.uniform(-20, 10), random.uniform(-10, 10), random.uniform(-40, -10), (240, 210, 100), radius=2, max_life=0.5))
                continue

            # Rotazione speciale (Garen Giudizio)
                champ.death_timer += delta_time
                champ.death_alpha = max(0, int(255 * (1.0 - champ.death_timer / 0.8)))
                continue

            # Rotazione speciale
            if champ.name == "Garen" and champ.spell_animation_timer > 0:
                champ.rotation_angle = (champ.rotation_angle + 1080 * delta_time) % 360
            else:
                champ.rotation_angle = 0

            # 1. Ricerca Bersaglio
            if not champ.target or not champ.target.is_alive():
                if champ in self.player_team:
                    champ.find_closest_target(self.enemy_team)
                else:
                    champ.find_closest_target(self.player_team)
            
            if not champ.target:
                champ.anim_state = "IDLE"
                champ.anim_time += delta_time * 3
                continue

            # Direzione sguardo
            champ.facing_right = champ.target.x > champ.x
                
            # Timer abilità
            if champ.spell_animation_timer > 0:
                champ.spell_animation_timer -= delta_time

            # 2. Movimento o Attacco
            distance = champ.get_distance(champ.target)
            
            if distance > champ.attack_range:
                champ.anim_state = "RUNNING"
                champ.anim_time += delta_time * 14
                champ.move_towards_target(delta_time)
                # Polvere di corsa sotto i piedi
                if random.random() < 0.30:
                    self.particles.append(Particle(champ.x + random.uniform(-8, 8), champ.y + 24, random.uniform(-15, 15), random.uniform(-5, 0), (140, 150, 170), radius=3, max_life=0.25))
            else:
                champ.anim_state = "ATTACKING"
                champ.attack_timer += delta_time
                time_per_attack = 1.0 / champ.attack_speed
                
                if champ.attack_timer >= time_per_attack:
                    champ.attack_timer = 0
                    
                    # 3. Mossa Speciale o Attacco Base
                    if champ.current_mana >= champ.mana_max:
                        champ.cast_spell(self.enemy_team, self.player_team)
                        
                        # Generazione VFX Spettacolari
                        if champ.name == "Garen":
                            self.slash_effects.append(SlashVFX(champ.x, champ.y, radius=70, color=(255, 215, 50), duration=0.8))
                        elif champ.name == "Darius":
                            tx = champ.target.x if champ.target else champ.x
                            ty = champ.target.y if champ.target else champ.y
                            self.slash_effects.append(SlashVFX(tx, ty, radius=75, color=(240, 40, 40), duration=0.35))
                            self.shockwaves.append(ShockwaveVFX(tx, ty, max_radius=60, color=(220, 30, 30), duration=0.3))
                        elif champ.name == "Ashe":
                            if champ.target:
                                self.projectiles.append(Projectile(champ.x, champ.y - 12, champ.target, speed=600, proj_type="ICE_ARROW", color=(140, 230, 255)))
                        elif champ.name == "Ahri":
                            if champ.target:
                                self.projectiles.append(Projectile(champ.x, champ.y - 15, champ.target, speed=520, proj_type="ORB", color=(255, 120, 220)))
                        elif champ.name == "Vi":
                            tx = champ.target.x if champ.target else champ.x
                            ty = champ.target.y if champ.target else champ.y
                            self.shockwaves.append(ShockwaveVFX(tx, ty, max_radius=85, color=(100, 220, 255), duration=0.45))
                            for _ in range(16):
                                self.particles.append(Particle(tx, ty, random.uniform(-120, 120), random.uniform(-120, 120), (255, 210, 80), radius=4, max_life=0.4))
                        elif champ.name == "Zed":
                            tx = champ.target.x if champ.target else champ.x
                            ty = champ.target.y if champ.target else champ.y
                            self.slash_effects.append(SlashVFX(tx, ty, radius=60, color=(200, 30, 50), duration=0.25))
                            self.shockwaves.append(ShockwaveVFX(champ.x, champ.y, max_radius=50, color=(50, 20, 40), duration=0.3))
                        elif champ.name == "Braum":
                            self.shockwaves.append(ShockwaveVFX(champ.x, champ.y, max_radius=75, color=(140, 225, 255), duration=0.6))
                        elif champ.name == "Ezreal":
                            if champ.target:
                                self.projectiles.append(Projectile(champ.x, champ.y - 15, champ.target, speed=680, proj_type="BASIC", color=(255, 235, 70)))
                        elif champ.name == "Jinx":
                            if champ.target:
                                self.projectiles.append(Projectile(champ.x, champ.y - 20, champ.target, speed=480, proj_type="ROCKET", color=(255, 70, 70)))
                        elif champ.name == "Riven":
                            tx = champ.target.x if champ.target else champ.x
                            ty = champ.target.y if champ.target else champ.y
                            self.slash_effects.append(SlashVFX(tx, ty, radius=65, color=(60, 240, 130), duration=0.4))
                        elif champ.name == "Katarina":
                            for _ in range(3):
                                self.slash_effects.append(SlashVFX(champ.x + random.uniform(-30, 30), champ.y + random.uniform(-30, 30), radius=55, color=(240, 50, 70), duration=0.3))
                        elif champ.name == "Yasuo":
                            if champ.target:
                                self.projectiles.append(Projectile(champ.x, champ.y - 15, champ.target, speed=550, proj_type="TORNADO", color=(180, 230, 255)))
                        elif champ.name == "Shen":
                            self.shockwaves.append(ShockwaveVFX(champ.x, champ.y, max_radius=70, color=(80, 220, 255), duration=0.7))
                        elif champ.name == "Kayle":
                            for enemy in self.enemy_team:
                                if enemy.is_alive():
                                    self.projectiles.append(Projectile(enemy.x, enemy.y - 250, enemy, speed=700, proj_type="DIVINE_SWORD", color=(255, 235, 90)))
                        elif champ.name == "Lux":
                            tx = (champ.target.x + 800) if (champ.target and champ.target.x > champ.x) else (champ.x + 800 if champ.facing_right else champ.x - 800)
                            ty = champ.target.y if champ.target else champ.y
                            self.custom_vfx.append(LaserBeamVFX(champ.x, champ.y - 10, tx, ty, color=(255, 245, 120), duration=0.45))
                        elif champ.name == "Sejuani":
                            self.shockwaves.append(ShockwaveVFX(champ.x, champ.y, max_radius=130, color=(120, 220, 255), duration=0.6))
                        elif champ.name == "Aurelion":
                            for enemy in self.enemy_team:
                                if enemy.is_alive():
                                    self.projectiles.append(Projectile(enemy.x + random.uniform(-30, 30), enemy.y - 280, enemy, speed=600, proj_type="METEOR", color=(140, 80, 255)))
                        elif champ.name == "Azir":
                            tx = champ.target.x if champ.target else champ.x + 300
                            ty = champ.target.y if champ.target else champ.y
                            self.custom_vfx.append(SandSoldiersVFX(champ.x, champ.y, tx, ty, duration=0.55))
                        elif champ.name == "Thresh":
                            tx = champ.target.x if champ.target else champ.x + 250
                            ty = champ.target.y if champ.target else champ.y
                            self.custom_vfx.append(HookChainVFX(champ.x, champ.y, tx, ty, duration=0.45))
                    else:
                        # Attacco Base con Scatto Melee o Proiettile Ranged
                        champ.basic_attack(champ.target)
                        
                        if champ.attack_range > 100:
                            # Ranged Projectile
                            proj_col = (255, 225, 70) if champ.name == "Ezreal" else ((255, 120, 220) if champ.name == "Ahri" else ((140, 230, 255) if champ.name in ["Ashe", "Lux"] else (180, 220, 255)))
                            self.projectiles.append(Projectile(champ.x, champ.y - 12, champ.target, speed=540, proj_type="BASIC", color=proj_col))
                        else:
                            # Melee Lunge & Slash Arc
                            if champ.target:
                                dx = champ.target.x - champ.x
                                dy = champ.target.y - champ.y
                                d = math.sqrt(dx**2 + dy**2) or 1.0
                                champ.lunge_offset_x = (dx / d) * 22
                                champ.lunge_offset_y = (dy / d) * 22
                                champ.lunge_timer = 0.2
                                
                                slash_col = (255, 220, 100) if champ in self.player_team else (240, 80, 80)
                                self.slash_effects.append(SlashVFX(champ.target.x, champ.target.y, radius=36, color=slash_col, duration=0.2))
                                for _ in range(6):
                                    self.particles.append(Particle(champ.target.x, champ.target.y, random.uniform(-60, 60), random.uniform(-60, 60), slash_col, radius=3, max_life=0.3))
        
        # --- 3. CONTROLLO FINE BATTAGLIA ---
        if not any(c.is_alive() for c in self.enemy_team):
            self.is_over = True
            self.winner = "player"
        elif not any(c.is_alive() for c in self.player_team):
            self.is_over = True
            self.winner = "enemy"

    def draw_hp_bar(self, surface, champ, cx, cy):
        """ Disegna la barra HP e Mana sopra il personaggio """
        BAR_WIDTH = 48
        BAR_HEIGHT = 6
        
        y = cy - 48 
        x = cx - BAR_WIDTH // 2
        
        # Sfondo nero bordo
        pygame.draw.rect(surface, (0, 0, 0), (x - 1, y - 1, BAR_WIDTH + 2, BAR_HEIGHT + 2), border_radius=3)
        
        # HP
        ratio = champ.hp / max(1, champ.max_hp)
        pygame.draw.rect(surface, (120, 0, 0), (x, y, BAR_WIDTH, BAR_HEIGHT), border_radius=3)
        hp_color = (0, 210, 60) if champ in self.player_team else (220, 50, 50)
        pygame.draw.rect(surface, hp_color, (x, y, max(0, int(BAR_WIDTH * ratio)), BAR_HEIGHT), border_radius=3)

        # MANA
        mana_y = y + BAR_HEIGHT + 2
        if champ.mana_max > 0:
            mana_ratio = champ.current_mana / max(1, champ.mana_max)
            pygame.draw.rect(surface, (0, 0, 0), (x - 1, mana_y - 1, BAR_WIDTH + 2, BAR_HEIGHT + 2), border_radius=3)
            pygame.draw.rect(surface, (30, 35, 50), (x, mana_y, BAR_WIDTH, BAR_HEIGHT), border_radius=3)
            pygame.draw.rect(surface, (0, 160, 255), (x, mana_y, max(0, int(BAR_WIDTH * mana_ratio)), BAR_HEIGHT), border_radius=3)

    def draw(self, surface):
        """ Disegna l'intera battaglia con grafica e personaggi 2D animati """
        # 1. Sfondo Arena AI
        bg_surf = get_background_image("board_bg", surface.get_width(), surface.get_height())
        surface.blit(bg_surf, (0, 0))
        
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 145))
        surface.blit(overlay, (0, 0))
        
        # 2. Header Battaglia Glassmorphism
        head_rect = pygame.Rect(surface.get_width() // 2 - 250, 16, 500, 44)
        draw_glass_panel(surface, head_rect, border_radius=22, bg_color=(14, 18, 28, 220), border_color=(230, 190, 70, 180), border_width=1)
        head_font = pygame.font.SysFont("Arial", 15, bold=True)
        draw_text(f"VS {self.opponent_name.upper()} • SCONTRO IN CORSO", head_font, GOLD, surface, head_rect.centerx, head_rect.centery)
        
        # 3. Sidebar Sinergie a sinistra & Classifica a destra & Damage Meter
        mouse_pos = pygame.mouse.get_pos()
        draw_hud_augments(surface, mouse_pos, getattr(self.game, 'player_augments', []), start_x=12, start_y=30)
        traits_count = len(getattr(self, "player_traits", []))
        meter_y = max(390, 75 + traits_count * 44 + 36)
        elapsed_sec = max(0.5, (pygame.time.get_ticks() - self.battle_start_ticks) / 1000.0)
        self.damage_meter.draw(surface, mouse_pos, self.player_team, elapsed_seconds=elapsed_sec, start_x=12, start_y=meter_y)
        
        if hasattr(self.game, 'lobby_manager'):
            self.game.lobby_manager.draw_leaderboard_sidebar(surface, mouse_pos, start_x=1230, start_y=75)
        
        # 4. Campo di battaglia a griglia curva (7x4)
        cell_w, cell_h = 100, 100
        offset_x, offset_y = 350, 230
        cols, rows = 7, 4
        
        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(offset_x + c * cell_w, offset_y + r * cell_h, cell_w, cell_h)
                cell_surf = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                
                if r >= 2:
                    pygame.draw.rect(cell_surf, (18, 38, 26, 210), (2, 2, cell_w - 4, cell_h - 4), border_radius=12) # Lato Player
                    pygame.draw.rect(cell_surf, (45, 160, 80, 140), (2, 2, cell_w - 4, cell_h - 4), width=1, border_radius=12)
                else:
                    pygame.draw.rect(cell_surf, (38, 18, 20, 210), (2, 2, cell_w - 4, cell_h - 4), border_radius=12) # Lato Enemy
                    pygame.draw.rect(cell_surf, (200, 60, 60, 140), (2, 2, cell_w - 4, cell_h - 4), width=1, border_radius=12)
                    
                surface.blit(cell_surf, (rect.x, rect.y))

        # 5. Disegna Onde d'Urto al Suolo
        for wave in self.shockwaves:
            wave.draw(surface)

        # --- 6. DISEGNA I CAMPIONI (VERI PERSONAGGI 2D ANIMATI) ---
        # Ordina per Y in modo che i campioni in primo piano coprano quelli dietro
        render_order = sorted(self.all_champs, key=lambda c: c.y)
        
        for champ in render_order:
            if champ.is_alive() or getattr(champ, 'death_alpha', 0) > 0:
                # Calcola ondeggiamento e offset
                bob_y = math.sin(champ.anim_time) * 4 if getattr(champ, 'anim_state', 'IDLE') == "RUNNING" else math.sin(champ.anim_time) * 1.5
                cx = int(champ.x + champ.lunge_offset_x)
                cy = int(champ.y + champ.lunge_offset_y + bob_y)

                # Ombra realistica al suolo
                shadow_alpha = min(160, getattr(champ, 'death_alpha', 255))
                shadow_surf = pygame.Surface((64, 20), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (5, 8, 14, shadow_alpha), (0, 0, 64, 20))
                surface.blit(shadow_surf, (cx - 32, int(champ.y) + 24))

                # Anello Aura Squadra al Suolo (Verde Player / Rosso Nemico)
                team_col = (40, 220, 80, 140) if champ in self.player_team else (230, 50, 50, 140)
                halo_surf = pygame.Surface((56, 18), pygame.SRCALPHA)
                pygame.draw.ellipse(halo_surf, team_col, (0, 0, 56, 18), width=2)
                surface.blit(halo_surf, (cx - 28, int(champ.y) + 25))

                # SPRITE DEL PERSONAGGIO 2D
                sprite_surf = champ.get_sprite_surface(width=86, height=86)
                
                # Rotazione (se attiva)
                if getattr(champ, 'rotation_angle', 0) != 0:
                    sprite_surf = pygame.transform.rotate(sprite_surf, champ.rotation_angle)
                    
                # Trasparenza Morte
                if getattr(champ, 'death_alpha', 255) < 255:
                    sprite_surf = sprite_surf.copy()
                    sprite_surf.set_alpha(champ.death_alpha)

                surface.blit(sprite_surf, (cx - sprite_surf.get_width() // 2, cy - sprite_surf.get_height() // 2))
                
                if champ.is_alive():
                    # Indicatore Stelle (★)
                    stars = getattr(champ, 'level', 1)
                    if stars >= 2:
                        for s in range(min(stars, 3)):
                            sx = cx - (stars - 1) * 7 + s * 14
                            sy = cy - 58
                            pygame.draw.circle(surface, GOLD, (sx, sy), 4)
                            pygame.draw.circle(surface, (0, 0, 0), (sx, sy), 4, width=1)

                    # Barre HP e Mana
                    self.draw_hp_bar(surface, champ, cx, cy)

                    # Badge Oggetti Equipaggiati (Icone Grafiche)
                    champ_items = getattr(champ, "items", [])
                    if champ_items:
                        for idx, itm in enumerate(champ_items[:3]):
                            it_x = cx - 18 + idx * 18
                            it_y = cy + 28
                            it_box = pygame.Rect(it_x - 8, it_y - 8, 16, 16)
                            draw_item_icon(surface, itm, it_box)

        # 7. Disegna Fendenti e Archi d'Attacco
        for slash in self.slash_effects:
            slash.draw(surface)

        # 8. Disegna Proiettili in Volo
        for proj in self.projectiles:
            proj.draw(surface)

        # 9. Disegna Particelle VFX
        for p in self.particles:
            p.draw(surface)

        # 10. Disegna Custom VFX (Laser Lux, Soldati Azir, Catene Thresh)
        for vfx in self.custom_vfx:
            vfx.draw(surface)

        # 11. Disegna Popup Danno con Ombreggiatura
        for champ in self.all_champs:
            for popup in list(champ.damage_popup_texts): 
                shadow = TEXT_FONT.render(popup["text"], True, (0, 0, 0))
                text_obj = TEXT_FONT.render(popup["text"], True, popup["color"])
                
                popup["pos"][1] -= 0.6 
                
                shadow_rect = shadow.get_rect(center=(int(popup["pos"][0]) + 2, int(popup["pos"][1]) + 2))
                popup_rect = text_obj.get_rect(center=(int(popup["pos"][0]), int(popup["pos"][1])))
                
                surface.blit(shadow, shadow_rect)
                surface.blit(text_obj, popup_rect)
                
                popup["timer"] -= self.clock.get_time() / 1000.0
                if popup["timer"] <= 0:
                    champ.damage_popup_texts.remove(popup)

        # 12. Scheda Dettaglio / Ispettore Campione (se attivo)
        if self.inspected_champion and hasattr(self.game, 'shop_manager'):
            self.game.shop_manager.draw_champion_inspector(surface, self.inspected_champion)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.inspected_champion:
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_SPACE]:
                self.inspected_champion = None
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                sm = getattr(self.game, 'shop_manager', None)
                if sm:
                    if sm.inspector_close_rect.collidepoint(mouse_pos) or not sm.inspector_rect.collidepoint(mouse_pos):
                        self.inspected_champion = None
                        return
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                sm = getattr(self.game, 'shop_manager', None)
                if sm and not sm.inspector_rect.collidepoint(mouse_pos):
                    self.inspected_champion = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # Click destro su un campione in combattimento per ispezionarlo
            for champ in self.all_champs:
                if champ.is_alive():
                    dist = ((champ.x - mouse_pos[0]) ** 2 + (champ.y - mouse_pos[1]) ** 2) ** 0.5
                    if dist <= 42:
                        self.inspected_champion = champ
                        return