import os
import random
import sqlite3
import numpy as np
import pyttsx3 # Vocea AI
import asyncio
import edge_tts
import math
import time
import logging
import gc
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, vfx, ColorClip, clips_array, AudioFileClip, CompositeAudioClip, ImageClip
from moviepy.video.fx.all import gamma_corr, lum_contrast, mirror_x, speedx, fadein, fadeout

LIMITA_CLIP_SECUNDE = 28  # sincronizat cu database.py
DB_NAME = "youtube_empire.db"

def init_poker_tracker():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS poker_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fisier TEXT UNIQUE,
            secunda_curenta REAL DEFAULT 0,
            durata_totala REAL,
            epuizat INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_durata_video(cale):
    try:
        clip_temp = VideoFileClip(cale)
        durata = clip_temp.duration
        clip_temp.close()
        return durata
    except Exception as e:
        print(f"⚠️ Eroare la citire durată: {e}")
        return 0

def get_urmatorul_segment_poker(folder_poker, limita):
    conn = sqlite3.connect(DB_NAME)
    
    if not os.path.exists(folder_poker):
        conn.close()
        return None, None, None, None, None
        
    fisiere = sorted([f for f in os.listdir(folder_poker) if f.endswith('.mp4')])
    
    for idx, fisier in enumerate(fisiere):
        cale_completa = os.path.join(folder_poker, fisier)
        
        row = conn.execute(
            "SELECT secunda_curenta, durata_totala, epuizat FROM poker_tracker WHERE fisier = ?",
            (fisier,)
        ).fetchone()
        
        if row is None:
            durata = get_durata_video(cale_completa)
            conn.execute(
                "INSERT INTO poker_tracker (fisier, secunda_curenta, durata_totala) VALUES (?, 0, ?)",
                (fisier, durata)
            )
            conn.commit()
            secunda_curenta, durata_totala, epuizat = 0, durata, 0
        else:
            secunda_curenta, durata_totala, epuizat = row
        
        if epuizat:
            continue
            
        secunde_ramase = durata_totala - secunda_curenta
        
        if secunde_ramase < limita:
            conn.execute(
                "UPDATE poker_tracker SET epuizat = 1 WHERE fisier = ?",
                (fisier,)
            )
            conn.commit()
            print(f"🗑️ [{fisier}] epuizat — {secunde_ramase:.1f}s rămase. Aruncat.")
            continue
        
        start = secunda_curenta
        end = start + limita
        
        # ✅ Calculăm sezon și episod
        sezon = idx + 1
        conn2 = sqlite3.connect(DB_NAME)
        row_ep = conn2.execute("""
            SELECT numar_episod FROM videos 
            WHERE status IN ('uploaded', 'pending')
            AND numar_episod > 0
            ORDER BY numar_episod DESC 
            LIMIT 1
        """).fetchone()
        conn2.close()

        episod = 1
        if row_ep and row_ep[0]:
            episod = row_ep[0] + 1
        
        conn.execute(
            "UPDATE poker_tracker SET secunda_curenta = ? WHERE fisier = ?",
            (end, fisier)
        )
        conn.commit()
        
        secunde_dupa = durata_totala - end
        clipuri_ramase = int(secunde_dupa // limita)
        
        if clipuri_ramase <= 2:
            print(f"⚠️  ALARMĂ: [{fisier}] mai are doar {clipuri_ramase} clip(uri)!")
            print(f"   Descarcă un nou clip de poker cât mai curând!")
            print(f"♠️ [POKER] {fisier} | S{sezon} E{episod} | {start:.0f}s → {end:.0f}s")
        
        conn.close()
        return cale_completa, start, end, sezon, episod
    
    conn.close()
    print("🚨 CRITIC: Toate clipurile de poker sunt EPUIZATE!")
    print("   Descarcă imediat clipuri noi în assets/pokerclips/")
    return None, None, None, None, None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("engine.log"),
        logging.StreamHandler()
    ]
)

# ============================================================
# 🔄 POOL DE USER AGENTS — Rotație automată la fiecare call
# ============================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# ============================================================
# 💾 CACHE DB — Evităm request-uri inutile (6 ore TTL)
# ============================================================
CACHE_TTL_ORE = 6

