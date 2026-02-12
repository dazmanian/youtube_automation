import sqlite3
import yt_dlp
import os
import time
import sys

# --- CONFIGURARE ---
DB_NAME = "youtube_empire.db"
FOLDER_DOWNLOAD = "downloads"
FFMPEG_FILENAME = "ffmpeg.exe"
RETRY_ATTEMPTS = 3

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ [DB CRITICAL]: Nu pot conecta la baza de date: {e}")
        return None

def get_video_de_procesat():
    """
    Găsește un video pending și îl marchează ca 'processing'.
    """
    conn = get_db_connection()
    if not conn: return None

    cursor = conn.cursor()
    video_data = None

    try:
        # 1. Căutăm un video pending
        cursor.execute("SELECT id, sursa_url FROM videos WHERE status='pending' LIMIT 1")
        row = cursor.fetchone()

        if row:
            video_id = row['id']
            url = row['sursa_url']
            
            # 2. Îl marcăm ca 'processing' ca să nu-l ia altcineva
            cursor.execute("UPDATE videos SET status='processing' WHERE id=?", (video_id,))
            conn.commit()
            
            video_data = (video_id, url)
            print(f"🔒 [LOCK]: Video ID {video_id} preluat pentru descărcare.")
        
    except sqlite3.Error as e:
        print(f"⚠️ [DB ERROR]: {e}")
    finally:
        conn.close()

    return video_data

def update_status(video_id, status_nou, cale_fisier=""):
    """Actualizează statusul final (downloaded/error) și calea fișierului."""
    conn = get_db_connection()
    if not conn: return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE videos SET status=?, cale_fisier=? WHERE id=?", 
            (status_nou, cale_fisier, video_id)
        )
        conn.commit()
        print(f"📝 [DB UPDATE]: ID {video_id} -> {status_nou}")
    except sqlite3.Error as e:
        print(f"❌ [DB UPDATE FAIL]: {e}")
    finally:
        conn.close()

def descarca_video(url, video_id):
    """
    Descarcă videoul folosind yt-dlp și ffmpeg.
    """
    # Căile absolute
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, FOLDER_DOWNLOAD)
    ffmpeg_path = os.path.join(base_dir, FFMPEG_FILENAME)
    
    # Verificări
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not os.path.exists(ffmpeg_path):
        print(f"❌ [MISSING]: Nu găsesc {FFMPEG_FILENAME} în {base_dir}")
        print("   -> Asigură-te că ffmpeg.exe e lângă worker.py!")
        return None

    nume_fisier = f"video_{video_id}.mp4"
    cale_finala = os.path.join(output_dir, nume_fisier)
    
    # Dacă există deja, îl ștergem ca să nu avem dubluri corupte
    if os.path.exists(cale_finala):
        try:
            os.remove(cale_finala)
        except:
            pass

    print(f"⬇️ [WORKER]: Descarc ID {video_id} de la {url}...")
    
    # Configurare yt-dlp
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': cale_finala,
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': base_dir, # Folderul unde e ffmpeg.exe
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Validare
        if os.path.exists(cale_finala) and os.path.getsize(cale_finala) > 1000:
            print(f"✅ [SUCCESS]: Descărcat: {nume_fisier}")
            return cale_finala
        else:
            print("❌ [ERROR]: Fișierul descărcat e gol sau lipsește.")
            return None

    except Exception as e:
        print(f"❌ [DOWNLOAD CRASH]: {e}")
        return None

# --- RULAREA INDIVIDUALĂ ---
if __name__ == "__main__":
    print("👷 WORKER MANUAL START...")
    
    # Test Loop
    while True:
        task = get_video_de_procesat()
        
        if task:
            id_vid, url_vid = task
            cale = descarca_video(url_vid, id_vid)
            
            if cale:
                update_status(id_vid, 'downloaded', cale)
            else:
                update_status(id_vid, 'error_download')
        else:
            print("💤 Niciun task 'pending'.")
            break