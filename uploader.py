import os
import sqlite3
import time
import logging
import random
import pickle
from datetime import datetime, timedelta
import pytz

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ============================================================
# ⚙️ CONFIGURARE
# ============================================================
DB_NAME          = "youtube_empire.db"
CREDENTIALS_FILE = "credentials.json"   # Fișierul descărcat de pe Google Cloud
TOKEN_FILE       = "token.pickle"        # Creat automat după primul login
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
TIMEZONE_RO      = pytz.timezone("Europe/Bucharest")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("uploader.log", encoding='utf-8'),  # ← adaugă encoding
        logging.StreamHandler(stream=open(os.devnull, 'w'))     # ← mută consola în silence
    ]
)

# ============================================================
# 🔐 AUTENTIFICARE GOOGLE — Se face o singură dată
# ============================================================
def get_youtube_client():
    """
    Prima rulare: deschide browserul pentru login Google.
    Ulterior: folosește token.pickle salvat local, fără browser.
    """
    creds = None

    # Dacă avem deja un token salvat, îl încărcăm
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    # Dacă tokenul e expirat sau nu există, facem autentificarea
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("🔄 Refresh token automat...")
            creds.refresh(Request())
        else:
            logging.info("🌐 Prima autentificare — se deschide browserul...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Salvăm tokenul pentru data viitoare
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        logging.info("✅ Token salvat în token.pickle")

    return build("youtube", "v3", credentials=creds)

# ============================================================
# 📦 CITIRE DIN DB — Următorul clip pending
# ============================================================
def get_urmatorul_clip():
    """Returnează cel mai vechi clip cu status='pending' din DB."""
    try:
        conn = sqlite3.connect(DB_NAME)
        row = conn.execute("""
            SELECT id, cale_fisier, titlu_video, descriere
            FROM videos
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT 1
        """).fetchone()
        conn.close()
        return row  # (id, cale, titlu, descriere) sau None
    except Exception as e:
        logging.error(f"⚠️ [DB READ] Eroare: {e}")
        return None

def marcheaza_uploadat(video_id_db, youtube_video_id):
    """Marchează clipul ca 'uploaded' în DB și salvează ID-ul YouTube."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("""
            UPDATE videos
            SET status = 'uploaded', youtube_id = ?
            WHERE id = ?
        """, (youtube_video_id, video_id_db))
        conn.commit()
        conn.close()
        logging.info(f"✅ [DB] Clip {video_id_db} marcat ca uploaded.")
    except Exception as e:
        logging.error(f"⚠️ [DB UPDATE] Eroare: {e}")

def init_db_coloana_youtube_id():
    """Adaugă coloana youtube_id în tabelul videos dacă nu există."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("ALTER TABLE videos ADD COLUMN youtube_id TEXT")
        conn.commit()
        conn.close()
    except Exception:
        pass  # Coloana există deja, ignorăm

# ============================================================
# 📤 UPLOAD EFECTIV
# ============================================================
def uploadeaza_clip(youtube, cale_fisier, titlu, descriere):
    """
    Uploadează un clip pe YouTube ca Short (public).
    Returnează ID-ul videoclipului sau None la eroare.
    """
    if not os.path.exists(cale_fisier):
        logging.error(f"❌ Fișierul nu există: {cale_fisier}")
        return None

    logging.info(f"📤 Uploading: {titlu}")
    logging.info(f"   Fișier: {cale_fisier}")

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": titlu[:100],           # YouTube limită: 100 caractere
                    "description": descriere[:5000], # YouTube limită: 5000 caractere
                    "categoryId": "28",              # Science & Technology
                    "defaultLanguage": "en",
                    "defaultAudioLanguage": "en"
                },
                "status": {
                    "privacyStatus": "public",       # Public imediat
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(
                cale_fisier,
                mimetype="video/mp4",
                resumable=True                       # Rezumabil — nu se pierde la erori de rețea
            )
        )

        # Executăm uploadul cu progress tracking
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                procent = int(status.progress() * 100)
                logging.info(f"   ⏳ Upload progres: {procent}%")

        youtube_id = response.get("id")
        logging.info(f"✅ [SUCCES] Upload complet! ID: {youtube_id}")
        logging.info(f"   🔗 https://youtube.com/watch?v={youtube_id}")
        cale_thumb = f"{cale_fisier}_thumb.png"
        if os.path.exists(cale_thumb):
            try:
                youtube.thumbnails().set(
                    videoId=youtube_id,
                    media_body=MediaFileUpload(cale_thumb, mimetype="image/png")
                ).execute()
                logging.info(f"🖼️ Thumbnail uploadat cu succes!")
            except Exception as e:
                logging.warning(f"⚠️ Thumbnail eșuat: {e}")
        else:
            logging.warning(f"⚠️ Thumbnail negăsit: {cale_thumb}")
            
        # ✅ COMENTARIU PINNUIT — Link affiliate vizibil imediat
        try:
            # Postăm comentariul
            comment = youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": youtube_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": f"🛒 GET IT HERE 👉 linktr.ee/GadgetHunterShop\n⏰ Price changes anytime — grab it now!\n✅ Link in BIO"
                            }
                        }
                    }
                }
            ).execute()
            
            comment_id = comment["snippet"]["topLevelComment"]["id"]
            
            # Pinnuim comentariul
            youtube.videos().update(
                part="localizations",
                body={
                    "id": youtube_id,
                    "localizations": {}
                }
            ).execute()

            youtube.comments().update(
                part="snippet",
                body={
                    "id": comment_id,
                    "snippet": {
                        "textOriginal": f"🛒 GET IT HERE 👉 linktr.ee/GadgetHunterShop\n⏰ Price changes anytime — grab it now!\n✅ Link in BIO",
                        "isPinned": True
                    }
                }
            ).execute()
            
            logging.info(f"📌 Comentariu pinnuit cu succes!")
            
        except Exception as e:
            logging.warning(f"⚠️ Comentariu eșuat: {e}")
            
        return youtube_id

    except Exception as e:
        logging.error(f"❌ [UPLOAD EROARE]: {e}")
        return None

