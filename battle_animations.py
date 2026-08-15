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
        self.proj_type = proj_type # "BASIC", "ORB", "ROCKET", "METEOR", "DIVINE_SWORD", "MYSTIC_ARC"
        self.color = color
        self.on_hit = on_hit
        self.is_alive = True
        self.trail_timer = 0.0
        self.rotation = 0.0
        self.size = 12 if proj_type in ["ORB", "ROCKET"] else 8

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
        count = 20 if self.proj_type in ["ROCKET", "METEOR"] else 10
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(50, 180)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            col = self.color if self.proj_type != "ROCKET" else random.choice([(255, 60, 60), (255, 180, 40), (255, 240, 80)])
            particles_list.append(Particle(self.x, self.y, vx, vy, col, radius=random.randint(3, 6), max_life=0.45))

    def draw(self, surface):
        if not self.is_alive:
            return
            
        cx, cy = int(self.x), int(self.y)
        if self.proj_type == "ORB":
            # Sfera magica rotante con doppio anello
            pygame.draw.circle(surface, (255, 100, 200), (cx, cy), 10)
            pygame.draw.circle(surface, (100, 220, 255), (cx, cy), 6)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 3)
        elif self.proj_type == "ROCKET":
            # Ogiva razzo con fiammata
            pygame.draw.circle(surface, (230, 60, 60), (cx, cy), 8)
            pygame.draw.circle(surface, (255, 200, 40), (cx, cy), 5)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)
        elif self.proj_type == "METEOR":
            # Meteora cosmica gigante
            pygame.draw.circle(surface, (120, 50, 240), (cx, cy), 14)
            pygame.draw.circle(surface, (255, 180, 50), (cx, cy), 9)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 4)
        elif self.proj_type == "DIVINE_SWORD":
            # Spada di luce celestiale
            pygame.draw.line(surface, (255, 240, 140), (cx, cy - 16), (cx, cy + 16), 4)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 6)
        else:
            # Dardo d'energia base
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
