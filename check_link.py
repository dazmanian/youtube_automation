import sqlite3

# Conectare
conn = sqlite3.connect("youtube_empire.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Luăm ultimul video urcat
cursor.execute("SELECT id, titlu_video, affiliate_link FROM videos ORDER BY id DESC LIMIT 1")
row = cursor.fetchone()

print("\n🔍 DIAGNOSTIC VIDEO:")
if row:
    print(f"🆔 ID: {row['id']}")
    print(f"🎬 Titlu: {row['titlu_video']}")
    print(f"🔗 Link Afiliere: '{row['affiliate_link']}'") # Vezi dacă e gol între ghilimele!
    
    if not row['affiliate_link']:
        print("❌ EROARE: Câmpul de link este GOL sau NULL!")
    else:
        print("✅ Link-ul există în bază.")
else:
    print("Nu am găsit niciun video.")

conn.close()
input("\nApasă Enter...")