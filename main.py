import time
import sys
import schedule # pip install schedule

# --- IMPORTURI (DEPARTAMENTELE TALE) ---
try:
    import database        # Contabilul (Memoria)
    import worker          # Aprovizionarea (Descarcă de pe Net)
    import editor          # Producția (Montează Video)
    import upload_selenium # Distribuția (Urcă pe YouTube)
except ImportError as e:
    print(f"❌ [CRITIC]: Lipsește un modul esențial! {e}")
    print("   -> Asigură-te că ai fișierele: database.py, worker.py, editor.py, upload_selenium.py")
    sys.exit()

# --- DEFINIREA MISIUNILOR (JOBS) ---

def job_download():
    """
    PASUL 1: Aprovizionarea.
    Cheamă 'worker.py' să verifice dacă ai pus link-uri noi în bază.
    """
    print("\n📦 [1. DOWNLOAD]: Verific baza de date pentru comenzi noi...")
    
    # 1. Întrebăm Worker-ul dacă e de muncă
    task = worker.get_video_de_procesat() # Returnează (id, url)
    
    if task:
        id_video, url_video = task
        print(f"   🎯 Am preluat comanda ID {id_video}: {url_video}")
        
        # 2. Executăm descărcarea
        cale_fisier = worker.descarca_video(url_video, id_video)
        
        if cale_fisier:
            # 3. Raportăm succesul -> Status devine 'downloaded'
            worker.update_status(id_video, 'downloaded', cale_fisier)
            print("   ✅ Descărcare reușită! Trimis la editare.")
        else:
            # 4. Raportăm eșecul
            worker.update_status(id_video, 'error_download')
            print("   ❌ Eroare la descărcare.")
    else:
        print("   💤 Nimic nou de descărcat (Coada 'pending' e goală).")

def job_editare():
    """
    PASUL 2: Producția.
    Transformă video-ul brut în video editat (Shorts).
    """
    print("\n🎬 [2. EDITARE]: Caut materie primă în depozit...")
    
    # 1. Întrebăm Editorul dacă are video-uri descărcate
    video_brut = editor.get_video_descarcat()
    
    if video_brut:
        id_video = video_brut[0]
        cale_sursa = video_brut[1]
        titlu = video_brut[2]
        
        print(f"   🔨 Procesez ID {id_video}: {titlu}")
        
        # 2. Executăm editarea
        cale_finala = editor.proceseaza_video(cale_sursa, titlu, id_video)
        
        if cale_finala:
            # 3. Raportăm succesul -> Status devine 'processed'
            editor.update_status_final(id_video, cale_finala)
            print("   ✅ Editare completă! Trimis la distribuție.")
        else:
            print("   ❌ Editare eșuată.")
    else:
        print("   💤 Nimic nou de editat (Status 'downloaded' lipsă).")

def job_upload():
    """
    PASUL 3: Distribuția.
    Urcă video-urile finite pe YouTube.
    """
    print("\n🌍 [3. UPLOAD]: Verific livrări către YouTube...")
    
    # Apelăm distribuitorul (el știe singur să caute 'processed' în bază)
    upload_selenium.upload_selenium()

def start_empire():
    """
    Funcția Principală care leagă totul.
    """
    print("╔════════════════════════════════════════╗")
    print("║   🚀 YOUTUBE EMPIRE AUTOMATION v4.0    ║")
    print("╚════════════════════════════════════════╝")
    
    # Inițializare Bază de Date (ca să fim siguri că există tabelele)
    database.initializeaza_db()

    # --- EXECUTARE TEST (O singură dată - Flux Complet) ---
    print("\n⚡ [MOD EXECUȚIE]: Rulez o tură completă acum...")
    job_download() # Descarcă
    job_editare()  # Editează
    job_upload()   # Urcă
    
    print("\n🏁 [FINAL]: Tură completă realizată.")

    # --- EXECUTARE AUTOMATĂ (Scheduler - Decomentează pentru Autopilot) ---
    # print("\n⏰ [AUTO]: Intru în mod de așteptare (Check la fiecare minut)...")
    
    # schedule.every(1).minutes.do(job_download)
    # schedule.every(2).minutes.do(job_editare)
    # schedule.every(10).minutes.do(job_upload)
    
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

if __name__ == "__main__":
    start_empire()