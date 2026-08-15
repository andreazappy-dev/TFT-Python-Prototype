# audio_generator.py
import os
import wave
import math
import struct
import random

SAMPLE_RATE = 44100
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")

def write_wav(filename, samples, sample_rate=SAMPLE_RATE, channels=1):
    """Scrive una lista di float (-1.0 a 1.0) in un file WAV 16-bit PCM"""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    filepath = os.path.join(AUDIO_DIR, filename)
    
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(sample_rate)
        
        # Converte campioni float in interi a 16 bit (-32768 a 32767)
        raw_data = bytearray()
        for sample in samples:
            # Clipping di sicurezza
            clamped = max(-1.0, min(1.0, sample))
            val = int(clamped * 32767.0)
            raw_data.extend(struct.pack("<h", val))
            if channels == 2:
                raw_data.extend(struct.pack("<h", val)) # Duplica per stereo
                
        wf.writeframes(raw_data)
    print(f"Generato audio: {filename}")
    return filepath

def adsr(t, total_time, attack=0.01, decay=0.05, sustain_level=0.7, release=0.1):
    """Calcola l'inviluppo ADSR per il tempo t"""
    if t < attack:
        return t / max(0.001, attack)
    elif t < attack + decay:
        dt = t - attack
        return 1.0 - (1.0 - sustain_level) * (dt / max(0.001, decay))
    elif t < total_time - release:
        return sustain_level
    else:
        dt = t - (total_time - release)
        return max(0.0, sustain_level * (1.0 - (dt / max(0.001, release))))

def synth_sine(freq, t):
    return math.sin(2.0 * math.pi * freq * t)

def synth_triangle(freq, t):
    p = (freq * t) % 1.0
    return 4.0 * abs(p - 0.5) - 1.0

def synth_square(freq, t, duty=0.5):
    return 1.0 if (freq * t) % 1.0 < duty else -1.0

# --- GENERATORI SFX ---

def generate_coin_buy():
    """Suono di monete scintillanti all'acquisto"""
    duration = 0.35
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Due campane/pings armonici
        note1 = synth_sine(987.77, t) * math.exp(-t * 15.0) # B5
        note2 = synth_sine(1318.51, max(0.0, t - 0.08)) * math.exp(-max(0.0, t - 0.08) * 12.0) if t >= 0.08 else 0.0 # E6
        note3 = synth_sine(1975.53, max(0.0, t - 0.15)) * math.exp(-max(0.0, t - 0.15) * 14.0) if t >= 0.15 else 0.0 # B6
        
        sample = (note1 * 0.4 + note2 * 0.4 + note3 * 0.3)
        samples.append(sample)
        
    write_wav("coin_buy.wav", samples)

def generate_sell():
    """Suono metallico alla vendita"""
    duration = 0.25
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 800.0 - t * 1500.0
        tone = synth_triangle(max(100.0, freq), t) * (1.0 - t / duration)
        noise = (random.random() * 2.0 - 1.0) * math.exp(-t * 20.0) * 0.2
        samples.append((tone * 0.5 + noise) * 0.8)
        
    write_wav("sell.wav", samples)

def generate_reroll():
    """Fruscio d'aria / scatto rapido al roll"""
    duration = 0.22
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        sweep = synth_sine(400.0 + math.sin(t * 30.0) * 200.0 + t * 400.0, t)
        noise = (random.random() * 2.0 - 1.0) * 0.4
        env = math.sin(math.pi * (t / duration))
        samples.append((sweep * 0.3 + noise * 0.4) * env)
        
    write_wav("reroll.wav", samples)

def generate_xp_buy():
    """Suono di accumulo energia per XP"""
    duration = 0.4
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        f1 = 440.0 + (t / duration) * 220.0
        f2 = 660.0 + (t / duration) * 330.0
        tone = (synth_sine(f1, t) + synth_sine(f2, t)) * 0.35
        env = adsr(t, duration, attack=0.02, decay=0.1, sustain_level=0.8, release=0.15)
        samples.append(tone * env)
        
    write_wav("xp_buy.wav", samples)

