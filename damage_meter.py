# damage_meter.py
import pygame
from config import draw_text, WIDTH, HEIGHT, GOLD, WHITE, BLACK, RED, GREEN, TEXT_FONT, SMALL_FONT, MICRO_FONT, HEADER_FONT
from asset_loader import draw_glass_panel

class DamageMeter:
    """
    Damage Meter & DPS Tracker in tempo reale per Mini TFT.
    Monitora Danni Fisici, Magici, Danni Subiti e Cure di ciascun campione della squadra.
    """
    def __init__(self):
        self.is_visible = True
        self.active_tab = "DANNI" # "DANNI", "SUBITI", "CURE"
        self.tab_rects = {}
        self.toggle_btn_rect = None
        
    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        return self.is_visible

    def handle_event(self, event):
        """Gestisce il cambio di scheda o il toggle con click o tasto TAB"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.toggle_visibility()
                return True
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.toggle_btn_rect and self.toggle_btn_rect.collidepoint(mouse_pos):
                self.toggle_visibility()
                return True
                
            if self.is_visible:
                for tab_name, rect in self.tab_rects.items():
                    if rect.collidepoint(mouse_pos):
                        self.active_tab = tab_name
                        return True
        return False

    def draw(self, surface, mouse_pos, champions_team, elapsed_seconds=1.0, start_x=None, start_y=None):
        """
        Disegna il pannello Glassmorphic del Damage Meter con barre bicolore proporzionali e DPS.
        """
        if not champions_team:
            return

        panel_w = 265
        panel_h = min(360, 80 + len(champions_team) * 38)
        px = start_x if start_x is not None else (WIDTH - panel_w - 15)
        py = start_y if start_y is not None else 75
        
        # 1. Pulsante Toggle compatto
        self.toggle_btn_rect = pygame.Rect(px, py - 32, 110, 26)
        btn_hover = self.toggle_btn_rect.collidepoint(mouse_pos)
        btn_bg = (24, 32, 48, 230) if btn_hover else (14, 18, 28, 200)
        pygame.draw.rect(surface, btn_bg, self.toggle_btn_rect, border_radius=13)
        pygame.draw.rect(surface, GOLD if self.is_visible else (120, 130, 150), self.toggle_btn_rect, width=1, border_radius=13)
        
        toggle_label = "📊 DANNI [TAB]" if self.is_visible else "📊 MOSTRA [TAB]"
        draw_text(toggle_label, pygame.font.SysFont("Arial", 10, bold=True), GOLD if self.is_visible else (190, 200, 220), surface, self.toggle_btn_rect.centerx, self.toggle_btn_rect.centery)
        
        if not self.is_visible:
            return

        # 2. Card Glassmorphism Principale
        panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        draw_glass_panel(surface, panel_rect, border_radius=16, bg_color=(12, 16, 26, 235), border_color=(80, 100, 130, 180), border_width=1)
        
        # 3. Header Schede Commutabili (DANNI, SUBITI, CURE)
        tab_w = 78
        tab_h = 24
        tabs = [("DANNI", "Danni"), ("SUBITI", "Subiti"), ("CURE", "Cure")]
        self.tab_rects.clear()
        
        for i, (tab_key, tab_label) in enumerate(tabs):
            tx = px + 10 + i * (tab_w + 6)
            ty = py + 10
            t_rect = pygame.Rect(tx, ty, tab_w, tab_h)
            self.tab_rects[tab_key] = t_rect
            
            is_active = self.active_tab == tab_key
            is_hover = t_rect.collidepoint(mouse_pos)
            
            if is_active:
                if tab_key == "DANNI":
                    t_col = (235, 120, 30)
                elif tab_key == "SUBITI":
                    t_col = (70, 140, 230)
                else:
                    t_col = (40, 200, 110)
                t_bg = (25, 32, 48)
                t_border = t_col
            else:
                t_col = (150, 160, 175)
                t_bg = (16, 20, 30) if is_hover else (12, 15, 22)
                t_border = (50, 60, 75)
                
            pygame.draw.rect(surface, t_bg, t_rect, border_radius=6)
            pygame.draw.rect(surface, t_border, t_rect, width=1, border_radius=6)
            draw_text(tab_label, pygame.font.SysFont("Arial", 11, bold=True), t_col, surface, t_rect.centerx, t_rect.centery)

        # 4. Ordinamento dei campioni per la metrica attiva
        valid_champs = [c for c in champions_team if c is not None]
        if self.active_tab == "DANNI":
            valid_champs.sort(key=lambda c: c.total_damage_dealt, reverse=True)
            max_val = max(1, max((c.total_damage_dealt for c in valid_champs), default=1))
        elif self.active_tab == "SUBITI":
            valid_champs.sort(key=lambda c: c.damage_taken, reverse=True)
            max_val = max(1, max((c.damage_taken for c in valid_champs), default=1))
        else:
            valid_champs.sort(key=lambda c: c.healing_done, reverse=True)
            max_val = max(1, max((c.healing_done for c in valid_champs), default=1))

        # 5. Rendering delle righe statistiche
        row_y = py + 44
        for champ in valid_champs:
            # Mini Token Ritratto
            token = champ.get_token_surface(size=26)
            surface.blit(token, (px + 10, row_y + 4))
            
            # Anello stelle / tier
            tier_col = getattr(champ, 'tier_color', WHITE)
            pygame.draw.circle(surface, tier_col, (px + 23, row_y + 17), 13, width=1)
            
            # Nome e livello pulito
            lvl = getattr(champ, 'level', 1)
            lvl_text = f" (L{lvl})" if lvl > 1 else ""
            name_text = f"{champ.name[:7]}{lvl_text}"
            draw_text(name_text, pygame.font.SysFont("Arial", 10, bold=True), WHITE, surface, px + 42, row_y + 5, center=False)
            
            # Valore Totale e DPS
            if self.active_tab == "DANNI":
                val = champ.total_damage_dealt
                phys = champ.damage_dealt_physical
                magic = champ.damage_dealt_magic
            elif self.active_tab == "SUBITI":
                val = champ.damage_taken
                phys = val
                magic = 0
            else:
                val = champ.healing_done
                phys = val
                magic = 0

            dps_val = int(val / max(0.5, elapsed_seconds))
            stat_num_text = f"{val} ({dps_val} DPS)" if dps_val > 0 else f"{val}"
            draw_text(stat_num_text, pygame.font.SysFont("Arial", 9, bold=True), (210, 220, 240), surface, px + panel_w - 10, row_y + 5, center=False)
            # Re-allinea a destra
            
            # Barra Orizzontale Proporzionale
            bar_x = px + 42
            bar_y = row_y + 20
            max_bar_w = 210
            bar_h = 10
            
            # Sfondo barra
            pygame.draw.rect(surface, (18, 22, 32), (bar_x, bar_y, max_bar_w, bar_h), border_radius=5)
            
            if max_val > 0 and val > 0:
                fill_w = max(4, int(max_bar_w * (val / max_val)))
                
                if self.active_tab == "DANNI":
                    # Barra bicolore: Fisico (Arancio) + Magico (Viola/Ciano)
                    phys_ratio = phys / max(1, val)
                    phys_w = int(fill_w * phys_ratio)
                    magic_w = fill_w - phys_w
                    
                    if phys_w > 0:
                        pygame.draw.rect(surface, (235, 120, 30), (bar_x, bar_y, phys_w, bar_h), border_radius=5)
                    if magic_w > 0:
                        pygame.draw.rect(surface, (160, 80, 240), (bar_x + phys_w, bar_y, magic_w, bar_h), border_radius=5)
                elif self.active_tab == "SUBITI":
                    pygame.draw.rect(surface, (70, 140, 230), (bar_x, bar_y, fill_w, bar_h), border_radius=5)
                else:
                    pygame.draw.rect(surface, (40, 200, 110), (bar_x, bar_y, fill_w, bar_h), border_radius=5)
                    
            pygame.draw.rect(surface, (50, 60, 80), (bar_x, bar_y, max_bar_w, bar_h), width=1, border_radius=5)
            
            row_y += 36
