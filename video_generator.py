import os
import random
import sqlite3
import numpy as np
import pyttsx3 # Vocea AI
import asyncio
import edge_tts
import math
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, vfx, ColorClip, clips_array, AudioFileClip, CompositeAudioClip, ImageClip
from moviepy.video.fx.all import gamma_corr, lum_contrast, mirror_x, speedx, fadein, fadeout

# --- 1. CONFIGURARE IMAGEMAGICK ---
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"}) 

# --- CONFIGURARE GENERALĂ ---
PATH_OUTPUT = "output_videos"
VIDEO_SURSA = "video_brut.mp4"
DB_NAME = "youtube_empire.db"

# --- INPUT INTERACTIV ---
print("\n💎 --- GENERATOR V8.0 (POKER SPLIT EXCLUSIVE | DUAL FACTORY: YT + TIKTOK) ---")
TITLU_PRODUS = input("1. Nume Produs: ").strip()
LINK_AFILIERE = input("2. Link Afiliere: ").strip()
LINK_SURSA = input("3. Sursă Video: ").strip()
CONT_TARGET = input("4. Cont Target(Gadgets): ").strip()
START_SEC = input("5. Secunda de start (ex: 120 pt min 2:00) [Lasă GOL pt Automat]: ").strip()

if not TITLU_PRODUS or not LINK_AFILIERE: exit()

# --- 3. FUNCȚII AUXILIARE ---
def resize_to_fill(clip, target_w, target_h):
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
    VOICE = "en-US-ChristopherNeural" 
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(nume_fisier)

def genereaza_voce_ai(text):
    nume_fisier = "voce_temp.mp3"
    try:
        asyncio.run(_genereaza_voce_async(text, nume_fisier))
        if os.path.exists(nume_fisier): return nume_fisier
        return None
    except Exception as e:
        print(f"⚠️ [VOCE EROARE]: {e}")
        return None

def extrage_pret_amazon(url_amazon):
    print(f"🔍 [SCRAPER]: Verific prețul pe Amazon...")
    options = Options()
    options.add_argument("--headless")  # Nu deschide fereastra Chrome
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Pasul 1: Mergem pe Amazon US direct pentru a seta un cookie de regiune
        driver.get("https://www.amazon.com/?language=en_US&currency=USD")
        driver.add_cookie({"name": "i18n-prefs", "value": "USD", "domain": ".amazon.com"})
        driver.add_cookie({"name": "lc-main", "value": "en_US", "domain": ".amazon.com"})
        
        # Pasul 2: Mergem la produsul tău
        separator = "&" if "?" in url_amazon else "?"
        url_final = f"{url_amazon}{separator}language=en_US&currency=USD"
        
        driver.get(url_final)
        time.sleep(5) # Lăsăm timp pentru redirectările de monedă

        # Pasul 3: Extracție cu verificare
        try:
            # Luăm partea întreagă
            pret_raw = driver.find_element(By.CLASS_NAME, "a-price-whole").text
            # Luăm zecimalele
            zecimale_raw = driver.find_element(By.CLASS_NAME, "a-price-fraction").text
            
            # Curățăm orice caracter non-numeric (scot puncte/virgule de RO)
            pret_curat = "".join(filter(str.isdigit, pret_raw))
            zecimale_curat = "".join(filter(str.isdigit, zecimale_raw))

            if not pret_curat:
                # Uneori prețul e în altă clasă dacă e ofertă fulger
                pret_alt = driver.find_element(By.ID, "priceblock_ourprice").text
                pret_final = pret_alt
            else:
                pret_final = f"${pret_curat}.{zecimale_curat}"
        except:
            pret_final = "Check Price"

        # Extracție Reducere
        reducere = None
        try:
            reducere = driver.find_element(By.CLASS_NAME, "savingsPercentage").text.replace('-', '').strip()
        except:
            pass

        print(f"💰 [SUCCES]: Preț final setat: {pret_final} ({reducere if reducere else 'No Disc'})")
        return pret_final, reducere

    except Exception as e:
        print(f"⚠️ [SCRAPER EROARE]: {e}")
        return "Check Price", None
    finally:
        driver.quit()
def adauga_in_imperiu(cale, titlu, descriere, stil):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        url_u = f"{LINK_SURSA}_{stil}_{random.randint(1000,9999)}"
        cursor.execute("INSERT INTO videos (sursa_url, affiliate_link, cont_target, titlu_video, descriere, cale_fisier, status) VALUES (?,?,?,?,?,?, 'pending')", 
                       (url_u, LINK_AFILIERE, CONT_TARGET, titlu, descriere, cale))
        conn.commit()
        conn.close()
    except Exception as e: print(f"⚠️ DB Error: {e}")

