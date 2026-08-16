# carousel.py
import math
import random
import pygame
from config import draw_text, draw_star, GOLD, WHITE, BLACK, BLUE, LIGHT_BLUE, RED, GREEN, GRAY, WIDTH, HEIGHT
from items import get_random_component_key, get_item_data, draw_item_icon, get_item_icon_surface
from asset_loader import get_background_image, draw_glass_panel, get_champion_sprite
from battle_animations import Particle

class CarouselChampion:
    """
    Rappresenta un campione che ruota nell'anello centrale del carosello
    trasportando un componente di oggetto sopra la testa.
    """
    def __init__(self, champion_template, item_key, initial_angle, orbit_radius=200):
        self.champion = champion_template.copy()
        self.item_key = item_key
        self.item_data = get_item_data(item_key)
        self.angle = float(initial_angle)
        self.orbit_radius = float(orbit_radius)
        self.x = 0.0
        self.y = 0.0
        self.is_claimed = False
        self.claimed_by = None
        self.item_float_timer = random.uniform(0, 3.14)
        self.hitbox_radius = 34

    @property
    def claimed(self):
        return self.is_claimed

    @claimed.setter
    def claimed(self, val):
        self.is_claimed = val

    def update(self, dt, center_x=None, center_y=None, rotation_speed=None):
        if self.is_claimed:
            return
        speed = rotation_speed if rotation_speed is not None else 0.35
        self.angle += speed * dt
        if center_x is not None and center_y is not None:
            self.x = center_x + math.cos(self.angle) * self.orbit_radius
            self.y = center_y + math.sin(self.angle) * self.orbit_radius
        self.item_float_timer += dt * 3.5

    def draw(self, surface, center_x=None, center_y=None):
        if self.is_claimed:
            return

        if center_x is not None and center_y is not None:
            cx = center_x + math.cos(self.angle) * self.orbit_radius
            cy = center_y + math.sin(self.angle) * self.orbit_radius
            self.x = cx
            self.y = cy
        else:
            cx, cy = int(self.x), int(self.y)

        # 1. Ombra ed Halo sul terreno
        shadow_surf = pygame.Surface((60, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (5, 8, 14, 160), (0, 0, 60, 20))
        surface.blit(shadow_surf, (cx - 30, cy + 18))

        # 2. Halo Sottostante del Tier
        tier_col = getattr(self.champion, 'tier_color', (160, 160, 160))
        halo_surf = pygame.Surface((64, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(halo_surf, (*tier_col[:3], 180), (0, 0, 64, 22), width=2)
        surface.blit(halo_surf, (cx - 32, cy + 17))

        # 3. Sprite 2D del Personaggio
        facing_right = math.cos(self.angle + math.pi / 2) >= 0
        sprite = get_champion_sprite(self.champion.name, width=76, height=76, flip_x=not facing_right)
        surface.blit(sprite, (cx - 38, cy - 38))

        # 4. Nome e Costo
        name_font = pygame.font.SysFont("Arial", 11, bold=True)
        draw_text(self.champion.name, name_font, (0, 0, 0), surface, cx + 1, cy + 29)
        draw_text(self.champion.name, name_font, WHITE, surface, cx, cy + 28)

        # 5. Componente Oggetto Fluttuante con Halo Pulsante
        float_offset_y = math.sin(self.item_float_timer) * 5.0
        item_y = cy - 48 + float_offset_y
        
        # Halo pulsante dell'oggetto
        item_col = self.item_data.get("color", (240, 200, 50))
        item_halo = pygame.Surface((44, 44), pygame.SRCALPHA)
        pulse_alpha = int(120 + math.sin(self.item_float_timer * 2) * 50)
        pygame.draw.circle(item_halo, (*item_col[:3], pulse_alpha), (22, 22), 18)
        surface.blit(item_halo, (cx - 22, int(item_y - 22)))

        # Icona Grafica Reale dell'Oggetto
        item_box = pygame.Rect(cx - 14, int(item_y - 14), 28, 28)
        draw_item_icon(surface, self.item_key, item_box)


class CarouselAvatar:
    """
    Rappresenta l'avatar del giocatore (Little Legend) o di un bot
    che corre nell'arena per scegliere un campione.
    """
    def __init__(self, name, is_human, initial_angle, barrier_radius=320, color=(60, 210, 255)):
        self.name = name
        self.is_human = is_human
        self.angle = initial_angle
        self.barrier_radius = barrier_radius
        self.color = color
        
        # Posizione iniziale sulla barriera
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        
        self.is_locked = True
        self.unlock_time = 0.0
        self.claimed_champ = None
        self.speed = 280.0 if is_human else 220.0
        self.anim_time = random.uniform(0, 3.14)
        self.facing_right = True
        self.target_carousel_champ = None # Per i bot AI

    def set_initial_pos(self, center_x, center_y):
        self.x = center_x + math.cos(self.angle) * self.barrier_radius
        self.y = center_y + math.sin(self.angle) * self.barrier_radius
        self.target_x = self.x
        self.target_y = self.y

    def update(self, dt, particles_list):
        self.anim_time += dt * 8.0
        
        # Movimento verso il target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 4:
            self.facing_right = dx > 0
            step = self.speed * dt
            if dist <= step:
                self.x = self.target_x
                self.y = self.target_y
            else:
                self.x += (dx / dist) * step
                self.y += (dy / dist) * step
                
            # Particelle scia / polvere di corsa
            if random.random() < 0.35:
                p_col = (100, 220, 255) if self.is_human else (180, 190, 210)
                particles_list.append(Particle(
                    self.x + random.uniform(-6, 6),
                    self.y + 16,
                    random.uniform(-10, 10),
                    random.uniform(-10, 5),
                    p_col,
                    radius=random.randint(2, 4),
                    max_life=0.35
                ))

    def draw(self, surface, center_x, center_y):
        cx, cy = int(self.x), int(self.y)
        
        # 1. Barriera traslucida se ancora bloccato
        if self.is_locked:
            bx = center_x + math.cos(self.angle) * self.barrier_radius
            by = center_y + math.sin(self.angle) * self.barrier_radius
            
            barrier_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(barrier_surf, (40, 60, 90, 140), (32, 32), 26)
            pygame.draw.circle(barrier_surf, (100, 180, 255, 200), (32, 32), 26, width=2)
            surface.blit(barrier_surf, (int(bx - 32), int(by - 32)))
            
            # Catenaccio / icona lucchetto
            draw_text("🔒", pygame.font.SysFont("Segoe UI Emoji", 14), WHITE, surface, int(bx), int(by) - 18)

        # 2. Ombra al suolo dell'avatar
        shadow_surf = pygame.Surface((44, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (5, 8, 14, 160), (0, 0, 44, 14))
        surface.blit(shadow_surf, (cx - 22, cy + 14))

        # 3. Aura e Corpo dell'Avatar (Little Legend o Bot)
        bob_y = math.sin(self.anim_time) * 3.0
        ay = cy + bob_y
        
        # Bagliore / Aura
        aura_surf = pygame.Surface((52, 52), pygame.SRCALPHA)
        aura_col = (*self.color[:3], 100 if self.is_human else 50)
        pygame.draw.circle(aura_surf, aura_col, (26, 26), 22)
        surface.blit(aura_surf, (cx - 26, int(ay - 26)))

        # Corpo Little Legend
        body_rect = pygame.Rect(cx - 16, int(ay - 20), 32, 36)
        main_col = (40, 180, 255) if self.is_human else self.color
        pygame.draw.rect(surface, main_col, body_rect, border_radius=14)
        pygame.draw.rect(surface, WHITE if self.is_human else (210, 220, 235), body_rect, width=2, border_radius=14)

        # Visore / Faccina
        eye_x = cx + (4 if self.facing_right else -4)
        eye_y = int(ay - 8)
        pygame.draw.circle(surface, (12, 16, 26), (eye_x, eye_y), 4)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x + (1 if self.facing_right else -1), eye_y - 1), 2)

        # 4. Nome / Target sopra la testa
        label_text = "TU (Giocatore)" if self.is_human else self.name
        label_col = (80, 240, 255) if self.is_human else (215, 225, 240)
        draw_text(label_text, pygame.font.SysFont("Arial", 11, bold=True), (0, 0, 0), surface, cx + 1, int(ay - 31))
        draw_text(label_text, pygame.font.SysFont("Arial", 11, bold=True), label_col, surface, cx, int(ay - 32))


class CarouselManager:
    """
    Gestisce l'intera logica, rendering a 60 FPS, collisioni, countdown,
    sblocco a scaglioni e transizione nello Shop della Shared Draft Phase.
    """
    def __init__(self, game, round_number=1):
        self.game = game
        self.round_number = round_number
        self.center_x = WIDTH // 2
        self.center_y = HEIGHT // 2 + 25
        self.carousel_radius = 210.0
        self.barrier_radius = 330.0
        self.rotation_speed = 0.38 # Radianti al secondo
        
        self.particles = []
        self.is_completed = False
        self.completion_timer = 0.0
        self.countdown = 3.0 # Conto alla rovescia iniziale di 3 secondi
        self.elapsed_time = 0.0
        self.total_timeout = 24.0 # Durata massima del carosello
        
        # 1. Popola i Campioni del Carosello con Oggetti
        self.carousel_champs = self._generate_carousel_pool()
        
        # 2. Crea gli Avatar (1 Umano + 7 Bot)
        self.avatars = self._create_avatars()
        
        # 3. Calcola i tempi di sblocco (meccanica comeback TFT)
        self._calculate_unlock_schedule()

    def _generate_carousel_pool(self):
        """Genera 8 campioni bilanciati in base al round del carosello con 8 componenti casuali"""
        pool = []
        db = self.game.champions_database
        
        # Filtra i campioni per costo in base al round
        if self.round_number <= 2:
            allowed_champs = [c for c in db if c.cost in [1, 2]]
        elif self.round_number <= 5:
            allowed_champs = [c for c in db if c.cost in [2, 3, 4]]
        else:
            allowed_champs = [c for c in db if c.cost in [3, 4, 5]]
            
        if not allowed_champs:
            allowed_champs = db

        num_slots = 8
        step_angle = (2.0 * math.pi) / num_slots
        
        for i in range(num_slots):
            champ_template = random.choice(allowed_champs)
            item_key = get_random_component_key()
            angle = i * step_angle
            c_champ = CarouselChampion(champ_template, item_key, angle, orbit_radius=self.carousel_radius)
            c_champ.update(0, self.center_x, self.center_y, 0)
            pool.append(c_champ)
            
        return pool

    def _create_avatars(self):
        avatars = []
        num_players = 8
        step_angle = (2.0 * math.pi) / num_players
        
        # 1. Giocatore umano
        human = CarouselAvatar("Tu", is_human=True, initial_angle=step_angle * 0, barrier_radius=self.barrier_radius, color=(60, 220, 255))
        human.set_initial_pos(self.center_x, self.center_y)
        avatars.append(human)
        
        # 2. I 7 Bot della lobby
        bots = getattr(self.game.lobby_manager, 'bots', [])
        for i in range(7):
            b_name = bots[i].name if i < len(bots) else f"Bot_{i+1}"
            b_col = bots[i].color if i < len(bots) else (200, 150, 80)
            angle = step_angle * (i + 1)
            bot_avatar = CarouselAvatar(b_name, is_human=False, initial_angle=angle, barrier_radius=self.barrier_radius, color=b_col)
            bot_avatar.set_initial_pos(self.center_x, self.center_y)
            avatars.append(bot_avatar)
            
        return avatars

    def _calculate_unlock_schedule(self):
        """
        Calcola i secondi in cui ogni avatar viene sbloccato.
        Al Round 1: tutti contemporaneamente a countdown == 0.
        Nei Round successivi: i giocatori con meno HP vengono sbloccati per primi (a coppie ogni 2.5s).
        """
        if self.round_number == 1:
            for av in self.avatars:
                av.unlock_time = 0.0
        else:
            # Ordina per HP crescente (chi ha meno HP viene sbloccato prima)
            player_hp_list = []
            player_hp_list.append((self.avatars[0], self.game.player_hp))
            
            bots = getattr(self.game.lobby_manager, 'bots', [])
            for i, av in enumerate(self.avatars[1:]):
                hp = bots[i].hp if i < len(bots) else 100
                player_hp_list.append((av, hp))
                
            player_hp_list.sort(key=lambda x: x[1]) # HP crescente
            
            # Sblocca a coppie di 2 ogni 2.5 secondi
            for idx, (av, _) in enumerate(player_hp_list):
                batch_index = idx // 2
                av.unlock_time = batch_index * 2.5

    def handle_event(self, event):
        """Gestisce il movimento della Little Legend del giocatore"""
        human = self.avatars[0]
        
        if event.type == pygame.MOUSEBUTTONDOWN and (event.button == 1 or event.button == 3):
            if not human.is_locked and not human.claimed_champ:
                mouse_pos = event.pos
                human.target_x = float(mouse_pos[0])
                human.target_y = float(mouse_pos[1])
                
                # Particella click a terra
                for _ in range(8):
                    ang = random.uniform(0, math.pi * 2)
                    spd = random.uniform(30, 80)
                    self.particles.append(Particle(
                        mouse_pos[0], mouse_pos[1],
                        math.cos(ang) * spd, math.sin(ang) * spd,
                        (80, 220, 255), radius=3, max_life=0.3
                    ))

    def update(self):
        """Update principale a 60 FPS"""
        raw_dt = self.game.clock.get_time() / 1000.0
        dt = raw_dt if raw_dt > 0.001 else (1.0 / 60.0)
        dt = min(0.05, dt)
        self.elapsed_time += dt

        # 1. Countdown iniziale
        if self.countdown > 0:
            self.countdown -= dt
            if self.countdown <= 0:
                self.countdown = 0
                if hasattr(self.game, 'audio'):
                    self.game.audio.play_sfx("level_up")

        # 2. Sblocco barriere in base al tempo trascorso
        time_since_start = max(0.0, self.elapsed_time - 3.0)
        for av in self.avatars:
            if av.is_locked and time_since_start >= av.unlock_time and self.countdown <= 0:
                av.is_locked = False
                # Particelle apertura barriera
                bx = self.center_x + math.cos(av.angle) * self.barrier_radius
                by = self.center_y + math.sin(av.angle) * self.barrier_radius
                for _ in range(14):
                    ang = random.uniform(0, math.pi * 2)
                    spd = random.uniform(40, 120)
                    self.particles.append(Particle(
                        bx, by, math.cos(ang) * spd, math.sin(ang) * spd,
                        (120, 220, 255), radius=4, max_life=0.45
                    ))

        # 3. Aggiorna rotazione campioni del carosello
        for c_champ in self.carousel_champs:
            c_champ.update(dt, self.center_x, self.center_y, self.rotation_speed)

        # 4. Aggiorna e muovi gli Avatar (Player & Bot)
        human = self.avatars[0]
        
        # Supporto tastiera WASD / Frecce per il giocatore
        if not human.is_locked and not human.claimed_champ:
            keys = pygame.key.get_pressed()
            move_x = 0
            move_y = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]: move_y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: move_y += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: move_x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move_x += 1
            
            if move_x != 0 or move_y != 0:
                human.target_x = human.x + move_x * 40
                human.target_y = human.y + move_y * 40

        # AI dei Bot: cercano il campione/oggetto più vicino disponibile
        for bot in self.avatars[1:]:
            if not bot.is_locked and not bot.claimed_champ:
                available_champs = [c for c in self.carousel_champs if not c.is_claimed]
                if available_champs:
                    # Se il bersaglio precedente è stato preso, ricalcola verso il più vicino
                    if not bot.target_carousel_champ or bot.target_carousel_champ.is_claimed:
                        bot.target_carousel_champ = min(
                            available_champs,
                            key=lambda c: math.sqrt((c.x - bot.x)**2 + (c.y - bot.y)**2)
                        )
                    
                    if bot.target_carousel_champ:
                        bot.target_x = bot.target_carousel_champ.x
                        bot.target_y = bot.target_carousel_champ.y

        for av in self.avatars:
            av.update(dt, self.particles)

        # 5. Collisioni e Ritiro Campione (Claim)
        for av in self.avatars:
            if not av.is_locked and not av.claimed_champ:
                for c_champ in self.carousel_champs:
                    if not c_champ.is_claimed:
                        dist = math.sqrt((av.x - c_champ.x)**2 + (av.y - c_champ.y)**2)
                        if dist < (c_champ.hitbox_radius + 20):
                            self._claim_champion(av, c_champ)
                            break

        # 6. Particelle
        for p in list(self.particles):
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)

        # 7. Controllo Fine Carosello
        all_claimed = all(c.is_claimed for c in self.carousel_champs) or all(av.claimed_champ is not None for av in self.avatars)
        if all_claimed or self.elapsed_time >= self.total_timeout:
            # Se il giocatore non ha preso niente (timeout), assegnagli il primo disponibile
            if not human.claimed_champ:
                remaining = [c for c in self.carousel_champs if not c.is_claimed]
                if remaining:
                    self._claim_champion(human, remaining[0])
            
            self.completion_timer += dt
            if self.completion_timer >= 1.5:
                self.finish_carousel()

    def _claim_champion(self, avatar, carousel_champ):
        """Assegna il campione ed il suo oggetto all'avatar che lo tocca"""
        carousel_champ.is_claimed = True
        carousel_champ.claimed_by = avatar
        avatar.claimed_champ = carousel_champ
        
        # Effetto visivo di raccolta scintillante
        for _ in range(22):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(60, 200)
            self.particles.append(Particle(
                carousel_champ.x, carousel_champ.y,
                math.cos(ang) * spd, math.sin(ang) * spd,
                GOLD if avatar.is_human else (100, 200, 255),
                radius=random.randint(3, 6),
                max_life=0.55
            ))
            
        if avatar.is_human:
            if hasattr(self.game, 'audio'):
                self.game.audio.play_sfx("merge_star")
            print(f"🎠 CAROSELLO: Hai scelto {carousel_champ.champion.name} con {carousel_champ.item_data['name']}!")
            # Porta l'avatar verso il bordo per festeggiare
            avatar.target_x = self.center_x + math.cos(avatar.angle) * (self.barrier_radius + 40)
            avatar.target_y = self.center_y + math.sin(avatar.angle) * (self.barrier_radius + 40)
        else:
            # Allontana il bot verso il suo spawn
            avatar.target_x = self.center_x + math.cos(avatar.angle) * (self.barrier_radius + 30)
            avatar.target_y = self.center_y + math.sin(avatar.angle) * (self.barrier_radius + 30)

    def finish_carousel(self):
        """
        Finalizza il Carosello: trasferisce il campione scelto e l'oggetto
        alla panchina/inventario del giocatore umano e dei bot, poi torna allo Shop.
        """
        human = self.avatars[0]
        if human.claimed_champ:
            chosen_champ = human.claimed_champ.champion
            chosen_item = human.claimed_champ.item_key
            
            # 1. Equipaggia o inserisci l'oggetto
            res, _ = chosen_champ.equip_item(chosen_item)
            if res == 'full':
                if len(self.game.player_items) < 8:
                    self.game.player_items.append(chosen_item)

            # 2. Inserisci il campione nella panchina o scacchiera
            placed = False
            for i in range(self.game.bench_slots):
                if self.game.bench[i] is None:
                    self.game.bench[i] = chosen_champ
                    placed = True
                    break
            if not placed:
                for i in range(self.game.board_slots):
                    if self.game.board[i] is None:
                        self.game.board[i] = chosen_champ
                        placed = True
                        break
                        
            # Controlla eventuali merge a 2 o 3 stelle
            if hasattr(self.game, 'shop_manager'):
                self.game.shop_manager.merge_champions(chosen_champ)

        # 3. Assegna le scelte ai Bot
        bots = getattr(self.game.lobby_manager, 'bots', [])
        for i, bot_av in enumerate(self.avatars[1:]):
            if bot_av.claimed_champ and i < len(bots):
                bot_obj = bots[i]
                bot_champ = bot_av.claimed_champ.champion
                bot_item = bot_av.claimed_champ.item_key
                bot_champ.equip_item(bot_item)
                bot_obj.board.append(bot_champ)

        # 4. Transizione nello SHOP
        self.game.game_state = "SHOP"
        print("🎠 Carosello concluso con successo. Si passa alla fase di preparazione!")

    def draw(self, surface):
        """Disegna l'arena magica circolare, i campioni rotanti, gli avatar e l'HUD"""
        # 1. Sfondo celestiale
        bg_surf = get_background_image("board_bg", WIDTH, HEIGHT)
        surface.blit(bg_surf, (0, 0))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 22, 190))
        surface.blit(overlay, (0, 0))

        # 2. Cerchio Magico dell'Arena
        arena_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Pavimento runico esterno (Barriere)
        pygame.draw.circle(arena_surf, (20, 32, 50, 160), (self.center_x, self.center_y), int(self.barrier_radius + 40))
        pygame.draw.circle(arena_surf, (60, 120, 180, 140), (self.center_x, self.center_y), int(self.barrier_radius + 40), width=2)
        
        # Anello orbitale centrale
        pygame.draw.circle(arena_surf, (25, 45, 70, 200), (self.center_x, self.center_y), int(self.carousel_radius + 25))
        pygame.draw.circle(arena_surf, (210, 175, 75, 180), (self.center_x, self.center_y), int(self.carousel_radius), width=3)
        pygame.draw.circle(arena_surf, (90, 160, 240, 130), (self.center_x, self.center_y), int(self.carousel_radius - 25), width=1)
        
        # Stemma esagonale al centro esatto
        pygame.draw.circle(arena_surf, (15, 22, 35, 230), (self.center_x, self.center_y), 50)
        pygame.draw.circle(arena_surf, (245, 200, 60, 220), (self.center_x, self.center_y), 50, width=2)
        
        surface.blit(arena_surf, (0, 0))
        draw_star(surface, self.center_x, self.center_y, radius=18, color=GOLD)

        # 3. Disegna i Campioni del Carosello
        for c_champ in self.carousel_champs:
            c_champ.draw(surface)

        # 4. Disegna gli Avatar (Giocatore & Bot)
        for av in self.avatars:
            av.draw(surface, self.center_x, self.center_y)

        # 5. Particelle
        for p in self.particles:
            p.draw(surface)

        # 6. Header Top Bar & Conto alla Rovescia
        header_rect = pygame.Rect(WIDTH // 2 - 320, 20, 640, 56)
        draw_glass_panel(surface, header_rect, border_radius=28, bg_color=(12, 16, 28, 235), border_color=(230, 190, 65, 220), border_width=2)
        
        title_text = f"CAROSELLO CONDIVISO - ROUND {self.round_number}"
        draw_text(title_text, pygame.font.SysFont("Arial", 22, bold=True), GOLD, surface, header_rect.centerx, header_rect.centery)

        # Banner Conto alla Rovescia / Guida
        sub_font = pygame.font.SysFont("Arial", 14, bold=True)
        if self.countdown > 0:
            count_num = int(self.countdown) + 1
            msg = f"LE BARRIERE SI APRIRANNO TRA {count_num}..."
            draw_text(msg, pygame.font.SysFont("Arial", 18, bold=True), (255, 100, 100), surface, WIDTH // 2, 95)
        else:
            human = self.avatars[0]
            if human.is_locked:
                time_left = max(0.0, human.unlock_time - (self.elapsed_time - 3.0))
                msg = f"SBLOCCO IN BASE AGLI HP TRA {time_left:.1f}s (Priorità a chi ha meno HP)..."
                draw_text(msg, sub_font, (255, 200, 80), surface, WIDTH // 2, 95)
            elif not human.claimed_champ:
                draw_text("CORRI VERSO UN CAMPIONE PER PRENDERLO INSIEME AL SUO OGGETTO! (Click Mouse o WASD)", sub_font, (120, 255, 160), surface, WIDTH // 2, 95)
            else:
                draw_text("CAMPIONE SCELTO! PREPARAZIONE AL PROSSIMO ROUND IN CORSO...", sub_font, GOLD, surface, WIDTH // 2, 95)
