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

# Palette tematiche procedurali per ritratti campioni
THEME_PALETTES = {
    "garen": ((40, 90, 180), (220, 180, 50)),
    "darius": ((140, 20, 20), (210, 40, 40)),
    "ashe": ((60, 150, 220), (210, 240, 255)),
    "vi": ((160, 30, 120), (240, 80, 180)),
    "ahri": ((190, 40, 120), (255, 140, 200)),
    "zed": ((30, 20, 35), (200, 30, 50)),
    "braum": ((35, 75, 130), (140, 210, 255)),
    "ezreal": ((180, 140, 20), (255, 235, 90)),
    "jinx": ((180, 30, 100), (40, 210, 230)),
    "riven": ((50, 110, 80), (140, 235, 160)),
    "katarina": ((130, 20, 30), (240, 50, 70)),
    "yasuo": ((40, 85, 140), (120, 210, 255)),
    "shen": ((60, 40, 110), (160, 100, 240)),
    "kayle": ((180, 140, 30), (255, 245, 160)),
    "lux": ((190, 160, 50), (255, 250, 180)),
    "sejuani": ((40, 95, 140), (160, 230, 255)),
    "aurelion": ((40, 20, 110), (150, 90, 255)),
    "azir": ((180, 130, 20), (255, 215, 60)),
    "thresh": ((15, 65, 55), (40, 235, 170))
}

def get_champion_raw_image(name):
    """Carica l'immagine originale del campione o genera una texture procedurale tematica HD"""
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
            
    # Generazione procedurale artistica con gradiente e stemma
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    palette = THEME_PALETTES.get(key, ((50, 60, 80), (180, 190, 210)))
    col_bg, col_fg = palette
    
    # Gradiente radiale
    for r in range(120, 0, -3):
        ratio = r / 120.0
        c = (
            int(col_bg[0] * ratio + col_fg[0] * (1 - ratio)),
            int(col_bg[1] * ratio + col_fg[1] * (1 - ratio)),
            int(col_bg[2] * ratio + col_fg[2] * (1 - ratio))
        )
        pygame.draw.circle(surf, c, (120, 120), r)
        
    # Bordo e Lettera Stile Riot
    pygame.draw.circle(surf, col_fg, (120, 120), 116, width=4)
    font = pygame.font.SysFont("Arial", 80, bold=True)
    txt_surf = font.render(name[0], True, (255, 255, 255))
    surf.blit(txt_surf, (120 - txt_surf.get_width() // 2, 120 - txt_surf.get_height() // 2 - 10))
    
    # Nome in basso
    sub_font = pygame.font.SysFont("Arial", 22, bold=True)
    name_surf = sub_font.render(name[:9], True, col_fg)
    surf.blit(name_surf, (120 - name_surf.get_width() // 2, 175))
    
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