def generate_level_up():
    """Fanfara trionfale di level up"""
    duration = 0.7
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    notes = [523.25, 659.25, 783.99, 1046.50] # C5, E5, G5, C6
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        note_idx = min(len(notes) - 1, int(t / 0.12))
        note_t = t - (note_idx * 0.12)
        freq = notes[note_idx]
        
        tone = synth_triangle(freq, t) * 0.4 + synth_sine(freq * 2.0, t) * 0.2
        env = math.exp(-note_t * 5.0) if note_idx < len(notes)-1 else adsr(note_t, duration - 0.36, 0.02, 0.1, 0.6, 0.2)
        samples.append(tone * env * 0.9)
        
    write_wav("level_up.wav", samples)

def generate_merge_star():
    """Armonia scintillante magica quando tre campioni si fondono"""
    duration = 0.6
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    arpeggio = [659.25, 830.61, 987.77, 1318.51, 1661.22] # E5, G#5, B5, E6, G#6
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        note_idx = min(len(arpeggio) - 1, int(t / 0.09))
        freq = arpeggio[note_idx]
        
        shimmer = synth_sine(freq, t) * 0.4 + synth_sine(freq * 2.0 + math.sin(t * 40.0) * 10.0, t) * 0.2
        env = (1.0 - t / duration) * 0.9
        samples.append(shimmer * env)
        
    write_wav("merge_star.wav", samples)

def generate_drop_token():
    """Pop morbido al rilascio della pedina"""
    duration = 0.12
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 300.0 * math.exp(-t * 25.0) + 60.0
        tone = synth_sine(freq, t) * math.exp(-t * 20.0)
        samples.append(tone * 0.8)
        
    write_wav("drop_token.wav", samples)

def generate_attack_melee():
    """Impatto fisico fendente/pugno"""
    duration = 0.18
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        f = 220.0 * math.exp(-t * 20.0) + 40.0
        punch = synth_triangle(f, t) * 0.5
        noise = (random.random() * 2.0 - 1.0) * math.exp(-t * 30.0) * 0.5
        env = math.exp(-t * 15.0)
        samples.append((punch + noise) * env)
        
    write_wav("attack_melee.wav", samples)

def generate_attack_ranged():
    """Dardo/laser magico"""
    duration = 0.2
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 1200.0 * math.exp(-t * 15.0) + 200.0
        tone = synth_sine(freq, t) * 0.4 + synth_triangle(freq * 0.5, t) * 0.3
        env = math.exp(-t * 10.0)
        samples.append(tone * env)
        
    write_wav("attack_ranged.wav", samples)

def generate_spell_cast():
    """Esplosione magica e abilità speciale"""
    duration = 0.6
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        sweep = synth_sine(200.0 + (t * 600.0 if t < 0.2 else (0.6 - t) * 500.0), t)
        sparkle = synth_sine(1400.0 + math.sin(t * 50.0) * 200.0, t) * 0.3
        sub = synth_sine(80.0, t) * 0.5
        env = adsr(t, duration, 0.05, 0.15, 0.6, 0.25)
        samples.append((sweep * 0.4 + sparkle * 0.3 + sub * 0.4) * env * 0.9)
        
    write_wav("spell_cast.wav", samples)

def generate_victory():
    """Jingle vittorioso"""
    duration = 1.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    notes = [523.25, 659.25, 783.99, 1046.50]
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        chord = 0.0
        for n_idx, freq in enumerate(notes):
            delay = n_idx * 0.12
            if t >= delay:
                dt = t - delay
                tone = synth_sine(freq, t) * 0.3 + synth_triangle(freq * 0.5, t) * 0.2
                env = math.exp(-dt * 2.0)
                chord += tone * env
        samples.append(chord * 0.6)
        
    write_wav("victory.wav", samples)

def generate_defeat():
    """Rintocco cupo per sconfitta"""
    duration = 0.9
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    notes = [392.00, 369.99, 329.63, 220.00] # Descending sad
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        idx = min(len(notes)-1, int(t / 0.2))
        freq = notes[idx]
        tone = synth_triangle(freq, t) * 0.4 + synth_sine(freq * 0.5, t) * 0.3
        env = math.exp(-(t % 0.2) * 5.0) * (1.0 - t / duration)
        samples.append(tone * env * 0.8)
        
    write_wav("defeat.wav", samples)

# --- GENERATORI BGM (MUSICA) ---

