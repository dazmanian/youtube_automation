import sqlite3
import datetime
import os
import time

# --- CONFIGURARE ---
DB_NAME = "youtube_empire.db"

def clear_screen():
    # Curăță ecranul pentru un aspect PRO (Windows/Mac/Linux)
    os.system('cls' if os.name == 'nt' else 'clear')

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30.0) 
        conn.row_factory = sqlite3.Row 
        return conn
    except sqlite3.Error as e:
        print(f"❌ [DB FATAL]: Nu pot conecta la baza de date: {e}")
        return None

def initializeaza_db():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    
    # Creare Tabel Principal (Cu toate coloanele necesare)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sursa_url TEXT,
            titlu_video TEXT,
            descriere TEXT,
            cont_target TEXT,
            affiliate_link TEXT,
            status TEXT DEFAULT 'pending', 
            cale_fisier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_at TIMESTAMP,
            error_log TEXT
        )
    ''')
    
    # Siguranță: Încercăm să adăugăm coloane dacă lipsesc (pentru baze vechi)
    try: cursor.execute("ALTER TABLE videos ADD COLUMN descriere TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE videos ADD COLUMN error_log TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE videos ADD COLUMN youtube_id TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE videos ADD COLUMN numar_episod INTEGER DEFAULT 0")
    except: pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poker_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fisier TEXT UNIQUE,
            secunda_curenta REAL DEFAULT 0,
            durata_totala REAL,
            epuizat INTEGER DEFAULT 0
        )
    ''')
 
    conn.commit()
    conn.close()

def vezi_status_poker():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT fisier, secunda_curenta, durata_totala, epuizat FROM poker_tracker ORDER BY fisier ASC")
        rows = cursor.fetchall()
    except: rows = []
    conn.close()

    print("♠️  STATUS CLIPURI POKER:")
    print(f"{'FISIER':<25} | {'FOLOSIT':<10} | {'TOTAL':<10} | {'RAMASE':<10} | STATUS")
    print("-" * 75)
    
    if not rows:
        print("   (Niciun clip poker tracked încă)")
    else:
        for row in rows:
            fisier = row['fisier'][:22] + '..' if len(row['fisier']) > 22 else row['fisier']
            folosit = f"{int(row['secunda_curenta'])}s"
            total = f"{int(row['durata_totala'])}s"
            ramase = int(row['durata_totala'] - row['secunda_curenta'])
            clipuri_ramase = ramase // 28 # 28 = limita clip secunde , impartire la intreg
            status = "✅ ACTIV" if not row['epuizat'] else "🗑️  EPUIZAT"
            print(f"{fisier:<25} | {folosit:<10} | {total:<10} | {clipuri_ramase} clipuri  | {status}")
    print("\n")

# --- FUNCȚII DE RAPORTARE (DASHBOARD) ---
def raport_elon_musk():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Statistici
    try:
        cursor.execute("SELECT COUNT(*) FROM videos")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM videos WHERE status='pending'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM videos WHERE status='uploaded'")
        uploaded = cursor.fetchone()[0]
    except:
        total = 0; pending = 0; uploaded = 0

    conn.close()

    # Grafică Dashboard
    clear_screen()
    print("\n🚀  YOUTUBE EMPIRE COMMAND CENTER  🚀")
    print("════════════════════════════════════════")
    print(f"📦 TOTAL INVENTAR:    {total} videoclipuri")
    print(f"⏳ ÎN AȘTEPTARE:      {pending}")
    print(f"✅ DEJA POSTATE:      {uploaded}")
    print("════════════════════════════════════════")
    
    # Calcul "Runway" (Câte zile de libertate ai)
    zile_libertate = pending // 2 # 2 postari pe zi
    if zile_libertate > 0:
        print(f"💎 LIBERTATE: Ai conținut asigurat pentru {zile_libertate} zile!")
    else:
        print(f"⚠️  ALARMĂ: Stoc epuizat! Pornește Generatorul!")
    print("════════════════════════════════════════\n")

