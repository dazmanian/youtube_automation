import yt_dlp
import os
import re

def get_next_filename(folder, prefix):
    # Ne asigurăm că folderul există, dacă nu, îl creăm
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Găsim toate fișierele din folder
    files = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith('.mp4')]
    
    max_num = 1 # Pornim cu baza 1. Dacă există deja 1, următorul va fi minim 2
    for f in files:
        # Extragem numărul din numele fișierului (ex: din "poker3.mp4" extrage "3")
        match = re.search(r'\d+', f)
        if match:
            num = int(match.group())
            if num > max_num:
                max_num = num
                
    next_num = max_num + 1
    return os.path.join(folder, f"{prefix}{next_num}.mp4")

def download_video(url, output_path):
    # Dacă există deja (ex: la video_brut), îl ștergem ca să nu se suprapună
    if os.path.exists(output_path):
        os.remove(output_path)
        
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'cookiefile': 'cookies.txt',  # 🔥 Menținem fișierul de cookies
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n⏳ Descarc videoclipul în: {output_path} ...")
            ydl.download([url])
        print(f"✅ Descărcare completă! Salvat ca: {output_path}")
    except Exception as e:
        print(f"❌ Eroare la descărcare: {e}")

if __name__ == "__main__":
    print("\n📥 --- DOWNLOADER MANAGER ---")
    print("1. 📦 Reclamă Produs    -> video_brut.mp4")
    print("2. ♠️ Fundal Poker      -> assets/pokerclips/poker[x].mp4")
    print("3. 🚗 Fundal GTA/TikTok -> assets/tikclips/tik[x].mp4")
    
    alegere = input("\nCe fel de clip descarci? (1/2/3): ").strip()
    
    if alegere not in ["1", "2", "3"]:
        print("❌ Alegere invalidă! Pornește scriptul din nou.")
        exit()

    link = input("🔗 Introdu link-ul de la YouTube: ").strip()
    
    # Logica de direcționare ("Dispecerul")
    if alegere == "1":
        nume_custom = input("📝 Nume fișier (ex: ninja, scale, ruler): ").strip()
        cale_finala = f"{nume_custom}_brut.mp4" if nume_custom else "video_brut.mp4"
    elif alegere == "2":
        cale_finala = get_next_filename(os.path.join("assets", "pokerclips"), "poker")
    elif alegere == "3":
        cale_finala = get_next_filename(os.path.join("assets", "tikclips"), "tik")
        
    download_video(link, cale_finala)