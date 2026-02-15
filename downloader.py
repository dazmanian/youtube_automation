import yt_dlp
import os

# --- PUNE LINK-UL AICI ---
# Exemplu: Un video lung de review sau un compilation
link_youtube = "https://youtu.be/id-ELcWR8_c?si=Y0AtLxBgoSrLnj1_" 

def descarca_video(url):
    print(f"⬇️ [DOWNLOAD]: Încep descărcarea pentru: {url}")
    
    # Ștergem vechiul video ca să nu facem conflicte
    if os.path.exists("video_brut.mp4"):
        os.remove("video_brut.mp4")

    # Setări PRO: Descarcă cel mai bun video și cel mai bun audio și le unește
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'video_brut.mp4',
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ [GATA]: Video original salvat ca 'video_brut.mp4'")
    except Exception as e:
        print(f"❌ [EROARE DOWNLOAD]: {e}")

if __name__ == "__main__":
    descarca_video(link_youtube)