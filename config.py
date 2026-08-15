# config.py
import pygame

# Inizializza solo i moduli che servono (font)
# pygame.init() verrà chiamato in game.py
pygame.font.init() 

# --- Costanti di Gioco ---
WIDTH, HEIGHT = 1400, 900

# --- Colori ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 120, 215)
LIGHT_BLUE = (0, 150, 255)
GRAY = (50, 50, 50)
GREEN = (60, 200, 100)
RED = (200, 60, 60)
GOLD = (230, 180, 30)

# --- Font Ottimizzati ---
TITLE_FONT = pygame.font.SysFont("Arial", 46, bold=True)
SUBTITLE_FONT = pygame.font.SysFont("Arial", 24, bold=True)
HEADER_FONT = pygame.font.SysFont("Arial", 17, bold=True)
BUTTON_FONT = pygame.font.SysFont("Arial", 16, bold=True)
TEXT_FONT = pygame.font.SysFont("Arial", 14, bold=True)
SMALL_FONT = pygame.font.SysFont("Arial", 12, bold=True)
MICRO_FONT = pygame.font.SysFont("Arial", 10, bold=True)


# --- Funzione Utile (Utility) ---
def draw_text(text, font, color, surface, x, y, center=True):
    """ Funzione helper per disegnare testo centrato o allineato a sinistra. """
    try:
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        surface.blit(text_obj, text_rect)
    except Exception as e:
        print(f"Errore in draw_text: {e}")
