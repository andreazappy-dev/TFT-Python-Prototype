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

# --- Font Ottimizzati ad Alta Definizione (Helvetica Neue / Arial) ---
def get_font(size, bold=True):
    return pygame.font.SysFont(["Helvetica Neue", "Arial", "sans-serif"], size, bold=bold)

TITLE_FONT = get_font(38, bold=True)
SUBTITLE_FONT = get_font(22, bold=True)
HEADER_FONT = get_font(16, bold=True)
BUTTON_FONT = get_font(14, bold=True)
TEXT_FONT = get_font(13, bold=True)
SMALL_FONT = get_font(11, bold=True)
MICRO_FONT = get_font(10, bold=True)

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