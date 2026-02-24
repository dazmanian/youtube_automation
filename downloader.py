import yt_dlp
import os

# Numele pe care îl așteaptă Fabrica ta
VIDEO_OUTPUT = "video_brut.mp4" 

def download_video(url):
    # Dacă există deja un video vechi, îl ștergem ca să nu se încurce
    if os.path.exists(VIDEO_OUTPUT):
        os.remove(VIDEO_OUTPUT)
        
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': VIDEO_OUTPUT,
        'merge_output_format': 'mp4',
        # 'cookiesfrombrowser': ('chrome',), # Am scos comanda care dădea eroare
        'cookiefile': 'cookies.txt',         # 🔥 NOU: Folosim fișierul fizic extras de tine
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("⏳ Descarc videoclipul ca un om real...")
            ydl.download([url])
        print("✅ Descărcare completă!")
    except Exception as e:
        print(f"❌ Eroare la descărcare: {e}")

if __name__ == "__main__":
    link = input("🔗 Introdu link-ul de la YouTube: ")
    download_video(link)