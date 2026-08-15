# audio_manager.py
import os
import pygame

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")

class AudioManager:
    """
    Gestore centralizzato per tutti gli effetti sonori e la musica di sottofondo.
    Supporta controlli di volume, mute (tasto M) e fallback sicuro in caso di assenza driver audio.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AudioManager()
        return cls._instance

    def __init__(self):
        self.enabled = True
        self.is_muted = False
        self.sfx_volume = 0.65
        self.music_volume = 0.45
        self.current_track = None
        self.sounds = {}
        
        # Inizializza mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
            print("Audio Manager inizializzato con successo.")
        except Exception as e:
            print(f"Attenzione: Impossibile inizializzare pygame.mixer: {e}")
            self.enabled = False

        if self.enabled:
            self._load_sounds()

    def _load_sounds(self):
        """Carica tutti gli SFX in memoria"""
        sfx_names = [
            "coin_buy", "sell", "reroll", "xp_buy", "level_up",
            "merge_star", "drop_token", "attack_melee", "attack_ranged",
            "spell_cast", "victory", "defeat"
        ]
        for name in sfx_names:
            path = os.path.join(AUDIO_DIR, f"{name}.wav")
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(self.sfx_volume)
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"Errore caricamento sound {name}: {e}")

    def play_sfx(self, name):
        """Riproduce un effetto sonoro per nome"""
        if not self.enabled or self.is_muted:
            return
        
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception as e:
                pass

    def play_music(self, track_name, loop=True):
        """Riproduce la musica di sottofondo specificata"""
        if not self.enabled:
            return
        
        if self.current_track == track_name and pygame.mixer.music.get_busy():
            return # Traccia già in riproduzione
            
        path = os.path.join(AUDIO_DIR, f"{track_name}.wav")
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.0 if self.is_muted else self.music_volume)
                pygame.mixer.music.play(-1 if loop else 0)
                self.current_track = track_name
            except Exception as e:
                print(f"Errore play music {track_name}: {e}")

    def stop_music(self):
        if self.enabled:
            try:
                pygame.mixer.music.stop()
                self.current_track = None
            except Exception:
                pass

    def toggle_mute(self):
        """Attiva o disattiva l'audio globale (Mute/Unmute)"""
        self.is_muted = not self.is_muted
        if self.enabled:
            try:
                if self.is_muted:
                    pygame.mixer.music.set_volume(0.0)
                else:
                    pygame.mixer.music.set_volume(self.music_volume)
            except Exception:
                pass
        print(f"Audio {'MUTO' if self.is_muted else 'ATTIVO'}")
        return self.is_muted

    def set_sfx_volume(self, vol):
        self.sfx_volume = max(0.0, min(1.0, vol))
        for snd in self.sounds.values():
            snd.set_volume(0.0 if self.is_muted else self.sfx_volume)

    def set_music_volume(self, vol):
        self.music_volume = max(0.0, min(1.0, vol))
        if self.enabled and not self.is_muted:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except Exception:
                pass
