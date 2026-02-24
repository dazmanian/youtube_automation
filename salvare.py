import sqlite3
import os

DB_NAME = "youtube_empire.db"
PATH_OUTPUT = "output_videos"

def recupereaza_videoclipuri():
    print("🚁 START MISIUNE DE SALVARE 🚁\n")
    
    # Ne asigurăm că tabelul există (în caz că tot nu a fost creat)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    
    # Căutăm clipurile în folder
    if not os.path.exists(PATH_OUTPUT):
        print(f"❌ Nu găsesc folderul {PATH_OUTPUT}!")
        return

    clipuri_gasite = [f for f in os.listdir(PATH_OUTPUT) if f.endswith(".mp4")]
    
    if not clipuri_gasite:
        print("❌ Nu am găsit niciun videoclip în folder!")
        return
        
    print(f"👀 Am găsit {len(clipuri_gasite)} videoclipuri nerefuzate. Hai să le înregistrăm!")
    
    # Îți cerem datele pe care le-a uitat
    titlu = input("📝 Nume Produs (ex: The Ultimate Home Hack!): ").strip()
    link = input("🔗 Link Afiliere Amazon: ").strip()
    cont = input("🎯 Cont Target: ").strip()
    sursa_video = input("🎥 Sursă Video (Link pentru Credit): ").strip()
    
    desc_SEO = f"""Get the {titlu} here! 🤯👇

🛒 GET THE LINK:
👉 Go to my Channel/Profile BIO!
(🔗 linktr.ee/GadgetHunterShop)


🌟 Why you need this gadget:
This is one of the best Amazon finds of 2026! If you love cool tech and home hacks, this video is for you. Don't forget to subscribe for daily product hunting!

🔍 Search Tags:
#shorts #amazonfinds #gadgets #tech #musthaves #tiktokmademebuyit #giftideas #productreview #poker #pokerstars #ggpoker #{cont}

🛑 Disclaimer:
As an Amazon Associate, I earn from qualifying purchases. This helps support the channel!

🎥 Video Credit: {sursa_video}
"""

    count = 0
    for clip in clipuri_gasite:
        cale_completa = os.path.join(PATH_OUTPUT, clip)
        
        # Verificăm să nu îl dublăm dacă era deja în DB
        cursor.execute("SELECT id FROM videos WHERE cale_fisier=?", (cale_completa,))
        if cursor.fetchone():
            print(f"⏭️ {clip} este deja în baza de date. Trecem peste.")
            continue
            
        # Îl băgăm în baza de date (Folosim sursa_video și la coloana sursa_url)
        cursor.execute("""
            INSERT INTO videos (sursa_url, affiliate_link, cont_target, titlu_video, descriere, cale_fisier, status) 
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (sursa_video, link, cont, titlu, desc_SEO, cale_completa))
        
        count += 1
        print(f"✅ Inregistrat cu succes: {clip}")

    conn.commit()
    conn.close()
    print(f"\n🎉 MISIUNE ÎNDEPLINITĂ! Am recuperat {count} videoclipuri în sistem.")

if __name__ == "__main__":
    recupereaza_videoclipuri()