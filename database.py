import sqlite3
import datetime
import time

# --- CONFIGURARE ---
DB_NAME = "youtube_empire.db"

def get_db_connection():
    """
    Creează o conexiune robustă cu timeout.
    """
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30.0) 
        conn.row_factory = sqlite3.Row 
        return conn
    except sqlite3.Error as e:
        print(f"❌ [DB FATAL]: Nu pot conecta la baza de date: {e}")
        return None

def initializeaza_db():
    """
    Construiește structura imperiului și face UPDATE automat dacă lipsesc coloane.
    """
    conn = get_db_connection()
    if not conn: return

    cursor = conn.cursor()
    
    # 1. CREARE TABEL (Pentru instalări noi)
    # Am adăugat 'descriere' direct aici pentru viitor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Date de intrare
            sursa_url TEXT UNIQUE,
            titlu_video TEXT,
            descriere TEXT,         -- <--- NOU: Coloana pentru textul SEO
            cont_target TEXT,       -- 'Gadgets' sau 'Home'
            affiliate_link TEXT,
            
            -- Management de stare
            status TEXT DEFAULT 'pending', 
            retry_count INTEGER DEFAULT 0,
            
            -- Căile fișierelor
            cale_fisier TEXT,       
            
            -- Jurnal de bord
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_at TIMESTAMP,
            
            -- Diagnostic
            error_log TEXT
        )
    ''')
    
    # 2. AUTO-REPARARE (MIGRATIONS)
    # Asta rezolvă problema ta actuală ("no such column: descriere")
    # Încearcă să adauge coloana. Dacă există, ignoră eroarea.
    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN descriere TEXT")
        print("🔧 [DB UPDATE]: Am adăugat automat coloana lipsă 'descriere'.")
    except sqlite3.OperationalError:
        # Eroarea asta apare dacă coloana există deja. E de bine!
        pass

    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN titlu_video TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print(f"🏛️  [DATABASE]: Baza de date '{DB_NAME}' este verificată și completă.")

def adauga_video(url, link_afiliere, cont, titlu):
    """
    Adaugă o nouă misiune în registru.
    """
    conn = get_db_connection()
    if not conn: return

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO videos (sursa_url, affiliate_link, cont_target, titlu_video, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (url, link_afiliere, cont, titlu, datetime.datetime.now()))
        
        conn.commit()
        print(f"✅ [INSERT]: Video adăugat în coada pentru {cont}!")
        
    except sqlite3.IntegrityError:
        print("⚠️ [DUPLICAT]: Acest link există deja în sistem. Ignor.")
    except Exception as e:
        print(f"❌ [EROARE INSERT]: {e}")
    finally:
        conn.close()

def sterge_video(video_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id=?", (video_id,))
    conn.commit()
    conn.close()
    print(f"🗑️  [DELETE]: Video ID {video_id} șters.")

def vezi_statistici():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n════════════════════════════════════════")
    print("📊 RAPORT DE STARE IMPERIU")
    print("════════════════════════════════════════")
    
    cursor.execute("SELECT status, COUNT(*) FROM videos GROUP BY status")
    rows = cursor.fetchall()
    
    if not rows:
        print("📭 Baza de date este goală.")
    else:
        for row in rows:
            print(f" • {row['status'].upper()}: {row[1]} videoclipuri")

    print("\n--- DETALII COADA PENDING ---")
    cursor.execute("SELECT id, cont_target, titlu_video FROM videos WHERE status='pending'")
    pending = cursor.fetchall()
    for row in pending:
         print(f"ID [{row['id']}] | 🎯 {row['cont_target']} | 🎬 {row['titlu_video']}")
         
    print("════════════════════════════════════════\n")
    conn.close()

# --- INTERFAȚA DE COMANDĂ (CLI) ---
if __name__ == "__main__":
    initializeaza_db()
    
    while True:
        print("\n🎛️  CENTRUL DE COMANDĂ")
        print("1. ➕ Adaugă Video Nou")
        print("2. 📊 Vezi Statistici & Coada")
        print("3. ❌ Șterge un Video (după ID)")
        print("4. 👋 Ieșire")
        
        optiune = input("\nComanda ta, Sire? (1-4): ")
        
        if optiune == "1":
            url = input("🔗 Link Video (YouTube/TikTok): ").strip()
            if not url: continue
            cont = input("🎯 Cont (Gadgets/Home): ").strip()
            titlu = input("📝 Titlu (organizare): ").strip()
            link_af = input("💰 Link Afiliere (opțional): ").strip()
            adauga_video(url, link_af, cont, titlu)
            
        elif optiune == "2":
            vezi_statistici()
            
        elif optiune == "3":
            try:
                vid_id = input("🆔 ID-ul videoului de șters: ")
                sterge_video(vid_id)
            except:
                print("ID invalid.")

        elif optiune == "4":
            print("Sistem închis.")
            break
        else:
            print("Comandă necunoscută.")