# ============================================================
# ⏰ SCHEDULER — Așteaptă ora corectă și uploadează
# ============================================================
def calculeaza_urmatoarea_ora(ultimul_interval=None):
    acum = datetime.now(TIMEZONE_RO)
    
    # Interval 1: 15:00 - 17:00
    minute_random_1 = random.randint(0, 120)
    target_1 = acum.replace(hour=15, minute=0, second=0, microsecond=0) + timedelta(minutes=minute_random_1)
    if target_1 <= acum:
        target_1 += timedelta(days=1)

    # Interval 2: 00:00 - 02:00
    minute_random_2 = random.randint(0, 120)
    target_2 = acum.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=minute_random_2)
    if target_2 <= acum:
        target_2 += timedelta(days=1)

    # Dacă ultimul upload a fost în intervalul 1, forțăm intervalul 2 și invers
    if ultimul_interval == 1:
        urmatoarea = target_2
    elif ultimul_interval == 2:
        urmatoarea = target_1
    else:
        urmatoarea = min(target_1, target_2, key=lambda t: t - acum)

    secunde_pana_atunci = (urmatoarea - acum).total_seconds()
    
    # Returnăm și care interval e
    interval_curent = 1 if urmatoarea == target_1 else 2
    return urmatoarea, int(secunde_pana_atunci), interval_curent

def ruleaza_scheduler():
    logging.info("🚀 UPLOADER PORNIT — Scheduler activ")
    logging.info("   Intervale programate: 15:00-17:00 și 00:00-02:00 (România)")

    init_db_coloana_youtube_id()
    youtube = get_youtube_client()
    logging.info("✅ Autentificare Google reușită!")

    ultimul_interval = None  # ← NOU

    while True:
        clip = get_urmatorul_clip()
        if clip is None:
            logging.warning("⚠️ Nu mai sunt clipuri pending în DB!")
            time.sleep(3600)
            continue

        ora_upload, secunde_asteptare, interval_curent = calculeaza_urmatoarea_ora(ultimul_interval)  # ← NOU
        ore = secunde_asteptare // 3600
        minute = (secunde_asteptare % 3600) // 60

        logging.info(f"⏰ Următorul upload la: {ora_upload.strftime('%d.%m.%Y %H:%M')} (România)")
        logging.info(f"   Aștept: {ore}h {minute}m")
        logging.info(f"   Clip pregătit: '{clip[2]}'")

        time.sleep(secunde_asteptare)

        clip = get_urmatorul_clip()
        if clip is None:
            logging.warning("⚠️ Clipul a dispărut din DB între timp.")
            continue

        video_id_db, cale_fisier, titlu, descriere = clip

        logging.info(f"\n{'='*50}")
        logging.info(f"📤 START UPLOAD: {titlu}")
        logging.info(f"{'='*50}")

        youtube_id = uploadeaza_clip(youtube, cale_fisier, titlu, descriere)

        if youtube_id:
            marcheaza_uploadat(video_id_db, youtube_id)
            ultimul_interval = interval_curent  # ← NOU — reținem ce interval am folosit
            logging.info(f"🎉 Clip postat cu succes!")
        else:
            logging.error(f"❌ Upload eșuat pentru clipul ID {video_id_db}.")

        time.sleep(30)

# ============================================================
# 🏁 ENTRY POINT
# ============================================================
if __name__ == "__main__":
    ruleaza_scheduler()