def generate_shop_theme():
    """Musica ambient melodica per la fase di preparazione (12s loop)"""
    duration = 12.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    # Progressione: Am (A C E) -> F (F A C) -> C (C E G) -> G (G B D)
    chords = [
        [220.00, 261.63, 329.63, 440.00], # Am
        [174.61, 220.00, 261.63, 349.23], # F
        [261.63, 329.63, 392.00, 523.25], # C
        [196.00, 246.94, 293.66, 392.00]  # G
    ]
    chord_len = duration / len(chords) # 3.0 sec per chord
    
    for c_idx, chord in enumerate(chords):
        start_t = c_idx * chord_len
        end_t = start_t + chord_len
        start_sample = int(start_t * SAMPLE_RATE)
        end_sample = int(end_t * SAMPLE_RATE)
        
        # Arpeggiatore
        for i in range(start_sample, min(num_samples, end_sample)):
            t = i / SAMPLE_RATE
            local_t = t - start_t
            
            # Bassline profondo
            bass_freq = chord[0] * 0.5
            bass = synth_sine(bass_freq, t) * 0.25 * math.exp(-((local_t % 1.5) * 1.5))
            
            # Arpeggio note
            arp_idx = int((local_t / 0.375) % len(chord))
            note_freq = chord[arp_idx]
            arp_t = (local_t % 0.375)
            lead = synth_sine(note_freq, t) * 0.2 * math.exp(-arp_t * 4.0)
            harm = synth_triangle(note_freq * 2.0, t) * 0.05 * math.exp(-arp_t * 5.0)
            
            # Pad delicato
            pad = sum(synth_sine(f, t) for f in chord) * 0.04
            
            samples[i] += (bass + lead + harm + pad) * 0.7
            
    write_wav("shop_theme.wav", samples)

def generate_battle_theme():
    """Musica incalzante ed energica per la battaglia (12s loop)"""
    duration = 12.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    # Progressione: Dm -> Bb -> F -> C (energico)
    chords = [
        [146.83, 220.00, 293.66, 349.23], # Dm
        [116.54, 174.61, 233.08, 293.66], # Bb
        [174.61, 220.00, 261.63, 349.23], # F
        [130.81, 196.00, 261.63, 329.63]  # C
    ]
    chord_len = duration / len(chords)
    
    for c_idx, chord in enumerate(chords):
        start_t = c_idx * chord_len
        end_t = start_t + chord_len
        start_sample = int(start_t * SAMPLE_RATE)
        end_sample = int(end_t * SAMPLE_RATE)
        
        for i in range(start_sample, min(num_samples, end_sample)):
            t = i / SAMPLE_RATE
            local_t = t - start_t
            
            # Cassa / kick synth ritmico ogni 0.5s
            kick_t = (t % 0.5)
            kick_freq = 150.0 * math.exp(-kick_t * 30.0) + 35.0
            kick = synth_sine(kick_freq, t) * 0.35 * math.exp(-kick_t * 15.0)
            
            # Bassline ritmico sincopato (16th notes a 120 bpm = 0.25s)
            bass_step = int((local_t / 0.25) % 4)
            bass_freq = chord[0] if bass_step != 2 else chord[1] * 0.5
            bass_t = (local_t % 0.25)
            bass = synth_saw = (synth_triangle(bass_freq, t) * 0.3 + synth_square(bass_freq, t, 0.3) * 0.1) * math.exp(-bass_t * 8.0)
            
            # Synth lead staccato
            lead_idx = int((local_t / 0.25) % len(chord))
            lead_freq = chord[lead_idx] * 2.0
            lead_t = (local_t % 0.25)
            lead = synth_triangle(lead_freq, t) * 0.18 * math.exp(-lead_t * 5.0)
            
            samples[i] += (kick + bass + lead) * 0.65
            
    write_wav("battle_theme.wav", samples)

def generate_all_audio():
    """Genera tutti gli asset audio se non presenti"""
    print("Inizio generazione asset audio procedurale...")
    generate_coin_buy()
    generate_sell()
    generate_reroll()
    generate_xp_buy()
    generate_level_up()
    generate_merge_star()
    generate_drop_token()
    generate_attack_melee()
    generate_attack_ranged()
    generate_spell_cast()
    generate_victory()
    generate_defeat()
    generate_shop_theme()
    generate_battle_theme()
    print("Tutti gli asset audio sono stati generati con successo!")

if __name__ == "__main__":
    generate_all_audio()
