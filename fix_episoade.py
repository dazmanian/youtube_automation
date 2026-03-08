import sqlite3

conn = sqlite3.connect("youtube_empire.db")

# Afișăm situația curentă
print("\n📋 ULTIMELE 5 CLIPURI UPLOADATE:")
rows = conn.execute("""
    SELECT id, titlu_video, numar_episod 
    FROM videos 
    WHERE status = 'uploaded' 
    ORDER BY id DESC 
    LIMIT 5
""").fetchall()

for r in rows:
    print(f"  ID:{r[0]} | E{r[1]} | {r[2]}")

# Input interactiv
episod = input("\n⏱️  Setează ultimul episod uploadat la: ").strip()

if episod.isdigit():
    conn.execute("UPDATE videos SET numar_episod = ? WHERE status = 'uploaded'", (int(episod),))
    conn.commit()
    print(f"✅ Toate clipurile uploadate setate la E{episod}. Următorul va fi E{int(episod)+1}.")
else:
    print("❌ Număr invalid!")

conn.close()