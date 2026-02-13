import sqlite3
import os
import sys
import numpy as np
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx
from moviepy.config import change_settings
from moviepy.video.fx.all import crop, resize, gamma_corr, lum_contrast, mirror_x

# --- CONFIGURARE INDUSTRIALĂ ---
DB_NAME = "youtube_empire.db"
FOLDER_OUTPUT = "output"
FFMPEG_FILENAME = "ffmpeg.exe"

# 1. SETĂM CĂILE ABSOLUTE (Ca să nu avem surprize)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_FFMPEG = os.path.join(BASE_DIR, FFMPEG_FILENAME)
PATH_OUTPUT = os.path.join(BASE_DIR, FOLDER_OUTPUT)

# Verificăm FFmpeg
if os.path.exists(PATH_FFMPEG):
    change_settings({"FFMPEG_BINARY": PATH_FFMPEG})
else:
    print(f"⚠️ [CONFIG]: Nu găsesc ffmpeg.exe la: {PATH_FFMPEG}")
    print("   -> Asigură-te că este în același folder cu editor.py!")

# 2. DETECTARE IMAGEMAGICK (Pentru Text)
# Căutăm versiuni comune
potential_paths = [
    r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
    r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
    r"C:\Program Files\ImageMagick-7.1.3-Q16-HDRI\magick.exe"
]

found_magick = False
for path in potential_paths:
    if os.path.exists(path):
        change_settings({"IMAGEMAGICK_BINARY": path})
        print(f"✅ [CONFIG]: ImageMagick detectat: {path}")
        found_magick = True
        break

if not found_magick:
    print("⚠️ [ATENȚIE]: Nu am găsit ImageMagick. Textele NU vor apărea pe video.")

def get_video_descarcat():
    """Găsește un video cu status 'downloaded'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    video = None
    try:
        cursor.execute("SELECT id, cale_fisier, titlu_video FROM videos WHERE status='downloaded' LIMIT 1")
        video = cursor.fetchone()
    except Exception as e:
        print(f"❌ [DB EROARE]: {e}")
    finally:
        conn.close()
    return video

def update_status_final(video_id, cale_finala, status_nou='processed'):
    """Actualizează statusul la 'processed' și salvează calea finală a fișierului editat."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET status=?, cale_fisier=? WHERE id=?", (status_nou, cale_finala, video_id))
    conn.commit()
    conn.close()

