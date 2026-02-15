import os
import random
import sqlite3
import numpy as np
import pyttsx3 # Vocea AI
import asyncio
import edge_tts
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, vfx, ColorClip, clips_array, AudioFileClip, CompositeAudioClip
from moviepy.video.fx.all import gamma_corr, lum_contrast, mirror_x, speedx, fadein, fadeout

# --- 1. CONFIGURARE IMAGEMAGICK ---
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"}) 

# --- CONFIGURARE GENERALĂ ---
PATH_OUTPUT = "output_videos"
VIDEO_SURSA = "video_brut.mp4"
DB_NAME = "youtube_empire.db"
FOLDER_SATISFYING = os.path.join("assets", "satisfying")

# --- INPUT INTERACTIV ---
print("\n💎 --- CONFIGURARE PREMIUM V2 (FIXED COLORS) ---")
TITLU_PRODUS = input("1. Nume Produs (ex: Flying Orb Ball): ").strip()
LINK_AFILIERE = input("2. Link Afiliere: ").strip()
LINK_SURSA = input("3. Sursă Video: ").strip()
CONT_TARGET = input("4. Cont Target (Gadgets / Home): ").strip()

if not TITLU_PRODUS or not LINK_AFILIERE: exit()

# --- FUNCȚII AUXILIARE ---

def resize_to_fill(clip, target_w, target_h):
    """Bulldozer Crop: Mărește cu 1% extra ca să nu avem erori de crop."""
    if clip.w == 0 or clip.h == 0: return clip
    scale_x = target_w / clip.w
    scale_y = target_h / clip.h
    final_scale = max(scale_x, scale_y) + 0.01
    
    try:
        clip_resized = clip.resize(final_scale)
        return clip_resized.crop(x_center=clip_resized.w/2, y_center=clip_resized.h/2, width=target_w, height=target_h)
    except:
        return clip.resize((target_w, target_h))

async def _genereaza_voce_async(text, nume_fisier):
    """Motorul asincron pentru Edge TTS"""
    # VOICES DISPONIBILE TOP TIER:
    # "en-US-ChristopherNeural" -> Voce masculină, serioasă, tech, documentar (BEST FOR GADGETS)
    # "en-US-AriaNeural"        -> Voce feminină, entuziastă, TikTok style
    # "en-US-GuyNeural"         -> Voce masculină, casual, știri
    
    VOICE = "en-US-ChristopherNeural" 
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(nume_fisier)
    
def genereaza_voce_ai(text):
    """Wrapper sincron pentru funcția asincronă (ca să nu stricăm restul codului)"""
    nume_fisier = "voce_temp.mp3"
    try:
        # Rulăm procesul asincron într-un mod sincron
        asyncio.run(_genereaza_voce_async(text, nume_fisier))
        
        if os.path.exists(nume_fisier):
            return nume_fisier
        else:
            return None
    except Exception as e:
        print(f"⚠️ [VOCE EROARE]: {e}")
        return None

