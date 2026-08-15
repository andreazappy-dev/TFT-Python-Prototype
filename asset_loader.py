# asset_loader.py
import os
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "champions")
SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", "sprites")

# Cache per evitare ricaricamenti continui
_RAW_CACHE = {}
_CARD_CACHE = {}
_TOKEN_CACHE = {}
_SPRITE_CACHE = {}

def get_champion_sprite(name, width=80, height=80, flip_x=False, white_flash=False):
    """
    Carica lo sprite a figura intera trasparente del campione.
    Supporta flip orizzontale e white-flash shader per reazione al colpo.
    """
    key = name.lower()
    cache_key = (key, width, height, flip_x, white_flash)
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key]

    cutout_path = os.path.join(SPRITES_DIR, f"{key}_cutout.png")
    if os.path.exists(cutout_path):
        try:
            base_surf = pygame.image.load(cutout_path).convert_alpha()
        except Exception as e:
            print(f"Errore caricamento sprite {cutout_path}: {e}")
            base_surf = create_circular_token(name, size=width)
    else:
        # Fallback al ritaglio da raw image
        base_surf = create_circular_token(name, size=width)

    scaled_surf = pygame.transform.smoothscale(base_surf, (width, height))
    if flip_x:
        scaled_surf = pygame.transform.flip(scaled_surf, True, False)

    if white_flash:
        flash_surf = scaled_surf.copy()
        # Rendi tutti i pixel visibili bianchi mantenendo la trasparenza
        white_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        white_overlay.fill((255, 255, 255, 240))
        flash_surf.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        final_surf = flash_surf
    else:
        final_surf = scaled_surf

    _SPRITE_CACHE[cache_key] = final_surf
    return final_surf

def get_champion_raw_image(name):
    """Carica l'immagine originale del campione o crea un fallback"""
    key = name.lower()
    if key in _RAW_CACHE:
        return _RAW_CACHE[key]
    
    file_path = os.path.join(ASSETS_DIR, f"{key}.jpg")
    if os.path.exists(file_path):
        try:
            img = pygame.image.load(file_path).convert_alpha()
            _RAW_CACHE[key] = img
            return img
        except Exception as e:
            print(f"Errore nel caricamento di {file_path}: {e}")
            
    # Fallback: superficie colorata
    surf = pygame.Surface((200, 200), pygame.SRCALPHA)
    surf.fill((60, 60, 70))
    _RAW_CACHE[key] = surf
    return surf

def create_circular_token(name, size=50, flip_x=False):
    """
    Crea un token circolare con maschera alpha anti-aliasing.
    Ritorna una Surface Pygame con sfondo trasparente.
    """
    cache_key = (name.lower(), size, flip_x)
    if cache_key in _TOKEN_CACHE:
        return _TOKEN_CACHE[cache_key]

    raw_img = get_champion_raw_image(name)
    if flip_x:
        raw_img = pygame.transform.flip(raw_img, True, False)

    # Ridimensiona l'immagine mantenendo le proporzioni
    scaled_img = pygame.transform.smoothscale(raw_img, (size, size))

    # Maschera circolare
    token_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    mask_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    radius = size // 2
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (radius, radius), radius)

    # Applica la maschera circolare
    token_surface.blit(scaled_img, (0, 0))
    token_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    _TOKEN_CACHE[cache_key] = token_surface
    return token_surface

def create_card_image(name, width=150, height=130):
    """
    Crea l'immagine per la carta nello shop, con angoli arrotondati e sfumatura scura in basso.
    """
    cache_key = (name.lower(), width, height)
    if cache_key in _CARD_CACHE:
        return _CARD_CACHE[cache_key]

    raw_img = get_champion_raw_image(name)
    scaled_img = pygame.transform.smoothscale(raw_img, (width, height))

    card_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    card_surface.blit(scaled_img, (0, 0))

    # Maschera con angoli arrotondati
    mask_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask_surface, (255, 255, 255, 255), (0, 0, width, height), border_radius=10)
    card_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    # Sfumatura scura dal basso per facilitare la lettura del nome e delle stats
    gradient = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height // 2, height):
        progress = (y - height // 2) / (height // 2)
        alpha = int(progress * 210)
        pygame.draw.line(gradient, (10, 10, 15, alpha), (0, y), (width, y))
    
    card_surface.blit(gradient, (0, 0))

    _CARD_CACHE[cache_key] = card_surface
    return card_surface

# Cache Sfondi
_BG_CACHE = {}
BG_DIR = os.path.join(os.path.dirname(__file__), "assets", "backgrounds")

def get_background_image(name, width=1400, height=900):
    """Carica e ridimensiona uno sfondo artistico con caching"""
    cache_key = (name, width, height)
    if cache_key in _BG_CACHE:
        return _BG_CACHE[cache_key]

    file_path = os.path.join(BG_DIR, f"{name}.jpg")
    if os.path.exists(file_path):
        try:
            img = pygame.image.load(file_path).convert()
            scaled = pygame.transform.smoothscale(img, (width, height))
            _BG_CACHE[cache_key] = scaled
            return scaled
        except Exception as e:
            print(f"Errore caricamento sfondo {file_path}: {e}")

    # Fallback
    surf = pygame.Surface((width, height))
    surf.fill((15, 18, 25))
    _BG_CACHE[cache_key] = surf
    return surf

def draw_glass_panel(surface, rect, border_radius=14, bg_color=(18, 22, 32, 215), border_color=(180, 150, 60, 160), border_width=1):
    """Disegna un pannello arrotondato stile Glassmorphism con trasparenza e bordo illuminato"""
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, bg_color, (0, 0, rect.width, rect.height), border_radius=border_radius)
    if border_width > 0 and border_color:
        pygame.draw.rect(panel, border_color, (0, 0, rect.width, rect.height), width=border_width, border_radius=border_radius)
    surface.blit(panel, (rect.x, rect.y))

