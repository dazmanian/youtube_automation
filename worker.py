import sqlite3
import yt_dlp
import os
import sys

# --- CONFIGURARE ---
DB_NAME = "youtube_empire.db"
FOLDER_DOWNLOAD = "downloads"
FFMPEG_FILENAME = "ffmpeg.exe"

# Căi absolute (Siguranță maximă)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, FOLDER_DOWNLOAD)
FFMPEG_PATH = os.path.join(BASE_DIR, FFMPEG_FILENAME)

# Verificări
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- CONEXIUNE BAZA DE DATE ---
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ [DB CRITICAL]: Nu pot conecta la baza de date: {e}")
        return None

# --- PASUL 1: PRELUARE MISIUNE ---
def get_video_de_procesat():
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor()
    task = None
    try:
        # Luăm un video care e 'pending'
        cursor.execute("SELECT id, sursa_url FROM videos WHERE status='pending' LIMIT 1")
        row = cursor.fetchone()
        if row:
            video_id = row['id']
            url = row['sursa_url']
            
            # Îl blocăm (status='processing') ca să nu-l ia alt worker
            cursor.execute("UPDATE videos SET status='processing' WHERE id=?", (video_id,))
            conn.commit()
            
            print(f"🔒 [WORKER]: Am preluat comanda ID {video_id}.")
            task = (video_id, url)
    except Exception as e:
        print(f"⚠️ [DB ERROR]: {e}")
    finally:
        conn.close()
    return task

def salveaza_metadata_brut(video_id, titlu_original):
    """
    NOU: Salvăm DOAR titlul original.
    Lăsăm descrierea SEO și link-urile pentru pasul de Upload (Selenium).
    """
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Actualizăm doar titlul_video
        cursor.execute("UPDATE videos SET titlu_video=? WHERE id=?", (titlu_original, video_id))
        conn.commit()
        print(f"📚 [INFO]: Titlul original a fost salvat: '{titlu_original[:30]}...'")
    except Exception as e:
        print(f"⚠️ [METADATA FAIL]: Nu am putut salva titlul: {e}")
    finally:
        conn.close()

def update_status(video_id, status_nou, cale_fisier=None):
    """Actualizează statusul final (downloaded sau error)."""
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        if cale_fisier:
            cursor.execute("UPDATE videos SET status=?, cale_fisier=? WHERE id=?", (status_nou, cale_fisier, video_id))
        else:
            cursor.execute("UPDATE videos SET status=? WHERE id=?", (status_nou, video_id))
        conn.commit()
        print(f"📝 [STATUS]: ID {video_id} -> {status_nou}")
    except Exception as e:
        print(f"❌ [DB UPDATE FAIL]: {e}")
    finally:
        conn.close()

def descarca_video(url, video_id):
    """Descarcă video-ul și extrage titlul brut."""
    print(f"⬇️ [WORKER]: Descarc ID {video_id}...")

    if not os.path.exists(FFMPEG_PATH):
        print(f"❌ [LIPSA FFMPEG]: Nu găsesc ffmpeg.exe!")
        return None

    nume_fisier = f"video_{video_id}.mp4"
    cale_finala = os.path.join(OUTPUT_DIR, nume_fisier)

    # Curățenie preventivă
    if os.path.exists(cale_finala):
        try: os.remove(cale_finala)
        except: pass

    # Configurare yt-dlp
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': cale_finala,
        'ffmpeg_location': BASE_DIR,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # AICI E MAGIA: extract_info cu download=True
            info = ydl.extract_info(url, download=True)
            
            # 1. Extragem titlul original (dacă nu există, punem un placeholder)
            titlu_brut = info.get('title', 'Gadget Video')
            
            # 2. Îl salvăm în baza de date imediat
            salveaza_metadata_brut(video_id, titlu_brut)

        # Verificare finală fișier
        if os.path.exists(cale_finala) and os.path.getsize(cale_finala) > 1000:
            print(f"✅ [SUCCESS]: Descărcare completă.")
            return cale_finala
        else:
            return None

    except Exception as e:
        print(f"❌ [CRASH DOWNLOAD]: {e}")
        return None

# --- RULARE TEST ---
if __name__ == "__main__":
    task = get_video_de_procesat()
    if task:
        path = descarca_video(task[1], task[0])
        if path:
            update_status(task[0], 'downloaded', path)
        else:
            update_status(task[0], 'error_download')
    else:
        print("💤 Nimic de muncă.")