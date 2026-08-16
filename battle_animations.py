# battle_animations.py
import math
import random
import pygame
from config import GOLD, WHITE, RED, GREEN, BLUE

class Particle:
    """Particella visiva per scintille, fumo, polvere e magie"""
    def __init__(self, x, y, vx, vy, color, radius=3, max_life=0.5, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.max_life = max_life
        self.life = max_life
        self.gravity = gravity

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha_ratio = max(0.0, min(1.0, self.life / self.max_life))
        r = max(1, int(self.radius * alpha_ratio))
        
        # Disegna cerchietto con bagliore
        surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        col_with_alpha = (self.color[0], self.color[1], self.color[2], int(255 * alpha_ratio))
        pygame.draw.circle(surf, col_with_alpha, (r + 1, r + 1), r)
        surface.blit(surf, (int(self.x - r - 1), int(self.y - r - 1)))

class Projectile:
    """Proiettile animato balistico o a ricerca bersaglio"""
    def __init__(self, start_x, start_y, target, speed=450, proj_type="BASIC", color=(255, 220, 80), on_hit=None):
        self.x = float(start_x)
        self.y = float(start_y)
        self.target = target
        self.target_x = target.x if target else start_x + 100
        self.target_y = target.y if target else start_y
        self.speed = speed
        self.proj_type = proj_type # "BASIC", "ORB", "ROCKET", "METEOR", "DIVINE_SWORD", "ICE_ARROW", "TORNADO", "DAGGER"
        self.color = color
        self.on_hit = on_hit
        self.is_alive = True
        self.trail_timer = 0.0
        self.rotation = 0.0
        self.size = 14 if proj_type in ["ORB", "ROCKET", "TORNADO"] else 8

    def update(self, dt, particles_list):
        if not self.is_alive:
            return
            
        if self.target and hasattr(self.target, 'is_alive') and self.target.is_alive():
            self.target_x = self.target.x
            self.target_y = self.target.y

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        self.rotation = math.degrees(math.atan2(-dy, dx))

        # Rilascio particelle scia
        self.trail_timer += dt
        if self.trail_timer >= 0.02:
            self.trail_timer = 0.0
            if self.proj_type == "ROCKET":
                particles_list.append(Particle(self.x, self.y, random.uniform(-20, 20), random.uniform(-20, 20), (180, 180, 190), radius=5, max_life=0.4))
                particles_list.append(Particle(self.x, self.y, random.uniform(-10, 10), random.uniform(-10, 10), (255, 120, 30), radius=3, max_life=0.2))
            elif self.proj_type == "ORB":
                particles_list.append(Particle(self.x, self.y, random.uniform(-15, 15), random.uniform(-15, 15), (255, 130, 220), radius=4, max_life=0.3))
                particles_list.append(Particle(self.x, self.y, random.uniform(-15, 15), random.uniform(-15, 15), (80, 210, 255), radius=4, max_life=0.3))
            elif self.proj_type == "METEOR":
                particles_list.append(Particle(self.x, self.y, random.uniform(-30, 30), random.uniform(-30, 30), (140, 70, 255), radius=6, max_life=0.4))
                particles_list.append(Particle(self.x, self.y, random.uniform(-20, 20), random.uniform(-20, 20), (255, 200, 50), radius=4, max_life=0.3))
            elif self.proj_type == "ICE_ARROW":
                particles_list.append(Particle(self.x, self.y, random.uniform(-15, 15), random.uniform(-15, 15), (140, 230, 255), radius=4, max_life=0.35))
                particles_list.append(Particle(self.x, self.y, random.uniform(-10, 10), random.uniform(-10, 10), (255, 255, 255), radius=2, max_life=0.2))
            elif self.proj_type == "TORNADO":
                particles_list.append(Particle(self.x, self.y, random.uniform(-25, 25), random.uniform(-25, 25), (200, 235, 255), radius=5, max_life=0.4))
                particles_list.append(Particle(self.x, self.y, random.uniform(-15, 15), random.uniform(-15, 15), (120, 180, 220), radius=3, max_life=0.25))
            elif self.proj_type == "DAGGER":
                particles_list.append(Particle(self.x, self.y, random.uniform(-10, 10), random.uniform(-10, 10), (255, 60, 60), radius=3, max_life=0.25))
            else:
                particles_list.append(Particle(self.x, self.y, random.uniform(-10, 10), random.uniform(-10, 10), self.color, radius=3, max_life=0.25))

        step = self.speed * dt
        if dist <= step or dist < 12:
            self.is_alive = False
            self.x = self.target_x
            self.y = self.target_y
            if self.on_hit:
                self.on_hit(self.target)
            self.create_impact_vfx(particles_list)
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step

    def create_impact_vfx(self, particles_list):
        count = 20 if self.proj_type in ["ROCKET", "METEOR", "ICE_ARROW", "TORNADO"] else 10
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(50, 180)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            col = self.color
            if self.proj_type == "ROCKET":
                col = random.choice([(255, 60, 60), (255, 180, 40), (255, 240, 80)])
            elif self.proj_type == "ICE_ARROW":
                col = random.choice([(120, 220, 255), (180, 245, 255), (255, 255, 255)])
            elif self.proj_type == "TORNADO":
                col = random.choice([(200, 230, 255), (150, 200, 240), (255, 255, 255)])
            particles_list.append(Particle(self.x, self.y, vx, vy, col, radius=random.randint(3, 6), max_life=0.45))

    def draw(self, surface):
        if not self.is_alive:
            return
            
        cx, cy = int(self.x), int(self.y)
        if self.proj_type == "ORB":
            pygame.draw.circle(surface, (255, 100, 200), (cx, cy), 10)
            pygame.draw.circle(surface, (100, 220, 255), (cx, cy), 6)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 3)
        elif self.proj_type == "ROCKET":
            pygame.draw.circle(surface, (230, 60, 60), (cx, cy), 8)
            pygame.draw.circle(surface, (255, 200, 40), (cx, cy), 5)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)
        elif self.proj_type == "METEOR":
            pygame.draw.circle(surface, (120, 50, 240), (cx, cy), 14)
            pygame.draw.circle(surface, (255, 180, 50), (cx, cy), 9)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 4)
        elif self.proj_type == "ICE_ARROW":
            # Freccia di ghiaccio appuntita
            pygame.draw.line(surface, (140, 225, 255), (cx - 10, cy), (cx + 10, cy), 4)
            pygame.draw.circle(surface, (255, 255, 255), (cx + 8, cy), 5)
        elif self.proj_type == "TORNADO":
            # Vortice di vento
            pygame.draw.circle(surface, (180, 220, 255, 180), (cx, cy), 16, width=3)
            pygame.draw.circle(surface, (230, 245, 255), (cx, cy), 8)
        elif self.proj_type == "DIVINE_SWORD":
            pygame.draw.line(surface, (255, 240, 140), (cx, cy - 16), (cx, cy + 16), 4)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 6)
        else:
            pygame.draw.circle(surface, self.color, (cx, cy), 6)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 3)