def init_cache_db():
    """Creează tabela de cache dacă nu există."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pret_cache (
            url TEXT PRIMARY KEY,
            pret TEXT,
            reducere TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

def get_din_cache(url_amazon):
    """Returnează (pret, reducere) din cache dacă e fresh, altfel None."""
    try:
        conn = sqlite3.connect(DB_NAME)
        row = conn.execute(
            "SELECT pret, reducere FROM pret_cache WHERE url=? AND timestamp > ?",
            (url_amazon, time.time() - CACHE_TTL_ORE * 3600)
        ).fetchone()
        conn.close()
        if row:
            logging.info(f"💾 [CACHE HIT]: Preț din cache: {row[0]}")
            return row[0], row[1]
        return None, None
    except Exception as e:
        logging.warning(f"⚠️ [CACHE READ ERROR]: {e}")
        return None, None

def salveaza_in_cache(url_amazon, pret, reducere):
    """Salvează prețul în cache cu timestamp curent."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute(
            "INSERT OR REPLACE INTO pret_cache (url, pret, reducere, timestamp) VALUES (?,?,?,?)",
            (url_amazon, pret, reducere, time.time())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(f"⚠️ [CACHE WRITE ERROR]: {e}")

# ============================================================
# 🛡️ STEALTH OPTIONS — Configurare Chrome anti-detectie
# ============================================================
def build_driver():
    """Construiește un driver Chrome cu setări stealth."""
    options = Options()
    options.add_argument("--headless=new")           # Noul headless (Chrome 112+), mai greu de detectat
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")   # 🔄 Rotație

    # Eliminăm semnăturile de automation
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Patch JS: ascunde navigator.webdriver (detectat de Amazon)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver

# ============================================================
# 🔍 EXTRACTOR PREȚ — Cu fallback pe mai multe selectori
# ============================================================
PRICE_SELECTORS = [
    # Selector 1: Standard (cel mai comun)
    (By.CLASS_NAME, "a-price-whole"),
    # Selector 2: Oferte fulger / Subscribe & Save
    (By.CSS_SELECTOR, "#priceblock_ourprice"),
    (By.CSS_SELECTOR, "#priceblock_dealprice"),
    # Selector 3: Layout nou Amazon (2024+)
    (By.CSS_SELECTOR, "span.a-offscreen"),
    # Selector 4: Clasa generică de preț
    (By.CSS_SELECTOR, ".a-price .a-offscreen"),
]

def extrage_pret_din_pagina(driver):
    """
    Încearcă toți selectorii în ordine.
    Returnează (pret_str, reducere_str) sau ("Check Price", None).
    """
    pret_final = "Check Price"
    reducere = None

    # --- Încearcă metoda principală (whole + fraction) ---
    try:
        # Așteptăm explicit elementul în loc de sleep fix
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "a-price-whole"))
        )
        pret_raw = driver.find_element(By.CLASS_NAME, "a-price-whole").text
        zecimale_raw = driver.find_element(By.CLASS_NAME, "a-price-fraction").text

        pret_curat = "".join(filter(str.isdigit, pret_raw))
        zecimale_curat = "".join(filter(str.isdigit, zecimale_raw))

        if pret_curat:
            pret_final = f"${pret_curat}.{zecimale_curat}"
            logging.info(f"✅ Selector primar OK: {pret_final}")
            # Nu returnăm încă — mai extragem și reducerea
    except Exception:
        logging.info("⏭️ Selector primar eșuat, încerc fallback-uri...")

    # --- Fallback dacă metoda principală a eșuat ---
    if pret_final == "Check Price":
        for by, selector in PRICE_SELECTORS[1:]:
            try:
                elem = driver.find_element(by, selector)
                text = elem.get_attribute("textContent") or elem.text
                text = text.strip()
                if text and "$" in text:
                    pret_final = text.split("\n")[0].strip()
                    logging.info(f"✅ Fallback selector '{selector}' OK: {pret_final}")
                    break
            except Exception:
                continue

    # --- Extracție reducere ---
    reducere_selectors = [
        (By.CLASS_NAME, "savingsPercentage"),
        (By.CSS_SELECTOR, "#savingsPercentage"),
        (By.CSS_SELECTOR, ".a-color-price.a-size-base.a-text-bold"),
    ]
    for by, selector in reducere_selectors:
        try:
            reducere_text = driver.find_element(by, selector).text
            reducere = reducere_text.replace("-", "").replace("%", "").strip() + "%"
            logging.info(f"🏷️ Reducere găsită: {reducere}")
            break
        except Exception:
            continue

    return pret_final, reducere

