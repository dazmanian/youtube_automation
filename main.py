import os
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    clear_screen()
    print("╔════════════════════════════════════════╗")
    print("║   🚀 YOUTUBE EMPIRE AUTOMATION V3.0    ║")
    print("║        (Poker Split Edition ♠️)         ║")
    print("╚════════════════════════════════════════╝")

def main_menu():
    while True:
        banner()
        print("\n🎛️  PANOU DE CONTROL:")
        print("1. 📥 [DOWNLOADER]:  Descarcă video brut")
        print("2. 🏭 [GENERATOR]:   Crează 5 variante (50/50 Poker Split)")
        print("3. 🚀 [UPLOADER]:    Postează automat (Scheduler API)")
        print("4. 🔧 [BACKUP]:      Upload Manual (Selenium)")
        print("5. 📊 [DATABASE]:    Vezi Statistici & Coada")
        print("6. ❌ Ieșire")
        
        choice = input("\nComanda ta > ")
        
        if choice == "1":
            print("\n🚀 Pornesc Downloader...")
            os.system("python downloader.py")
            input("\n✅ Apasă Enter să revii la meniu...")
            
        elif choice == "2":
            print("\n🏭 Pornesc Fabrica Video...")
            os.system("python video_generator.py")
            input("\n✅ Apasă Enter să revii la meniu...")
            
        elif choice == "3":
            print("\n🚀 Pornesc Uploader cu Scheduler...")
            print("⚠️ Scriptul va rula continuu și va posta la orele programate!")
            print("   15:00-17:00 și 00:00-02:00 (România)")
            input("Apasă Enter să continui...")
            os.system("python uploader.py")
            input("\n✅ Apasă Enter să revii la meniu...")
            
        elif choice == "4":
            print("\n🔧 Pornesc Upload Manual (Selenium - Backup)...")
            print("⚠️ ATENȚIE: Închide toate ferestrele Chrome înainte!")
            input("Apasă Enter dacă ai închis Chrome...")
            os.system("python upload_selenium.py")
            input("\n✅ Apasă Enter să revii la meniu...")

        elif choice == "5":
            os.system("python database.py")
            input("\n✅ Apasă Enter să revii la meniu...")
            
        elif choice == "6":
            print("Succes, CEO! 👋")
            break
        else:
            print("Comandă invalidă.")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()