def vezi_coada_detaliata():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, cont_target, titlu_video, status FROM videos WHERE status='pending' ORDER BY id ASC LIMIT 10")
        rows = cursor.fetchall()
    except: rows = []
    conn.close()

    print("📋 URMĂTOARELE 10 VIDEOCLIPURI LA RÂND:")
    print(f"{'ID':<5} | {'CONT':<10} | {'TITLU (Scurtat)':<30}")
    print("-" * 50)
    
    if not rows:
        print("   (Niciun video în așteptare)")
    else:
        for row in rows:
            t = row['titlu_video'] if row['titlu_video'] else "Fara Titlu"
            titlu_scurt = (t[:27] + '..') if len(t) > 27 else t
            print(f"{row['id']:<5} | {row['cont_target']:<10} | {titlu_scurt:<30}")
    print("\n")

# --- FUNCȚII DE ACȚIUNE ---
def adauga_video_manual():
    print("📝 ADĂUGARE MANUALĂ (Doar pentru teste/urgențe)")
    url = input("🔗 Link Video: ").strip()
    if not url: return
    cont = input("🎯 Cont (Gadgets/Home): ").strip()
    titlu = input("📝 Titlu: ").strip()
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO videos (sursa_url, cont_target, titlu_video, created_at)
            VALUES (?, ?, ?, ?)
        ''', (url, cont, titlu, datetime.datetime.now()))
        conn.commit()
        print("✅ Salvat!")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Eroare: {e}")
        input("Apasă Enter...")
    finally:
        conn.close()

def sterge_video():
    vid_id = input("🗑️  ID-ul videoului de șters: ")
    
    if not vid_id.isdigit():
       print("❌ ID invalid!")
       return
   
    conn = get_db_connection()
    conn.execute("DELETE FROM videos WHERE id=?", (vid_id,))
    conn.commit()
    conn.close()
    print("✅ Șters cu succes!")
    time.sleep(1)

def reset_errors():
    # Funcție "God Mode" - Resetează videoclipurile blocate
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET status='pending' WHERE status='error'")
    changes = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"🔧 Am reparat {changes} videoclipuri care aveau erori.")
    time.sleep(2)

def reset_poker_tracker():
    conn = get_db_connection()
    conn.execute("DELETE FROM poker_tracker")
    conn.commit()
    conn.close()
    print("✅ Poker tracker resetat! Episoadele reîncep de la S1 E1.")
    time.sleep(2)
    
def set_pozitie_poker():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fisier, secunda_curenta FROM poker_tracker")
    rows = cursor.fetchall()
    conn.close()
    
    print("♠️  FIȘIERE DISPONIBILE:")
    for row in rows:
        print(f"   → {row['fisier']} (acum la secunda {int(row['secunda_curenta'])})")
    
    fisier = input("\n📁 Nume fișier (ex: poker2.mp4): ").strip()
    secunda = input("⏱️  Setează la secunda: ").strip()
    
    if not secunda.isdigit():
        print("❌ Secunda invalidă!")
        return
    
    conn = get_db_connection()
    conn.execute(
        "UPDATE poker_tracker SET secunda_curenta = ?, epuizat = 0 WHERE fisier = ?",
        (int(secunda), fisier)
    )
    conn.commit()
    conn.close()
    print(f"✅ [{fisier}] setat la secunda {secunda}!")
    time.sleep(1)

# --- MENIU PRINCIPAL ---
if __name__ == "__main__":
    initializeaza_db()
    
    while True:
        raport_elon_musk()
        vezi_coada_detaliata()
        
        print("ACTION MENU:")
        print("1. ➕ Adaugă Video Manual (Urgență)")
        print("2. 🗑️  Șterge un Video")
        print("3. 🔧 Reparator (Resetează Erorile)")
        print("4. ♠️  Status Clipuri Poker")
        print("5. 🔄 Reset Poker Tracker")
        print("6. ⏱️  Setează Poziție Poker")
        print("7. 👋 Ieșire")
        
        optiune = input("\nCEO > ")
        
        if optiune == "1": adauga_video_manual()
        elif optiune == "2": sterge_video()
        elif optiune == "3": reset_errors()
        elif optiune == "4": vezi_status_poker()
        elif optiune == "5": reset_poker_tracker()
        elif optiune == "6": set_pozitie_poker()
        elif optiune == "7":
            print("To the moon! 🚀")
            break