class SlashVFX:
    """Arco di fendente corpo a corpo con scia e bagliore"""
    def __init__(self, x, y, angle=0, radius=38, color=(245, 220, 100), duration=0.2):
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = radius
        self.color = color
        self.duration = duration
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    @property
    def is_alive(self):
        return self.time < self.duration

    def draw(self, surface):
        if not self.is_alive:
            return
        progress = self.time / self.duration
        alpha = int(255 * (1.0 - progress))
        
        surf = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
        start_a = self.angle - math.pi / 3
        end_a = self.angle + math.pi / 3
        
        arc_rect = pygame.Rect(5, 5, self.radius * 2, self.radius * 2)
        col_with_alpha = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.arc(surf, col_with_alpha, arc_rect, start_a, end_a, width=4)
        surface.blit(surf, (int(self.x - self.radius - 5), int(self.y - self.radius - 5)))

class ShockwaveVFX:
    """Onda d'urto ad anello circolare sul terreno"""
    def __init__(self, x, y, max_radius=60, color=(100, 220, 255), duration=0.4):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.color = color
        self.duration = duration
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    @property
    def is_alive(self):
        return self.time < self.duration

    def draw(self, surface):
        if not self.is_alive:
            return
        progress = self.time / self.duration
        curr_radius = int(self.max_radius * progress)
        alpha = int(220 * (1.0 - progress))
        if curr_radius > 2:
            surf = pygame.Surface((self.max_radius * 2 + 4, self.max_radius * 2 + 4), pygame.SRCALPHA)
            col_with_alpha = (self.color[0], self.color[1], self.color[2], alpha)
            pygame.draw.circle(surf, col_with_alpha, (self.max_radius + 2, self.max_radius + 2), curr_radius, width=3)
            surface.blit(surf, (int(self.x - self.max_radius - 2), int(self.y - self.max_radius - 2)))