# --- 4. ENGINE PRINCIPAL ---
def main():
    if not os.path.exists(PATH_OUTPUT): os.makedirs(PATH_OUTPUT)
    if not os.path.exists(VIDEO_SURSA):
        print(f"❌ Lipsă '{VIDEO_SURSA}'! Rulează downloader.")
        return

    print(f"\n🎬 Procesez: {TITLU_PRODUS}")
    
    pret_real, reducere_reala = extrage_pret_amazon(LINK_AFILIERE)
    
    try: clip_mare = VideoFileClip(VIDEO_SURSA)
    except: return

    durata_totala = clip_mare.duration
    W, H = 1080, 1920 
    
    # 🔥 AICI ESTE MAGIA: Definim linia de producție dublă
    platforme = [
        {
            "nume": "youtube", 
            "folder": os.path.join("assets", "pokerclips"), 
            "limita": 58,
            "tags_specifice": "#poker #pokerstars #ggpoker"
        },
        {
            "nume": "tiktok", 
            "folder": os.path.join("assets", "tikclips"), 
            "limita": 15,
            "tags_specifice": "#gta5 #gta6"
        }
    ]

    # LOOP 1: Trecem prin fiecare platformă
    for config in platforme:
        nume_plat = config["nume"]
        folder_bg = config["folder"]
        limita_max = config["limita"]
        
        print(f"\n==================================================")
        print(f"🚀 PORNIM LINIA DE PRODUCȚIE PENTRU: {nume_plat.upper()}")
        print(f"==================================================")

        # LOOP 2: Generăm cele 5 variante pentru platforma curentă
        for i in range(5):
            print(f"\n🔨 Varianta {i+1}/5: {nume_plat.upper()} SPLIT SCREEN (50/50)")
            
            # A. CALCUL TIMP (Adaptat la platformă)
            start_t = 0
            durata_ideala = min(durata_totala, limita_max)
            
            # Logica de Start (Manual vs Automat)
            if START_SEC.isdigit():
                start_t = int(START_SEC) + (i * durata_ideala)
            else:
                if durata_totala > limita_max:
                    # Distribuim cele 5 clipuri de-a lungul videoclipului sursă
                    start_t = ((durata_totala - limita_max) / 5) * i + random.randint(0, 3)
            
            if start_t + durata_ideala > durata_totala: 
                start_t = max(0, durata_totala - durata_ideala)
            
            # Tăiem reclama
            clip = clip_mare.subclip(start_t, start_t + durata_ideala)

            # B. VIZUAL - 50/50 EXACT
            elemente = []
            target_top_h = int(H * 0.50)   # 50% FIX pentru Produs
            target_bot_h = int(H * 0.50)   # 50% FIX pentru Poker
        
            clip_top = resize_to_fill(clip, W, target_top_h)

            if os.path.exists(folder_bg) and os.listdir(folder_bg):
                  try:
                      bg_path = os.path.join(folder_bg, random.choice(os.listdir(folder_bg)))
                      bg_clip = VideoFileClip(bg_path)
                    
                      if bg_clip.duration < clip.duration: 
                          bg_clip = bg_clip.loop(duration=clip.duration)
                      else:
                          r_start = random.uniform(0, bg_clip.duration - clip.duration)
                          bg_clip = bg_clip.subclip(r_start, r_start + clip.duration)
                    
                      clip_bot = resize_to_fill(bg_clip, W, target_bot_h)
                      clip_final_split = clips_array([[clip_top], [clip_bot]])
                  except Exception as e: 
                      print(f"⚠️ Eroare la bg clip ({nume_plat}): {e}")
                      clip_final_split = resize_to_fill(clip, W, H)
            else: 
                print(f"⚠️ Nu ai videoclipuri în folderul {folder_bg}!")
                clip_final_split = resize_to_fill(clip, W, H)

            elemente.append(clip_final_split)

            # --- C. ELEMENTE GRAFICE PREMIUM (V8.5) ---
        
            y_baza = int(H * 0.40) # Ambele stau FIX în același loc
            offset_text = 109      # Reglajul pentru centrarea textului în cadran
        
            # 1. FUNCȚIILE DE OPACITATE PURE
            def op_pret(t):
                return max(0.0, min(1.0, (math.cos((t - 6.0) * math.pi) + 1) / 2))

            def op_buton(t):
                return 1.0 - op_pret(t)

            # 2. BUTONUL GET LINK (Fundal 1)
            if os.path.exists("buton_bio.png"):
                # FĂRĂ has_mask=True, MoviePy detectează singur PNG-ul
                btn_bio = ImageClip("buton_bio.png").resize(width=450).set_duration(clip.duration - 6.0)
                btn_bio = btn_bio.set_position(('center', y_baza)).set_start(6.0)
                
                # Aplicăm opacitatea DOAR pe mască (pe transparență)
                if btn_bio.mask is not None:
                    btn_bio.mask = btn_bio.mask.fl(lambda gf, t: gf(t) * op_buton(t))
                elemente.append(btn_bio)

            # 3. CADRUL DE PREȚ (Fundal 2)
            if os.path.exists("forma_pret.png"):
                img_pret = ImageClip("forma_pret.png").resize(width=450).set_duration(clip.duration - 6.0)
                img_pret = img_pret.set_position(('center', y_baza)).set_start(6.0)
                
                # Aplicăm opacitatea DOAR pe mască
                if img_pret.mask is not None:
                    img_pret.mask = img_pret.mask.fl(lambda gf, t: gf(t) * op_pret(t))
                elemente.append(img_pret)

                # 4. TEXTUL PREȚULUI (Cel mai în față)
                p_val = pret_real if pret_real else "Check Price"
                r_val = f"{reducere_reala} OFF! | " if reducere_reala else ""
                txt_p = TextClip(f"{r_val}{p_val}", fontsize=35, color='white', font='TheBoldFont.ttf')
                txt_p = txt_p.set_position(('center', y_baza + offset_text)).set_start(6.0).set_duration(clip.duration - 6.0)
                
                # Și textul are mască, o manipulăm la fel
                if txt_p.mask is not None:
                    txt_p.mask = txt_p.mask.fl(lambda gf, t: gf(t) * op_pret(t))
                elemente.append(txt_p) # Rămâne cel mai în față

            # 5. TRUST BADGE
            if os.path.exists("trust_badge.png"):
                badge = ImageClip("trust_badge.png").resize(width=150).set_duration(clip.duration - 6.0)
                badge = badge.set_position((W - 170, int(H * 0.05))).set_start(6.0).crossfadein(0.5)
                elemente.append(badge)

            # 6. BARA DE PROGRES
            bar_h = 12
            p_bar = ColorClip(size=(W, bar_h), color=(255,0,0), duration=clip.duration)
            p_bar = p_bar.resize(lambda t: (max(1, int(W * (t / clip.duration))), bar_h)).set_position(('left', 'bottom'))
            elemente.append(p_bar)

            # D. EXPORT
            final_video = CompositeVideoClip(elemente, size=(W,H))
            
            if clip.audio and 'bg_clip' in locals() and bg_clip.audio:
                audio_mixat = CompositeAudioClip([
                    clip.audio.volumex(0.05),        
                    bg_clip.audio.volumex(1.0) # Se aplică la fel și pt Poker și pt GTA
                ])
                final_video.audio = audio_mixat
            
            # 🔥 NOU: Adăugăm un timestamp (Timpul exact) ca să nu se suprascrie NICIODATĂ
            timestamp = int(time.time())
            out_name = os.path.join(PATH_OUTPUT, f"{nume_plat}_{timestamp}_var_{i+1}.mp4")
            print(f"⏳ [RENDER] Scriem: {out_name}")
            final_video.write_videofile(out_name, fps=30, codec='libx264', preset='ultrafast', logger=None)
            
            # --- DESCRIEREA "SEO BOMBER" PREMIUM ---
            desc_SEO = f"""Get The {TITLU_PRODUS} Here! 🤯👇
        
🛒 GET THE LINK:
👉 Go to my Channel/Profile BIO!
(🔗 linktr.ee/GadgetHunterShop)


🌟 Why you need this gadget:
This is one of the best Amazon finds of 2026! If you love cool tech and home hacks, this video is for you. Don't forget to subscribe for daily product hunting!

🔍 Search Tags:
#shorts #amazonfinds #gadgets #tech #musthaves #tiktokmademebuyit #giftideas #productreview {config['tags_specifice']} #{CONT_TARGET}

🛑 Disclaimer:
As an Amazon Associate, I earn from qualifying purchases. This helps support the channel!

🎥 Video Credit: {LINK_SURSA}
"""
        
        # 🔥 SALVĂM ÎN BAZA DE DATE DOAR PENTRU YOUTUBE
            if nume_plat == "youtube":
                # Cream o lista de variatii vizuale ca sa facem fiecare titlu unic
                emoji_spin = ["🤯", "🔥", "👀", "✨", "💯"]
                titlu_unic = f"{TITLU_PRODUS} {emoji_spin[i]}" # Adaugă un emoji diferit pt fiecare din cele 5
                adauga_in_imperiu(out_name, titlu_unic, desc_SEO, f"{nume_plat}_{i+1}")
                print(f"📥 [DB] Salvat automat în pending: {out_name}")
            else:
                print(f"⏭️ [SKIP DB] Pregătit pentru upload manual: {out_name}")

    clip_mare.close()
    print("\n✅ FABRICA A TERMINAT! Ai 5 clipuri pentru YouTube și 5 pentru TikTok în folderul 'output_videos'.")

if __name__ == "__main__":
    main()