# ============================================================
# 🚀 FUNCȚIA PRINCIPALĂ — Cu cache + retry + cleanup garantat
# ============================================================
def extrage_pret_amazon(url_amazon, retry=2):
    """
    Extrage prețul de pe Amazon cu:
    - Cache de 6 ore (evită request-uri inutile)
    - User-agent rotation (evită blocarea)
    - WebDriverWait în loc de sleep fix
    - Fallback pe mai mulți selectori
    - Retry automat la eșec
    - Cleanup garantat al driver-ului
    """
    logging.info(f"🔍 [SCRAPER]: Start pentru URL: {url_amazon[:60]}...")

    # 1. Verificăm cache-ul mai întâi
    init_cache_db()
    pret_cache, reducere_cache = get_din_cache(url_amazon)
    if pret_cache:
        return pret_cache, reducere_cache

    # 2. Scraping cu retry
    for attempt in range(1, retry + 1):
        driver = None
        try:
            logging.info(f"🌐 [Attempt {attempt}/{retry}]: Deschidem Chrome...")
            driver = build_driver()

            # Setăm cookies de regiune ÎNAINTE de a merge pe produs
            driver.get("https://www.amazon.com/?language=en_US")
            driver.add_cookie({"name": "i18n-prefs", "value": "USD", "domain": ".amazon.com"})
            driver.add_cookie({"name": "lc-main",    "value": "en_US", "domain": ".amazon.com"})

            # Construim URL-ul final
            separator = "&" if "?" in url_amazon else "?"
            url_final = f"{url_amazon}{separator}language=en_US&currency=USD"
            driver.get(url_final)

            # Delay random — comportament uman, nu robotic
            time.sleep(random.uniform(3.0, 6.5))

            # Verificăm dacă Amazon ne-a dat CAPTCHA
            if "robot" in driver.title.lower() or "captcha" in driver.page_source.lower():
                logging.warning(f"🤖 [CAPTCHA DETECTAT] la attempt {attempt}!")
                time.sleep(random.uniform(10, 20))  # Așteptăm mai mult înainte de retry
                continue

            pret, reducere = extrage_pret_din_pagina(driver)

            # 3. Salvăm în cache și returnăm
            salveaza_in_cache(url_amazon, pret, reducere)
            logging.info(f"💰 [SUCCES]: {pret} | Reducere: {reducere or 'N/A'}")
            return pret, reducere

        except Exception as e:
            logging.error(f"⚠️ [SCRAPER EROARE] Attempt {attempt}: {e}")
            if attempt == retry:
                return "Check Price", None
            time.sleep(random.uniform(5, 12))  # Pauză între retry-uri

        finally:
            # ✅ CLEANUP GARANTAT — se execută mereu, indiferent de eroare
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass

    return "Check Price", None

# --- 1. CONFIGURARE IMAGEMAGICK ---
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"}) 

# --- CONFIGURARE GENERALĂ ---
PATH_OUTPUT = "output_videos"
VIDEO_SURSA = input("6. Fișier video sursă (ex: ninja_brut.mp4): ").strip() or "video_brut.mp4"

# --- INPUT INTERACTIV ---
print("\n💎 --- GENERATOR V8.0 (POKER SPLIT EXCLUSIVE | DUAL FACTORY: YT + TIKTOK) ---")
LINK_AFILIERE = input("1. Link Afiliere: ").strip()
LINK_SURSA = input("2. Sursă Video: ").strip()
CONT_TARGET = input("3. Cont Target(Gadgets): ").strip()
START_SEC = input("4. Secunda de start (ex: 120 pt min 2:00) [Lasă GOL pt Automat]: ").strip()

print("\n🎬 TIP CONȚINUT POKER:")
print("1. ♠️  Episoade Seriale (poker[x].mp4) → badge S/E")
print("2. 🏆 Best Moments     (best[x].mp4)  → fără badge")
tip_ales = input("\nAlegere (1/2): ").strip()
TIP_CONTINUT = "poker" if tip_ales == "1" else "best"

if not LINK_AFILIERE: exit()

# --- 3. FUNCȚII AUXILIARE ---
def resize_to_fill(clip, target_w, target_h):
    if clip.w == 0 or clip.h == 0: return clip
    scale_x = target_w / clip.w
    scale_y = target_h / clip.h
    final_scale = max(scale_x, scale_y) + 0.01
    
    try:
        clip_resized = clip.resize(final_scale)
        return clip_resized.crop(x_center=clip_resized.w/2, y_center=clip_resized.h/2, width=target_w, height=target_h)
    except (ValueError, AttributeError) as e:
        print(f"⚠️ resize_to_fill error: {e}")
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

def adauga_in_imperiu(cale, titlu, descriere, stil, episod):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        url_u = f"{LINK_SURSA}_{stil}_{random.randint(1000,9999)}"
        cursor.execute("INSERT INTO videos (sursa_url, affiliate_link, cont_target, titlu_video, descriere, cale_fisier, status, numar_episod) VALUES (?,?,?,?,?,?, 'pending', ?)", 
                       (url_u, LINK_AFILIERE, CONT_TARGET, titlu, descriere, cale, episod))
        conn.commit()
        conn.close()
    except Exception as e: print(f"⚠️ DB Error: {e}")
    