class LaserBeamVFX:
    """Raggio Laser Gigante di Lux a tutta mappa"""
    def __init__(self, start_x, start_y, target_x, target_y, color=(255, 235, 120), duration=0.5):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.color = color
        self.duration = duration
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    @property
    def is_alive(self):
        return self.time < self.duration

    def draw(self, surface):
        if not self.is_alive:
            return
        progress = self.time / self.duration
        alpha = int(255 * (1.0 - progress))
        beam_w = int(22 * (1.0 - progress * 0.5))
        
        # Linea laser con bagliore
        surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        col_core = (255, 255, 255, alpha)
        col_outer = (*self.color[:3], int(alpha * 0.7))
        
        pygame.draw.line(surf, col_outer, (self.start_x, self.start_y), (self.target_x, self.target_y), beam_w + 10)
        pygame.draw.line(surf, col_core, (self.start_x, self.start_y), (self.target_x, self.target_y), max(2, beam_w // 2))
        surface.blit(surf, (0, 0))

class SandSoldiersVFX:
    """Falange di soldati di sabbia dorata di Azir"""
    def __init__(self, start_x, start_y, target_x, target_y, duration=0.6):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.duration = duration
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    @property
    def is_alive(self):
        return self.time < self.duration

    def draw(self, surface):
        if not self.is_alive:
            return
        progress = min(1.0, self.time / self.duration)
        cx = self.x + (self.target_x - self.x) * progress
        cy = self.y + (self.target_y - self.y) * progress
        
        for offset in [-35, 0, 35]:
            sx, sy = int(cx), int(cy + offset)
            pygame.draw.circle(surface, (255, 200, 50), (sx, sy), 14)
            pygame.draw.circle(surface, (255, 240, 140), (sx, sy), 7)
            pygame.draw.line(surface, (255, 230, 80), (sx, sy), (sx + 20, sy), 4)

class HookChainVFX:
    """Catena spettrale di Thresh che si estende verso il bersaglio"""
    def __init__(self, start_x, start_y, target_x, target_y, duration=0.45):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.duration = duration
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    @property
    def is_alive(self):
        return self.time < self.duration

    def draw(self, surface):
        if not self.is_alive:
            return
        progress = min(1.0, self.time / self.duration)
        tip_x = self.start_x + (self.target_x - self.start_x) * progress
        tip_y = self.start_y + (self.target_y - self.start_y) * progress
        
        # Maglie della catena verde spettrale
        pygame.draw.line(surface, (40, 230, 160), (self.start_x, self.start_y), (tip_x, tip_y), 4)
        pygame.draw.circle(surface, (120, 255, 200), (int(tip_x), int(tip_y)), 8)
        pygame.draw.circle(surface, (255, 255, 255), (int(tip_x), int(tip_y)), 4)