def proceseaza_video(cale_input, titlu_produs, id_video):
    print(f"🎬 [EDITOR]: Procesez ID {id_video}...")
    
    # Verificare cale input (poate fi relativă sau absolută, le tratăm pe ambele)
    if not os.path.isabs(cale_input):
        cale_input = os.path.join(BASE_DIR, cale_input)

    if not os.path.exists(cale_input):
        print(f"❌ [EROARE]: Fișierul sursă lipsește fizic: {cale_input}")
        return None

    clip = None
    try:
        # 1. Încărcare
        clip = VideoFileClip(cale_input)
        
        # 2. Speed Up (1.1x) - Pentru retenție
        #clip = clip.fx(vfx.speedx, 1.1)

        # 3. Limitare durată (59s)
        if clip.duration > 59:
            clip = clip.subclip(0, 59)

        # 4. BLUR-STACK EFFECT (Format 9:16)
        # Background
        bg_clip = clip.resize(height=1920) 
        bg_clip = bg_clip.crop(x1=bg_clip.w/2 - 540, width=1080, height=1920)
        bg_clip = bg_clip.fx(vfx.mirror_x)
        bg_clip = bg_clip.resize(0.08).resize(12.5)
        bg_clip = bg_clip.fx(vfx.colorx, 0.35)

        # Main Video
        main_clip = clip.resize(width=1080)
        main_clip = main_clip.set_position("center")
        main_clip = main_clip.fx(vfx.colorx, 1.2) # Culori vibrante

        elemente = [bg_clip, main_clip]

        # 5. TEXTE (Doar dacă avem ImageMagick)
        if found_magick:
            try:
                
                FONT_ALES = 'TheBoldFont.ttf'
                '''
                # Curățăm titlul
                clean_title = ''.join(e for e in titlu_produs if e.isalnum() or e.isspace())[:25].upper()
                
                # Numele fișierului tău de font (trebuie să fie lângă script!)
                
                
                # --- SCHIMBAREA 2: TITLU PREMIUM ---
                # Galben Auriu (#FFD700) + Contur Negru Gros
                txt_sus = TextClip(clean_title, 
                                   fontsize=70, 
                                   color='#FFD700',      # Auriu
                                   font=FONT_ALES,    # Font Gros
                                   stroke_color='black', 
                                   stroke_width=5,       # Contur foarte vizibil
                                   method='caption',
                                   size=(900, None))
                # Poziționat la 15% din înălțime (Sus, vizibil)
                txt_sus = txt_sus.set_position(('center', 200)).set_duration(clip.duration)
                elemente.append(txt_sus)
                '''
                
                # --- MRBEAST STYLE CTA: "THE DOPAMINE STACK" ---

                # 1. LAYER-UL DE BAZĂ (Shadow/Outline) - "Ancora"
                # Rol: Asigură că textul se citește perfect chiar și pe fundal alb sau colorat.
                # MrBeast folosește mereu contur negru gros.
                shadow = TextClip("LINK IN BIO 👇", 
                                 fontsize=75,                # Puțin mai mare
                                 color='black',              # Negru pur
                                 font=FONT_ALES, 
                                 stroke_color='black', 
                                 stroke_width=20,            # Contur MASIV (Outline)
                                 method='caption', size=(950, None))

                # 2. LAYER-UL DE NEON (Glow) - "Atractorul"
                # Rol: Atrage ochiul periferic. Cyan-ul electric este culoarea cu cea mai mare vizibilitate digitală.
                neon = TextClip("LINK IN BIO 👇", 
                                 fontsize=75, 
                                 color='#00FFFF',            # Electric Cyan
                                 font=FONT_ALES, 
                                 stroke_color='#00FFFF', 
                                 stroke_width=8,             # Un glow mediu
                                 method='caption', size=(950, None)).set_opacity(0.8) # Aproape opac!
                
                # 3. LAYER-UL PRINCIPAL (Text) - "Mesajul"
                # Rol: Claritate HD. Albul pe negru/cyan este contrastul suprem.
                text_alb = TextClip("LINK IN BIO 👇", 
                                 fontsize=75, 
                                 color='white',              # Alb Imaculat
                                 font=FONT_ALES, 
                                 method='caption', size=(950, None))
                
                # --- ANIMAȚIA PSIHOLOGICĂ (Heartbeat) ---
                # Facem textul să "respire" (pulseze). Asta creează urgență subconștientă.
                # Funcția sinoidală (sin) face textul să crească și să scadă fin.
                import numpy as np
                
                # Definim poziția (Jos, centrat)
                pos_y = 1450
                
                # Aplicăm animația doar pe Neon și Shadow pentru efect 3D, textul alb rămâne fix sau pulsează ușor
                neon = neon.resize(lambda t: 1 + 0.04 * np.sin(5 * t))  # Puls rapid
                shadow = shadow.resize(lambda t: 1 + 0.04 * np.sin(5 * t)) 
                text_alb = text_alb.resize(lambda t: 1 + 0.04 * np.sin(5 * t))
                
                # Le așezăm în poziție
                shadow = shadow.set_position(('center', pos_y)).set_duration(clip.duration)
                neon = neon.set_position(('center', pos_y)).set_duration(clip.duration)
                text_alb = text_alb.set_position(('center', pos_y)).set_duration(clip.duration)

                # Adăugăm în ordine (Spate -> Față)
                elemente.append(shadow)   # Fundalul negru
                elemente.append(neon)     # Strălucirea
                elemente.append(text_alb) # Textul clar
                
            except Exception as e:
                print(f"⚠️ [TEXT ERROR]: {e}")

        # 6. Export
        final_video = CompositeVideoClip(elemente, size=(1080, 1920))
        
        if not os.path.exists(PATH_OUTPUT):
            os.makedirs(PATH_OUTPUT)
            
        nume_iesire = os.path.join(PATH_OUTPUT, f"short_final_{id_video}.mp4")
        
        print("⏳ [RENDER]: Randează MP4 (asta durează puțin)...")
        # Folosim preset 'ultrafast' pentru viteză maximă și compatibilitate
        final_video.write_videofile(
            nume_iesire,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            bitrate="6000k",
            preset='ultrafast', 
            threads=4,
            logger=None # Ascunde spam-ul, arată doar bara
        )
        
        print(f"✨ [DONE]: Video salvat: {nume_iesire}")
        return nume_iesire

    except Exception as e:
        print(f"❌ [CRITICAL]: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if clip: 
            clip.close()

# --- TEST INDIVIDUAL ---
if __name__ == "__main__":
    task = get_video_descarcat()
    if task:
        cale = proceseaza_video(task[1], task[2], task[0])
        if cale:
            update_status_final(task[0], cale)
            os.startfile(cale)
    else:
        print("💤 Nimic 'downloaded' în bază.")