def adauga_in_imperiu(cale_video, titlu_final, descriere_finala, stil):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        url_unic = f"{LINK_SURSA}_{stil}_{random.randint(10000,99999)}"
        cursor.execute('''
            INSERT INTO videos (sursa_url, affiliate_link, cont_target, titlu_video, descriere, cale_fisier, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (url_unic, LINK_AFILIERE, CONT_TARGET, titlu_final, descriere_finala, cale_video, datetime.now()))
        conn.commit()
        conn.close()
        print(f"🏛️ [DB]: Varianta '{stil}' salvată cu succes!")
    except Exception as e:
        print(f"❌ [DB EROARE]: {e}")

# --- ENGINE PRINCIPAL ---
def main():
    if not os.path.exists(PATH_OUTPUT): os.makedirs(PATH_OUTPUT)
    if not os.path.exists(VIDEO_SURSA):
        print(f"❌ Lipsă '{VIDEO_SURSA}'! Rulează downloader.")
        return

    print(f"\n🎬 Procesez: {TITLU_PRODUS}")
    try: clip_mare = VideoFileClip(VIDEO_SURSA)
    except: return

    durata_totala = clip_mare.duration
    W, H = 1080, 1920 

    stiluri = ["split", "speed", "dark", "zoom", "mirror"]

    for i, stil in enumerate(stiluri):
        print(f"🔨 Varianta {i+1}: {stil.upper()}")
        
        # A. CALCUL TIMP
        start_t, durata = 0, durata_totala
        if durata_totala > 65:
            start_t = ((durata_totala - 60) / 5) * i + random.randint(0, 5)
            durata = 58
        if start_t + durata > durata_totala: start_t = max(0, durata_totala - durata)
        
        clip = clip_mare.subclip(start_t, start_t + durata)

        # B. VIZUAL
        elemente = []
        if stil == "split":
            # --- CONFIGURARE PROPORȚII (AICI E SPLIT-UL) ---
            target_top_h = int(H * 0.65)   # 65% Produs (Sus)
            target_bot_h = H - target_top_h # 35% Gameplay (Jos)
            
            clip_top = resize_to_fill(clip, W, target_top_h)

            if os.path.exists(FOLDER_SATISFYING) and os.listdir(FOLDER_SATISFYING):
                try:
                    sat_path = os.path.join(FOLDER_SATISFYING, random.choice(os.listdir(FOLDER_SATISFYING)))
                    
                    # 🔥 MUTE COMPLET LA VIDEO-UL DE FUNDAL
                    sat_clip = VideoFileClip(sat_path).without_audio() 
                    
                    if sat_clip.duration < clip.duration: sat_clip = sat_clip.loop(duration=clip.duration)
                    else:
                        r_start = random.uniform(0, sat_clip.duration - clip.duration)
                        sat_clip = sat_clip.subclip(r_start, r_start + clip.duration)
                    
                    clip_bot = resize_to_fill(sat_clip, W, target_bot_h)
                    clip = clips_array([[clip_top], [clip_bot]])
                except: clip = resize_to_fill(clip, W, H)
            else: clip = resize_to_fill(clip, W, H)
        else:
            if stil == "speed": clip = clip.fx(speedx, 1.3)
            clip = resize_to_fill(clip, W, H)
            if stil == "mirror": clip = clip.fx(mirror_x)
            if stil == "dark": clip = clip.fx(vfx.colorx, 0.8)

        elemente.append(clip)

        # C. GRAFICĂ & FLASH
        flash = ColorClip(size=(W, H), color=(255,255,255), duration=0.2).set_opacity(0.8)
        elemente.append(flash)

        # --- FIX BARA PROGRES (AICI AM REPARAT) ---
        bar_h = 15
        p_bar = ColorClip(size=(W, bar_h), color=(255,0,0), duration=clip.duration)
        # Folosim max(1, ...) ca să nu fie niciodată lățimea 0
        p_bar = p_bar.resize(lambda t: (max(1, int(W * (t / clip.duration))), bar_h))
        p_bar = p_bar.set_position(('left', 'bottom'))
        elemente.append(p_bar)

        # D. TEXT NEON (VERSIUNEA ELON MUSK / HOLOGRAPHIC)
        if stil != "split":
          try:
            txt_str = "LINK IN BIO 👇"
            # Folosim un font bold. Dacă nu există, fallback pe Arial.
            font_path = 'TheBoldFont.ttf' if os.path.exists('TheBoldFont.ttf') else 'Arial'
            
            # --- 1. STRATUL DE UMBRĂ ADÂNCĂ (Deep Shadow) ---
            # Acesta dă contrastul maxim ca să se citească pe orice fundal (chiar și alb)
            shadow = TextClip(txt_str, fontsize=80, color='black', font=font_path, 
                              stroke_color='black', stroke_width=25, method='caption', size=(950, None))
            
            # --- 2. STRATUL DE ATMOSFERĂ (Magenta Glow) ---
            # Un glow secundar mov/roz care dă efectul de "scump"
            atmosphere = TextClip(txt_str, fontsize=80, color='#BD00FF', font=font_path, 
                                  stroke_color='#BD00FF', stroke_width=15, method='caption', size=(950, None)).set_opacity(0.6)
            
            # --- 3. STRATUL PRINCIPAL NEON (Electric Cyan) ---
            # Glow-ul principal, puternic și tăios
            neon = TextClip(txt_str, fontsize=80, color='#00FFFF', font=font_path, 
                            stroke_color='#00FFFF', stroke_width=8, method='caption', size=(950, None)).set_opacity(0.9)
            
            # --- 4. STRATUL CORE (Alb Pur) ---
            # Textul propriu-zis, alb imaculat pentru citire
            white = TextClip(txt_str, fontsize=80, color='white', font=font_path, method='caption', size=(950, None))

            # --- POZIȚIONARE ȘI ANIMATIE "HEARTBEAT" ---
            y_pos = 1450 # Jos, deasupra la gameplay
            
            # Definim funcția de puls: O bătaie rapidă și "agresivă" care cere atenție
            # 1.0 este mărimea normală, 0.04 este intensitatea pulsului (4%), 5 este viteza
            def pulse_anim(t):
                return 1 + 0.04 * np.sin(6 * t)

            layer_stack = [shadow, atmosphere, neon, white]
            
            for el in layer_stack:
                # Aplicăm animația de resize (puls)
                el = el.resize(pulse_anim)
                # Setăm poziția și durata
                el = el.set_position(('center', y_pos)).set_duration(clip.duration)
                elemente.append(el)
                
          except Exception as e: 
            print(f"⚠️ Eroare Text Premium: {e}")

        # E. EXPORT
        voce = genereaza_voce_ai(f"Check out this {TITLU_PRODUS}!")
        final_video = CompositeVideoClip(elemente, size=(W,H))
        
        if voce and os.path.exists(voce):
            v_clip = AudioFileClip(voce).volumex(1.5)
            # Dacă video nu are audio, punem doar vocea
            if clip.audio:
                final_video.audio = CompositeAudioClip([clip.audio.volumex(0.8), v_clip.set_start(0.5)])
            else:
                final_video.audio = v_clip.set_start(0.5)
        
        out_name = os.path.join(PATH_OUTPUT, f"short_{i}_{stil}.mp4")
        print(f"⏳ [RENDER] Scriem: {out_name}")
        final_video.write_videofile(out_name, fps=30, codec='libx264', preset='ultrafast', logger=None)
        
        if voce and os.path.exists(voce): os.remove(voce)

        desc = f"{TITLU_PRODUS}\n\n🛒 BUY HERE:\n👉 {LINK_AFILIERE}\n\n#shorts #amazonfinds #{CONT_TARGET}"
        adauga_in_imperiu(out_name, TITLU_PRODUS, desc, stil)

    clip_mare.close()
    print("\n✅ GATA! Fără erori!")

if __name__ == "__main__":
    main()