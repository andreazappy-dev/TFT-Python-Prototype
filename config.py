# config.py
import math
import pygame

# Inizializza solo i moduli che servono (font)
# pygame.init() verrà chiamato in game.py
pygame.font.init() 

# --- Costanti di Gioco (Full HD 1920x1080) ---
WIDTH, HEIGHT = 1920, 1080

# --- Colori ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 120, 215)
LIGHT_BLUE = (0, 150, 255)
GRAY = (50, 50, 50)
GREEN = (60, 200, 100)
RED = (220, 55, 65)
GOLD = (240, 195, 40)

# --- Font Ottimizzati per 1920x1080 ---
TITLE_FONT = pygame.font.SysFont("Arial", 52, bold=True)
SUBTITLE_FONT = pygame.font.SysFont("Arial", 26, bold=True)
HEADER_FONT = pygame.font.SysFont("Arial", 20, bold=True)
BUTTON_FONT = pygame.font.SysFont("Arial", 18, bold=True)
TEXT_FONT = pygame.font.SysFont("Arial", 15, bold=True)
SMALL_FONT = pygame.font.SysFont("Arial", 13, bold=True)
MICRO_FONT = pygame.font.SysFont("Arial", 11, bold=True)

# --- Funzioni Helper Grafiche ---
def draw_text(text, font, color, surface, x, y, center=True):
    """ Funzione helper per disegnare testo centrato o allineato a sinistra in modo sicuro. """
    try:
        # Pulisce eventuali caratteri unicode non supportati
        clean_text = str(text).replace("•", "-").replace("✨", "").replace("🗑️", "").replace("★", "")
        text_obj = font.render(clean_text, True, color)
        text_rect = text_obj.get_rect()
        if center:
            text_rect.center = (int(x), int(y))
        else:
            text_rect.topleft = (int(x), int(y))
        surface.blit(text_obj, text_rect)
    except Exception as e:
        print(f"Errore in draw_text: {e}")

def draw_star(surface, cx, cy, radius=8, color=GOLD):
    """ Disegna una stella a 5 punte geometrica perfetta (senza font/tofu bugs). """
    points = []
    inner_radius = radius * 0.45
    for i in range(10):
        r = radius if i % 2 == 0 else inner_radius
        angle = i * math.pi / 5 - math.pi / 2
        px = cx + math.cos(angle) * r
        py = cy + math.sin(angle) * r
        points.append((px, py))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (0, 0, 0), points, width=1)

def draw_cross(surface, cx, cy, radius=6, color=WHITE, width=2):
    """ Disegna un'icona X di chiusura pulita e anti-aliased. """
    pygame.draw.line(surface, color, (cx - radius, cy - radius), (cx + radius, cy + radius), width=width)
    pygame.draw.line(surface, color, (cx - radius, cy + radius), (cx + radius, cy - radius), width=width)