def op_pret(t):
    return max(0.0, min(1.0, (math.cos((t - 6.0) * math.pi) + 1) / 2))

def op_buton(t):
    return 1.0 - op_pret(t)

# --- 4. ENGINE PRINCIPAL ---
def main():
    init_poker_tracker()
    if not os.path.exists(PATH_OUTPUT): os.makedirs(PATH_OUTPUT)
    if not os.path.exists(VIDEO_SURSA):
        print(f"❌ Lipsă '{VIDEO_SURSA}'! Rulează downloader.")
        return
    
    pret_real, reducere_reala = extrage_pret_amazon(LINK_AFILIERE)
    
    try: clip_mare = VideoFileClip(VIDEO_SURSA)
    except: return

    durata_totala = clip_mare.duration
    W, H = 1080, 1920 
    
    # ==========================================
    # 🗄️ BAZA DE DATE A PRODUSELOR (Combustibilul)
    # ==========================================
    # Aici doar adaugi produse noi când le găsești pe Amazon. Nu te atingi de restul codului!

    inventar_produse = {
     "toloco": {
        "nume": "Toloco Massage Gun",
        "tags_nisa": "#massagegun #backpainrelief",
        "hooks": [
            "I FIRED MY MASSAGE THERAPIST",        # 🔥 Șocant
            "MY BACK STOPPED HURTING INSTANTLY",   # 😮 Serios/rezultat
            "POV YOUR BACK PAIN IS GONE",          # 👁️ POV
            "THERAPISTS HATE THIS CHEAP THING",    # 😂 Amuzant
            "I SPENT $0 ON MASSAGES NOW"           # 😂 Amuzant/cifră
        ],
        "titluri": [
            "This Massage Gun Destroyed My Pain",
            "I Cancelled Every Massage Appointment",
            "My Back Finally Stopped Hurting Forever",
            "This Thing Replaced My Massage Therapist",
            "I Fixed My Back For $50"
        ]
      },
     "air_purifier": {
        "nume": "Air Purifier",
        "tags_nisa": "#airpurifier #blueair",
        "hooks": [
            "I WAS BREATHING POISON DAILY",        # 🔥 Șocant
            "MY ALLERGIES DISAPPEARED OVERNIGHT",  # 😮 Serios/rezultat
            "POV YOUR HOME AIR IS TOXIC",          # 👁️ POV
            "MY LUNGS FINALLY FILED A COMPLAINT",  # 😂 Amuzant
            "I TESTED MY AIR AND PANICKED"         # 😂 Amuzant/tensiune
        ],
        "titluri": [
            "I Was Breathing Poison Every Night",
            "This Device Changed My Home Air Forever",
            "My Allergies Disappeared After One Week",
            "I Finally Tested My Home Air Quality",
            "This Air Purifier Shocked My Doctor"
        ]
      },
     "ninja_airfryer": {
         "nume": "Ninja Air Fryer",
         "tags_nisa": "#airfryer #ninja #cooking",
         "hooks": [
             "MY OVEN STAYS OFF FOREVER",           # 🔥 Șocant
             "I COOK FASTER THAN DOORDASH NOW",     # 😮 Serios/rezultat
             "POV YOUR OVEN COLLECTS DUST",         # 👁️ POV
             "MY OVEN IS COLLECTING DUST NOW",      # 😂 Amuzant
             "I APOLOGIZED TO MY AIRFRYER TODAY"    # 😂 Amuzant/absurd
        ],
         "titluri": [
             "My Oven Has Been Off For Months",
             "This Air Fryer Replaced My Entire Kitchen",
             "I Cook Everything In This One Thing",
             "My Gas Bill Dropped After This Purchase",
             "This Changed How I Cook Forever"
        ]
      },
     "wyze_scale": {
         "nume": "Wyze Smart Scale",
         "tags_nisa": "#smartscale #fitness #weightloss",
         "hooks": [
             "MY SCALE LIED FOR YEARS",             # 🔥 Șocant
             "I FINALLY KNOW MY REAL BODY",         # 😮 Serios/rezultat
             "POV YOUR SCALE IS LYING TO YOU",      # 👁️ POV
             "MY OLD SCALE WAS A PATHOLOGICAL LIAR",# 😂 Amuzant
             "I SUED MY SCALE FOR DEFAMATION"       # 😂 Amuzant/absurd
        ],
         "titluri": [
             "My Scale Was Lying To Me For Years",
             "This Smart Scale Knows Everything About Me",
             "I Finally Know My Real Body Stats",
             "My Doctor Was Shocked By This Scale",
             "This Scale Changed My Fitness Forever"
        ]

      },
     "hozo_ruler": {
         "nume": "HOZO NeoRulerGo",
         "tags_nisa": "#gadgets #diytool #cooltech",
         "hooks": [
             "MY CONTRACTOR HATES THIS THING",      # 🔥 Șocant
             "I MEASURED EVERYTHING IN SECONDS",    # 😮 Serios/rezultat
             "POV YOUR TAPE MEASURE IS USELESS",    # 👁️ POV
             "MY TAPE MEASURE RETIRED LAST WEEK",   # 😂 Amuzant
             "I MEASURED MY WHOLE HOUSE IN MINUTES" # 😂 Amuzant/exagerare
        ],
         "titluri": [
             "This Ruler Reads Your Mind",
             "My Contractor Hates This $40 Device",
             "I Measured My Entire House In Minutes",
             "This Thing Replaced Every Measuring Tool",
             "My Tape Measure Retired Last Week"
        ]
      },
     "ninja_crispi": {
         "nume": "Ninja CRISPi 4in1 Airfryer",
         "tags_nisa": "#airfryer #ninja #cooking #kitchengadgets #foodtiktok",
          "hooks": [
              "I FIRED MY PERSONAL CHEF",            # 🔥 Șocant
              "I COOK LIKE GORDON RAMSAY NOW",       # 😮 Serios/rezultat
              "POV YOU JUST ENTERED YOUR CHEF ERA",  # 👁️ POV
              "GORDON RAMSAY WOULD BE JEALOUS",      # 😂 Amuzant
              "MY MICROWAVE FEELS PERSONALLY ATTACKED" # 😂 Amuzant/absurd
        ],
          "titluri": [
              "This Air Fryer Changed Everything Forever",
              "I Fired My Personal Chef Last Week",
              "My Kitchen Will Never Be The Same",
              "I Cook Like Gordon Ramsay Now",
              "This 4in1 Airfryer Broke The Internet"
        ]
      }
    }
    
    # ==========================================
    # 🏆 BEST MOMENTS — Timestamp-uri manuale
    # ==========================================
    best_moments = {
        "best2.mp4": [123, 275, 401, 502, 556, 690],
    }
    
    # ==========================================
    # 🕹️ PANOUL DE CONTROL (Ce producem azi?)
    # ==========================================
    # Asta e SINGURA linie pe care o modifici dimineața. Îi spui fabricii ce să proceseze.
    ID_PRODUS_CURENT = "hozo_ruler"  # <--- Schimbi aici din 'toloco' în 'sleep_mask'
 
    # Sistemul extrage automat datele produsului:
    produs_activ = inventar_produse[ID_PRODUS_CURENT]
    
    print(f"\n🎬 Procesez: {produs_activ['nume']}")
    
    
    # ==========================================
    # 🏭 INFRASTRUCTURA DE POSTARE (Motorul)
    # ==========================================
    # Definim linia de producție dublă
    platforme = [
        {
            "nume": "youtube", 
            "folder": os.path.join("assets", "pokerclips"), 
            "limita": 28, ## ← SCHIMBI din 58 în 28
            "tags_specifice": f"#poker #pokerstars #ggpoker {produs_activ['tags_nisa']}"
        },
        {
            "nume": "tiktok", 
            "folder": os.path.join("assets", "tikclips"), 
            "limita": 15,
            "tags_specifice": f"#gta5 #gta6 {produs_activ['tags_nisa']}"
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
        for i in range(2):
            
            print(f"\n🔨 Varianta {i+1}/2: {nume_plat.upper()} SPLIT SCREEN (50/50)")
            
            bg_clip = None
            clip_bot = None
            sfx_whoosh = None
            sfx_pop = None
            clip_final_split = None
            bg_path = None      
            seg_start = None
            seg_end = None 
            
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
            
            sezon = 1
            episod = 1

            if os.path.exists(folder_bg) and os.listdir(folder_bg):
                  try:
                      # ✅ EPISODIC — consumă secvențial, nu random
                      if nume_plat == "youtube":
                          if TIP_CONTINUT == "poker":
                              bg_path, seg_start, seg_end, sezon, episod = get_urmatorul_segment_poker(folder_bg, limita_max)
                          else:
                              fisiere_best = sorted([f for f in os.listdir(folder_bg) if f.startswith('best') and f.endswith('.mp4')])
                              if not fisiere_best:
                                  print("❌ Nu există fișiere best*.mp4 în pokerclips!")
                                  continue
                              bg_path = os.path.join(folder_bg, random.choice(fisiere_best))
                              bg_clip_temp = VideoFileClip(bg_path)
                              nume_fisier = os.path.basename(bg_path)
                              secunde_disponibile = best_moments.get(nume_fisier, None)
                              if secunde_disponibile:
                                  seg_start = float(random.choice(secunde_disponibile))
                                  print(f"🏆 Best moment selectat: {nume_fisier} la secunda {seg_start}")
                              else:
                                  seg_start = random.uniform(0, bg_clip_temp.duration - limita_max)
                                  print(f"🎲 Random fallback: {nume_fisier} la secunda {seg_start:.1f}")
                              seg_end = seg_start + limita_max
                              bg_clip_temp.close()
                              sezon, episod = None, None
                          if bg_path is None:
                              print(f"❌ Nu există clipuri poker disponibile!")
                              clip_final_split = resize_to_fill(clip, W, H)
                              elemente.append(clip_final_split)
                              continue
                          bg_clip = VideoFileClip(bg_path).subclip(seg_start, seg_end)
                      else:
                          # TikTok rămâne random ca înainte
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
            
            # ✅ HOOK TEXT PREMIUM — primele 2.5 secunde
            if os.path.exists("BebasNeue-Regular.ttf"):
    
                hook_cuvinte = random.choice(produs_activ['hooks']).split()
                str_inainte = hook_cuvinte[0]
                str_auriu = hook_cuvinte[1] if len(hook_cuvinte) > 1 else ""
                str_dupa = " ".join(hook_cuvinte[2:])

                def adauga_hook_simplu(text, start, durata):
                    # STROKE — 4 shadow-uri negre
                    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                        s = TextClip(text, fontsize=58, color='black',
                                     font='BebasNeue-Regular.ttf',
                                     method='caption', size=(950, None), align='center')
                        s = (s.set_position(('center', int(H * 0.18) + dy))
                              .set_opacity(0.9)
                              .set_start(start).set_duration(durata)
                              .fadein(0.1).fadeout(0.2))
                        elemente.append(s)
                    # TEXT ALB
                    t = TextClip(text, fontsize=58, color='white',
                                 font='BebasNeue-Regular.ttf',
                                 method='caption', size=(950, None), align='center')
                    t = (t.set_position(('center', int(H * 0.18)))
                          .set_start(start).set_duration(durata)
                          .fadein(0.1).fadeout(0.2))
                    elemente.append(t)

                # HOOK 1 — 0s până la 2.5s
                text_complet = f"{str_inainte} {str_auriu} {str_dupa}".strip()
                adauga_hook_simplu(text_complet, 0, 2.5)

                # HOOK 2 — 2.5s până la 4.0s
                adauga_hook_simplu("HERE'S WHY... 👇", 2.5, 1.5)
            
            # ♠️ NETFLIX EPISODE BADGE — dreapta sus în zona poker
            if nume_plat == "youtube" and episod is not None and os.path.exists("BebasNeue-Regular.ttf"):
    
               badge_w, badge_h = 155, 48
               badge_y = int(H * 0.50) + 24
               badge_x_final = W - badge_w - 16
               t_aparitie = 1.5
               t_anim = 0.4
               
               def badge_pozitie(t):
                   if t < t_aparitie:
                       return (W + 10, badge_y)
                   progres = min(1.0, (t - t_aparitie) / t_anim)
                   progres_smooth = 1 - (1 - progres) ** 3
                   x_curent = W + 10 - (W + 10 - badge_x_final) * progres_smooth
                   return (int(x_curent), badge_y)
            

               # FUNDAL roșu Netflix — dreptunghi rotunjit simulat cu ColorClip
               badge_bg = ColorClip(size=(badge_w, badge_h), color=(180, 0, 0))
               badge_bg = (badge_bg
                           .set_position(badge_pozitie)
                           .set_opacity(0.88)
                           .set_start(t_aparitie)
                           .set_duration(clip.duration - t_aparitie)
                           .fadein(t_anim))
               elemente.append(badge_bg)

               # TEXT S1 · E3
               badge_text = TextClip(
                   f"S{sezon}  ·  E{episod}",
                   fontsize=30,
                   color='white',
                   font='BebasNeue-Regular.ttf',
               )
               badge_text = (badge_text
                             .set_position(lambda t: (
                                 int(badge_pozitie(t)[0]) + 12,
                                 badge_y + 8
                             ))
                             .set_start(t_aparitie)
                             .set_duration(clip.duration - t_aparitie)
                             .fadein(t_anim))
               elemente.append(badge_text)

            # --- C. ELEMENTE GRAFICE PREMIUM (V8.5) ---
        
            y_baza = int(H * 0.35) # Ambele stau FIX în același loc
            offset_text = 172      # Reglajul pentru centrarea textului în cadran

            # 3. BUTONUL GET LINK (Fundal 1)
            if os.path.exists("buton_bio.png"):
                # FĂRĂ has_mask=True, MoviePy detectează singur PNG-ul
                btn_bio = ImageClip("buton_bio.png").resize(width=750).set_duration(clip.duration - 6.0)
                btn_bio = (btn_bio
                           .set_position(('center', y_baza))
                           .set_start(6.0)
                           .fadein(0.5))
                
                # Aplicăm opacitatea DOAR pe mască (pe transparență)
                if btn_bio.mask is not None:
                    btn_bio.mask = btn_bio.mask.fl(lambda gf, t: gf(t) * op_buton(t))
                elemente.append(btn_bio)

            # 4. CADRUL DE PREȚ (Fundal 2)
            if os.path.exists("forma_pret.png"):
                img_pret = ImageClip("forma_pret.png").resize(width=750).set_duration(clip.duration - 6.0)
                img_pret = (img_pret
                            .set_position(('center', y_baza))
                            .set_start(6.0)
                            .fadein(0.5))
                
                # Aplicăm opacitatea DOAR pe mască
                if img_pret.mask is not None:
                    img_pret.mask = img_pret.mask.fl(lambda gf, t: gf(t) * op_pret(t))
                elemente.append(img_pret)

                # 5. TEXTUL PREȚULUI (Cel mai în față)
                p_val = pret_real if pret_real else "Check Price"
                r_val = f"{reducere_reala} OFF! | " if reducere_reala else ""
                txt_p = TextClip(f"{r_val}{p_val}", fontsize=64, color='#fbbe12', font='BebasNeue-Regular.ttf')
                txt_p = (txt_p
                         .set_position(('center', y_baza + offset_text))
                         .set_start(6.0)
                         .set_duration(clip.duration - 6.0)
                         .fadein(0.5))
                
                # Și textul are mască, o manipulăm la fel
                if txt_p.mask is not None:
                    txt_p.mask = txt_p.mask.fl(lambda gf, t: gf(t) * op_pret(t))
                elemente.append(txt_p) # Rămâne cel mai în față
                

            # 6. BARA DE PROGRES
            bar_h = 12
            p_bar = ColorClip(size=(W, bar_h), color=(255,0,0), duration=clip.duration)
            p_bar = p_bar.resize(lambda t: (max(1, int(W * (t / clip.duration))), bar_h)).set_position(('left', 'bottom'))
            elemente.append(p_bar)

            # D. EXPORT ȘI MASTERIZARE AUDIO PREMIUM
            final_video = CompositeVideoClip(elemente, size=(W,H))
            
            # Lista în care vom stoca toate track-urile audio pentru mixajul final
            track_uri_audio = []
            
            # ==========================================
            # 🧠 AI MIXER: Analizăm sunetul produsului și fundalul
            # ==========================================
            if clip.audio and bg_clip is not None and bg_clip.audio:
                try:
                    # Citim amplitudinea maximă a clipului cu produsul
                    peak_vol = clip.audio.max_volume()
                    print(f"🔊 [AI MIXER] Amplitudine detectată: {peak_vol:.2f}")
                except Exception as e:
                    # Failsafe: Dacă MP4-ul e ciudat și nu se poate citi, trecem pe default
                    peak_vol = 0.5 
                    print("⚠️ [AI MIXER] Eroare la citire volum. Folosim valoarea de siguranță.")

                # Decizia algoritmică
                if peak_vol > 0.7:
                    vol_produs = 0.10  # Prea zgomotos -> îl reducem drastic
                    print("📉 Reducem zgomotul puternic la 10%.")
                elif peak_vol > 0.1:
                    vol_produs = 0.30  # Sunet bun/ASMR -> îl lăsăm să se audă percuția
                    print("⚖️ Sunet ASMR detectat. Setăm la 30%.")
                else:
                    vol_produs = 0.0   # Mut -> îl tăiem de tot
                    print("🔇 Clip mut. Tăiem complet sunetul.")
                
                # Adăugăm sunetul produsului (ajustat) și fundalul în lista de mixaj
                track_uri_audio.append(clip.audio.volumex(vol_produs))
                track_uri_audio.append(bg_clip.audio.volumex(0.85)) # Redus ușor pentru a lăsa loc de SFX
                
            # ==========================================
            # 🎧 SFX: Efectele Sonore Premium (MrBeast Style)
            # ==========================================
            folder_sfx = "sfx" # Noul tău folder dedicat
            
            # 1. The Whoosh (Apariția butonului la secunda 6.0)
            cale_whoosh = os.path.join(folder_sfx, "whoosh.mp3")
            if os.path.exists(cale_whoosh):
                # .volumex(0.6) - Vrem să se simtă, nu să sperie
                sfx_whoosh = AudioFileClip(cale_whoosh).volumex(0.6).set_start(6.0)
                track_uri_audio.append(sfx_whoosh)
                print("💨 Adăugat SFX: Whoosh la 6.0s")
            
            # 2. The Pop (Săritura "Snappy" a steluțelor la secunda 7.0)
            cale_pop = os.path.join(folder_sfx, "pop.mp3")
            if os.path.exists(cale_pop):
                # .volumex(0.9) - Vrem să fie clar și ascuțit, să taie prin zgomotul de fundal
                sfx_pop = AudioFileClip(cale_pop).volumex(0.9).set_start(7.0)
                track_uri_audio.append(sfx_pop)
                print("🫧 Adăugat SFX: Dopamine Pop la 7.0s")

            # ==========================================
            # 🎛️ MIXAJUL FINAL
            # ==========================================
            if track_uri_audio:
                # Amestecăm absolut tot: produs, fundal, whoosh și pop
                audio_mixat = CompositeAudioClip(track_uri_audio)
                final_video.audio = audio_mixat
            
            # ==========================================
            # 💾 SALVAREA FIȘIERULUI
            # ==========================================
            # 🔥 NOU: Adăugăm un timestamp (Timpul exact) ca să nu se suprascrie NICIODATĂ
            timestamp = int(time.time())
            out_name = os.path.join(PATH_OUTPUT, f"{nume_plat}_{timestamp}_var_{i+1}.mp4")
            print(f"⏳ [RENDER] Scriem: {out_name}")
            final_video.write_videofile(out_name, fps=30, codec='libx264', preset='ultrafast', logger=None)
            final_video.save_frame(f"{out_name}_thumb.png", t=8.0)
            
            try:
                final_video.close()
                clip.close()
                clip_top.close()
                if clip_final_split is not None:  
                   clip_final_split.close()
                if clip_bot is not None:
                    clip_bot.close()
                if bg_clip is not None:
                    bg_clip.close()
                if sfx_whoosh is not None:
                    sfx_whoosh.close()
                if sfx_pop is not None:
                    sfx_pop.close()
            except Exception as e:
                logging.warning(f"⚠️ [CLEANUP] Eroare: {e}")
            
            
            # ✅ ADAUGI DUPĂ CLEANUP:
            gc.collect()
            print(f"🧹 RAM eliberat după clipul {i+1}")
            
            # --- DESCRIEREA "SEO BOMBER" PREMIUM ---
            desc_SEO = f"""⚠️ You NEED this in your life! Get it before it sells out! 👇
        
🛒 GET THE LINK:
👉 Go to my Channel/Profile BIO!
(🔗 linktr.ee/GadgetHunterShop)
⏰ Price may change anytime — grab it now!

🌟 Why everyone is buying this:
This {produs_activ['nume']} is going viral on Amazon right now! 
Thousands of 5-star reviews don't lie. 
Check the link in bio before the price goes back up!

🔍 Search Tags:
#shorts #amazonfinds #amazonmusthaves #amazonusa #usa {config['tags_specifice']} #{CONT_TARGET}

🛑 Disclaimer:
As an Amazon Associate, I earn from qualifying purchases. This helps support the channel!

🎥 Video Credit: {LINK_SURSA}
"""
        
        # 🔥 SALVĂM ÎN BAZA DE DATE DOAR PENTRU YOUTUBE
            if nume_plat == "youtube":
                # Cream o lista de variatii vizuale ca sa facem fiecare titlu unic
                emoji_spin = ["🤯", "🔥", "👀", "✨", "💯"]
                if TIP_CONTINUT == "poker":
                    titlu_unic = f"{random.choice(produs_activ['titluri'])} {emoji_spin[i]} | S{sezon} E{episod}"
                else:
                    titlu_unic = f"{random.choice(produs_activ['titluri'])} {emoji_spin[i]} 🏆"
                adauga_in_imperiu(out_name, titlu_unic, desc_SEO, f"{nume_plat}_{i+1}", episod if episod is not None else 0)
                print(f"📥 [DB] Salvat automat în pending: {out_name}")
            else:
                print(f"⏭️ [SKIP DB] Pregătit pentru upload manual: {out_name}")

    clip_mare.close()
    print("\n✅ FABRICA A TERMINAT! Ai 2 clipuri pentru YouTube și 2 pentru TikTok în folderul 'output_videos'.")

if __name__ == "__main__":
    main()